# Prokofiev MusicBrainz Work-list alignment review

Date: 2026-08-26

Issue: #159

## Pre-flight checklist

- Treated the existing Prokofiev collection as trusted legacy input.
- Used MusicBrainz Work IDs as supporting evidence, not as canonical identity
  authority.
- Kept unresolved candidates and uncertain MBIDs out of canonical Work YAML.
- Preserved the model `Person -> Work Group -> Work -> Performance`; no
  Recording or Release entities were introduced.
- Classified only consequential Work identity or Work-version boundaries as
  active curator decisions.

## Result

The Prokofiev Work migration contains 96 local Works. The prior finite
MusicBrainz Works-list pass aligned 63 Works with MusicBrainz IDs. This review
documents the remaining 33 items without promoting uncertain authority data into
canonical YAML.

| Classification | Count | Action |
| --- | ---: | --- |
| Curator decision required | 5 local Works in 4 decisions | Keep open as explicit Work/version-boundary decisions |
| Good candidate but resolver ambiguous | 2 | Record candidate evidence; do not write MBID |
| No reliable parent Work in finite MusicBrainz list | 26 | Treat as background authority gap |

## Curator decisions required

These items have consequential local identity or version-boundary questions.
They should remain visible in issue or curator workflow until a decision is
made.

| Local Work | Local ID | Evidence | Decision needed |
| --- | --- | --- | --- |
| Alexander Nevsky, Op. 78 (cantata) | `sergei-prokofiev-alexander-nevsky-work` | MusicBrainz has `Alexander Nevsky, op. 78` (`bfa47ae2-a283-4785-a614-b88693cd9887`) and `3 Songs from Alexander Nevsky, Op. 78bis` (`b066a40a-9ace-4558-be80-14a93f86e11d`). The local source also has a separate 1938 film-score row. | Decide whether the two local rows represent the same Work, film score versus cantata/suite boundary, or separate curated Works. |
| Alexander Nevsky, Op. 78 (film) | `sergei-prokofiev-alexander-nevsky-2-work` | Same evidence as above; this row is dated 1938 and describes the Eisenstein film. | Decide whether this row should share a Work Group or Work ID with the cantata row, or remain a separate Work. |
| Lieutenant Kijé, Op. 60 | `sergei-prokofiev-lieutenant-kije-work`; context: `sergei-prokofiev-suite-from-lieutenant-kije-work` | MusicBrainz has `Lieutenant Kije Suite, op. 60` (`f168363e-9a3c-34d4-879f-2c20e0b87b52`) and `2 Songs from Lieutenant Kije, Op. 60bis` (`306a677c-f773-4fa0-8069-fc5385f8531b`). | Decide whether the local main-title record should share the suite MBID, share one Work Group with the suite, or remain distinct. |
| Symphony No. 2 in D minor, revised version, Op. 136 | `sergei-prokofiev-symphony-no-2-in-d-minor-revised-version-work` | MusicBrainz exposes `Symphony no. 2 in D minor, op. 40` (`4f0ad7d0-b12f-47b9-ab9e-c53629cd2041`), but the finite artist list did not expose a separate Op. 136 Work. The local row marks Op. 136 as unrealized. | Decide whether Op. 136 remains unresolved as an unrealized/revision boundary rather than inheriting the Op. 40 MBID. |
| War and Peace, Suite, Op. 91 | `sergei-prokofiev-war-and-peace-suite-work` | MusicBrainz has the opera `War and Peace, op. 91` (`03b4640c-5d6d-4a3d-8e21-a299dd896f7a`) and a weaker `Symphonic Suite from "War and Peace"` candidate (`78c692b2-ebf6-4480-b14f-fa3f53ff9822`). | Decide whether the local suite should point to the opera Work, a suite Work, or remain unresolved. |

## Candidate evidence recorded, not written

These have plausible MusicBrainz Work candidates, but the finite list included
nearby parts, suites or sections that make automatic writing unsafe.

| Local Work | Local ID | Best candidate | Reason MBID remains unwritten |
| --- | --- | --- | --- |
| On the Dnieper, Op. 51 | `sergei-prokofiev-on-the-dnieper-work` | `On the Dnieper, op. 51` (`c870f7b4-b2ff-4173-b47b-1d356fa3ae60`) | MusicBrainz also lists `Conclusion` and the Op. 51bis suite close enough to require human review. |
| Peter and the Wolf, Op. 67 | `sergei-prokofiev-peter-and-the-wolf-work` | `Peter and the Wolf, op. 67` (`812b5cc4-a7a0-3809-aa6c-290c9ebd79be`) | MusicBrainz exposes many narrative sections; the resolver filtered many but not all of them. |

## Background authority gaps

These 26 Works had no reliable parent Work in the finite MusicBrainz artist
list. Under the current architecture, missing MusicBrainz coverage is not an
active curator backlog when the local Work identity is otherwise coherent.

- `sergei-prokofiev-ala-i-lolli-work` — Ala i Lolli
- `sergei-prokofiev-american-overture-2-work` — American Overture, Op. 42bis
- `sergei-prokofiev-american-overture-work` — American Overture, Op. 42
- `sergei-prokofiev-andante-from-piano-sonata-no-4-arranged-for-orchestra-work` — Andante from Piano Sonata No. 4, arranged for orchestra, Op. 29bis
- `sergei-prokofiev-andante-from-string-quartet-no-1-arranged-for-string-orchestra-work` — Andante from String Quartet No. 1, arranged for string orchestra, Op. 50bis
- `sergei-prokofiev-cantata-for-the-20th-anniversary-of-the-october-revolution-work` — Cantata for the 20th Anniversary of the October Revolution, Op. 74
- `sergei-prokofiev-kotovsky-work` — Kotovsky
- `sergei-prokofiev-le-pas-d-acier-the-steel-step-work` — Le pas d'acier / The Steel Step, Op. 41
- `sergei-prokofiev-lermontov-work` — Lermontov
- `sergei-prokofiev-piano-concerto-no-6-work` — Piano Concerto No. 6, Op. 134
- `sergei-prokofiev-scythian-suite-work` — Scythian Suite, Op. 20
- `sergei-prokofiev-suite-2-from-romeo-and-juliet-work` — Suite 2 from Romeo and Juliet, Op. 64ter
- `sergei-prokofiev-suite-3-from-romeo-and-juliet-work` — Suite 3 from Romeo and Juliet, Op. 101
- `sergei-prokofiev-suite-from-chout-work` — Suite from Chout, Op. 21bis
- `sergei-prokofiev-suite-from-egyptian-nights-work` — Suite from Egyptian Nights, Op. 61
- `sergei-prokofiev-suite-from-on-the-dnieper-work` — Suite from On the Dnieper, Op. 51bis
- `sergei-prokofiev-suite-from-semyon-kotko-work` — Suite from Semyon Kotko, Op. 81bis
- `sergei-prokofiev-suite-from-the-gambler-four-portraits-and-denouement-work` — Suite from The Gambler ("Four Portraits and Denouement"), Op. 49
- `sergei-prokofiev-suite-from-the-love-for-three-oranges-work` — Suite from The Love for Three Oranges, Op. 33bis
- `sergei-prokofiev-symphonic-march-work` — Symphonic March, Op. 88
- `sergei-prokofiev-the-partisans-in-the-ukrainian-steppes-work` — The Partisans in the Ukrainian Steppes
- `sergei-prokofiev-thirty-years-work` — Thirty Years, Op. 113
- `sergei-prokofiev-tonya-work` — Tonya
- `sergei-prokofiev-two-poems-for-female-chorus-and-orchestra-work` — Two Poems for Female Chorus and Orchestra, Op. 7
- `sergei-prokofiev-urals-rhapsody-from-the-tale-of-the-stone-flower-work` — Urals Rhapsody from The Tale of the Stone Flower, Op. 128
- `sergei-prokofiev-vocal-suite-from-the-fiery-angel-work` — Vocal Suite from The Fiery Angel, Op. 37bis

## Canonical data impact

No canonical Work, Work Group or Performance YAML was changed. The four
identity/version-boundary questions above remain the only active curator
decisions from this review. The other unresolved MusicBrainz alignments are
documented evidence or background authority gaps and should not be surfaced as
PR-blocking curator tasks.
