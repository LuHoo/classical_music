# ADR 0003: External authority sources

- Status: Accepted
- Date: 2026-07-16

## Context

ADR 0001 defines the repository as a curated catalogue of classical musical works and their recommended performances.

ADR 0002 defines the internal domain model.

Most metadata required by the catalogue already exists in well-established external databases. Duplicating this information would increase maintenance effort, introduce inconsistencies and distract from the primary purpose of the project.

The purpose of this repository is not to become a comprehensive music database.

Its primary purpose is musical curation.

## Decision

The repository shall treat external music databases as authoritative sources whenever practical.

The repository stores only:

- information required to identify internal entities;
- metadata that cannot reliably be obtained elsewhere;
- curator-specific information;
- operational information.

Metadata that is maintained by authoritative external sources should normally not be duplicated.

## Principles

### External authorities

The project recognises several external authority sources.

Each source has its own area of responsibility.

No single authority is expected to provide all required information.

### Curatorial ownership

The repository is the authoritative source only for:

- recommendations;
- preferred performances;
- preferred releases;
- candidate performances;
- historical recommendations;
- editorial notes;
- local identifiers;
- operational metadata.

These data do not exist elsewhere and therefore belong in this repository.

### Metadata ownership

Whenever practical, factual metadata should remain owned by the relevant authority source.

Examples include:

- composer metadata;
- work metadata;
- artist metadata;
- release metadata.

The repository should reference these data rather than duplicate them.

### Stable identifiers

Where available, stable external identifiers should be stored instead of copied metadata.

Examples include:

- MusicBrainz identifiers;
- Discogs identifiers.

The exact identifier strategy will be defined in a later ADR.

## Authority roles

The following responsibilities are currently envisaged.

| Source | Primary responsibility |
|----------|------------------------|
| MusicBrainz | Canonical identities and relationships |
| Discogs | Commercial releases and label metadata |
| Wikipedia | General descriptive information |
| Grove Music Online | Musicological reference |
| Gramophone | Critical reviews and editorial research |
| Streaming platforms | Listening availability only |

This table documents intended responsibilities rather than implementation details.

The exact integrations may evolve over time.

## Streaming services

Streaming services are not authority sources.

They provide access to recordings but are not considered reliable sources of canonical metadata.

Streaming identifiers and URLs are operational data.

## Data ownership

The following table summarises ownership.

| Information | Authority |
|-------------|-----------|
| Composer identity | MusicBrainz |
| Work identity | MusicBrainz |
| Artist identity | MusicBrainz |
| Commercial release | Discogs / MusicBrainz |
| Listening availability | Streaming platforms |
| Recommendation | Repository |
| Preferred performance | Repository |
| Preferred release | Repository |
| Curatorial notes | Repository |

## Import philosophy

External metadata should normally be imported rather than entered manually.

Imported metadata may be normalised to fit the internal domain model but should not be rewritten without good reason.

The import process should minimise manual work while allowing the curator to review ambiguous cases.

## Local additions

The repository may maintain local information that is absent from authority sources.

Typical examples include:

- work families;
- recommendation history;
- listening notes;
- editorial comments;
- personal ratings;
- preferred release selection.

These additions complement rather than replace external metadata.

## Consequences

### Advantages

- Much smaller repository.
- Reduced maintenance effort.
- Better metadata consistency.
- Easier future synchronisation.
- Ability to benefit from improvements in external databases.
- Clear separation between factual metadata and editorial judgement.

### Trade-offs

- The project depends on the continued availability of external authority sources.
- Import tooling becomes an important part of the architecture.
- Different authority sources may occasionally disagree.

## Future work

Future ADRs will define:

- identifier strategy;
- metadata import pipeline;
- authority reconciliation;
- streaming abstraction;
- caching strategy;
- validation rules.
