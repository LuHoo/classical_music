#!/usr/bin/env python3
"""Best Classical scale probe. Grouping is provisional, never canonical identity."""

import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlsplit

from ruamel.yaml import YAML


def tidal_ref(url):
    p = urlsplit(url)
    if p.hostname not in {"tidal.com", "www.tidal.com", "listen.tidal.com"}:
        return None
    m = re.search(r"/(track|album)/(\d+)", p.path)
    return m.groups() if m else None


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v)


def stem(title):
    # Only a triage hint. Colon may separate composer, work, movement, or aria.
    return re.split(r":\s*(?=[IVX]+[a-z]?[.\s]|\d+[.\s])", title, maxsplit=1)[0]


def norm(value):
    text = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def analyse(source, root, start=34, end=333):
    if (
        source.get("source_url")
        != "https://tidal.com/playlist/c11f614b-c011-43b2-be10-639f5cf7e5e3"
        or source.get("playlist", {}).get("attributes", {}).get("lastModifiedAt")
        != "2026-10-02T12:06:31.897Z"
        or not 1 <= start <= end <= 2000
    ):
        raise ValueError(
            "Position-specific corrections require the verified Best Classical snapshot"
        )
    began = time.perf_counter()
    resources = {(r["type"], r["id"]): r for r in source["included"]}
    index = defaultdict(list)
    performances = {}
    yaml = YAML(typ="safe")
    works = {
        w["id"]: w
        for f in (root / "data/works").rglob("*.yaml")
        if (w := yaml.load(f.read_text()))
    }
    for f in sorted((root / "data/performances").rglob("*.yaml")):
        p = yaml.load(f.read_text())
        performances[p["id"]] = p
        for url in strings(p.get("links", {})):
            ref = tidal_ref(url)
            if ref:
                index[ref].append(p["id"])
    selected = [i for i in source["items"] if start <= i["position"] <= end]
    if len(selected) != end - start + 1:
        raise ValueError("Source does not contain the complete requested window")
    rows = []
    for item in selected:
        rid = item["resource"]["id"]
        r = resources.get((item["resource"]["type"], rid), {})
        a = r.get("attributes", {})
        rel = r.get("relationships", {})
        albums = [x["id"] for x in rel.get("albums", {}).get("data", [])]
        artists = [
            resources.get(("artists", x["id"]), {})
            .get("attributes", {})
            .get("name", "?")
            for x in rel.get("artists", {}).get("data", [])
        ]
        usage_ref = rel.get("usageRules", {}).get("data") or {}
        usage = resources.get(("usageRules", usage_ref.get("id")), {}).get(
            "attributes", {}
        )
        rows.append(
            {
                "position": item["position"],
                "track_id": rid,
                "title": a.get("title"),
                "isrc": a.get("isrc"),
                "album_ids": albums,
                "artists": artists,
                "usage_rules": usage,
                "exact_track_matches": sorted(set(index[("track", rid)])),
                "album_link_candidates": sorted(
                    {p for aid in albums for p in index[("album", aid)]}
                ),
                "group_hint": stem(a.get("title", "")),
            }
        )
    groups = []
    for row in rows:
        # Album + provisional work title, not alternating soloists or artist order.
        if 188 <= row["position"] <= 198:
            row["group_hint"] = "Shostakovich: King Lear, Incidental Music, Op. 58a"
        if 117 <= row["position"] <= 119:
            row["group_hint"] = "Sibelius: 3 Late Fragments (Compl. Virtanen)"
        key = (row["group_hint"], row["album_ids"])
        if groups and key == groups[-1]["key"]:
            groups[-1]["tracks"].append(row)
        else:
            groups.append({"key": key, "tracks": [row]})
    for g in groups:
        g.pop("key")
        g["positions"] = [g["tracks"][0]["position"], g["tracks"][-1]["position"]]
        g["exact_performance_anchors"] = sorted(
            {p for t in g["tracks"] for p in t["exact_track_matches"]}
        )
        title = norm(g["tracks"][0]["group_hint"])
        artists = norm(" ".join(a for t in g["tracks"] for a in t["artists"]))
        candidates = []
        for pid, p in performances.items():
            w = works.get(p["work_id"], {})
            wt = norm(w.get("title", ""))
            similarity = SequenceMatcher(None, title, wt).ratio()
            names = [x.get("name", "") for x in p.get("performers", [])]
            overlap = sum(
                bool(n) and norm(n).split()[-1] in artists.split() for n in names
            )
            score = similarity + min(overlap, 2) * 0.2
            candidates.append((score, similarity, overlap, pid, w.get("title")))
        candidates.sort(reverse=True)
        g["title_performer_candidates"] = [
            {
                "performance_id": p,
                "work_title": t,
                "title_score": round(s, 3),
                "name_overlap": o,
            }
            for _, s, o, p, t in candidates[:3]
        ]
    counts = Counter(r["track_id"] for r in rows)
    return {
        "positions": [start, end],
        "track_count": len(rows),
        "distinct_track_ids": len(counts),
        "repeated_occurrences": sum(n - 1 for n in counts.values()),
        "distinct_isrcs": len({r["isrc"] for r in rows if r["isrc"]}),
        "missing_track_metadata": sum(r["title"] is None for r in rows),
        "exact_url_track_occurrences": sum(
            bool(r["exact_track_matches"]) for r in rows
        ),
        "provisional_group_count": len(groups),
        "exact_anchored_group_count": sum(
            bool(g["exact_performance_anchors"]) for g in groups
        ),
        "analysis_seconds": round(time.perf_counter() - began, 3),
        "groups": groups,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--start", type=int, default=34)
    parser.add_argument("--end", type=int, default=333)
    parser.add_argument("--source-run", default="37024628787")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if any("data" in p.resolve().parts for p in [args.output, args.inventory] if p):
        parser.error("Analysis output must remain outside canonical data")
    result = analyse(json.loads(args.source.read_text()), root, args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.inventory:
        inventory = {
            "source_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
            "source_run": f"https://github.com/LuHoo/classical_music/actions/runs/{args.source_run}",
            "positions": result["positions"],
            "provisional_units": [
                {
                    "positions": g["positions"],
                    "title_hint": g["tracks"][0]["group_hint"],
                    "track_ids_isrcs": [
                        [t["track_id"], t["isrc"]] for t in g["tracks"]
                    ],
                    "link_anchor": any(
                        t["exact_track_matches"] or t["album_link_candidates"]
                        for t in g["tracks"]
                    ),
                    "nl_stream_indicated": sum(
                        "STREAM" in t["usage_rules"].get("subscription", [])
                        and t["usage_rules"].get("countryCode") == "NL"
                        for t in g["tracks"]
                    ),
                }
                for g in result["groups"]
            ],
        }
        args.inventory.parent.mkdir(parents=True, exist_ok=True)
        args.inventory.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
        )
    print(json.dumps({k: v for k, v in result.items() if k != "groups"}))
    for n, g in enumerate(result["groups"], 1):
        print(
            n,
            g["positions"],
            g["tracks"][0]["group_hint"],
            "| candidates:",
            [
                (c["performance_id"], c["title_score"], c["name_overlap"])
                for c in g["title_performer_candidates"][:1]
            ],
        )
