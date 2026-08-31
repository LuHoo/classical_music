"""Command-line interface for publication validation.

This module provides a CLI entry point for validating publication-ready data.
It can be called from build scripts and GitHub Actions workflows to fail closed
on broken canonical references.

Usage:
    python -m classical_music.cli_validator
    python -m classical_music.cli_validator --repo /path/to/repo

The command exits with:
    0 = publication validation passed
    1 = publication validation failed (broken references)
"""

import sys
from pathlib import Path
from typing import Optional

from .publication_validator import PublicationValidator


def main(repo_path: Optional[str] = None) -> int:
    """Run publication validation and exit with appropriate code.

    Args:
        repo_path: Optional path to repository root. If None, uses current directory.

    Returns:
        Exit code: 0 for success, 1 for validation errors.
    """
    if repo_path:
        repo_root = Path(repo_path)
    else:
        repo_root = Path.cwd()

    print("\n" + "=" * 70)
    print("PUBLICATION VALIDATION")
    print("=" * 70)
    print(f"\nRepository: {repo_root}")
    print("Validating canonical data for publication...\n")

    validator = PublicationValidator(repo_root)
    result = validator.validate()

    # Print summary
    print(f"\n{result.summary()}")

    if result.error_count() > 0:
        print(f"\n❌ PUBLICATION BLOCKED - {result.error_count()} critical error(s):")
        print("=" * 70)

        for error in result.errors:
            print(f"\n[{error.rule_id}] {error.entity_type}/{error.entity_id}")
            print(f"  Field: {error.field}")
            print(f"  Issue: {error.message}")
            print(f"  File: {error.source_file}")

        if result.warning_count() > 0:
            print(f"\n⚠️  Plus {result.warning_count()} non-blocking warning(s)")

    else:
        if result.warning_count() > 0:
            print(f"\n⚠️  {result.warning_count()} non-blocking warning(s) (publication proceeds)")
        print("\n✅ PUBLICATION APPROVED - All critical references valid")

    print("\n" + "=" * 70)
    print(f"Exit code: {result.exit_code()}")
    print("=" * 70 + "\n")

    return result.exit_code()


if __name__ == "__main__":
    # When run as a module script
    # Allow optional --repo argument
    repo_path = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--repo" and len(sys.argv) > 2:
            repo_path = sys.argv[2]
        else:
            print("Usage: python -m classical_music.cli_validator [--repo /path/to/repo]")
            sys.exit(1)

    exit_code = main(repo_path)
    sys.exit(exit_code)


if __name__ == "classical_music.cli_validator":
    # When run as: python -m classical_music.cli_validator
    exit_code = main()
    sys.exit(exit_code)
