#!/usr/bin/env python3
"""Read-only canonical audit plus generated Chamber publication output."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from classical_music.chamber_import import (MANIFEST, audit, check_inventory,
                                           occurrence_fingerprint)

if __name__ == "__main__":
    print(json.dumps(audit(ROOT), indent=2))
