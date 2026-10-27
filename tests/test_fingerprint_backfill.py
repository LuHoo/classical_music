"""Fingerprint backfill tests: synthetic repos and fakes, never live requests.

The backfill is operational only: it reads canonical performance YAML files
and writes a ledger under reports/tidal-maintenance/. These tests pin the
selection order, the fail-closed capture path, the ledger shape shared with
check_tidal_links, and the workflow contracts (issue #396).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import backfill_tidal_fingerprints as backfill  # noqa: E402

NOW = "2026-10-26T12:00:00+00:00"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def synthetic_repo(tmp_path: Path, urls: list[str]) -> Path:
    performances = tmp_path / "data" / "performances"
    performances.mkdir(parents=True)
    yaml = YAML()
    for index, url in enumerate(urls):
        record = {
            "id": f"performance-{index}",
            "work_id": f"work-{index}",
            "links": {"tidal": {"url": url}},
        }
        with (performances / f"performance-{index}.yaml").open("w") as handle:
            yaml.dump(record, handle)
    return tmp_path


class FakeTransport:
    """Stand-in for Transport: canned pages, no network."""

    def __init__(self, pages: dict[str, tuple[int, str]] | None = None):
        self.pages = pages or {}

    def get(self, url, headers=None):
        code, body = self.pages.get(url, (404, ""))
        return _Response(code, url, body)


class _Response:
    def __init__(self, code, url, body):
        self.code = code
        self.url = url
        self.body = body
        self.error = ""


class FakeAPI:
    """Stand-in for TidalAPI: identities by URL, ValueError when dead."""

    def __init__(self, identities: dict[str, dict]):
        self.identities = identities

    def identity(self, url):
        if url in self.identities:
            return self.identities[url]
        raise ValueError("Tidal API unavailable (HTTP 404)")


class SelectionTest(unittest.TestCase):
    def test_never_attempted_first_then_least_recent_and_ties_by_url(self):
        ledger = {
            "version": 1,
            "fingerprints": {
                "https://tidal.com/track/2": {"last_checked": "2026-10-01T00:00:00+00:00"},
                "https://tidal.com/track/1": {"last_checked": "2026-10-02T00:00:00+00:00"},
                "https://tidal.com/track/9": {"isrc": "NLV912300001"},
            },
        }
        urls = [f"https://tidal.com/track/{n}" for n in (5, 4, 3, 2, 1, 9)]
        selected = backfill.select_due(urls, ledger, 3)
        # 3 and 4 and 5 never attempted (sorted by url), then 2 (older than 1); 9 has an identifier.
        self.assertEqual(
            selected,
            ["https://tidal.com/track/3", "https://tidal.com/track/4", "https://tidal.com/track/5"],
        )
        self.assertEqual(
            backfill.select_due(urls, ledger, 5)[-2:],
            ["https://tidal.com/track/2", "https://tidal.com/track/1"],
        )

    def test_limit_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, r"at least 1"):
            backfill.select_due([], {"version": 1, "fingerprints": {}}, 0)


class CaptureTest(unittest.TestCase):
    def test_api_identity_wins_and_records_last_checked(self):
        api = FakeAPI({"https://tidal.com/track/1": {"isrc": "GBLLH2588619", "title": "Synthetic"}})
        entry = backfill.capture("https://tidal.com/track/1", FakeTransport(), api, NOW)
        self.assertEqual(entry, {"isrc": "GBLLH2588619", "title": "Synthetic", "last_checked": NOW})

    def test_dead_url_is_recorded_as_attempt_never_fatal(self):
        entry = backfill.capture("https://tidal.com/track/2", FakeTransport(), FakeAPI({}), NOW)
        self.assertFalse(backfill.has_identifier(entry))
        self.assertEqual(entry["status"], "unavailable")
        self.assertEqual(entry["last_checked"], NOW)


class RunTest(unittest.TestCase):
    def test_run_captures_adopts_and_writes_ledger_outside_data(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1", "https://tidal.com/track/2"])
            ledger_path = root / "reports" / "tidal-maintenance" / "fingerprints.json"
            report_path = root / "reports" / "tidal-maintenance" / "latest.json"
            report_path.parent.mkdir(parents=True)
            report_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "fingerprints": {
                            "https://tidal.com/track/2": {"isrc": "NLV912300002"},
                            "https://tidal.com/track/1": {"title": "no identifier"},
                        }
                    }
                )
            )
            api = FakeAPI({"https://tidal.com/track/1": {"isrc": "GBLLH2588619"}})
            summary = backfill.run(
                root,
                FakeTransport(),
                ledger_path=ledger_path,
                report_path=report_path,
                api=api,
                limit=20,
            )
            self.assertEqual(summary["captured"], 1)
            self.assertEqual(summary["adopted_from_round"], 1)
            self.assertEqual(summary["known_fingerprints"], 2)
            self.assertEqual(summary["remaining"], 0)
            ledger = json.loads(ledger_path.read_text())
            self.assertEqual(ledger["version"], 1)
            self.assertEqual(
                ledger["fingerprints"]["https://tidal.com/track/2"]["isrc"], "NLV912300002"
            )
            self.assertTrue(ledger_path.with_suffix(".md").exists())

    def test_ledger_shape_is_usable_as_check_links_previous(self):
        # check_tidal_links.run() reads previous.get("checks", []) and
        # previous.get("fingerprints", {}); the ledger must satisfy both reads.
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            ledger_path = root / "reports" / "tidal-maintenance" / "fingerprints.json"
            backfill.run(root, FakeTransport(), ledger_path=ledger_path, api=None, limit=20)
            previous = json.loads(ledger_path.read_text())
            self.assertEqual(previous.get("checks", []), [])
            self.assertIsInstance(previous.get("fingerprints", {}), dict)

    def test_malformed_ledger_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            ledger_path = root / "reports" / "tidal-maintenance" / "fingerprints.json"
            ledger_path.parent.mkdir(parents=True)
            ledger_path.write_text(json.dumps({"version": 2, "fingerprints": {}}))
            with self.assertRaisesRegex(ValueError, r"fingerprints mapping"):
                backfill.run(root, FakeTransport(), ledger_path=ledger_path, api=None)

    def test_state_inside_canonical_data_is_rejected_by_cli(self):
        with self.assertRaises(SystemExit) as err:
            backfill.main(["--state", "data/fingerprints.json", "--limit", "20"])
        self.assertEqual(err.exception.code, 2)

    def test_cli_rejects_unbounded_limit(self):
        with self.assertRaises(SystemExit) as err:
            backfill.main(["--limit", "0"])
        self.assertEqual(err.exception.code, 2)


def synthetic_import(root: Path, tracks: list[dict], name: str = "snapshot-test.json") -> Path:
    """Write a playlist-import snapshot with the units[].tracks[] shape."""
    imports = root / "reports" / "playlist-import" / "piano"
    imports.mkdir(parents=True, exist_ok=True)
    path = imports / name
    path.write_text(json.dumps({"schema_version": 1, "units": [{"tracks": tracks}]}))
    return path


class ImportAdoptionTest(unittest.TestCase):
    """Import snapshots are raw Tidal evidence: adopt their ISRCs (#410)."""

    def _ledger(self):
        return {"version": 1, "fingerprints": {}}

    def test_adopts_isrc_for_recognized_snapshot_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            synthetic_import(
                root,
                [
                    {"id": "1", "isrc": "DKECA2295701", "title": "January"},
                    {"id": "2", "isrc": "NOT-A-ISRC"},  # invalid ISRC is skipped
                    {"isrc": "GBLLH2588619"},  # missing id is skipped
                ],
            )
            ledger = self._ledger()
            adopted = backfill.adopt_import_fingerprints(
                ledger, root / "reports" / "playlist-import", ["https://tidal.com/track/1"]
            )
            self.assertEqual(adopted, 1)
            self.assertEqual(
                ledger["fingerprints"]["https://tidal.com/track/1"]["isrc"],
                "DKECA2295701",
            )
            self.assertIn("playlist-import/piano/", ledger["fingerprints"]["https://tidal.com/track/1"]["source"])

    def test_never_overwrites_an_existing_identifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            synthetic_import(root, [{"id": "1", "isrc": "DKECA2295701"}])
            ledger = {
                "version": 1,
                "fingerprints": {"https://tidal.com/track/1": {"isrc": "GBLLH2588619"}},
            }
            self.assertEqual(
                backfill.adopt_import_fingerprints(
                    ledger, root / "reports" / "playlist-import", ["https://tidal.com/track/1"]
                ),
                0,
            )
            self.assertEqual(
                ledger["fingerprints"]["https://tidal.com/track/1"]["isrc"],
                "GBLLH2588619",
            )

    def test_ignores_files_without_units_and_only_reads_known_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            synthetic_import(root, [{"id": "1", "isrc": "DKECA2295701"}])
            other = root / "reports" / "playlist-import" / "piano" / "prepared-120.json"
            other.write_text(json.dumps({"entries": [{"id": "9", "isrc": "DKECA2295701"}]}))
            empty = root / "reports" / "playlist-import" / "piano" / "window-empty.json"
            empty.write_text(json.dumps({"schema_version": 1}))
            ledger = self._ledger()
            adopted = backfill.adopt_import_fingerprints(
                ledger, root / "reports" / "playlist-import", ["https://tidal.com/track/1"]
            )
            self.assertEqual(adopted, 1)
            self.assertNotIn("https://tidal.com/track/9", ledger["fingerprints"])

    def test_snapshot_tracks_outside_canonical_set_are_not_adopted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            synthetic_import(
                root,
                [
                    {"id": "1", "isrc": "DKECA2295701"},
                    {"id": "2", "isrc": "GBLLH2588619"},  # live track, not canonical
                ],
            )
            ledger = self._ledger()
            adopted = backfill.adopt_import_fingerprints(
                ledger, root / "reports" / "playlist-import", ["https://tidal.com/track/1"]
            )
            self.assertEqual(adopted, 1)
            self.assertNotIn("https://tidal.com/track/2", ledger["fingerprints"])

    def test_adoption_matches_url_variants_by_resource_identity(self):
        # Canonical YAML may carry http://www.tidal.com forms; the import
        # snapshot only knows the resource. The fingerprint must land under
        # the exact canonical URL string the checker looks up.
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["http://www.tidal.com/track/1"])
            synthetic_import(root, [{"id": "1", "isrc": "DKECA2295701"}])
            ledger = self._ledger()
            adopted = backfill.adopt_import_fingerprints(
                ledger, root / "reports" / "playlist-import", ["http://www.tidal.com/track/1"]
            )
            self.assertEqual(adopted, 1)
            self.assertEqual(
                ledger["fingerprints"]["http://www.tidal.com/track/1"]["isrc"],
                "DKECA2295701",
            )
            self.assertNotIn("https://tidal.com/track/1", ledger["fingerprints"])

    def test_malformed_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), [])
            bad = synthetic_import(root, [{"id": "1", "isrc": "DKECA2295701"}])
            bad.write_text(json.dumps({"units": [{"tracks": "not-a-list"}]}))
            with self.assertRaisesRegex(ValueError, r"malformed tracks"):
                backfill.adopt_import_fingerprints(
                    self._ledger(), root / "reports" / "playlist-import", []
                )

    def test_run_reports_import_adoption_in_summary_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = synthetic_repo(Path(tmp), ["https://tidal.com/track/1"])
            synthetic_import(root, [{"id": "1", "isrc": "DKECA2295701"}])
            ledger_path = root / "reports" / "tidal-maintenance" / "fingerprints.json"
            summary = backfill.run(
                root, FakeTransport(), ledger_path=ledger_path, api=None, limit=5
            )
            self.assertEqual(summary["adopted_from_imports"], 1)
            self.assertEqual(summary["attempted"], 0, "adopted URLs leave the pending pool")
            self.assertEqual(summary["remaining"], 0)
            report = ledger_path.with_suffix(".md").read_text()
            self.assertIn("adopted from playlist imports 1", report)


class ReportTransparencyTest(unittest.TestCase):
    """The report must show pending statuses, dead anchors, and queue order (#402)."""

    def _run(self, tmp, urls, pages=None):
        root = synthetic_repo(Path(tmp), urls)
        ledger_path = root / "reports" / "tidal-maintenance" / "fingerprints.json"
        summary = backfill.run(
            root, FakeTransport(pages), ledger_path=ledger_path, api=None, limit=5
        )
        return summary, ledger_path

    def test_unavailable_list_names_only_canonical_dead_pending_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = self._run(tmp, ["https://tidal.com/track/1", "https://tidal.com/track/2"])
            self.assertEqual(len(summary["unavailable"]), 2)
            item = summary["unavailable"][0]
            self.assertEqual(item["url"], "https://tidal.com/track/1")
            self.assertEqual(
                item["performances"],
                [
                    {
                        "performance": "performance-0",
                        "work": "work-0",
                        "file": "performance-0.yaml",
                    }
                ],
                "every dead anchor must name the performance to repair",
            )

    def test_status_counts_and_next_up_reflect_select_due_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = self._run(tmp, [f"https://tidal.com/track/{n}" for n in range(1, 4)])
            self.assertEqual(
                summary["pending_status_counts"], {"unavailable": 3}
            )
            self.assertEqual(
                [item["url"] for item in summary["next_up"]],
                [f"https://tidal.com/track/{n}" for n in range(1, 4)],
            )
            self.assertTrue(all(item["last_checked"] != "-" for item in summary["next_up"]))

    def test_next_up_is_empty_when_everything_has_a_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = self._run(tmp, ["https://tidal.com/track/1"])
            root = Path(tmp)
            ledger = json.loads(
                (root / "reports/tidal-maintenance/fingerprints.json").read_text()
            )
            ledger["fingerprints"]["https://tidal.com/track/1"] = {
                "isrc": "GBLLH2588619"
            }
            ledger_path = root / "reports/tidal-maintenance/fingerprints.json"
            ledger_path.write_text(json.dumps(ledger))
            summary = backfill.run(
                root, FakeTransport(), ledger_path=ledger_path, api=None, limit=5
            )
            self.assertEqual(summary["next_up"], [])
            self.assertEqual(summary["unavailable"], [])
            self.assertEqual(summary["pending_status_counts"], {})

    def test_markdown_renders_the_new_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary, ledger_path = self._run(tmp, ["https://tidal.com/track/1"])
            report = ledger_path.with_suffix(".md").read_text()
            self.assertIn("## Pending URLs by status", report)
            self.assertIn("- unavailable: 1", report)
            self.assertIn("## Confirmed unavailable (1)", report)
            self.assertIn("https://tidal.com/track/1", report)
            self.assertIn("performance-0.yaml", report)
            self.assertIn("## Next up (1)", report)


class WorkflowContractTest(unittest.TestCase):
    def test_backfill_workflow_is_bounded_and_read_only(self):
        from ruamel.yaml import YAML as _YAML

        workflow = _YAML(typ="safe").load(
            (REPOSITORY_ROOT / ".github/workflows/tidal-fingerprint-backfill.yml").read_text()
        )
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertEqual(workflow["on"]["schedule"], [{"cron": "13,43 * * * *"}])
        self.assertEqual(
            workflow["on"]["workflow_dispatch"]["inputs"]["limit"]["default"], "60"
        )
        job = workflow["jobs"]["backfill"]
        self.assertEqual(job["timeout-minutes"], 20)
        step = next(
            s for s in job["steps"] if s["name"].startswith("Capture fingerprints")
        )
        self.assertIn("--limit \"$BACKFILL_LIMIT\"", step["run"])
        self.assertNotIn("issues", job.get("permissions", {}))
        restore = next(s for s in job["steps"] if s["name"] == "Restore maintenance rotation state")
        for name in ("state.json", "latest.json", "fingerprints.json"):
            self.assertIn(name, restore["with"]["path"])
        save = next(s for s in job["steps"] if s["name"] == "Save maintenance rotation state")
        for name in ("state.json", "latest.json", "fingerprints.json"):
            self.assertIn(name, save["with"]["path"])

    def test_hourly_round_uses_the_backfill_ledger_as_previous(self):
        from ruamel.yaml import YAML as _YAML

        workflow = _YAML(typ="safe").load(
            (REPOSITORY_ROOT / ".github/workflows/tidal-link-check.yml").read_text()
        )
        round_step = next(
            s
            for s in workflow["jobs"]["round"]["steps"]
            if s["name"] == "Check 20 least recently checked Tidal URLs"
        )
        self.assertIn("--previous reports/tidal-maintenance/fingerprints.json", round_step["run"])
        self.assertIn("--limit 20", round_step["run"])
        self.assertNotIn("--apply", round_step["run"])


if __name__ == "__main__":
    unittest.main()
