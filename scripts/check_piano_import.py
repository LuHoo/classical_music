#!/usr/bin/env python3
"""Read-only audit of the complete, reviewed Piano source intake."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from classical_music.piano_import import (MANIFEST, audit, check_inventory,
    occurrence_fingerprint, metadata_fingerprint)

if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
