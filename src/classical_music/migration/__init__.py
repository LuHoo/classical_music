"""Migration pipeline for legacy Markdown to canonical YAML."""

from .models import (
    PerformanceCandidate,
    ReviewClassification,
    SourceLocation,
    SourceRecord,
    WorkCandidate,
)
from .parser import parse_composer_markdown

__all__ = [
    "SourceLocation",
    "SourceRecord",
    "WorkCandidate",
    "PerformanceCandidate",
    "ReviewClassification",
    "parse_composer_markdown",
]
