#!/usr/bin/env python3
"""Apply a curator decision on an earmarked candidate-review issue (#316/#318 flow).

The earmarked workflow (register_earmarked_recording.py) registers a candidate
recording and opens a comparison issue, but had no sanctioned route to process
the curator decision. This script closes that gap. It promotes a reviewed
candidate to the recommended performance of a work — or rejects it — using the
same record vocabulary as ./curator, so that ./curator finish keeps passing.

Default is apply: use --dry-run for a write-free plan. The script never talks
to GitHub or TIDAL and performs no playlist actions.

Promote (--choice CODE, not "existing"):
  1. new performance data/performances/<work_id>-earmarked-<code>.yaml;
  2. the single existing performance of the work (if any) is removed, and
     every intake manifest that imported it is updated with the standard
     removal vocabulary: unit disposition "not_selected", a resolved choice
     that attributes the new performance, pruned new_records, an entry in
     changed_existing with action "removed_by_curator", recomputed summary;
  3. the docs/*.md recommendation anchor for the replaced track is rewritten
     to the new performers and track URL;
  4. the data/recordings/ work entry flips status candidate -> recommended
     with the listening track link;
  5. decision record reports/curator-decisions/issue-<n>.json (schema shared
     with the curator CLI, decision_source "curator_cli");
  6. reports/curator-decisions/batch-status.json returns to status "pending".

Reject (--choice existing): decision record + recording work entry status
"not_selected"; canonical data is untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from ruamel.yaml import YAML

ISSUES = 'https://github.com/LuHoo/classical_music/issues/'
BATCH_STATUS = Path('reports/curator-decisions/batch-status.json')
ID_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
TRACK_URL = re.compile(r'^(?:https?://)?(?:www\.)?tidal\.com/(?:browse/)?track/([0-9]+)(?:[/?].*)?$')
MANIFEST_VOCABULARY = {'schema_version', 'source', 'summary', 'units', 'new_records',
                       'changed_existing', 'recommendation_choices', 'resolved_choices'}


def require(condition, message):
    if not condition:
        raise SystemExit('ERROR: ' + message)


def yaml_load(path):
    return YAML(typ='safe').load(path.read_text(encoding='utf-8'))


def emit_scalar(value):
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    text = str(value)
    if text == '' or re.search(r':(\s|$)', text) or ' #' in text or '#' in text and ' ' in text \
            or text[0] in '-!&*<>|%@`{}[],' or text != text.strip() \
            or text.startswith(("'", '"')) or '\n' in text:
        return "'" + text.replace("'", "''") + "'"
    return text


def emit_performance(perf):
    lines = [f'id: {perf["id"]}', f'work_id: {perf["work_id"]}', 'performers:']
    for person in perf['performers']:
        lines.append(f'  - name: {emit_scalar(person["name"])}')
        if person.get('role'):
            lines.append(f'    role: {emit_scalar(person["role"])}')
    lines.append('links:')
    lines.append('  tidal:')
    lines.append(f'    url: {emit_scalar(perf["links"]["tidal"]["url"])}')
    if perf.get('release'):
        lines.append('release:')
        lines.append(f'  album_title: {emit_scalar(perf["release"]["album_title"])}')
    lines.append('source:')
    for key, value in perf['source'].items():
        lines.append(f'  {key}: {emit_scalar(value)}')
    return '\n'.join(lines) + '\n'


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def parse_performer(text):
    text = text.strip()
    match = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', text)
    if match:
        name, role = match.group(1).strip(), match.group(2).strip()
    else:
        name, role = text, ''
    require(name, 'Empty performer name')
    return {'name': name, **({'role': role} if role else {})}



def update_recording(text, work_id, new_status, note, links_block):
    """Surgical status/links/notes update of one works entry; preserves formatting."""
    lines = text.split('\n')
    start = None
    for index, line in enumerate(lines):
        if re.match(r'^(\s*)- work_id: ' + re.escape(work_id) + r'\s*$', line):
            start = index
            indent = len(re.match(r'^(\s*)', line).group(1))
            break
    require(start is not None, f'Work entry {work_id} not found in recording')
    end = start + 1
    while end < len(lines):
        stripped = lines[end]
        if stripped.strip() and not stripped.startswith(' ' * (indent + 1)):
            break
        end += 1
    region = lines[start:end]
    flipped = False
    for index, line in enumerate(region):
        if re.match(r'^\s+status: candidate\s*$', line):
            region[index] = re.sub(r'status: candidate', 'status: ' + new_status, line, count=1)
            flipped = True
            break
    require(flipped, f'Status line of {work_id} not found in recording entry')
    insert_at = len(region)
    for index, line in enumerate(region):
        match = re.match(r'^(\s+)notes:[ \t]*(.*)$', line)
        if match and index > 0:
            existing = match.group(2).strip()
            require(existing and 'notes:' not in existing, 'Multi-line notes need manual merge')
            require(not existing.startswith(('>', '|')), 'Folded notes need manual merge')
            if len(existing) >= 2 and existing[0] == existing[-1] == "'":
                existing = existing[1:-1].replace("''", "'")
            region[index] = match.group(1) + 'notes: ' + \
                emit_scalar(existing + ' ' + note)
            insert_at = index
            break
    additions = [line for line in links_block.split('\n') if line]
    if insert_at == len(region):
        region.extend('  ' + line for line in additions)
        region.append('  notes: ' + emit_scalar(note))
    else:
        region[insert_at:insert_at] = ['  ' + line for line in additions]
    lines[start:end] = region
    return '\n'.join(lines)


def tidal_track_id(performance):
    links = performance.get('links')
    entries = links if isinstance(links, list) else [links.get('tidal')] if isinstance(links, dict) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        url = entry.get('url')
        match = url and TRACK_URL.match(url.strip())
        if match:
            return match.group(1)
    return None


def track_id_of(url):
    match = url and TRACK_URL.match(url.strip())
    require(match, f'Not a TIDAL track URL: {url!r}')
    return match.group(1)


def load_performances(root):
    performances, paths = {}, {}
    for path in sorted((root / 'data/performances').glob('*.yaml')):
        data = yaml_load(path)
        require(isinstance(data, dict) and data.get('id') and data.get('work_id'),
                f'Incomplete performance file: {path.name}')
        require(data['id'] not in performances, f'Duplicate performance ID: {data["id"]}')
        performances[data['id']] = data
        paths[data['id']] = path.relative_to(root)
    return performances, paths


def find_recording_candidate(root, work_id):
    hits = []
    for path in sorted((root / 'data/recordings').glob('*.y*ml')):
        data = yaml_load(path)
        if not isinstance(data, dict):
            continue
        for entry in data.get('works') or []:
            if isinstance(entry, dict) and entry.get('work_id') == work_id:
                hits.append((path, entry))
    require(hits, f'No data/recordings/ entry references work {work_id}')
    require(len(hits) == 1, f'Work {work_id} appears in multiple recordings; manual review required')
    path, entry = hits[0]
    require(entry.get('status') == 'candidate',
            f'Recording entry for {work_id} has status {entry.get("status")!r}, not candidate')
    return path.relative_to(root), entry


def docs_anchor_lines(root, track_id):
    pattern = re.compile(r'\[[^\]]*\]\(\s*(?:https?://)?(?:www\.)?tidal\.com/track/'
                         + track_id + r'[^\)]*\)')
    hits = []
    for path in sorted((root / 'docs').glob('*.md')):
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if pattern.search(line):
                hits.append((path.relative_to(root), number, line, pattern))
    return hits


def referencing_manifests(root, performance_id):
    """Intake manifests whose units/new_records/resolved choices reference the id."""
    hits = []
    for path in sorted((root / 'reports/playlist-import').rglob('*.json')):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(manifest, dict) or 'units' not in manifest:
            continue
        referenced = any(u.get('performance_id') == performance_id for u in manifest['units'])
        referenced = referenced or any(r['id'] == performance_id
                                       for r in manifest.get('new_records') or [])
        referenced = referenced or any(p.get('performance_id') == performance_id
                                      for c in manifest.get('resolved_choices') or []
                                      for p in (c.get('decision') or {}).get('performances') or [])
        if referenced:
            hits.append((path.relative_to(root), manifest))
    return hits


def manifest_is_supported(manifest):
    """The chamber/piano snapshot vocabulary; window manifests need manual review."""
    return MANIFEST_VOCABULARY <= set(manifest)


def recompute_summary(manifest):
    for status, summary in manifest['summary'].items():
        selected = [u for u in manifest['units'] if u['disposition'] == status]
        summary['units'] = len(selected)
        summary['track_occurrences'] = sum(len(u['positions']) for u in selected)
        summary['distinct_performances'] = len(
            {u['performance_id'] for u in selected if u.get('performance_id')})


def plan_manifest_update(manifest_path, manifest, unit_ids, removed_pid,
                         work_id, new_pid, tidal_url, issue, record_relative):
    """Update one intake manifest with the standard curator-removal vocabulary."""
    reference = record_relative
    for uid in unit_ids:
        unit = next(u for u in manifest['units'] if u.get('unit_id') == uid)
        require(unit.get('disposition') in ('import_new', 'reuse_existing'),
                f'Unit {uid} in {manifest_path} is {unit.get("disposition")!r}; '
                'removing its performance requires manual review')
        unit['disposition'] = 'not_selected'
        unit['review_classification'] = 'curator_not_selected'
        unit['curator_decision'] = reference
        unit['reason'] = (f'Earmarked curator decision #{issue}: the reviewed candidate '
                          'replaces this recommendation; retained as historical source evidence.')
        unit.pop('performance_id', None)
    manifest['new_records'] = [r for r in manifest.get('new_records') or []
                               if not (r.get('id') == removed_pid and r.get('entity') == 'performances')]
    already = [c for c in manifest.get('resolved_choices') or []
               if c.get('work_id') == work_id]
    require(not already, f'{manifest_path} already has a resolved choice for {work_id}')
    title = next((u.get('title') for u in manifest['units'] if u.get('unit_id') in unit_ids),
                 work_id)
    manifest.setdefault('resolved_choices', []).append({
        'work_id': work_id, 'title': title, 'units': list(unit_ids),
        'existing_performances': [removed_pid],
        'issue_url': ISSUES + str(issue),
        'decision': {
            'choice': 'selected_performance', 'selected_units': [],
            'not_selected_units': list(unit_ids),
            'performances': [{'performance_id': new_pid, 'profile': None,
                              'unit_id': None, 'tidal_url': tidal_url}],
            'implementation_report': str(manifest_path),
            'implementation_record': record_relative,
            'decision_record': record_relative}})
    changed = manifest.setdefault('changed_existing', [])
    require(not any(c.get('id') == removed_pid and c.get('action') == 'removed_by_curator'
                    for c in changed), f'{manifest_path} already records the removal')
    changed.append({'id': removed_pid, 'entity': 'performances',
                     'path': f'data/performances/{removed_pid}.yaml',
                     'action': 'removed_by_curator', 'decision_record': record_relative})
    recompute_summary(manifest)
    return json_bytes(manifest)


def plan(root, args, curator):
    today = datetime.now(timezone.utc)
    issue = args.issue
    record_relative = f'reports/curator-decisions/issue-{issue}.json'
    issue_url = ISSUES + str(issue)
    root = root.resolve()
    reject = args.choice.strip().lower() in ('existing', 'geen', 'unresolved')
    performances, performance_paths = load_performances(root)
    require(not (root / record_relative).exists(),
            f'Decision record {record_relative} already exists; review it manually')
    recording_relative, entry = find_recording_candidate(root, args.work)

    work_performances = {pid for pid, p in performances.items() if p['work_id'] == args.work}
    require(len(work_performances) <= 1,
            f'Work {args.work} has {len(work_performances)} performances; '
            'a profiled decision is required')
    replaced_pid = next(iter(work_performances)) if work_performances else None

    if reject:
        if not replaced_pid:
            require(False, 'Rejecting with "existing" requires an existing performance')
        note = f'Curator decision #{issue}: keep existing performance {replaced_pid}.'
        updated_text = update_recording(
            (root / recording_relative).read_text(encoding='utf-8'),
            args.work, 'not_selected', note, '')
        record = {'issue_url': issue_url, 'decision_source': 'curator_cli', 'curator': curator,
                  'recorded_at': today.isoformat(), 'requested_choice': args.choice,
                  'choice': 'existing', 'selected_units': [], 'not_selected_units': [],
                  'performance_id': replaced_pid, 'implementation_pr': None,
                  'replaced_performances': [], 'recording': str(recording_relative),
                  'work_id': args.work, 'docs_updates': []}
        changes = {str(recording_relative): updated_text.encode('utf-8'),
                   record_relative: json_bytes(record)}
        return changes, record, f'Issue #{issue}: keep existing performance {replaced_pid}.'

    track_id = track_id_of(args.track_url)
    tidal_url = f'https://tidal.com/track/{track_id}'
    pid = f'{args.work}-earmarked-{args.choice.strip().lower()}'
    require(ID_PATTERN.match(pid), f'Unsafe performance ID: {pid}')
    require(pid not in performances, f'Performance already exists: {pid}')
    require(track_id not in {tidal_track_id(p) for p in performances.values()},
            f'Track {track_id} is already a canonical performance')
    performers = [parse_performer(p) for p in args.performer]

    changes = {}
    perf = {'id': pid, 'work_id': args.work, 'performers': performers,
            'links': {'tidal': {'url': tidal_url}}}
    if args.album_title:
        perf['release'] = {'album_title': args.album_title}
    perf['source'] = {'file': str(recording_relative), 'url': issue_url,
                      'curator_decision': record_relative}
    changes[f'data/performances/{pid}.yaml'] = emit_performance(perf).encode('utf-8')

    manifest_updates = []
    not_selected_units = []
    if replaced_pid:
        removed = performances[replaced_pid]
        for manifest_path, manifest in referencing_manifests(root, replaced_pid):
            require(manifest_is_supported(manifest),
                    f'{manifest_path} uses an unsupported manifest format; manual review required')
            unit_ids = [u.get('unit_id') for u in manifest['units']
                        if u.get('performance_id') == replaced_pid]
            require(unit_ids, f'{manifest_path} references {replaced_pid} without a unit; manual review required')
            new_records_ids = {r.get('id') for r in manifest.get('new_records') or []}
            require(replaced_pid in new_records_ids or unit_ids,
                    f'{manifest_path} references {replaced_pid} only in resolved choices; manual review required')
            updated = json.loads(json.dumps(manifest))
            changes[str(manifest_path)] = plan_manifest_update(
                manifest_path, updated, unit_ids, replaced_pid, args.work, pid,
                tidal_url, issue, record_relative)
            manifest_updates.append(str(manifest_path))
            not_selected_units.extend(sorted(unit_ids))
        changes[str(performance_paths[replaced_pid])] = None

        anchors = docs_anchor_lines(root, tidal_track_id(removed))
        require(anchors, f'No docs/*.md anchor for replaced track {tidal_track_id(removed)}; '
                'add or rewrite the recommendation line manually')
        require(len(anchors) == 1, 'Multiple docs lines reference the replaced track: '
                + ', '.join(f'{p}:{n}' for p, n, _, _ in anchors) + '; manual review required')
        doc_path, doc_number, doc_line, anchor_pattern = anchors[0]
        scheme_match = re.search(r'\(\s*((?:https?://)?(?:www\.)?)tidal\.com', doc_line)
        prefix = scheme_match.group(1) if scheme_match else 'https://'
        names = ', '.join(p['name'] for p in performers)
        new_anchor = f'[*{names}*]({prefix}tidal.com/track/{track_id})'
        new_line = anchor_pattern.sub(lambda _: new_anchor, doc_line, count=1)
        doc_text = (root / doc_path).read_text(encoding='utf-8').splitlines(True)
        doc_text[doc_number - 1] = new_line + '\n'
        changes[str(doc_path)] = ''.join(doc_text).encode('utf-8')
        docs_updates = [f'{doc_path}:{doc_number}']
    else:
        docs_updates = []
        anchors = docs_anchor_lines(root, track_id)
        require(not anchors, f'Track {track_id} already appears in docs; manual review required')

    links_block = ('links:\n  tidal:\n    url: ' + tidal_url +
                   '\n    status: active\n    last_checked: ' + today.date().isoformat())
    note = (f'Curator decision #{issue}: {args.choice.strip()} — '
            + ', '.join(p['name'] for p in performers)
            + (f'; replaces {replaced_pid}.' if replaced_pid else '.'))
    updated_text = update_recording(
        (root / recording_relative).read_text(encoding='utf-8'),
        args.work, 'recommended', note, links_block)
    changes[str(recording_relative)] = updated_text.encode('utf-8')

    record = {'issue_url': issue_url, 'decision_source': 'curator_cli', 'curator': curator,
              'recorded_at': today.isoformat(), 'requested_choice': args.choice,
              'choice': args.choice.strip(), 'selected_units': [],
              'not_selected_units': not_selected_units,
              'performance_id': pid, 'implementation_pr': None,
              'replaced_performances': [performances[replaced_pid]] if replaced_pid else [],
              'recording': str(recording_relative), 'work_id': args.work,
              'docs_updates': docs_updates, 'manifest_updates': manifest_updates}
    changes[record_relative] = json_bytes(record)

    status_path = root / BATCH_STATUS
    if status_path.exists():
        state = json.loads(status_path.read_text(encoding='utf-8'))
        require(state.get('schema_version') == 1 and isinstance(state.get('issues'), list),
                'Unsupported batch-status schema; review manually')
        state = dict(state, status='pending',
                    issues=sorted(set(state['issues']) | {issue}),
                    updated_at=today.isoformat())
        changes[str(BATCH_STATUS)] = json_bytes(state)
    return changes, record, (f'Issue #{issue}: promote {args.choice.strip()} ({pid})'
                             + (f', replacing {replaced_pid}.' if replaced_pid else '.'))


def install(root, changes, expected):
    for relative, before in expected.items():
        path = root / relative
        now = path.read_bytes() if path.exists() else None
        require(now == before, f'File changed during planning: {relative}; rerun')
    written = []
    try:
        for relative, content in changes.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            written.append(relative)
            if content is None:
                path.unlink()
            else:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                    handle.write(content)
                os.replace(handle.name, path)
    except BaseException:
        for relative in reversed(written):
            path = root / relative
            if expected.get(relative) is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(expected[relative])
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('issue', type=int, help='candidate-review issue number')
    parser.add_argument('--choice', required=True,
                        help='candidate code, or "existing" to reject the earmarked candidate')
    parser.add_argument('--work', required=True, help='canonical work_id of the candidate')
    parser.add_argument('--performer', action='append', default=[],
                        help='reviewed performer: "Name" or "Name (role)"; repeatable')
    parser.add_argument('--track-url', help='reviewed TIDAL listening track of the candidate')
    parser.add_argument('--album-title', help='release album title of the candidate recording')
    parser.add_argument('--curator', default='LAH', help='curator identity for the decision record')
    parser.add_argument('--dry-run', action='store_true', help='plan only; write nothing')
    args = parser.parse_args(argv)
    require(args.issue > 0, 'Supply a positive issue number')
    require(args.choice and args.choice.strip(), 'Supply a choice')
    reject = args.choice.strip().lower() in ('existing', 'geen', 'unresolved')
    if not reject:
        require(args.performer, 'Candidate needs reviewed performers (repeat --performer "Name (role)")')
        require(args.track_url, 'Candidate needs its reviewed listening track (--track-url)')
    cwd = Path.cwd().resolve()
    root = cwd if (cwd / 'data').is_dir() else Path(__file__).resolve().parents[1]
    lock = root / '.curator.lock'
    try:
        if not args.dry_run:
            try:
                descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(descriptor, b'apply_earmarked_decision\n')
                os.close(descriptor)
            except FileExistsError as exc:
                raise SystemExit('ERROR: Another curator apply is running (.curator.lock).') from exc
        changes, record, message = plan(root, args, args.curator.strip() or 'LAH')
        if args.dry_run:
            print(message + ' [dry run]')
            print('Plan:')
            for relative, content in changes.items():
                print(('  DELETE ' if content is None else '  WRITE  ') + relative)
                if content and (relative.endswith('.yaml') or relative.endswith('.yml')):
                    print(''.join('    | ' + line + '\n' for line in
                                  content.decode('utf-8').splitlines()))
            return 0
        expected = {relative: (root / relative).read_bytes()
                    if (root / relative).exists() else None for relative in changes}
        install(root, changes, expected)
        print('Applied: ' + message)
        for relative in changes:
            print(('  DELETE ' if changes[relative] is None else '  WRITE  ') + relative)
        print('Eindcontrole: ./curator finish — daarna zelf reviewen, committen en mergen.')
        return 0
    finally:
        if not args.dry_run and lock.exists():
            lock.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())
