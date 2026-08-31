"""Generate Jekyll source pages from publication data."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape as html_escape
from pathlib import Path
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
            "parent: Composers",
            "grand_parent: Collection",
            "---",
            "",
            f"# {self._escape(person['name'])}",
            "",
            f'<p class="publication-note">{len(works)} works</p>',
            "",
        ]

        for group in work_groups:
            group_works = works_by_group.get(group["id"], [])
            if not group_works:
                continue
            body.append(f"## {self._escape(group['title'])}")
            body.append("")
            body.append('<ul class="work-list">')
            for work in group_works:
                body.append(
                    '<li><span class="work-list__row">'
                    f'<a class="work-list__title" href="{{{{ site.baseurl }}}}/publication/works/{work["id"]}/">'
                    f"{self._html(work['title'])}</a>"
                    + (' <span class="gem-badge">Gem</span>' if work.get("gem") else "")
                    + (
                        ""
                        if performances_by_work.get(work["id"])
                        else ' <span class="work-list__status">no recommendation yet</span>'
                    )
                    + "</span></li>"
                )
            body.append("</ul>")
            body.append("")

        self._write_page(self.output_dir / "composers" / f"{person['id']}.md", body)
        return 1

    def _write_work_page(self, work: dict[str, Any], performances: list[dict[str, Any]]) -> int:
        body = [
            "---",
            f'title: "{self._front_matter(work["title"])}"',
            "nav_exclude: true",
            "---",
            "",
            f"# {self._escape(work['title'])}",
            "",
        ]
        if work.get("catalogue"):
            body.append(f'<p class="work-meta">Catalogue: {self._html(str(work["catalogue"]))}</p>')
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
