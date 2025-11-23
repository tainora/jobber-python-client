#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - Batch Operations

Batch operations: Return web URLs for all created resources.

**Use Case**: Create multiple resources, return dashboard with clickable links.

Usage:
    uv run batch_with_urls.py
"""


def main() -> int:
    """Demonstrate batch operations with URLs."""
    print("=== Batch Operations with URLs ===\n")

    print("Pattern for batch create + visual confirmation:\n")
    print("1. Execute batch mutation for each resource")
    print("2. Collect jobberWebUri from each result")
    print("3. Generate summary report with links\n")

    print("Code example:")
    print("""
    created_urls = []

    for item in items_to_create:
        result = client.execute_query(mutation, {'input': item})
        created_urls.append(result['xCreate']['x']['jobberWebUri'])

    print(f"✅ Created {len(created_urls)} items:")
    for i, url in enumerate(created_urls, 1):
        print(f"   {i}. {url}")
    """)

    print("\nExample output:\n")
    print("  Created 5 jobs:")
    print("    1. 🔗 https://secure.getjobber.com/jobs/123")
    print("    2. 🔗 https://secure.getjobber.com/jobs/124")
    print("    3. 🔗 https://secure.getjobber.com/jobs/125")
    print("    4. 🔗 https://secure.getjobber.com/jobs/126")
    print("    5. 🔗 https://secure.getjobber.com/jobs/127")
    print()
    print("  👆 Click links to verify in Jobber\n")

    print("Best practices:")
    print("  • Always collect URLs during batch operations")
    print("  • Display summary with all links")
    print("  • Enable verification of each created resource")
    print("  • Use for automation reports (Slack, email, dashboards)")

    return 0


if __name__ == '__main__':
    exit(main())
