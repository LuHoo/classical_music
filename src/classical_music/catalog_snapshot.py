"""Shared, read-only raw catalog snapshot (issue #306).

Publication validation and publication generation both need the canonical
YAML records under ``data/``. Before this module existed they discovered,
read and parsed the same files repeatedly: a single ``validate + build`` run
parsed roughly 50,000 documents while the catalog only holds about 10,000.

A :class:`CatalogSnapshot` parses every catalog file exactly once and is then
shared by the consumers of one logical validation or publication build.

Design invariants
-----------------
Raw, not filtered
    The snapshot stores the parsed source documents, including documents
    without an ``id`` and documents that failed to parse. It is deliberately
    *not* the filtered publication model: source validation must still be able
    to observe records that the publication model would drop.

Immutable
    Parsed documents are frozen recursively (:class:`FrozenDict`,
    :class:`FrozenList`). One consumer can therefore never mutate the records
    another consumer reads. The frozen containers subclass ``dict``/``list``,
    so equality comparison and JSON serialisation keep working.

Request scoped
    There is no process-global cache and no invalidation logic. A snapshot is
    constructed per logical operation and discarded afterwards; every new
    validation or build parses the current contents of ``data/``.

Loader semantics
    ``YAML(typ="safe")`` with ``allow_duplicate_keys = False``, matching the
    loader the publication adapter already used. Duplicate mapping keys and
    syntax errors raise, and are preserved per record in
    :attr:`CatalogRecord.error` instead of being discarded.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Sequence

from ruamel.yaml import YAML

#: Catalog directories read into a snapshot, as ``(directory name, entity type)``.
ENTITY_DIRECTORIES: tuple[tuple[str, str], ...] = (
    ("persons", "Person"),
    ("work-groups", "WorkGroup"),
    ("works", "Work"),
    ("performances", "Performance"),
)

_READ_ONLY = "Catalog snapshot records are read-only"


def _blocked(*_args: Any, **_kwargs: Any) -> Any:
    raise TypeError(_READ_ONLY)


class FrozenDict(dict):
    """A ``dict`` that rejects mutation.

    Subclassing ``dict`` keeps equality, ``json.dump`` and ordinary read
    access free of wrapper overhead; only the mutating API is disabled.
    """

    __slots__ = ()

    __setitem__ = _blocked
    __delitem__ = _blocked
    __ior__ = _blocked
    clear = _blocked
    pop = _blocked
    popitem = _blocked
    setdefault = _blocked
    update = _blocked


class FrozenList(list):
    """A ``list`` that rejects mutation."""

    __slots__ = ()

    __setitem__ = _blocked
    __delitem__ = _blocked
    __iadd__ = _blocked
    __imul__ = _blocked
    append = _blocked
    clear = _blocked
    extend = _blocked
    insert = _blocked
    pop = _blocked
    remove = _blocked
    reverse = _blocked
    sort = _blocked


def freeze(value: Any) -> Any:
    """Return a recursively read-only view of a parsed YAML document."""
    if isinstance(value, dict):
        return FrozenDict((key, freeze(item)) for key, item in value.items())
    if isinstance(value, list):
        return FrozenList(freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class CatalogRecord:
    """One catalog source file and its parsed, frozen content."""

    path: Path
    entity_type: str
    data: Any = None
    error: str | None = None

    @property
    def mapping(self) -> FrozenDict | None:
        """The document when it is a mapping, otherwise ``None``.

        Documents that failed to parse, empty documents and documents whose
        root node is not a mapping are not usable by reference validation.
        """
        return self.data if isinstance(self.data, dict) and self.data else None

    @property
    def record_id(self) -> Any:
        """The ``id`` field when present."""
        mapping = self.mapping
        return mapping.get("id") if mapping is not None else None


@dataclass(frozen=True)
class CatalogSnapshot:
    """An immutable, single-parse view of the canonical catalog."""

    repo_root: Path
    records: Mapping[str, Sequence[CatalogRecord]]
    missing_directories: Mapping[str, Path]

    @classmethod
    def load(
        cls,
        repo_root: Path,
        entity_directories: Sequence[tuple[str, str]] = ENTITY_DIRECTORIES,
    ) -> "CatalogSnapshot":
        """Parse every catalog file under ``repo_root / "data"`` exactly once."""
        data_dir = Path(repo_root) / "data"
        yaml = YAML(typ="safe")
        yaml.allow_duplicate_keys = False

        records: dict[str, Sequence[CatalogRecord]] = {}
        missing: dict[str, Path] = {}

        for directory_name, entity_type in entity_directories:
            directory = data_dir / directory_name
            if not directory.exists():
                missing[entity_type] = directory
                records[entity_type] = ()
                continue

            loaded: list[CatalogRecord] = []
            for path in sorted(directory.glob("**/*.yaml")):
                try:
                    with open(path) as handle:
                        document = yaml.load(handle)
                except Exception as error:  # noqa: BLE001 - preserved per record
                    loaded.append(
                        CatalogRecord(path=path, entity_type=entity_type, error=str(error))
                    )
                    continue
                loaded.append(
                    CatalogRecord(
                        path=path, entity_type=entity_type, data=freeze(document)
                    )
                )
            records[entity_type] = tuple(loaded)

        return cls(
            repo_root=Path(repo_root),
            records=MappingProxyType(records),
            missing_directories=MappingProxyType(missing),
        )

    def records_for(self, entity_type: str) -> Sequence[CatalogRecord]:
        """All records of an entity type, ordered by source path."""
        return self.records.get(entity_type, ())

    def mappings(self, entity_type: str) -> Iterator[CatalogRecord]:
        """Records whose document is a non-empty mapping.

        Unparseable, empty and non-mapping documents are skipped, matching the
        behaviour publication validation had when it globbed the files itself.
        Those documents remain available through :meth:`records_for`.
        """
        for record in self.records_for(entity_type):
            if record.mapping is not None:
                yield record

    def ids(self, entity_type: str) -> frozenset:
        """Every ``id`` present in the raw records of an entity type."""
        return frozenset(
            record.record_id
            for record in self.mappings(entity_type)
            if record.record_id
        )

    def missing_directory(self, entity_type: str) -> Path | None:
        """The expected directory when it does not exist, otherwise ``None``."""
        return self.missing_directories.get(entity_type)
