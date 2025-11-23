#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jobber-python-client",
# ]
# ///
"""
Visual Confirmation URLs - Quote Dual URLs

Create quote and return BOTH jobberWebUri AND previewUrl.

**Key Difference**:
- jobberWebUri: Internal link (for account users)
- previewUrl: Client Hub link (for customers to view/approve)

Usage:
    uv run quote_dual_urls.py
"""


def main() -> int:
    """Demonstrate quote dual URL pattern."""
    print("=== Create Quote with Dual URLs ===\n")

    # NOTE: This requires a valid client ID and job ID
    # Replace with actual IDs from your Jobber account
    mutation = """
        mutation CreateQuote($input: QuoteCreate!) {
            quoteCreate(input: $input) {
                quote {
                    id
                    quoteNumber
                    jobberWebUri  # <-- Internal web UI link
                    previewUrl    # <-- Client Hub preview link
                }
                userErrors {
                    message
                }
            }
        }
    """

    # Example - would need real client/job IDs
    print("⚠️  Quote creation requires valid client and job IDs")
    print("    Pattern shown - adapt with your IDs\n")
    print("Mutation fields to include:")
    print("  • jobberWebUri  → View in your Jobber account")
    print("  • previewUrl    → Share with client for approval\n")

    print("Workflow:")
    print("  1. Team clicks jobberWebUri → Edit quote in Jobber")
    print("  2. Send previewUrl to customer → Customer approves/declines\n")

    print("Security:")
    print("  • jobberWebUri: Requires login, safe to share within team")
    print("  • previewUrl: Contains token, treat as semi-sensitive")
    print("    - Safe to send to customer")
    print("    - Don't publish publicly")
    print("    - Token may expire")

    return 0


if __name__ == "__main__":
    exit(main())
