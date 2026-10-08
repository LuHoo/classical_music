#!/usr/bin/env python3
"""Audit a reviewed Best Classical window without API access or canonical writes."""
import argparse
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from classical_music.best_classical_import import audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path,
        default=ROOT / 'reports/playlist-import/best-classical/window-333-1998.json')
    args = parser.parse_args()
    print(json.dumps(audit(args.manifest), indent=2))
