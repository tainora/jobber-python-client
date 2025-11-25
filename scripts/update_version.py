#!/usr/bin/env python3
"""
Update project version in pyproject.toml for semantic-release.

This script updates ONLY the [project] version field, avoiding the bug
where sed overwrites tool.ruff.target-version and tool.mypy.python_version.

Usage:
    python scripts/update_version.py <new_version>

Example:
    python scripts/update_version.py 1.2.0

Note: This script is called by semantic-release via .releaserc.json prepareCmd.
"""

import re
import sys
from pathlib import Path


def update_project_version(filepath: Path, new_version: str) -> None:
    """
    Update [project] version in pyproject.toml.

    Args:
        filepath: Path to pyproject.toml
        new_version: New version string (e.g., "1.2.0")

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        ValueError: If [project] section or version field not found
    """
    content = filepath.read_text()

    # Pattern matches version = "..." ONLY in [project] section
    # Uses lookahead/lookbehind to ensure we're in the right section
    pattern = r'(\[project\].*?^version = )"[^"]*"'

    # Search for the pattern
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(
            "Could not find [project] section with version field in pyproject.toml"
        )

    # Replace with new version
    updated_content = re.sub(
        pattern,
        rf'\1"{new_version}"',
        content,
        count=1,  # Only replace first occurrence
        flags=re.MULTILINE | re.DOTALL,
    )

    # Verify change was made
    if updated_content == content:
        raise ValueError(f"Version update failed - no changes made to {filepath}")

    # Write back
    filepath.write_text(updated_content)
    print(f"✅ Updated [project] version to {new_version} in {filepath}")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_version.py <new_version>")
        print("Example: python scripts/update_version.py 1.2.0")
        return 1

    new_version = sys.argv[1]
    pyproject_path = Path("pyproject.toml")

    try:
        update_project_version(pyproject_path, new_version)
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
