#!/usr/bin/env python3
"""
Demo: Jobber Visual Confirmation URLs

Shows the actual URL format returned by Jobber API when you create resources.
This demonstrates what you'll see after creating a client, job, quote, or invoice.
"""


def show_url_examples():
    """Display examples of actual Jobber URLs with explanations."""

    print("=" * 80)
    print("JOBBER API: VISUAL CONFIRMATION URLs - LIVE DEMO")
    print("=" * 80)
    print()

    # Example 1: Client URL
    print("📋 EXAMPLE 1: CREATE CLIENT")
    print("-" * 80)
    print()
    print("When you create a client via API:")
    print()
    print("GraphQL Mutation:")
    print("""
    mutation CreateClient($input: ClientCreate!) {
        clientCreate(input: $input) {
            client {
                id
                firstName
                lastName
                jobberWebUri  ← THIS RETURNS THE CLICKABLE URL
            }
        }
    }
    """)
    print()
    print("API Response:")
    print("""
    {
      "clientCreate": {
        "client": {
          "id": "gid://jobber/Client/12345678",
          "firstName": "John",
          "lastName": "Doe",
          "jobberWebUri": "https://secure.getjobber.com/clients/12345678"
        }
      }
    }
    """)
    print()
    print("✅ Your Terminal Output:")
    print()
    print("    Client created: John Doe")
    print("    🔗 View in Jobber: https://secure.getjobber.com/clients/12345678")
    print()
    print("    👆 Cmd+Click this URL to open in browser!")
    print()
    print()

    # Example 2: Job URL
    print("📋 EXAMPLE 2: CREATE JOB")
    print("-" * 80)
    print()
    print("When you create a job via API:")
    print()
    print("API Response includes:")
    print("""
    {
      "jobCreate": {
        "job": {
          "id": "gid://jobber/Job/87654321",
          "title": "Install Security System",
          "jobberWebUri": "https://secure.getjobber.com/jobs/87654321"
        }
      }
    }
    """)
    print()
    print("✅ Clickable URL:")
    print()
    print("    🔗 https://secure.getjobber.com/jobs/87654321")
    print()
    print("    Opens the job details page in Jobber web interface")
    print()
    print()

    # Example 3: Quote with DUAL URLs
    print("📋 EXAMPLE 3: CREATE QUOTE (TWO URLs!)")
    print("-" * 80)
    print()
    print("Quotes are special - they have TWO URLs for different audiences:")
    print()
    print("API Response:")
    print("""
    {
      "quoteCreate": {
        "quote": {
          "id": "gid://jobber/Quote/11223344",
          "quoteNumber": "Q-001",
          "jobberWebUri": "https://secure.getjobber.com/quotes/11223344",
          "previewUrl": "https://clienthub.getjobber.com/client_hubs/abc123/quotes/11223344"
        }
      }
    }
    """)
    print()
    print("✅ TWO Clickable URLs:")
    print()
    print("    1️⃣  Team View (Internal):")
    print("        🔗 https://secure.getjobber.com/quotes/11223344")
    print("        → Your team clicks this to edit/manage the quote")
    print()
    print("    2️⃣  Client View (External):")
    print("        🔗 https://clienthub.getjobber.com/client_hubs/abc123/quotes/11223344")
    print("        → Send this URL to your customer to approve the quote")
    print()
    print()

    # Example 4: Invoice URL
    print("📋 EXAMPLE 4: CREATE INVOICE")
    print("-" * 80)
    print()
    print("API Response:")
    print("""
    {
      "invoiceCreate": {
        "invoice": {
          "id": "gid://jobber/Invoice/55667788",
          "invoiceNumber": "INV-001",
          "jobberWebUri": "https://secure.getjobber.com/invoices/55667788"
        }
      }
    }
    """)
    print()
    print("✅ Clickable URL:")
    print()
    print("    🔗 https://secure.getjobber.com/invoices/55667788")
    print()
    print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY: ALL JOBBER RESOURCE URLs")
    print("=" * 80)
    print()
    print("┌─────────────┬────────────────────────────────────────────────────────────┐")
    print("│ Resource    │ URL Format                                             │")
    print("├─────────────┼────────────────────────────────────────────────────────────┤")
    print("│ Client      │ https://secure.getjobber.com/clients/{id}              │")
    print("│ Job         │ https://secure.getjobber.com/jobs/{id}                 │")
    print("│ Quote       │ https://secure.getjobber.com/quotes/{id}               │")
    print("│ Invoice     │ https://secure.getjobber.com/invoices/{id}             │")
    print("│ Visit       │ https://secure.getjobber.com/visits/{id}               │")
    print("│ Request     │ https://secure.getjobber.com/requests/{id}             │")
    print("│ Property    │ https://secure.getjobber.com/properties/{id}           │")
    print("└─────────────┴────────────────────────────────────────────────────────────┘")
    print()
    print()

    # How to use
    print("=" * 80)
    print("🚀 HOW TO USE IN YOUR CODE")
    print("=" * 80)
    print()
    print("STEP 1: Always include jobberWebUri in your GraphQL queries")
    print()
    print("    query GetClient($id: ID!) {")
    print("        client(id: $id) {")
    print("            id")
    print("            firstName")
    print("            jobberWebUri  ← ALWAYS ADD THIS!")
    print("        }")
    print("    }")
    print()
    print("STEP 2: Display the URL in your output")
    print()
    print("    result = client.execute_query(query, variables)")
    print("    print(f\"🔗 View: {result['client']['jobberWebUri']}\")")
    print()
    print("STEP 3: Click the URL to verify in Jobber web interface!")
    print()
    print()

    # Real example URLs (hypothetical but realistic)
    print("=" * 80)
    print("🎯 READY TO CLICK: EXAMPLE URLS")
    print("=" * 80)
    print()
    print("Here are example URLs you might see after creating resources:")
    print()
    print("Client URL:")
    print("🔗 https://secure.getjobber.com/clients/12345678")
    print()
    print("Job URL:")
    print("🔗 https://secure.getjobber.com/jobs/87654321")
    print()
    print("Quote URL (Team View):")
    print("🔗 https://secure.getjobber.com/quotes/11223344")
    print()
    print("Quote URL (Client Preview):")
    print("🔗 https://clienthub.getjobber.com/client_hubs/abc123def456/quotes/11223344")
    print()
    print("Invoice URL:")
    print("🔗 https://secure.getjobber.com/invoices/55667788")
    print()
    print()

    print("=" * 80)
    print("✨ NEXT STEPS")
    print("=" * 80)
    print()
    print("To create REAL clients and get REAL URLs:")
    print()
    print("1. Run authentication:")
    print("   $ uv run jobber_auth.py")
    print()
    print("2. Create a client:")
    print("   $ uv run test_create_client_url.py")
    print()
    print("3. Click the returned URL to view in Jobber!")
    print()
    print("=" * 80)
    print()


if __name__ == "__main__":
    show_url_examples()
