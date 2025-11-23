#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - Quick Win Validation Pattern

Demonstrates how to get web UI links from Jobber API for visual confirmation
of API operations. Users can click links to verify created/updated resources
in Jobber's web interface.

**The Pattern**: Jobber's GraphQL API returns `jobberWebUri` fields on most
resources (clients, jobs, quotes, invoices). Always include this field in
queries to provide users with clickable confirmation links.

Usage:
    uv run examples/visual_confirmation_urls.py
"""

from jobber import JobberClient


def example_create_client_with_url() -> None:
    """
    Create client and return web URL for visual confirmation.

    **Quick Win**: User can click link to see client in Jobber web UI.
    """
    print("=== Create Client with Web URL ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    # CRITICAL: Include jobberWebUri in mutation response
    mutation = """
        mutation CreateClient($input: ClientCreateInput!) {
            clientCreate(input: $input) {
                client {
                    id
                    firstName
                    lastName
                    jobberWebUri  # <-- WEB UI LINK
                }
                userErrors {
                    message
                    path
                }
            }
        }
    """

    variables = {"input": {"firstName": "John", "lastName": "Doe", "companyName": "Doe Industries"}}

    result = client.execute_query(mutation, variables)

    if result["clientCreate"]["userErrors"]:
        errors = result["clientCreate"]["userErrors"]
        print(f"❌ Failed to create client: {errors}")
        return

    created = result["clientCreate"]["client"]

    # Visual feedback with clickable link
    print("✅ Client created successfully!")
    print(f"   ID: {created['id']}")
    print(f"   Name: {created['firstName']} {created['lastName']}")
    print(f"   🔗 View in Jobber: {created['jobberWebUri']}")
    print("\n   👆 Click to verify in web interface")


def example_query_clients_with_urls() -> None:
    """
    Query clients and show web URLs for each.

    **Use Case**: Automation reports with clickable links.
    """
    print("\n=== Query Clients with Web URLs ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    # CRITICAL: Include jobberWebUri in query
    query = """
        query GetRecentClients {
            clients(first: 5) {
                nodes {
                    id
                    firstName
                    lastName
                    jobberWebUri  # <-- WEB UI LINK
                }
            }
        }
    """

    result = client.execute_query(query)

    print("Recent clients:\n")
    for client_data in result["clients"]["nodes"]:
        print(f"• {client_data['firstName']} {client_data['lastName']}")
        print(f"  🔗 {client_data['jobberWebUri']}\n")


def example_create_quote_with_preview_url() -> None:
    """
    Create quote and return BOTH jobberWebUri AND previewUrl.

    **Key Difference**:
    - jobberWebUri: Internal link (for account users)
    - previewUrl: Client Hub link (for customers to view/approve)
    """
    print("\n=== Create Quote with Dual URLs ===\n")

    # NOTE: This requires a valid client ID and job ID
    # Replace with actual IDs from your Jobber account
    print("⚠️  Quote creation requires valid client and job IDs")
    print("    Pattern shown - adapt with your IDs\n")
    print("Example setup:")
    print("    client = JobberClient.from_doppler('claude-config', 'dev')\n")
    print("Mutation fields to include:")
    print("  • jobberWebUri  → View in your Jobber account")
    print("  • previewUrl    → Share with client for approval")


def example_url_based_validation() -> None:
    """
    URL-based validation: Check resource exists by testing web URL.

    **Quick Win Validation**: If jobberWebUri returns valid URL,
    resource was created successfully.
    """
    print("\n=== URL-Based Validation Pattern ===\n")

    client = JobberClient.from_doppler("claude-config", "dev")

    query = """
        query GetClient($id: ID!) {
            client(id: $id) {
                id
                firstName
                jobberWebUri
            }
        }
    """

    # Example with hypothetical ID
    example_id = "gid://jobber/Client/123456"

    try:
        result = client.execute_query(query, variables={"id": example_id})

        if result["client"] and result["client"]["jobberWebUri"]:
            print("✅ Validation passed:")
            print(f"   Resource exists: {result['client']['firstName']}")
            print(f"   Web URL present: {result['client']['jobberWebUri']}")
            print("   Status: CONFIRMED")
        else:
            print("❌ Validation failed: No web URL returned")

    except Exception as e:
        print(f"❌ Validation failed: {e}")


def example_batch_operations_with_urls() -> None:
    """
    Batch operations: Return web URLs for all created resources.

    **Use Case**: Create multiple jobs, return dashboard with clickable links.
    """
    print("\n=== Batch Operations with URLs ===\n")

    print("Pattern for batch create + visual confirmation:\n")
    print("1. Execute batch mutation")
    print("2. Collect jobberWebUri from each result")
    print("3. Generate summary report with links\n")

    print("Example output:")
    print("  Created 5 jobs:")
    print("    • Job #1001: 🔗 https://secure.getjobber.com/jobs/123")
    print("    • Job #1002: 🔗 https://secure.getjobber.com/jobs/124")
    print("    • Job #1003: 🔗 https://secure.getjobber.com/jobs/125")
    print("  ")
    print("  Click links to verify in Jobber")


def print_best_practices() -> None:
    """Print best practices for visual confirmation pattern."""
    print("\n" + "=" * 70)
    print("BEST PRACTICES: Visual Confirmation URLs")
    print("=" * 70 + "\n")

    print("1. ALWAYS include jobberWebUri in mutations:")
    print("   mutation CreateX { xCreate { x { id jobberWebUri } } }\n")

    print("2. ALWAYS show web URL in success messages:")
    print("   print(f'✅ Created! View: {result[\"jobberWebUri\"]}')\n")

    print("3. For quotes, include BOTH URLs:")
    print("   • jobberWebUri  → Internal team view")
    print("   • previewUrl    → Client approval link\n")

    print("4. URL-based validation:")
    print("   • If jobberWebUri present → Resource exists")
    print("   • If jobberWebUri missing → Creation failed\n")

    print("5. Use URLs in automation reports:")
    print("   • Slack notifications with clickable links")
    print("   • Email summaries with dashboard links")
    print("   • Terminal output with ANSI hyperlinks\n")

    print("=" * 70)


def main() -> None:
    """Run all visual confirmation examples."""
    print("\n" + "=" * 70)
    print("Visual Confirmation URLs - Quick Win Validation")
    print("=" * 70 + "\n")

    print("This example demonstrates how to get web UI links from Jobber API")
    print("for visual confirmation of API operations.\n")

    try:
        # Example 1: Create with URL
        example_create_client_with_url()

        # Example 2: Query with URLs
        example_query_clients_with_urls()

        # Example 3: Quote dual URLs
        example_create_quote_with_preview_url()

        # Example 4: URL validation
        example_url_based_validation()

        # Example 5: Batch operations
        example_batch_operations_with_urls()

        # Best practices
        print_best_practices()

        print("\n✅ Examples completed!")
        print("\nNext steps:")
        print("1. Add jobberWebUri to your GraphQL queries")
        print("2. Include web links in success messages")
        print("3. Enable users to visually verify API operations")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("• Ensure Doppler secrets configured")
        print("• Check token has not expired")
        print("• Verify GraphQL query syntax")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
