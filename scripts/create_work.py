#!/usr/bin/env python3
"""Mint one canonical Work (and its Work Group) from curator-confirmed evidence.

Companion to ``register_earmarked_recording.py`` (#331): when an earmarked album
dry-run reports unmatched tracks whose work is not canonical yet, this script
turns the factual evidence (title, catalogue tokens, composer) into a proposed
``data/works/`` definition — with an automatically derived identifier, advisory
MusicBrainz version evidence and an explicit apply step.

The script never guesses. The composer must resolve to exactly one canonical
Person, a source is mandatory, and a shared catalogue token with an existing
work of the same composer blocks minting in favour of enrichment (``--enrich``):
that existing work is then the identity, and the missing token is added to it.
Title containment between the proposed and an existing work title is reported as
a warning for the curator, not silently resolved.

Identifiers follow current repository practice: ``work_id`` is
``<composer_id>-<work-slug>`` and a new group is ``<composer_id>-<work-slug>-group``
(e.g. ``richard-strauss-violin-concerto-op-8``). MusicBrainz evidence is advisory
only and is stored under ``external_ids`` exclusively when the curator passes an
explicit work ID.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'src'))

from ruamel.yaml import YAML

import register_earmarked_recording as reg

yaml = YAML()
yaml.default_flow_style = False


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_catalogue_entry(text):
    """'Sz. 87' -> ('sz', 'Sz. 87'); fail closed on anything that is not a
    single catalogue number in a form the matcher also reads."""
    value = (text or '').strip()
    match = reg.CATALOGUE.match(value)
    require(match and not value[match.end():].strip(),
            f'Not a single catalogue number: {text!r} '
            '(expected e.g. "Op. 8", "Sz. 87", "TrV 110", "BWV 1052", "D. 940")')
    return match.group(1).casefold(), value


def parse_catalogue_entries(values):
    entries, seen = [], set()
    for value in values:
        key, stored = parse_catalogue_entry(value)
        require(key not in seen, f'Duplicate catalogue prefix in input: {value!r}')
        seen.add(key)
        entries.append((key, stored))
    return entries


def resolve_composer(persons, needle):
    """Exactly one canonical Person by id or by (normalized) full name."""
    normalized = reg.norm(needle)
    hits = [pid for pid, name in persons.items()
            if pid == needle or reg.norm(name) == normalized]
    require(len(hits) == 1,
            'Composer does not resolve to exactly one canonical Person '
            f'({len(hits)} candidates for {needle!r}); add or disambiguate under data/persons/ first')
    return hits[0]


def build_source(source_file, source_url):
    source = {}
    if source_file:
        source['file'] = source_file
    if source_url:
        source['url'] = source_url
    require(source, 'A source is mandatory: pass --source-url and optionally --source-file')
    return source


def near_misses(works, composer_id, catalogue_values):
    """Existing works of the same composer sharing a catalogue token with the
    proposed evidence. Title containment alone is a warning, not a blocker."""
    tokens = set()
    for value in catalogue_values:
        tokens |= reg.catalogue_tokens(value)
    hits = []
    for work in works:
        if work.get('composer_id') != composer_id:
            continue
        shared = tokens & reg.work_catalogue_tokens(work)
        if shared:
            hits.append({'work_id': work['id'], 'title': work['title'],
                         'shared_catalogue_tokens': sorted(shared)})
    return hits


def title_warnings(works, composer_id, title):
    """Containment between the proposed title and an existing title of the same
    composer: evidence for the curator to inspect, never resolved silently."""
    proposed = reg.norm(title)
    warnings = []
    if not proposed:
        return warnings
    for work in works:
        if work.get('composer_id') != composer_id:
            continue
        existing = reg.norm(work['title'])
        if existing and (proposed in existing or existing in proposed):
            warnings.append({'work_id': work['id'], 'title': work['title']})
    return warnings


def external_suggestions(title, suggest_client):
    """Advisory MusicBrainz version evidence; fail-open like the register script."""
    if suggest_client is None:
        return None
    try:
        return suggest_client.work_suggestions(reg.suggestion_search_text(title))
    except (ValueError, OSError):
        return None


def dump_document(document):
    import io
    handle = io.StringIO()
    yaml.dump(document, handle)
    return handle.getvalue()


def work_path(root, work_id):
    return Path(root) / 'data/works' / (work_id + '.yaml')


def group_path(root, group_id):
    return Path(root) / 'data/work-groups' / (group_id + '.yaml')


def write_document(path, document):
    require(not path.exists(), f'Refusing to overwrite an existing file: {path.name}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        yaml.dump(document, handle)
    return path


def run_mint(root, *, title, composer, catalogue_entries, aliases, version, year, key,
             slug, work_group_id, group_title, source_url, source_file,
             musicbrainz_work_id, apply=False, suggest_client=None):
    root = Path(root)
    require(title and title.strip(), 'A work title is mandatory')
    title = title.strip()
    works, persons = reg.load_works(root), reg.load_persons(root)
    require(works and persons, 'Canonical data is missing or empty; refusing to guess')
    composer_id = resolve_composer(persons, composer)
    work_slug = slug or reg.slugify(title)
    work_id = f'{composer_id}-{work_slug}'

    require(not any(w['id'] == work_id for w in works),
            f'Work ID already exists: {work_id}; use --enrich to extend it, '
            'or --slug with a unique slug')
    blockers = near_misses(works, composer_id, [value for _, value in catalogue_entries])
    require(not blockers,
            'Refusing to mint: an existing work of this composer shares catalogue '
            'token(s) with the proposed evidence — it is almost certainly the same '
            'composition. Enrich it instead: ' +
            '; '.join(f"{b['work_id']} ({', '.join(b['shared_catalogue_tokens'])})" for b in blockers))
    warnings = title_warnings(works, composer_id, title)
    suggestions = external_suggestions(title, suggest_client)

    if work_group_id:
        require(group_path(root, work_group_id).exists(),
                f'Unknown work group: {work_group_id} (expected data/work-groups/{work_group_id}.yaml)')
        group_document = None
    else:
        group_id = f'{composer_id}-{work_slug}-group'
        require(not group_path(root, group_id).exists(),
                f'Work group ID already exists: {group_id}')
        group_document = {'id': group_id, 'composer_id': composer_id,
                          'title': (group_title or title).strip(),
                          'source': build_source(source_file, source_url)}

    work_document = {'id': work_id,
                     'work_group_id': work_group_id or group_document['id'],
                     'composer_id': composer_id, 'title': title}
    if catalogue_entries:
        work_document['catalogue'] = {key: value for key, value in catalogue_entries}
    if version:
        work_document['version'] = version
    if year:
        work_document['year'] = year
    if key:
        work_document['key'] = key
    if aliases:
        work_document['aliases'] = list(aliases)
    if musicbrainz_work_id:
        require(re.fullmatch(r'[0-9a-f-]{36}', musicbrainz_work_id),
                f'Not a MusicBrainz work ID: {musicbrainz_work_id!r}')
        work_document['external_ids'] = {'musicbrainz': musicbrainz_work_id}
    work_document['source'] = build_source(source_file, source_url)

    output = {'mode': 'mint', 'title': title, 'composer': {'id': composer_id, 'name': persons[composer_id]},
              'work_id': work_id, 'work_group_id': work_document['work_group_id'],
              'near_miss_blockers': blockers, 'title_warnings': warnings,
              'external_suggestions': suggestions,
              'work_yaml': dump_document(work_document), 'apply': apply}
    output['group_yaml'] = dump_document(group_document) if group_document else None
    if apply:
        written = [write_document(work_path(root, work_id), work_document)]
        if group_document:
            written.insert(0, write_document(group_path(root, group_document['id']), group_document))
        output['written'] = [str(path.relative_to(root)) for path in written]
    return output


def run_enrich(root, work_id, catalogue_entries, aliases, apply=False):
    root = Path(root)
    require(catalogue_entries or aliases,
            'Nothing to enrich: pass --catalogue and/or --alias')
    path = work_path(root, work_id)
    require(path.exists(), f'Unknown work: {work_id} (expected {path.name})')
    data = reg.read_yaml(path)
    require(isinstance(data, dict), f'Work file is not a mapping: {path.name}')
    changes, unchanged = [], []
    if catalogue_entries:
        catalogue = data.get('catalogue')
        require(catalogue is None or isinstance(catalogue, dict),
                f'catalogue in {path.name} is not a mapping; edit the file manually')
        catalogue = dict(catalogue or {})
        for key, value in catalogue_entries:
            if catalogue.get(key) == value:
                unchanged.append(f'catalogue {key}: {value}')
            elif key in catalogue:
                raise ValueError(
                    f'catalogue key {key!r} in {path.name} already has value '
                    f'{catalogue[key]!r}; refusing to replace {value!r} — review the file manually')
            else:
                catalogue[key] = value
                changes.append(f'catalogue {key}: {value}')
        if changes:
            data['catalogue'] = catalogue
    if aliases:
        existing = data.get('aliases')
        require(existing is None or isinstance(existing, list),
                f'aliases in {path.name} is not a list; edit the file manually')
        existing = list(existing or [])
        for alias in aliases:
            if alias in existing:
                unchanged.append(f'alias {alias}')
            else:
                existing.append(alias)
                changes.append(f'alias {alias}')
        if changes:
            data['aliases'] = existing
    output = {'mode': 'enrich', 'work_id': work_id, 'changes': changes, 'unchanged': unchanged,
              'work_yaml': dump_document(data), 'apply': apply}
    if apply:
        if not changes:
            raise ValueError(f'Nothing to change in {path.name}; refusing a no-op write')
        with path.open('w', encoding='utf-8') as handle:
            yaml.dump(data, handle)
        output['written'] = str(path.relative_to(root))
    return output


def run(root, *, title=None, composer=None, enrich=None, catalogue_entries=None,
        aliases=None, version=None, year=None, key=None, slug=None,
        work_group_id=None, group_title=None, source_url=None, source_file=None,
        musicbrainz_work_id=None, apply=False, suggest_client=None):
    if enrich:
        require(not title, 'Do not pass a work title together with --enrich')
        require(not (version or year or key or slug or work_group_id or group_title
                     or source_url or source_file or musicbrainz_work_id),
                '--enrich takes only --catalogue and/or --alias')
        return run_enrich(root, enrich, catalogue_entries or [], aliases or [], apply=apply)
    require(title, 'A work title is mandatory (or use --enrich WORK_ID)')
    require(composer, '--composer is mandatory when minting a new work')
    return run_mint(root, title=title, composer=composer,
                    catalogue_entries=catalogue_entries or [], aliases=aliases or [],
                    version=version, year=year, key=key, slug=slug,
                    work_group_id=work_group_id, group_title=group_title,
                    source_url=source_url, source_file=source_file,
                    musicbrainz_work_id=musicbrainz_work_id, apply=apply,
                    suggest_client=suggest_client)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('title', nargs='?', help='Work title, e.g. "Violin Concerto in D Minor, Op. 8"')
    parser.add_argument('--composer', help='Canonical composer: person ID or full name (exactly one match required)')
    parser.add_argument('--catalogue', action='append', default=[], metavar='NUM',
                       help='Catalogue number, repeatable, e.g. "Op. 8", "TrV 110", "Sz. 87"')
    parser.add_argument('--alias', action='append', default=[], metavar='ALIAS',
                       help='Work alias, repeatable, helps future matching')
    parser.add_argument('--version', help='Version designation when the work is a distinct version')
    parser.add_argument('--year', type=int, help='Composition year, when relevant')
    parser.add_argument('--key', help='Key, e.g. "D minor"')
    parser.add_argument('--slug', help='Override the work slug derived from the title')
    parser.add_argument('--work-group-id', help='Attach to an existing work group instead of minting a new one')
    parser.add_argument('--group-title', help='Title for the newly minted work group (default: the work title)')
    parser.add_argument('--source-url', help='Evidence URL for the source field (mandatory)')
    parser.add_argument('--source-file', help='Optional repository file for the source field')
    parser.add_argument('--musicbrainz-work-id', metavar='MBID',
                       help='MusicBrainz work ID stored as external evidence (never determines identity)')
    parser.add_argument('--enrich', metavar='WORK_ID',
                       help='Enrich an existing work with --catalogue/--alias instead of minting')
    parser.add_argument('--no-external-lookups', action='store_true',
                       help='Skip the advisory MusicBrainz version evidence in the preview')
    parser.add_argument('--apply', action='store_true',
                       help='Write the proposed file(s); without this flag nothing is written')
    args = parser.parse_args(argv)
    catalogue = parse_catalogue_entries(args.catalogue)
    try:
        result = run(ROOT, title=args.title, composer=args.composer, enrich=args.enrich,
                     catalogue_entries=catalogue, aliases=args.alias, version=args.version,
                     year=args.year, key=args.key, slug=args.slug,
                     work_group_id=args.work_group_id, group_title=args.group_title,
                     source_url=args.source_url, source_file=args.source_file,
                     musicbrainz_work_id=args.musicbrainz_work_id, apply=args.apply,
                     suggest_client=reg.NullSuggestionClient() if args.no_external_lookups else None)
    except ValueError as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    if result['mode'] == 'mint':
        print(f"Composer: {result['composer']['name']} ({result['composer']['id']})")
        print(f"Work ID: {result['work_id']}")
        print(f"Work group: {result['work_group_id']}"
              + ('' if result.get('group_yaml') else ' (existing)'))
    for blocker in result.get('near_miss_blockers') or []:
        print(f"  BLOCKED near-miss: {blocker['work_id']} shares "
              f"{', '.join(blocker['shared_catalogue_tokens'])}")
    for warning in result.get('title_warnings') or []:
        print(f"  WARNING: existing title overlaps: {warning['title']} ({warning['work_id']}) — inspect before applying")
    suggestions = result.get('external_suggestions')
    if suggestions:
        print('  MusicBrainz version evidence (advisory, never canonical):')
        for hit in suggestions:
            composers = ', '.join(c['name'] for c in hit['composers'])
            print(f"    - {hit['title']} (musicbrainz work {hit['musicbrainz_work_id']})"
                  f" — composer: {composers or 'not stated on the work'}")
    elif result.get('external_suggestions') is None and result['mode'] == 'mint' and not args.no_external_lookups:
        print('  MusicBrainz version evidence: unavailable (lookup failed)')
    for change in result.get('changes') or []:
        print(f"  Change: {change}")
    for unchanged in result.get('unchanged') or []:
        print(f"  Already present: {unchanged}")
    if result.get('group_yaml'):
        print('--- Proposed data/work-groups YAML ---')
        print(result['group_yaml'], end='')
    print('--- Proposed data/works YAML ---')
    print(result['work_yaml'], end='')
    if result['apply']:
        for written in result.get('written', []):
            print(f'Written: {written}')
        print('Validate with: .venv/bin/python scripts/validate_data.py')
        if result['mode'] == 'mint':
            print('Then re-run the earmarked dry-run to confirm the tracks now match as candidate.')
    else:
        print('Dry run: nothing written. Re-run with --apply to write the proposed file(s).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
