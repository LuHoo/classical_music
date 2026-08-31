## Licensing and Attribution

This repository contains a curated list of classical music recordings. All text and selection curation in this repository is © by the author and shared under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/), unless otherwise noted.

You are free to copy, share, and adapt the material for any purpose, including commercially — as long as you provide appropriate credit.

Note that any linked audio recordings, images, or external media may be subject to their own copyright and licensing terms. This repository does not host or distribute such media directly.

We’d love to hear from you if you find this collection useful or want to share your own recommendations.

## Internal recording data model

The repository now includes an internal proposal for recording metadata in [data/recordings/README.md](data/recordings/README.md), with example YAML files under [data/recordings](data/recordings).

## Publication site generation

The public collection pages are generated from canonical `data/` through the
publication adapter and validator. The generated Jekyll source is written to
`publication/` during build and is intentionally not committed.

```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
gem install bundler
bundle install
python -m classical_music.cli_validator
python scripts/generate_publication_site.py
bundle exec jekyll build
```

On pull requests, GitHub Actions runs the same validation, generation, and
Jekyll build path without deploying. Deployment to `gh-pages` only runs after a
push to `main`.
