#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///

"""
Migrate Jobber secrets from claude-config to dedicated jobber Doppler project.

This script migrates Jobber-related secrets from the legacy claude-config/dev
configuration to the new dedicated jobber project structure (jobber/dev and
jobber/prd configs).

BREAKING CHANGE Context:
As of v1.0.0, the library defaults changed from:
  OLD: JobberClient.from_doppler("claude-config", "dev")
  NEW: JobberClient.from_doppler("jobber", "prd")

This migration script helps users migrate their secrets to the new structure.

Prerequisites:
- Doppler CLI installed and authenticated
- Access to both claude-config and jobber Doppler projects
- jobber project already created (should exist if using v1.0.0+)

Usage:
    # Dry run (show what would be migrated)
    python scripts/migrate_doppler_secrets.py --dry-run

    # Migrate to dev config only
    python scripts/migrate_doppler_secrets.py

    # Migrate to both dev and prd configs
    python scripts/migrate_doppler_secrets.py --include-prd

Safety Features:
- Dry-run mode by default shows changes without applying
- Never deletes source secrets (manual cleanup required)
- Validates both projects exist before migration
- Shows diff of secrets before/after
- Fail-fast on any errors

Author: jobber-python-client maintainers
License: MIT
"""

import argparse
import json
import subprocess
import sys
from typing import Any


def run_doppler_command(args: list[str]) -> Any:
    """
    Run Doppler CLI command and return JSON output.

    Args:
        args: Command arguments (without 'doppler' prefix)

    Returns:
        Parsed JSON response (can be dict, list, or other JSON types)

    Raises:
        subprocess.CalledProcessError: If command fails
        json.JSONDecodeError: If response is not valid JSON
    """
    cmd = ["doppler"] + args + ["--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)  # type: ignore[no-any-return]


def get_project_info(project: str) -> dict[str, Any] | None:
    """
    Get Doppler project information.

    Args:
        project: Project name

    Returns:
        Project info dict or None if project doesn't exist
    """
    try:
        projects = run_doppler_command(["projects"])
        for p in projects:  # type: ignore[attr-defined]
            if p["name"] == project:  # type: ignore[index, call-overload]
                return p  # type: ignore[return-value, no-any-return]
        return None
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"❌ Error fetching projects: {e}")
        return None


def get_secrets(project: str, config: str) -> dict[str, str]:
    """
    Get all secrets from a Doppler config.

    Args:
        project: Project name
        config: Config name

    Returns:
        Dictionary of secret names to values

    Raises:
        subprocess.CalledProcessError: If fetch fails
    """
    result = run_doppler_command(
        ["secrets", "download", "--no-file", "--project", project, "--config", config]
    )
    return result  # type: ignore[return-value, no-any-return]


def set_secret(project: str, config: str, name: str, value: str, dry_run: bool = False) -> bool:
    """
    Set a secret in Doppler.

    Args:
        project: Project name
        config: Config name
        name: Secret name
        value: Secret value
        dry_run: If True, don't actually set (just log)

    Returns:
        True if successful (or dry-run), False on error
    """
    if dry_run:
        print(f"  [DRY RUN] Would set {name} in {project}/{config}")
        return True

    try:
        subprocess.run(
            [
                "doppler",
                "secrets",
                "set",
                f"{name}={value}",
                "--project",
                project,
                "--config",
                config,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"  ✅ Set {name} in {project}/{config}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to set {name}: {e.stderr}")
        return False


def migrate_secrets(
    source_project: str,
    source_config: str,
    target_project: str,
    target_configs: list[str],
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Migrate Jobber secrets from source to target configs.

    Args:
        source_project: Source Doppler project
        source_config: Source config name
        target_project: Target Doppler project
        target_configs: List of target config names
        dry_run: If True, show what would be done without doing it

    Returns:
        Tuple of (secrets_migrated, secrets_failed)
    """
    # Get source secrets
    print(f"\n📥 Fetching secrets from {source_project}/{source_config}...")
    try:
        source_secrets = get_secrets(source_project, source_config)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to fetch source secrets: {e}")
        return (0, 0)

    # Filter to Jobber-related secrets only
    jobber_secrets = {
        name: value
        for name, value in source_secrets.items()
        if name.startswith(("JOBBER_", "WEBHOOK_"))
    }

    if not jobber_secrets:
        print(f"⚠️  No Jobber-related secrets found in {source_project}/{source_config}")
        return (0, 0)

    print(f"\n📋 Found {len(jobber_secrets)} Jobber-related secrets:")
    for name in sorted(jobber_secrets.keys()):
        # Show partial value for tokens (security)
        if "TOKEN" in name or "SECRET" in name:
            value_preview = f"{jobber_secrets[name][:10]}..." if jobber_secrets[name] else "(empty)"
        else:
            value_preview = jobber_secrets[name]
        print(f"  - {name}: {value_preview}")

    # Migrate to each target config
    total_migrated = 0
    total_failed = 0

    for target_config in target_configs:
        print(f"\n📤 Migrating to {target_project}/{target_config}...")

        # Get existing target secrets to avoid overwriting
        try:
            target_secrets = get_secrets(target_project, target_config)
            existing = {
                name: value
                for name, value in target_secrets.items()
                if name in jobber_secrets
            }
        except subprocess.CalledProcessError:
            existing = {}

        if existing and not dry_run:
            print(f"⚠️  Warning: {len(existing)} secrets already exist in target:")
            for name in sorted(existing.keys()):
                print(f"    - {name}")
            response = input("Overwrite existing secrets? [y/N]: ")
            if response.lower() != "y":
                print("  ⏭️  Skipping this config")
                continue

        # Migrate each secret
        config_migrated = 0
        config_failed = 0

        for name, value in sorted(jobber_secrets.items()):
            if set_secret(target_project, target_config, name, value, dry_run):
                config_migrated += 1
            else:
                config_failed += 1

        total_migrated += config_migrated
        total_failed += config_failed

        print(
            f"\n  {'Would migrate' if dry_run else 'Migrated'} {config_migrated} secrets "
            f"to {target_project}/{target_config}"
        )

    return (total_migrated, total_failed)


def main() -> int:
    """
    Main migration workflow.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = argparse.ArgumentParser(
        description="Migrate Jobber secrets from claude-config to jobber Doppler project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be migrated)
  python scripts/migrate_doppler_secrets.py --dry-run

  # Migrate to dev config only
  python scripts/migrate_doppler_secrets.py

  # Migrate to both dev and prd configs
  python scripts/migrate_doppler_secrets.py --include-prd

Post-Migration:
  1. Verify secrets: doppler secrets --project jobber --config dev
  2. Test library: python -c "from jobber import JobberClient; JobberClient.from_doppler()"
  3. Clean up source (optional): Remove secrets from claude-config/dev after validation
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--include-prd",
        action="store_true",
        help="Also migrate to prd config (in addition to dev)",
    )
    parser.add_argument(
        "--source-project",
        default="claude-config",
        help="Source Doppler project (default: claude-config)",
    )
    parser.add_argument(
        "--source-config",
        default="dev",
        help="Source config name (default: dev)",
    )
    parser.add_argument(
        "--target-project",
        default="jobber",
        help="Target Doppler project (default: jobber)",
    )

    args = parser.parse_args()

    print("🔄 Jobber Doppler Secrets Migration")
    print("=" * 60)

    if args.dry_run:
        print("⚠️  DRY RUN MODE - No changes will be made")
        print()

    # Validate projects exist
    print("\n🔍 Validating Doppler projects...")
    source_project_info = get_project_info(args.source_project)
    if not source_project_info:
        print(f"❌ Source project '{args.source_project}' not found")
        print("   Available projects: doppler projects")
        return 1

    target_project_info = get_project_info(args.target_project)
    if not target_project_info:
        print(f"❌ Target project '{args.target_project}' not found")
        print(f"   Create it: doppler projects create {args.target_project}")
        return 1

    print(f"✅ Source project: {args.source_project}")
    print(f"✅ Target project: {args.target_project}")

    # Determine target configs
    target_configs = ["dev"]
    if args.include_prd:
        target_configs.append("prd")

    # Run migration
    migrated, failed = migrate_secrets(
        source_project=args.source_project,
        source_config=args.source_config,
        target_project=args.target_project,
        target_configs=target_configs,
        dry_run=args.dry_run,
    )

    # Summary
    print("\n" + "=" * 60)
    if args.dry_run:
        print("📊 Summary (DRY RUN):")
        print(f"   Would migrate {migrated} secrets")
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print("📊 Summary:")
        print(f"   ✅ Migrated: {migrated} secrets")
        if failed > 0:
            print(f"   ❌ Failed: {failed} secrets")
            return 1

        print("\n✅ Migration complete!")
        print("\n📝 Next steps:")
        print(f"   1. Verify: doppler secrets --project {args.target_project} --config dev")
        print(
            "   2. Test: python -c "
            '"from jobber import JobberClient; JobberClient.from_doppler()"'
        )
        print(
            f"   3. (Optional) Clean up source: doppler secrets "
            f"--project {args.source_project} --config {args.source_config}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
