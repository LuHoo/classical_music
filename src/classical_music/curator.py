"""Record curator decisions locally; run ./curator finish to validate the batch.

Defaults: apply locally, curator LAH. Use --dry-run for a write-free plan.
No Git, GitHub or TIDAL writes; historical source occurrences are immutable.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
import getpass
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import sys
import threading
import time

from ruamel.yaml import YAML

from classical_music.chamber_import import audit, validate_decision_records
from classical_music.playlist_choices import locate as locate_intake, refresh_window, update_report

ISSUES = 'https://github.com/LuHoo/classical_music/issues/'


class CuratorError(ValueError):
    """An unsafe, ambiguous or unsupported decision."""


def locate(root, issue):
    try:
        return locate_intake(root, issue)
    except ValueError as exc:
        raise CuratorError(str(exc)) from exc


def require(condition, message):
    if not condition:
        raise CuratorError(message)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def yaml_bytes(value):
    stream = io.StringIO()
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(value, stream)
    return stream.getvalue().encode()


def safe_path(root, relative):
    relative = Path(relative)
    require(not relative.is_absolute() and '..' not in relative.parts,
            f'Unsafe repository path: {relative}')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()), f'Path escapes repository: {relative}')
    return path


def find_choice(manifest, issue):
    url = ISSUES + str(issue)
    matches = [(c, resolved) for key, resolved in [('recommendation_choices', False), ('resolved_choices', True)]
               for c in manifest.get(key, []) if c['issue_url'] == url]
    require(len(matches) == 1, f'Issue #{issue} must identify exactly one registered curator choice.')
    return matches[0]


def resolve_choice(choice, token):
    aliases = choice.get('choice_aliases', {})
    require(all(v in choice['units'] or v == 'existing' for v in aliases.values()),
            'Invalid choice_aliases in manifest.')
    token = token.upper() if token.lower() != 'existing' else 'existing'
    selected = aliases.get(token, token)
    require(selected in choice['units'] or selected == 'existing' and choice['existing_performances'],
            'Unknown/unsupported choice. Use one of: ' + ', '.join([*aliases, *choice['units']] +
            (['existing'] if choice['existing_performances'] else [])))
    return selected


def refresh_summary(manifest):
    for status in manifest['summary']:
        units = [u for u in manifest['units'] if u['disposition'] == status]
        manifest['summary'][status] = dict(units=len(units),
            track_occurrences=sum(len(u['positions']) for u in units),
            distinct_performances=len({u['performance_id'] for u in units if u.get('performance_id')}))


def update_readme(text, manifest, issue, selected):
    for status, summary in manifest['summary'].items():
        text, n = re.subn(r'^\| ' + re.escape(status) + r' \|.*$',
                         f"| {status} | {summary['units']} | {summary['track_occurrences']} |", text, flags=re.M)
        require(n == 1, f'Cannot locate README summary row {status}.')
    counts = dict(Counter(r['entity'] for r in manifest['new_records']))
    if 'version_choice_issues' in manifest:
        text, n = re.subn(r"New records: .*?\. Existing recordings reused: \d+\.",
            f"New records: {counts}. Existing recordings reused: {manifest['summary']['reuse_existing']['distinct_performances']}.", text)
        require(n == 1, 'Cannot locate Piano README canonical counts.')
        text, n = re.subn(r'\*\*\d+ pending Work-level issues:\*\*.*? Answer',
            f"**{len(manifest['recommendation_choices']) + len(manifest['version_choice_issues'])} pending Work-level issues:** "
            f"{len(manifest['recommendation_choices'])} recommendation comparisons and "
            f"{len(manifest['version_choice_issues'])} version research issues. Answer", text)
        require(n == 1, 'Cannot locate Piano README pending count.')
        pattern = r'^(\| \[#' + str(issue) + r'\].*?) \|$'
        text, n = re.subn(pattern, lambda m: m[1] + f' **Resolved: {selected}** |', text, flags=re.M)
        require(n == 1, 'Cannot locate Piano README issue row.')
        return text
    text, n = re.subn(r"New canonical records: .*?\. Reuse covers \d+ existing Performances\.",
        f"New canonical records: {counts}. Reuse covers {manifest['summary']['reuse_existing']['distinct_performances']} existing Performances.", text)
    require(n == 1, 'Cannot locate README canonical counts.')
    text, n = re.subn(r'\*\*\d+ pending Work-level decisions\*\*',
                     f"**{len(manifest['recommendation_choices'])} pending Work-level decisions**", text)
    require(n == 1, 'Cannot locate README pending count.')
    pattern = r'^(\| \[#' + str(issue) + r'\].*?) \|$'
    text, n = re.subn(pattern, lambda m: m[1] + f' **Resolved: {selected}** |', text, flags=re.M)
    require(n == 1, 'Cannot locate README issue row.')
    return text


def plan_decision(root, issue, token, *, curator, decision_url=None,
                  replace_existing=False, playlist_remove=False):
    intake, manifest_path, manifest = locate(root, issue)
    choice, resolved = find_choice(manifest, issue)
    require(len(choice['units']) == len(set(choice['units'])), 'Repeated candidate units.')
    selected = resolve_choice(choice, token)
    units = {u['unit_id']: u for u in manifest['units'] if u.get('unit_id')}
    require(len(units) == len(manifest['units']) if intake.format != 'window' else
            len([u['unit_id'] for u in manifest['units'] if u.get('unit_id')]) ==
            len({u['unit_id'] for u in manifest['units'] if u.get('unit_id')}), 'Duplicate unit IDs.')
    candidates = [units[uid] for uid in choice['units']]
    require(all(u['work_id'] == choice['work_id'] and u.get('curator_issue') == choice['issue_url']
                for u in candidates), 'Candidate Work/issue mismatch.')
    source_url = manifest['source'].get('url') or 'https://tidal.com/playlist/' + manifest['source']['playlist_id']
    source_name = manifest['source'].get('name', intake.key)
    existing = choice['existing_performances']
    if selected == 'existing':
        require(len(existing) == 1, 'Multiple existing recommendations require a profiled decision.')
        selected_units = [u['unit_id'] for u in candidates if u.get('performance_id') == existing[0]]
    else:
        selected_units = [selected]
    if resolved:
        decision = choice['decision']
        require(decision['choice'] == 'selected_performance' and
                decision['selected_units'] == selected_units,
                'Issue already resolved with a different decision; review it manually.')
        record_path = safe_path(root, decision['implementation_record'])
        record = json.loads(record_path.read_text())
        require(record.get('issue_url') == choice['issue_url'],
                'Legacy grouped decision requires manual review; it is not an individual CLI record.')
        require(not playlist_remove or record.get('playlist_change'),
                'Decision already recorded without a playlist action; do not silently add one on retry.')
        return {}, record, 'Already recorded; no changes.'
    require(len(existing) <= 1, 'Multiple existing recommendations require a profiled decision.')
    require(all(u['disposition'] in ('recommendation_choice', 'reuse_existing') for u in candidates),
            'Candidate is not pending or reusable.')
    require(not choice.get('decision'), 'Pending choice already contains a decision.')
    if decision_url:
        require(re.fullmatch(re.escape(choice['issue_url']) + r'#issuecomment-\d+', decision_url),
                'Decision URL must be a comment on this issue.')
    record_relative = f'reports/curator-decisions/issue-{issue}.json'
    require(not (root / record_relative).exists(), 'Decision record already exists without a resolved manifest entry.')
    reference = decision_url or record_relative
    yaml = YAML(typ='safe')
    performances = {}
    performance_paths = {}
    for path in (root / 'data/performances').glob('*.yaml'):
        p = yaml.load(path.read_text())
        require(p['id'] not in performances, 'Duplicate canonical Performance ID.')
        performances[p['id']] = p
        performance_paths[p['id']] = path.relative_to(root)
    actual_existing = {p['id'] for p in performances.values() if p['work_id'] == choice['work_id']}
    require(actual_existing == set(existing), 'Existing recommendations differ from the reviewed choice.')
    selected_unit = units[selected_units[0]] if selected_units else None
    reuse_id = (selected_unit or {}).get('performance_id') or (existing[0] if selected == 'existing' else None)
    removed = set(existing) - ({reuse_id} if reuse_id else set())
    require(not removed or replace_existing,
            'This replaces an existing recommendation. Review the choice and pass --replace-existing explicitly.')
    other_source_track_ids = []
    # Refuse to invalidate another intake or another unit that shares the record.
    for path in (root / 'reports/playlist-import').rglob('*.json'):
        other = json.loads(path.read_text())
        if not isinstance(other, dict):
            continue
        other_source = other.get('source', {})
        other_url = other_source.get('url') or ('https://tidal.com/playlist/' + other_source['playlist_id']
                                               if other_source.get('playlist_id') else None)
        if path != root / manifest_path and other_url == source_url:
            other_source_track_ids.extend(t['id'] for u in other.get('units', []) for t in u.get('tracks', []))
        for unit in other.get('units', []):
            if path == root / manifest_path and unit.get('unit_id') in choice['units']:
                continue
            require(not (intake.format == 'window' and path.parent == (root / manifest_path).parent
                         and unit.get('work_id') == choice['work_id'] and
                         unit.get('disposition') == 'recommendation_choice'),
                    'Work has candidates in another window; register a reviewed consolidated intake first.')
            require(unit.get('performance_id') not in removed,
                    'Replaced Performance is referenced by another import unit; manual review required.')
    changes = {}
    archived = []
    for pid in sorted(removed):
        archived.append(performances[pid])
        changes[str(performance_paths[pid])] = None
        manifest['changed_existing'].append(dict(id=pid,
            **{('entity_type' if intake.format == 'window' else 'entity'): 'performances'},
            path=str(performance_paths[pid]), action='removed_by_curator', decision_record=record_relative))
    if reuse_id:
        perf = performances[reuse_id]
        pid = reuse_id
    else:
        require(selected_unit is not None, 'No selected source unit.')
        pid = choice['work_id'] + '-' + intake.key + '-' + selected.lower()
        require(re.fullmatch(r'[a-z0-9-]+', pid), 'Unsafe Performance ID.')
        path = f'data/performances/{pid}.yaml'
        require(not (root / path).exists() and pid not in performances, 'Performance already exists.')
        perf = dict(id=pid, work_id=choice['work_id'], performers=deepcopy(selected_unit.get('performers') or selected_unit.get('candidate_performers')),
                    links={'tidal': {'url': 'https://tidal.com/track/' + selected_unit.get('listening_track_id', selected_unit['tracks'][0]['id'])}},
                    release={'album_title': selected_unit['tracks'][0]['album_titles'][0]},
                    source={'file': str(manifest_path), 'url': source_url,
                            'unit_id': selected, 'curator_decision': reference})
        for field in ('excerpt', 'profile', 'version_assignment'):
            if selected_unit.get(field):
                perf[field] = selected_unit[field]
        require(perf['performers'] and all(isinstance(p, dict) and p.get('name') for p in perf['performers']),
                'Candidate needs reviewed performers (names and optional roles).')
        require(selected_unit.get('listening_track_id', selected_unit['tracks'][0]['id']) in
                {t['id'] for t in selected_unit['tracks']}, 'Listening anchor outside source unit.')
        changes[path] = yaml_bytes(perf)
        manifest['new_records'].append(dict(id=pid, path=path,
            **{('entity_type' if intake.format == 'window' else 'entity'): 'performances'}))
    not_selected = [uid for uid in choice['units'] if uid not in selected_units]
    for unit in candidates:
        accepted = unit['unit_id'] in selected_units
        unit['disposition'] = ('reuse_existing' if reuse_id else 'import_new') if accepted else 'not_selected'
        unit['review_classification'] = 'curator_accepted' if accepted else 'curator_not_selected'
        unit['reason'] = f'Curator selected {selected}; ' + ('all source movements included.' if accepted else 'retained as historical source evidence.')
        unit['curator_decision'] = reference
        if accepted:
            unit['performance_id'] = pid
        else:
            unit.pop('performance_id', None)
    decision = dict(choice='selected_performance', selected_units=selected_units,
                    not_selected_units=not_selected,
                    performances=[dict(performance_id=pid, profile=perf.get('profile'),
                        unit_id=selected_units[0] if selected_units else None,
                        tidal_url=perf['links']['tidal']['url'])],
                    implementation_report=str(manifest_path), implementation_record=record_relative,
                    decision_record=record_relative)
    if decision_url:
        decision['comment_url'] = decision_url
    choice['decision'] = decision
    manifest['recommendation_choices'].remove(choice)
    manifest.setdefault('resolved_choices', []).append(choice)
    record = dict(issue_url=choice['issue_url'], decision_source='curator_cli',
                  curator=curator, recorded_at=datetime.now(timezone.utc).isoformat(),
                  requested_choice=token, choice=selected, selected_units=selected_units, not_selected_units=not_selected,
                  performance_id=pid, implementation_pr=None, replaced_performances=archived)
    if decision_url:
        record['comment_url'] = decision_url
    if playlist_remove:
        require(not_selected, 'No unselected source units to remove.')
        rejected = [units[uid] for uid in not_selected]
        removed_ids = [t['id'] for u in rejected for t in u['tracks']]
        require(len(removed_ids) == len(set(removed_ids)),
                'Repeated removal IDs require manual occurrence-level review.')
        preserved_ids = [t['id'] for u in manifest['units'] if u.get('unit_id') not in not_selected for t in u['tracks']]
        require(not set(removed_ids) & set(preserved_ids + other_source_track_ids),
                'Removal shares track IDs with preserved occurrences; manual occurrence-level review required.')
        record['playlist_change'] = dict(status='pending', method='manual',
            authorization='Curator requested manual removal instructions with --playlist-remove-unselected.',
            playlist_url=source_url, playlist_name=source_name,
            work=choice['title'],
            actions=[dict(unit_id=u['unit_id'], performers=u.get('performers') or u.get('candidate_performers'),
                          track_ids=[t['id'] for t in u['tracks']], source_snapshot_positions=u['positions']) for u in rejected],
            planned_removed_track_ids=removed_ids,
            preserved_selected_track_ids=[t['id'] for uid in selected_units for t in units[uid]['tracks']])
    if intake.format == 'window':
        refresh_window(manifest)
    else:
        refresh_summary(manifest)
    changes[str(manifest_path)] = json_bytes(manifest)
    changes[record_relative] = json_bytes(record)
    readme = str(intake.report(manifest_path))
    text = (root / readme).read_text()
    changes[readme] = (update_report(text, manifest, intake) if intake.format == 'window' else
                       update_readme(text, manifest, issue, selected)).encode()
    return changes, record, (f'Issue #{issue}: {token} → {selected}; recommendation {pid}\n'
                             f'Not selected: {", ".join(not_selected) or "none"}')


def plan_playlist_done(root, issue, *, curator, note):
    intake, manifest_path, manifest = locate(root, issue)
    choice, resolved = find_choice(manifest, issue)
    require(resolved, 'Record a curator decision before confirming the playlist action.')
    relative = choice['decision'].get('implementation_record', '')
    require(relative, 'No individual decision record; review the legacy decision manually.')
    record = json.loads(safe_path(root, relative).read_text())
    require(record.get('issue_url') == choice['issue_url'],
            'Legacy grouped decision requires manual review; it is not an individual CLI record.')
    action = record.get('playlist_change', {})
    require(action, 'No manual playlist action was recorded.')
    if action.get('status') == 'done' or action.get('removed_track_ids') and not action.get('status'):
        return {}, record, 'Playlist action already recorded; no changes.'
    require(action.get('status') == 'pending', 'No pending playlist action.')
    require(note and note.strip(), 'Provide --note describing what you checked in the playlist.')
    action.update(status='done', confirmed_by=curator,
                  confirmed_at=datetime.now(timezone.utc).isoformat(),
                  verification=note, verification_type='curator_reported',
                  removed_track_ids=action['planned_removed_track_ids'])
    return {relative: json_bytes(record)}, record, f'Issue #{issue}: record curator-reported playlist completion.'


def manual_instructions(record):
    action = record.get('playlist_change')
    if not action:
        return 'No playlist action requested. TIDAL is unchanged.'
    if action.get('status') != 'pending':
        return 'Playlist completion already recorded (no live verification by this CLI).'
    lines = [f"Manual action — {action['playlist_name']}: {action['playlist_url']}",
             f"Work: {action['work']}. Check the current playlist before removing:"]
    for item in action['actions']:
        names = ', '.join(p['name'] for p in item['performers'])
        lines.append(f"  {item['unit_id']} — {names}: exact track IDs {', '.join(item['track_ids'])}")
    if action['preserved_selected_track_ids']:
        lines.append('Keep selected track IDs: ' + ', '.join(action['preserved_selected_track_ids']))
    else:
        lines.append('Keep the existing canonical recommendation; it is outside this source snapshot.')
    issue = record['issue_url'].rsplit('/', 1)[1]
    lines.append(f'After completing and checking: ./curator {issue} playlist-done --apply --note "what you checked"')
    return '\n'.join(lines)


def install_changes(root, changes, expected):
    """Optimistic concurrency check and rollback on ordinary write failures."""
    for relative, before in expected.items():
        path = safe_path(root, relative)
        require((path.read_bytes() if path.exists() else None) == before,
                f'File changed during preview: {relative}; rerun.')
    written = []
    try:
        for relative, content in changes.items():
            path = safe_path(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            written.append(relative)
            if content is None:
                path.unlink()
            else:
                # Same-filesystem replacement prevents partially written individual files.
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(content)
                try:
                    os.chmod(temporary, path.stat().st_mode & 0o777 if path.exists() else 0o644)
                    os.replace(temporary, path)
                finally:
                    temporary.unlink(missing_ok=True)
    except BaseException:
        for relative in reversed(written):
            path = root / relative
            if expected[relative] is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(expected[relative])
        raise


def input_snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for directory in
            ('data', 'reports/curator-decisions', 'reports/playlist-import', 'docs', 'side materials')
            for p in (root / directory).rglob('*') if p.is_file()}



@contextmanager
def cli_progress(interval=10):
    """Flush phase changes and periodic liveness messages to stderr, even in a pipe."""
    stopped = threading.Event()
    lock = threading.Lock()
    started = time.monotonic()
    phase = ['Voorbereiden']

    def report(message):
        with lock:
            phase[0] = message
            print(f'curator: {message}', file=sys.stderr, flush=True)

    def heartbeat():
        while not stopped.wait(interval):
            with lock:
                elapsed = int(time.monotonic() - started)
                print(f'curator: nog bezig — {phase[0]} (totaal {elapsed} s)',
                      file=sys.stderr, flush=True)

    worker = threading.Thread(target=heartbeat, name='curator-progress', daemon=True)
    worker.start()
    try:
        yield report
    finally:
        stopped.set()
        worker.join()


def execute(root, issue, token, *, apply=False, curator=None, decision_url=None,
            replace_existing=False, playlist_remove=False, note=None, progress=None):
    report = progress or (lambda message: None)
    report("Apply voorbereiden; schrijven gebeurt pas na geslaagde controles." if apply else
           "Preview gestart; er wordt niets opgeslagen.")
    require(__debug__, 'Python optimization disables repository audit assertions; run without -O.')
    curator = curator or getpass.getuser()
    require(curator.strip(), 'Curator identity is required.')
    root = root.resolve()
    report(f'Issue #{issue} en keuze {token} opzoeken')
    intake, manifest_path, _ = locate(root, issue)
    # Serialize CLI writers. Preview itself leaves no persistent files in the repository.
    lock = root / '.curator.lock'
    descriptor = None
    try:
        if apply:
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise CuratorError('Another curator apply is running (.curator.lock).') from exc
        report('Brongegevens lezen')
        if token == 'playlist-done':
            baseline = {str(manifest_path): (root / manifest_path).read_bytes()}
            baseline.update({str(p.relative_to(root)): p.read_bytes()
                             for p in (root / 'reports/curator-decisions').glob('*.json')})
        else:
            baseline = input_snapshot(root)
        report('Voorgestelde wijzigingen bepalen')
        if token == 'playlist-done':
            require(not (decision_url or replace_existing or playlist_remove), 'Decision flags do not apply to playlist-done.')
            changes, record, message = plan_playlist_done(root, issue, curator=curator, note=note)
        else:
            require(not note, '--note is only for playlist-done.')
            changes, record, message = plan_decision(root, issue, token, curator=curator,
                decision_url=decision_url, replace_existing=replace_existing, playlist_remove=playlist_remove)
        if not changes:
            return message + '\n' + manual_instructions(record)
        expected = dict(baseline)
        for relative in changes:
            expected.setdefault(relative, None)
        report('Tijdelijke validatiebestanden voorbereiden')
        with tempfile.TemporaryDirectory(prefix='curator-preview-') as folder:
            stage = Path(folder)
            for relative, content in expected.items():
                if content is not None:
                    path = safe_path(stage, relative)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
            for relative, content in changes.items():
                path = safe_path(stage, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                if content is None:
                    path.unlink()
                else:
                    path.write_bytes(content)
            # Reuse the inventory/publication fast path, without the broad identity scan.
            report('Beslisrecord controleren' if token == 'playlist-done' else
                   'Brongegevens en publicatie controleren; dit kan enkele minuten duren')
            if token == 'playlist-done':
                validate_decision_records(json.loads((stage / manifest_path).read_text()), stage)
            else:
                with redirect_stdout(io.StringIO()):
                    if intake.key == 'chamber':
                        audit(stage)
                    else:
                        intake.audit(stage, manifest_path)
            report('Resultaten vergelijken')
            for path in (stage / 'publication').rglob('*.md'):
                relative = str(path.relative_to(stage))
                target = safe_path(root, relative)
                before = target.read_bytes() if target.exists() else None
                if before != path.read_bytes():
                    expected[relative] = before
                    changes[relative] = path.read_bytes()
            # Also check that the affected Work renders the chosen anchor, including reuse.
            manifest = json.loads((stage / manifest_path).read_text())
            choice, _ = find_choice(manifest, issue)
            page = stage / 'publication/works' / (choice['work_id'] + '.md')
            if token != 'playlist-done':
                for perf in choice['decision']['performances']:
                    require(perf['tidal_url'] in page.read_text(), 'Selected recommendation missing from publication.')
            if apply:
                report('Controleren of bronbestanden intussen zijn gewijzigd')
                if token != 'playlist-done':
                    require(input_snapshot(root) == baseline, 'Repository inputs changed during validation; rerun.')
                report('Gevalideerde wijzigingen opslaan')
                install_changes(root, changes, expected)
        files = [p for p in changes if not p.startswith('publication/')]
        return ('Applied: ' if apply else 'Preview only: ') + message + '\n' + \
            ('Decision record validation passed.\n' if token == 'playlist-done' else
             'Inventory and publication validation passed.\n') + '\n'.join(('  DELETE ' if changes[p] is None else '  WRITE ') + p for p in files) + \
            '\n' + manual_instructions(record)
    finally:
        if descriptor is not None:
            os.close(descriptor)
            lock.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='./curator', description=__doc__)
    parser.add_argument('issue', help='Issue number, or finish to validate the batch')
    parser.add_argument('choice', nargs='?', help='Registered alias, source unit (C/P/etc.), existing, or playlist-done')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true', help='Record locally (default); validate later with finish')
    mode.add_argument('--dry-run', action='store_true', help='Plan only; do not write or run the final checks')
    parser.add_argument('--curator', default='LAH', help='Decision/confirmation author (default: LAH)')
    parser.add_argument('--decision-url', help='Optional existing decision comment on this issue')
    parser.add_argument('--replace-existing', action='store_true')
    parser.add_argument('--playlist-remove-unselected', action='store_true', help='Record manual removal instructions; never call TIDAL')
    parser.add_argument('--note', help='Required verification note for playlist-done')
    args = parser.parse_args(argv)
    from classical_music.curator_batch import record_decision, finish
    if args.issue == 'finish':
        if (args.choice or args.apply or args.dry_run or args.decision_url or
                args.replace_existing or args.playlist_remove_unselected or args.note):
            parser.error('finish takes no choice or decision flags')
        issue = None
    else:
        try:
            issue = int(args.issue)
        except ValueError:
            parser.error('Supply a positive issue number or finish')
        if issue <= 0 or args.choice is None:
            parser.error('Supply a positive issue number and a choice')
    try:
        with cli_progress() as progress:
            if issue is None:
                result = finish(Path(__file__).resolve().parents[2], progress=progress)
            else:
                result = record_decision(Path(__file__).resolve().parents[2], issue, args.choice,
                    apply=not args.dry_run, curator=args.curator, decision_url=args.decision_url,
                    replace_existing=args.replace_existing, playlist_remove=args.playlist_remove_unselected,
                    note=args.note, progress=progress)
        print(result)
    except (ValueError, AssertionError, OSError, KeyError, RuntimeError) as exc:
        parser.exit(2, f'curator: {exc}\n')
    return 0
