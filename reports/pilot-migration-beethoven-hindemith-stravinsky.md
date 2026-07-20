# Pilot Migration Report: Beethoven, Hindemith, Stravinsky

## Scope

This report summarises the pilot migration generated from the current composer Markdown pages for Ludwig van Beethoven, Paul Hindemith and Igor Stravinsky.

The pilot writes Person, Work Group, Work and Performance YAML records. It does not create canonical Recording, Release or Recommendation entities.

## Counts

| Composer | Source | Works | Performances | Gems |
| --- | --- | ---: | ---: | ---: |
| Ludwig van Beethoven | `docs/beethoven.md` | 239 | 102 | 16 |
| Paul Hindemith | `docs/hindemith.md` | 168 | 40 | 2 |
| Igor Stravinsky | `docs/stravinsky.md` | 103 | 34 | 6 |

## Review Notes

- Ludwig van Beethoven line 22: review Work/Work Group boundary for `Piano Concerto No. 1 in C major`.
- Ludwig van Beethoven line 24: review Work/Work Group boundary for `Piano Concerto No. 2 in B♭ major`.
- Ludwig van Beethoven line 52: review Work/Work Group boundary for `Beethoven's arrangement of Opus 61 for Piano in D major`.
- Ludwig van Beethoven line 66: review Work/Work Group boundary for `Choral Fantasy in C minor`.
- Ludwig van Beethoven line 114: review Work/Work Group boundary for `Variations for violin and piano on "Se vuol ballare"`.
- Ludwig van Beethoven line 156: review Work/Work Group boundary for `Piano Trio No. 4 in B♭ major "Gassenhauer"`.
- Ludwig van Beethoven line 244: review Work/Work Group boundary for `Symphony No. 7 in A major`.
- Ludwig van Beethoven line 252: review Work/Work Group boundary for `Violin Sonata No. 10 in G major`.
- Ludwig van Beethoven line 270: review Work/Work Group boundary for `Variations on Wenzel Müller's "Ich bin der Schneider Kakadu," in G major`.
- Ludwig van Beethoven line 294: review Work/Work Group boundary for `Schöne Minka, ich muss scheidem ('Air cosaque')`.
- Ludwig van Beethoven line 424: review Work/Work Group boundary for `Allemande, A`.
- Ludwig van Beethoven line 430: review Work/Work Group boundary for `Presto (Bagatelle), C minor`.
- Ludwig van Beethoven line 434: review Work/Work Group boundary for `Allegretto, C minor`.
- Ludwig van Beethoven line 446: review Work/Work Group boundary for `Allegretto (Bagatelle), C`.
- Ludwig van Beethoven line 484: review Work/Work Group boundary for `Symphony No. 1 in C major`.
- Ludwig van Beethoven line 486: review Work/Work Group boundary for `Symphony No. 2 in D major`.
- Ludwig van Beethoven line 490: review Work/Work Group boundary for `Symphony No. 3 "Eroica" in E♭ major`.
- Ludwig van Beethoven line 492: review Work/Work Group boundary for `Symphony No. 4 in B♭ major`.
- Ludwig van Beethoven line 494: review Work/Work Group boundary for `Symphony No. 6 "Pastoral" in F major`.
- Ludwig van Beethoven line 496: review Work/Work Group boundary for `Symphony No. 7 in A major`.
- Ludwig van Beethoven line 498: review Work/Work Group boundary for `Symphony No. 8 in F major`.
- Paul Hindemith line 18: review Work/Work Group boundary for `Cardillac`.
- Paul Hindemith line 22: review Work/Work Group boundary for `Neues vom Tage`.
- Paul Hindemith line 51: review Work/Work Group boundary for `Hérodiade`.
- Paul Hindemith line 53: review Work/Work Group boundary for `Hérodiade`.
- Paul Hindemith line 162: review Work/Work Group boundary for `Das Marienleben`.
- Paul Hindemith line 211: review Work/Work Group boundary for `Quintet`.
- Igor Stravinsky line 31: review Work/Work Group boundary for `The Firebird`.
- Igor Stravinsky line 33: review Work/Work Group boundary for `Petrushka`.
- Igor Stravinsky line 33: multiple Tidal links for `Petrushka`; confirm whether these are separate Works, profiles, or alternatives.
- Igor Stravinsky line 33: Tidal link label `1911 version` on `Petrushka` needs review.
- Igor Stravinsky line 33: Tidal link label `1947 version` on `Petrushka` needs review.
- Igor Stravinsky line 35: review Work/Work Group boundary for `The Rite of Spring`.
- Igor Stravinsky line 41: review Work/Work Group boundary for `Apollo`.
- Igor Stravinsky line 43: review Work/Work Group boundary for `Le Baiser de la fée`.
- Igor Stravinsky line 69: review Work/Work Group boundary for `Suite from Pulcinella`.
- Igor Stravinsky line 75: review Work/Work Group boundary for `Suite No. 2 for chamber orchestra`.
- Igor Stravinsky line 77: review Work/Work Group boundary for `Suite No. 1 for chamber orchestra`.
- Igor Stravinsky line 79: review Work/Work Group boundary for `Divertimento`.
- Igor Stravinsky line 81: review Work/Work Group boundary for `Quatre études for orchestra`.
- Igor Stravinsky line 87: review Work/Work Group boundary for `Tango for chamber orchestra`.
- Igor Stravinsky line 93: review Work/Work Group boundary for `Scherzo à la russe`.
- Igor Stravinsky line 156: review Work/Work Group boundary for `Les Noces`.
- Igor Stravinsky line 166: review Work/Work Group boundary for `Cantata: Babel`.
- Igor Stravinsky line 174: review Work/Work Group boundary for `The Flood`.
- Igor Stravinsky line 184: review Work/Work Group boundary for `Pastorale`.

## Known Pilot Limitations

- Performer identities are stored as display names unless they are the composer Person records.
- Work Groups are created conservatively, usually one per parsed Work; grouping across related versions should be reviewed manually.
- Source date text is retained as `date_text` rather than forced into a normalized date field.
- Multiple Tidal links on one source line are preserved as separate Performances and flagged for review.
- The pilot may need refinement before it becomes the general migration script.
