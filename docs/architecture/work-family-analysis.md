---
title: Work Family Analysis
nav_order: 6
---

# Work Family Analysis

> Status: Superseded by `repository-architecture.md` and `work.md`.
>
> This analysis records an earlier argument for demoting Work Family. The current
> authoritative design uses Work Group as a canonical grouping entity and requires
> every Work to belong to exactly one Work Group.

## Executive conclusion

`Work Family` should not remain a primary standalone domain entity in the conceptual model.

The existing collection is better explained by explicit, typed relationships between `Work` entities. A family-like grouping is still useful for navigation, validation and display, but it should be either derived from work relationships or stored as an implementation/presentation helper, not treated as an entity that owns musical facts.

The recommendation is therefore:

1. `Work Family` should be demoted from a primary domain entity to a derived or optional grouping construct.
2. Explicit work-to-work relationships should become mandatory whenever a work is catalogued as a revision, orchestration, arrangement, transcription, completion, reconstruction, excerpt, suite from another work, or otherwise derived work.
3. Groupings should normally be derived from connected components of these relationships. Explicit stored groups may be allowed later only for curated navigation labels or validation boundaries.
4. The minimum relationship vocabulary needed now is:
   - `revision_of`
   - `arrangement_of`
   - `orchestration_of`
   - `transcription_of`
   - `completion_of`
   - `reconstruction_of`
   - `suite_from`
   - `excerpt_from`
   - `part_of`
   - `based_on`
   - `adaptation_of`
   - `incorporates`
5. Ambiguous cases should remain textual notes until the catalogue can distinguish work, version, realization and performance practice consistently. These include minor revisions, alternative scorings that are not independently catalogued, performing editions, incomplete fragments, and incidental excerpts whose source work is not yet modelled locally.
6. ADR 0001 and ADR 0002 should later be updated where they say that works belong to at most one work family, that relationships between related works are owned by `Work Family`, and that `Work Family` is one of the six primary entities.

The practical model should be a hybrid: explicit relationships are semantically authoritative, while family/group views are computed for the website.

## Current architectural position

The existing architecture is work-centric. `docs/architecture/vision-and-design-principles.md` states that works are the central concept, that relationships are first-class citizens, and that domain knowledge should be separated from presentation.

ADR 0001 currently defines the repository as a catalogue of works and recommendations "organised into work families where appropriate". It says a work may optionally belong to a work family, and that a work family groups related works such as revisions, orchestrations, transcriptions, completions and reconstructions. It also says that recommendations belong to individual works, not families.

ADR 0002 makes `Work Family` one of six primary entities and assigns ownership of "relationships between related works" to `Work Family`. At the same time, ADR 0002 says that a work family is purely organisational, has no performances, releases or recommendations, and exists for navigation and grouping.

That creates a tension:

- If a work family is purely organisational, it is not a strong domain entity.
- If it owns relationships between works, then it owns facts that are not actually about the group but about directed derivation between individual works.
- If each work belongs to at most one family, the model assumes a tree-like grouping that the collection does not consistently support.

The current ADRs already point toward the answer: relationships are first-class, but `Work Family` is described mostly as a navigation tool.

## Evidence from the existing collection

The current collection contains many concrete cases where the important fact is not "these works are in the same family" but "this work is derived from that work in this particular way".

Representative examples:

- John Adams, `docs/adams.md`: `Shaker Loops` appears as a 1978 string septet and as a 1983 string-orchestra adaptation. `Wavemaker` is described as the source of the chamber `Shaker Loops`. These are not just siblings; there is a directional derivation chain.
- Johann Sebastian Bach, `docs/bachJS.md`: early and revised versions occur for Brandenburg Concerto No. 5 and Harpsichord Concerto No. 1. There are also orchestral arrangements and reconstructions, such as BWV 1059 marked as an abandoned fragment reconstructed by Francesco Corti.
- Samuel Barber, `docs/barber.md` and `data/works/samuel-barber/works.yaml`: `Adagio for Strings`, Op. 11a is associated with the String Quartet, Op. 11; `Souvenirs` exists as ballet and piano-suite forms; `Serenade` exists as a chamber work and string-orchestra version. The pilot YAML already notes that related versions are "modelled separately".
- Bela Bartok, `docs/bartok.md`: stage works have orchestral suites; `The Wooden Prince` has shorter and longer orchestral suites; works are revised and orchestrated across time.
- Beethoven, `docs/beethoven.md`: Op. 61a is Beethoven's own piano-concerto arrangement of the Violin Concerto, Op. 61. Piano trios after symphonies and variations on themes from Mozart or Handel show that a work can be derived from a different composer's work.
- Bruckner, `docs/bruckner.md`: symphonies have multiple dated versions, concepts and revisions. Symphony No. 4 alone has 1874-1876, 1878, 1880 and 1888 versions. This is a version graph, not merely a display group.
- Busoni, `docs/busoni.md`: `Turandot Suite`, `Die Brautwahl Suite`, and the chamber fantasy after `Carmen` demonstrate suites and works after other source works.
- Berio, `docs/berio.md` and `data/works/luciano-berio/works.yaml`: the `Sequenza` and `Chemins` works form a network. `Sequenza VI` is reused in `Chemins II` and `Chemins III`; `Chemins II` is reused in `Chemins III`; `O King` is incorporated into `Sinfonia`; `Opera` incorporates reworked materials from several works. This is the strongest evidence against a single-family tree.
- Mozart, `docs/mozart.md`: the C minor Mass and Requiem are catalogued through specific completions. Operas are represented through wind arrangements of parts.
- Poulenc, `docs/poulenc.md`: `Pastourelle` is an excerpt from `L'eventail de Jeanne` and better known in piano transcription; `Litanies a la Vierge Noire` exists in vocal-organ and orchestrated forms; `Capriccio` is after `Le bal masque`.
- Respighi, `docs/respighi.md`: `Rossiniana` is an orchestral suite after Rossini; `Belkis` has a suite from a ballet; `Antiche danze ed arie` are transcriptions.
- Sibelius, `docs/sibelius.md`: `Finlandia`, `Valse Triste`, `Scene with Cranes`, `Cantique` and `Devotion` are arrangements or excerpts from larger contexts; Symphony No. 8 is represented by late fragments completed by Virtanen.
- Shostakovich side materials: many film, ballet and stage works have suites, often arranged by Levon Atovmyan. These are systematic suite-from and arranged-by cases.
- Stravinsky, `docs/stravinsky.md`: `The Firebird`, `Petrushka` and `The Rite of Spring` have revisions; `Suite from Pulcinella`, `Divertimento`, `Suite Italienne`, `Suite No. 1`, `Suite No. 2`, `Quatre etudes`, and `Tango for chamber orchestra` are explicit arrangements, suites or orchestrations.

The first twenty composer pages already contain the relevant patterns: Adams, Bach, Barber, Bartok, Beethoven, Berio, Bruckner, Busoni, Dohnanyi, Dvorak, Gade, Holst, Ives, Mozart, Poulenc and others all include revisions, arrangements, versions, excerpts, suites or adaptations.

## Relationship types found

The collection contains these relationship types.

`revision_of`: Bruckner symphony versions; Stravinsky revisions of major ballets; Sibelius revisions of `En saga`, the Violin Concerto and Symphony No. 5; Barber revisions of operas and symphonies.

`arrangement_of`: Beethoven Op. 61a after the Violin Concerto; Mozart wind arrangements from operas; Dohnanyi `Valses nobles` after Schubert; Stravinsky `Suite No. 1`, `Suite No. 2`, `Tango`, and `Quatre etudes`; Holst arrangements of earlier composers.

`orchestration_of`: Bartok works first composed in one form and later orchestrated; Stravinsky `8 Instrumental Miniatures`; Holloway orchestrations of Chabrier and Debussy in side materials.

`transcription_of`: Respighi `Antiche danze ed arie`; Poulenc's `Pastourelle` in piano transcription; Bach/Busoni-like arrangements and transcriptions in side materials.

`completion_of`: Mozart Requiem completed by Sussmayr; Mozart C minor Mass completed by Beyer; Sibelius late fragments completed by Virtanen; Bach BWV 1059 reconstructed/completed for performance.

`reconstruction_of`: Bach fragments and lost/abandoned works where a performing work is reconstructed from incomplete material.

`suite_from`: Barber `Medea, Suite`; Respighi `Belkis`; Shostakovich film and ballet suites; Stravinsky `Suite from Pulcinella`; Adams `The Nixon Tapes`.

`excerpt_from`: Barber `Intermezzo from Vanessa`; Poulenc `Pastourelle`; Mozart opera overtures and parts; Sibelius `Finlandia` from `Press Celebrations Music`.

`part_of`: movements, songs, arias, opera parts, sets and cycles. This relationship is not the same as derivation: an excerpt may also be part of a larger work.

`based_on` or `adaptation_of`: Busoni after `Carmen`; Dohnanyi and Beethoven variations on themes from other composers; Berio arrangements of Monteverdi, Purcell and Weill; stage works based on plays, poems or texts.

`incorporates`: Berio is the clearest case. A later work may incorporate material from one or more earlier works without being simply an arrangement or revision.

Most of these relationships are directional. `revision_of`, `arrangement_of`, `orchestration_of`, `completion_of`, `suite_from`, `excerpt_from`, `based_on` and `incorporates` point from the derived work to the source work. The inverse is useful for navigation but should not be stored as a separate fact unless needed for denormalized implementation.

Some relationships are hierarchical, especially `part_of`. Others are genealogical but not hierarchical: `based_on`, `incorporates` and `arrangement_of` can create networks. Relationships are not generally symmetric.

Works can have multiple relationships at once. A suite can be both `suite_from` and `arrangement_of`; a completion can also be a reconstruction; a work can incorporate material from several earlier works. Berio's `Opera`, `Sinfonia`, and `Chemins` cases make this unavoidable.

## Evaluation of option A: Work Family

Option A keeps `Work Family` as a domain entity:

```text
Work Family
    |-- Work A
    |-- Work B
    `-- Work C
```

Advantages:

- Simple for website grouping.
- Easy to explain in ordinary catalogue language.
- Useful for showing versions of a Bruckner symphony together.
- Supports a compact "related works" section without traversing a graph.

Problems:

- It hides the type and direction of the relationship.
- It cannot naturally say that `Op. 61a` is an arrangement of `Op. 61`; it can only say both are in a group.
- It assumes each work belongs to at most one family, which fails for multi-source works and works that are both part of one structure and derived from another.
- It gives ownership of relationship facts to a group that has no musical behavior of its own.
- It risks artificial modelling: curators must invent a family even when the collection only needs one directed edge.
- It is less aligned with MusicBrainz, where work-to-work relationships include arrangement, orchestration, revision, based-on, parts, included works and medley relationships.

The strongest case for `Work Family` is Bruckner: multiple versions of the same numbered symphony are easy to display as a group. But even there the group has no independent recommendation, performance, release, authority identity or factual metadata that cannot be derived from the version relationships and shared catalogue number.

Conclusion for option A: useful as presentation, too weak as a primary domain entity.

## Evaluation of option B: Explicit work relationships

Option B models only typed relationships:

```text
Work B revision_of Work A
Work C orchestration_of Work A
Work D suite_from Work E
```

Advantages:

- Semantically precise.
- Matches the architecture principle that relationships are first-class citizens.
- Supports directionality and relationship type.
- Handles networks, not just trees.
- Allows a work to participate in multiple structures.
- Aligns well with MusicBrainz work-to-work relationships and import.
- Avoids inventing artificial groups.
- Keeps recommendations attached to individual works.

Problems:

- Website grouping has to be computed.
- Users may still expect a visible "versions of Symphony No. 4" group.
- Validation is more complex than checking a single `family_id`.
- A graph can become noisy if minor relationships are over-modelled.
- Some cases need a threshold for deciding whether a new `Work` exists.

Option B is conceptually strongest. Its main weakness is practical: it needs derived views for humans.

## Evaluation of option C: Hybrid model

Option C makes explicit relationships authoritative and uses groupings only for navigation, validation or presentation.

This is the recommended model.

The conceptual layer should contain:

```text
Work
    relationships:
      - type: revision_of
        target: bruckner-symphony-4-1874
      - type: suite_from
        target: stravinsky-pulcinella
```

The presentation layer may derive:

```text
Related works: Bruckner Symphony No. 4
    - 1874-1876 version
    - 1878 version
    - 1880 version
    - 1888 version
```

Advantages:

- Keeps the conceptual model honest.
- Preserves the easy website experience.
- Allows imported MusicBrainz relationships to map naturally.
- Avoids forcing every related work into exactly one family.
- Allows validation rules such as "derived works must point to a source".
- Keeps room for explicit curated groups later if they are genuinely needed.

Risks:

- If stored groups are introduced too early, they may drift from the relationship graph.
- If all groups are derived mechanically, some website labels may be awkward.
- The project will need clear rules for when to display connected works together.

The risk is manageable if ADRs clearly distinguish conceptual relationships from generated navigation.

## Difficult and ambiguous cases

Not every difference should create a separate `Work`.

Likely separate works:

- A published arrangement or orchestration that can receive its own recommendation.
- A version with a distinct catalogue identity, date, scoring or performance tradition.
- A completion or reconstruction recorded as a distinct performable entity.
- A suite or excerpt that is independently performed and recommended.
- A derived work by another creative contributor.

Likely not separate works:

- A routine performing edition.
- A private or one-off arrangement tied to a single recording.
- Minor cuts or performance variants.
- Remastering or release differences, which belong to `Release`.
- A recording-specific realization that does not have stable work identity.

The model may eventually need an entity such as `Version`, `Realization` or `Expression`, but the current collection does not yet require this as a primary entity. Most visible cases can be handled by treating independently performable, recommendable forms as `Work` and linking them explicitly. A future `Version` or `Expression` layer may be useful for:

- Bruckner-style textual versions where the catalogue wants both a common work identity and separately recommendable versions;
- performing completions of unfinished works;
- alternative editions that are below the threshold of a separate work but above mere release metadata.

For now, introducing such an entity would add complexity before the repository has schema pressure demanding it.

## Recommended conceptual model

The recommended conceptual model is:

```text
Composer
    contributes to
Work
    has typed relationship to Work

Work
    may have Recommendation
Recommendation
    identifies Performance
Performance
    published as Release
Release
    available through Availability
```

`Work` remains the central musical entity.

`Work Family` is removed from the primary conceptual model. If retained in implementation, it should be renamed or documented as something like `work_group`, `navigation_group` or `derived_work_cluster`, and it should not own musical facts.

Relationships between works are facts owned by the source `Work` relationship record, not by a family.

Website pages may still show families:

- "Versions of Bruckner Symphony No. 4"
- "Works derived from Pulcinella"
- "Sequenza and Chemins related works"
- "Suites from stage works"

But those groupings should be generated from relationships unless a curator explicitly overrides a label for display.

## Proposed cardinalities and constraints

Recommended cardinalities:

- A `Work` may have zero, one or many outgoing relationships to other works.
- A `Work` may have zero, one or many incoming relationships from other works.
- A `Work` may participate in more than one derived grouping because groupings are graph views, not ownership containers.
- A relationship has exactly one source work, one target work and one relationship type.
- A relationship type should define direction, inverse label and validation expectations.
- A `Recommendation` remains attached to exactly one `Work`.
- A `Work` may have no recommendation.

Recommended constraints:

- Do not store inverse relationships as separate facts.
- Prefer the most specific relationship type available.
- Use `based_on` only when no more specific relationship is justified.
- Use `part_of` for structural containment, not derivation.
- Use `excerpt_from` when an independently catalogued work is an extract from a larger work.
- Use `suite_from` when an independently catalogued suite is drawn from a stage, film, ballet or other larger work.
- Use `incorporates` where a later work reuses material from one or more earlier works but is not simply an arrangement or revision.
- Allow cross-composer relationships.
- Allow relationships to external authority works if the source work is not yet modelled locally, but keep that as a later schema decision.

## Consequences for ADR 0001 and ADR 0002

ADR 0001 should later be changed in these places:

- The definition of the repository should no longer say that it is organised into work families as part of the conceptual identity. It can say that related works may be grouped for navigation.
- The domain model diagram should replace `Work -> belongs to -> Work Family` with `Work -> related to -> Work`.
- The `Work Family` section should be removed or demoted to generated navigation grouping.
- The statement "Each work belongs to at most one work family" should be removed.
- The "Multiple related works" section should say that related works are connected by typed relationships, and that group displays are derived from those relationships.
- The future-work item about defining the relationship model between work families and works should become a task to define the work-to-work relationship vocabulary and validation rules.

ADR 0002 should later be changed in these places:

- `Work Family` should be removed from the list of six primary entities.
- The diagram should remove the `belongs to Work Family` edge.
- The ownership table should no longer assign "Relationships between related works" to `Work Family`; those facts should be owned by work-to-work relationship records.
- The `Work Family` entity section should be replaced by a note on derived navigation groups.
- The `Work` section should say that a work may have typed relationships to many other works, rather than belonging to one family.

ADR 0003 may later need a small update because it lists work families as local additions. That can become "local relationship curation and optional navigation group labels".

## Questions deferred to later design work

- Exact YAML shape for work-to-work relationships.
- Whether relationship records need IDs, dates, confidence, source citations or curator notes.
- Whether local work relationships may target external MusicBrainz work IDs before the target work exists locally.
- Whether `Version`, `Expression`, `Realization` or `Manifestation` should be introduced after more structured data exists.
- How to distinguish a separately recommendable `Work` from a performance-specific arrangement.
- How website generation should cluster related works and choose group labels.
- How much of MusicBrainz relationship vocabulary should be imported directly versus normalized to local terms.
- Whether `part_of` should cover movements, songs and opera numbers now, or whether that belongs to a later movement-level model.

External comparison notes:

- MusicBrainz models works as distinct intellectual or artistic creations and uses explicit work-to-work relationships such as arrangement, orchestration, revision, based-on, parts and included works. See [MusicBrainz Work-Work relationship types](https://musicbrainz.org/relationships/work-work), [MusicBrainz Work documentation](https://musicbrainz.org/doc/Work), and the [MusicBrainz classical work style guide](https://musicbrainz-docs-development.readthedocs.io/en/latest/style_guides/classical/work.html).
- MusicBrainz's classical guidance also uses a threshold for arrangement works: not every performance arrangement becomes a new work. This supports a local rule that only independently reusable, recommendable derived forms become `Work`.
- FRBR/LRM-style bibliography distinguishes Work, Expression, Manifestation and Item. This is useful as a conceptual warning: some "versions" may eventually be expression-like rather than separate works. However, the current repository should not import that full stack yet; the local scale and curation workflow are better served by `Work` plus explicit relationships until concrete schema pressure appears.
