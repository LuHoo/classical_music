from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "classify_prokofiev_alignment.py"


def load_policy():
    spec = importlib.util.spec_from_file_location("classify_prokofiev_alignment", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prokofiev_policy_clears_non_consequential_authority_gaps() -> None:
    policy = load_policy()
    payload = json.loads(
        (ROOT / "reports/verification/musicbrainz-work-list-alignment-prokofiev.json").read_text(
            encoding="utf-8"
        )
    )

    result = policy.classify_alignment(payload)

    assert result["coverage_check"]["complete"] is True
    assert result["counts"] == {
        "automatically_resolved_or_safely_classified": 7,
        "unchanged_authority_gap": 26,
        "background_suspicion": 0,
        "action_required": 0,
    }
    op136 = next(
        item
        for item in result["decisions"]
        if item["local_id"].endswith("revised-version-work")
    )
    assert op136["status"] == "automatically_resolved"
    assert op136["decision"] == "retain_as_distinct_local_work"


def test_safe_candidate_is_documented_without_canonical_write() -> None:
    policy = load_policy()
    result = policy.classify_alignment(
        {
            "composer_id": "sergei-prokofiev",
            "issue": 159,
            "unresolved_count": 1,
            "candidate_evidence_not_written": [
                {
                    "local_id": "sergei-prokofiev-on-the-dnieper-work",
                    "title": "On the Dnieper",
                    "best_candidate_musicbrainz_work_id": "candidate",
                }
            ],
        }
    )

    assert result["canonical_data_changed"] is False
    assert result["counts"]["automatically_resolved_or_safely_classified"] == 1
    assert result["decisions"][0]["candidate_musicbrainz_work_id"].startswith("c870")
