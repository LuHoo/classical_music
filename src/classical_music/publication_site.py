"""Generate Jekyll source pages from publication data."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as html_escape
from itertools import groupby
from pathlib import Path
import re

from ruamel.yaml import YAML
from typing import Any

from classical_music.publication_adapter import PublicationDataAdapter
from classical_music.publication_validator import PublicationValidator


@dataclass(frozen=True)
class SiteGenerationResult:
    """Summary of generated publication pages."""

    output_dir: Path
    page_count: int
    composer_count: int
    work_count: int


class PublicationSiteGenerator:
    """Generate a minimal work-centric Jekyll site from adapter output."""

    def __init__(self, repo_root: Path | None = None, output_dir: Path | None = None):
        if repo_root is None:
            repo_root = Path.cwd()

        self.repo_root = repo_root
        self.output_dir = output_dir or repo_root / "publication"
        self.adapter = PublicationDataAdapter(repo_root)

    def generate(self, validate: bool = True) -> SiteGenerationResult:
        """Generate deterministic Jekyll markdown pages."""
        if validate:
            validation = PublicationValidator(self.repo_root).validate()
            if not validation.passed:
                details = "; ".join(error.message for error in validation.errors[:5])
                raise RuntimeError(f"Publication validation failed: {details}")

        if not self.adapter.load_canonical_data():
            details = "; ".join(self.adapter.errors[:5])
            raise RuntimeError(f"Could not load canonical publication data: {details}")
        self.adapter.adapt_to_publication_model()

        self._reset_output_dir()

        persons = self._sorted_values(self.adapter.persons)
        work_groups = self._sorted_values(self.adapter.work_groups)
        works = self._sorted_values(self.adapter.works)
        performances_by_work = self._performances_by_work()
        works_by_composer = self._group_by(works, "composer_id")
        work_groups_by_composer = self._group_by(work_groups, "composer_id")
        works_by_group = self._group_by(works, "work_group_id")

        page_count = 0
        page_count += self._write_home(persons, works, performances_by_work)
        page_count += self._write_composer_index(persons, works_by_composer)

        for person in persons:
            person_id = person["id"]
            page_count += self._write_composer_page(
                person,
                work_groups_by_composer.get(person_id, []),
                works_by_composer.get(person_id, []),
                works_by_group,
                performances_by_work,
            )

        for work in works:
            page_count += self._write_work_page(work, performances_by_work.get(work["id"], []))

        return SiteGenerationResult(
            output_dir=self.output_dir,
            page_count=page_count,
            composer_count=len(persons),
            work_count=len(works),
        )

    def _reset_output_dir(self) -> None:
        if self.output_dir.exists():
            for path in sorted(self.output_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "composers").mkdir()
        (self.output_dir / "works").mkdir()

    def _write_home(
        self,
        persons: list[dict[str, Any]],
        works: list[dict[str, Any]],
        performances_by_work: dict[str, list[dict[str, Any]]],
    ) -> int:
        recommended_count = sum(1 for work in works if performances_by_work.get(work["id"]))
        body = [
            "---",
            'title: "Collection"',
            "permalink: /publication/",
            "nav_order: 1",
            "---",
            "",
            "# Classical Music Collection",
            "",
            '<div class="publication-summary" aria-label="Collection summary">',
            f'<div class="publication-stat"><strong>{len(persons)}</strong><span>composers</span></div>',
            f'<div class="publication-stat"><strong>{len(works)}</strong><span>works</span></div>',
            (
                f'<div class="publication-stat"><strong>{recommended_count}</strong>'
                "<span>works with recommendations</span></div>"
            ),
            "</div>",
            "",
            '<p class="publication-actions">'
            '<a href="{{ site.baseurl }}/publication/composers/">Browse composers</a>'
            "</p>",
            "",
            "## Works Without Recommendations",
            "",
            '<ul class="work-list">',
        ]

        without_performances = [work for work in works if not performances_by_work.get(work["id"])]
        for work in without_performances[:25]:
            body.append(
                '<li><span class="work-list__row">'
                f'<a class="work-list__title" href="{{{{ site.baseurl }}}}/publication/works/{work["id"]}/">'
                f"{self._html(work['title'])}</a>"
                '<span class="work-list__status">no recommendation yet</span>'
                "</span></li>"
            )
        if len(without_performances) > 25:
            body.append(
                '<li class="publication-note">'
                f"{len(without_performances) - 25} more works without recommendations"
                "</li>"
            )
        body.append("</ul>")

        self._write_page(self.output_dir / "index.md", body)
        return 1

    def _write_composer_index(
        self, persons: list[dict[str, Any]], works_by_composer: dict[str, list[dict[str, Any]]]
    ) -> int:
        body = [
            "---",
            'title: "Composers"',
            "permalink: /publication/composers/",
            "parent: Collection",
            "nav_order: 1",
            "---",
            "",
            "# Composers",
            "",
            '<ul class="composer-list">',
        ]
        for person in persons:
            count = len(works_by_composer.get(person["id"], []))
            body.append(
                f'<li><a href="{{{{ site.baseurl }}}}/publication/composers/{person["id"]}/">'
                f"{self._html(person['name'])}</a> "
                f'<span class="publication-note">{count} works</span></li>'
            )
        body.append("</ul>")

        self._write_page(self.output_dir / "composers" / "index.md", body)
        return 1

    def _write_composer_page(
        self,
        person: dict[str, Any],
        work_groups: list[dict[str, Any]],
        works: list[dict[str, Any]],
        works_by_group: dict[str, list[dict[str, Any]]],
        performances_by_work: dict[str, list[dict[str, Any]]],
    ) -> int:
        body = [
            "---",
            f'title: "{self._front_matter(person["name"])}"',
            f"permalink: /publication/composers/{person['id']}/",
            "parent: Composers",
            "grand_parent: Collection",
            "---",
            "",
            f"# {self._escape(person['name'])}",
            "",
            f'<p class="publication-note">{len(works)} works</p>',
            "",
        ]

        collections = self._composer_collections(person["id"], works)
        displayed = set()
        if collections:
            body.extend(["## Works with opus number", ""])
            by_id = {work["id"]: work for work in works}
            for collection in collections:
                members = [by_id[work_id] for work_id in collection["work_ids"]]
                displayed.update(collection["work_ids"])
                heading = f'<strong>{self._html(collection["title"])}</strong>'
                if collection.get("opus"):
                    heading += f', {self._html(collection["opus"])}'
                if collection.get("date_text"):
                    heading += f' ({self._html(collection["date_text"])})'
                entries = []
                # Repeat an album recommendation once for each consecutive covered run.
                # A gap or a different profile/excerpt starts a new run.
                for _, run in groupby(members, key=lambda work: self._recommendation_key(
                        performances_by_work.get(work["id"], []))):
                    run = list(run)
                    text = ", ".join(self._work_entry(work, [], catalogue_only=True) for work in run)
                    recommendations = self._inline_recommendations(performances_by_work.get(run[0]["id"], []))
                    if recommendations:
                        text += " — " + recommendations
                    entries.append(text)
                body.extend([f'<p class="collection-entry">{heading}, ' + "; ".join(entries) + "</p>", ""])

        remaining = [work for work in works if work["id"] not in displayed]
        sections: dict[str, list[dict[str, Any]]] = {}
        for work in sorted(remaining, key=self._work_sort_key):
            sections.setdefault(work.get("category") or "", []).append(work)
        for category, section_works in sections.items():
            heading = category or ("Other works" if collections else "Works")
            body.extend([f"## {self._escape(heading)}", ""])
            # A family heading is useful for versions, but repeats a singleton's title.
            families = self._group_by(section_works, "work_group_id")
            group_titles = {group["id"]: group["title"] for group in work_groups}
            for group_id, members in families.items():
                if len(members) > 1:
                    body.extend([f"### {self._escape(group_titles[group_id])}", ""])
                for work in sorted(members, key=self._work_sort_key):
                    body.extend(['<p class="work-entry">' + self._work_entry(
                        work, performances_by_work.get(work["id"], [])) + "</p>", ""])

        self._write_page(self.output_dir / "composers" / f"{person['id']}.md", body)
        return 1

    def _composer_collections(self, composer_id: str, works: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Optional editorial layout; membership never changes artistic Work identity."""
        path = self.repo_root / "data" / "publication" / f"{composer_id}.yaml"
        if not path.exists():
            return []
        data = YAML(typ="safe").load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("composer_id") != composer_id:
            raise RuntimeError(f"Invalid composer layout: {path}")
        collections = data.get("collections", [])
        available = {work["id"] for work in works}
        seen = set()
        if not isinstance(collections, list):
            raise RuntimeError(f"Invalid collections: {path}")
        for collection in collections:
            if not isinstance(collection, dict) or not collection.get("title") or not collection.get("work_ids"):
                raise RuntimeError(f"Invalid collection entry: {path}")
            for work_id in collection["work_ids"]:
                if work_id not in available or work_id in seen:
                    raise RuntimeError(f"Unknown, foreign or repeated collection Work {work_id}: {path}")
                seen.add(work_id)
        return collections

    @staticmethod
    def _work_sort_key(work: dict[str, Any]) -> tuple:
        """Natural title order keeps concerto/symphony numbers readable."""
        return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                     for part in re.split(r"(\d+)", work["title"]))

    def _catalogue_text(self, catalogue: Any, title: str = "", exclude: tuple[str, ...] = ()) -> str:
        values = catalogue.items() if isinstance(catalogue, dict) else [("", catalogue)]
        result = []
        normalized_title = re.sub(r"\s+", "", title).casefold()
        for key, value in values:
            if key in exclude or not value:
                continue
            text = str(value)
            if re.sub(r"\s+", "", text).casefold() not in normalized_title:
                result.append(text)
        return ", ".join(result)

    def _work_entry(self, work: dict[str, Any], performances: list[dict[str, Any]], catalogue_only: bool = False) -> str:
        label = (self._catalogue_text(work.get("catalogue"), exclude=("opus",)) if catalogue_only else "") or work["title"]
        entry = ('<span class="gem-mark" aria-label="Gem">💎</span> ' if work.get("gem") else "")
        entry += (f'<a class="work-title" href="{{{{ site.baseurl }}}}/publication/works/{work["id"]}/">'
                  f'<strong>{self._html(label)}</strong></a>')
        if not catalogue_only:
            catalogue = self._catalogue_text(work.get("catalogue"), work["title"])
            if catalogue:
                entry += ", " + self._html(catalogue)
            date = work.get("date_text") or work.get("year")
            if date:
                entry += f" ({self._html(str(date))})"
        recommendations = self._inline_recommendations(performances)
        if recommendations:
            entry += " — " + recommendations
        return entry

    @staticmethod
    def _recommendation_key(performances: list[dict[str, Any]]) -> tuple:
        return tuple((performance.get("tidal_url"), performance.get("profile"), performance.get("excerpt"),
                      tuple((item.get("name"), item.get("role")) for item in performance.get("performers", [])))
                     for performance in performances)

    def _inline_recommendations(self, performances: list[dict[str, Any]]) -> str:
        recommendations = []
        for performance in performances:
            names = ", ".join(item["name"] for item in performance.get("performers", []) if item.get("name")) or "Unknown performers"
            text = f'<em>{self._html(names)}</em>'
            if performance.get("tidal_url"):
                text = f'<a href="{self._html(performance["tidal_url"])}">{text}</a>'
            details = [performance[field] for field in ("profile", "excerpt") if performance.get(field)]
            if details:
                text += " (" + "; ".join(self._html(str(detail)) for detail in details) + ")"
            recommendations.append(text)
        return "; ".join(recommendations)

    def _write_work_page(self, work: dict[str, Any], performances: list[dict[str, Any]]) -> int:
        body = [
            "---",
            f'title: "{self._front_matter(work["title"])}"',
            f"permalink: /publication/works/{work['id']}/",
            "nav_exclude: true",
            "---",
            "",
            f"# {self._escape(work['title'])}",
            "",
        ]
        if work.get("catalogue"):
            body.append(f'<p class="work-meta">Catalogue: {self._html(self._catalogue_text(work["catalogue"]))}</p>')
            body.append("")
        if work.get("gem"):
            body.append('<p><span class="gem-badge">Gem</span></p>')
            body.append("")

        if performances:
            body.append("## Recommended Performances")
            body.append("")
            for profile, profile_performances in self._performances_by_profile(performances):
                if profile:
                    body.append(f'<section class="recommendation-profile"><h3>{self._html(profile)}</h3>')
                    body.append("")
                for performance in profile_performances:
                    body.extend(self._format_performance(performance))
                    body.append("")
                if profile:
                    body.append("</section>")
        else:
            body.append('<p class="recommendation-empty">No recommendation yet.</p>')
            body.append("")

        self._write_page(self.output_dir / "works" / f"{work['id']}.md", body)
        return 1

    def _performances_by_work(self) -> dict[str, list[dict[str, Any]]]:
        grouped = self._group_by(self._sorted_values(self.adapter.performances), "work_id")
        return {work_id: self._sorted_values(performances) for work_id, performances in grouped.items()}

    def _performances_by_profile(self, performances: list[dict[str, Any]]) -> list[tuple[str, list[dict[str, Any]]]]:
        grouped = self._group_by(performances, "profile")
        without_profile = [performance for performance in performances if not performance.get("profile")]
        result: list[tuple[str, list[dict[str, Any]]]] = []
        if without_profile:
            result.append(("", self._sorted_values(without_profile)))
        for profile in sorted(grouped):
            result.append((profile, self._sorted_values(grouped[profile])))
        return result

    def _format_performance(self, performance: dict[str, Any]) -> list[str]:
        performers = performance.get("performers", [])
        formatted_performers = []
        for item in performers:
            name = item.get("name")
            if not name:
                continue
            role = item.get("role")
            if role:
                formatted_performers.append(
                    '<span class="performer-credit">'
                    f'{self._html(name)} <span class="performer-role">({self._html(role)})</span>'
                    "</span>"
                )
            else:
                formatted_performers.append(f'<span class="performer-credit">{self._html(name)}</span>')

        summary = " ".join(formatted_performers) or '<span class="performer-credit">Unknown performers</span>'
        lines = [f'<div class="recommendation-card"><div class="performer-list">{summary}</div>']

        if performance.get("excerpt"):
            lines.append(f'<p class="recommendation-coverage">{self._html(performance["excerpt"])}</p>')

        if performance.get("tidal_url"):
            lines.append('<div class="recommendation-links">')
            lines.append(f'<a href="{performance["tidal_url"]}">Tidal</a>')
        if performance.get("gramophone_ref"):
            if not performance.get("tidal_url"):
                lines.append('<div class="recommendation-links">')
            lines.append(f'<span class="recommendation-meta">Gramophone: {self._html(str(performance["gramophone_ref"]))}</span>')
        if performance.get("tidal_url") or performance.get("gramophone_ref"):
            lines.append("</div>")
        lines.append("</div>")

        return lines

    def _write_page(self, path: Path, lines: list[str]) -> None:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    @staticmethod
    def _sorted_values(items: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        values = list(items.values()) if isinstance(items, dict) else list(items)
        return sorted(values, key=lambda item: (str(item.get("title") or item.get("name") or ""), str(item.get("id") or "")))

    @staticmethod
    def _group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            value = item.get(key)
            if value:
                grouped.setdefault(value, []).append(item)
        return grouped

    @staticmethod
    def _escape(value: str) -> str:
        return value.replace("|", "\\|")

    @staticmethod
    def _html(value: str) -> str:
        return html_escape(str(value), quote=True)

    @staticmethod
    def _front_matter(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    result = PublicationSiteGenerator().generate()
    print(
        f"Generated {result.page_count} publication pages for "
        f"{result.composer_count} composers and {result.work_count} works in {result.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
