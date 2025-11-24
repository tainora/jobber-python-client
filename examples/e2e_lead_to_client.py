#!/usr/bin/env python3
# /// script
# dependencies = ["jobber-python-client>=0.2.1"]
# ///

"""
End-to-End Lead Capture Workflow

Demonstrates autonomous client creation from lead data sources:
- Website contact forms
- Webhook events
- Email inquiries
- Manual lead entry

AI Agent Orchestration Pattern:
1. Receive lead data (any source)
2. Validate required fields (name, email/phone)
3. Construct GraphQL clientCreate mutation
4. Execute with fail-fast error handling
5. Return visual confirmation URL (jobberWebUri)

Skills Referenced:
- graphql-query-execution: Mutation construction & execution
- visual-confirmation-urls: Include jobberWebUri for verification
- oauth-pkce-doppler: Automatic token management

Workflow Autonomy: 100% (no human intervention after lead received)
"""

import sys
from typing import Any

from jobber import JobberClient
from jobber.exceptions import (
    AuthenticationError,
    ConfigurationError,
    GraphQLError,
    NetworkError,
)


def validate_lead_data(lead: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate lead data has required fields.

    AI Agent Decision Point:
    - Required: firstName, lastName
    - At least one: email OR phone
    - Optional: address fields (improve matching but not required)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    if not lead.get("firstName"):
        errors.append("Missing required field: firstName")
    if not lead.get("lastName"):
        errors.append("Missing required field: lastName")
    if not lead.get("email") and not lead.get("phone"):
        errors.append("Missing contact info: need email OR phone")

    return (len(errors) == 0, errors)


def construct_client_create_mutation(lead: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Construct GraphQL clientCreate mutation from lead data.

    AI Agent Decision Point:
    - ALWAYS include jobberWebUri field (visual-confirmation-urls pattern)
    - Validate mutation structure against schema (use schema introspection)
    - Use variables for type safety (prevent injection)

    Skills: graphql-query-execution, visual-confirmation-urls
    """
    mutation = """
        mutation CreateClient($input: ClientCreateInput!) {
            clientCreate(input: $input) {
                client {
                    id
                    name
                    jobberWebUri
                }
                userErrors {
                    message
                    path
                }
            }
        }
    """

    variables = {
        "input": {
            "firstName": lead["firstName"],
            "lastName": lead["lastName"],
        }
    }

    # Add optional fields if present
    if lead.get("email"):
        variables["input"]["email"] = lead["email"]
    if lead.get("phone"):
        variables["input"]["phone"] = lead["phone"]
    if lead.get("companyName"):
        variables["input"]["companyName"] = lead["companyName"]

    # Add address if available (improves client matching)
    if lead.get("street1") or lead.get("city"):
        variables["input"]["billingAddress"] = {}
        if lead.get("street1"):
            variables["input"]["billingAddress"]["street1"] = lead["street1"]
        if lead.get("street2"):
            variables["input"]["billingAddress"]["street2"] = lead["street2"]
        if lead.get("city"):
            variables["input"]["billingAddress"]["city"] = lead["city"]
        if lead.get("province"):
            variables["input"]["billingAddress"]["province"] = lead["province"]
        if lead.get("postalCode"):
            variables["input"]["billingAddress"]["postalCode"] = lead["postalCode"]
        if lead.get("country"):
            variables["input"]["billingAddress"]["country"] = lead["country"]

    return mutation, variables


def create_client_from_lead(lead: dict[str, Any]) -> dict[str, Any]:
    """
    Execute complete lead → client workflow.

    AI Agent Decision Point:
    - Validate lead data BEFORE API call (fail-fast at boundary)
    - Construct mutation with type-safe variables
    - Handle errors without retry (fail-fast, surface to caller)
    - Return jobberWebUri for visual verification

    Returns:
        {
            "client_id": "gid://...",
            "client_name": "John Doe",
            "jobber_web_url": "https://secure.getjobber.com/...",
        }

    Raises:
        ValueError: Invalid lead data
        GraphQLError: Mutation failed (duplicate client, invalid data)
        AuthenticationError: Token expired/invalid
        NetworkError: Network failure
        ConfigurationError: Missing Doppler secrets

    Error Handling Pattern:
    - NO automatic retry (fail-fast philosophy)
    - NO default values (explicit errors better than silent failures)
    - NO fallback (caller decides recovery strategy)
    - ALL errors propagated with context
    """
    # Step 1: Validate lead data (fail-fast at boundary)
    is_valid, errors = validate_lead_data(lead)
    if not is_valid:
        raise ValueError(f"Invalid lead data: {', '.join(errors)}")

    # Step 2: Construct mutation (type-safe, includes jobberWebUri)
    mutation, variables = construct_client_create_mutation(lead)

    # Step 3: Initialize client (oauth-pkce-doppler skill handles auth)
    try:
        client = JobberClient.from_doppler(
            project="jobber",  # NEW: dedicated Doppler project
            config="prd",
        )
    except ConfigurationError as e:
        print(f"❌ Doppler configuration error: {e}")
        print("Ensure secrets exist in Doppler: doppler secrets --project jobber --config prd")
        raise

    # Step 4: Execute mutation (fail-fast error handling)
    try:
        result = client.execute_query(mutation, variables)
    except AuthenticationError:
        print("❌ Authentication failed - token may be expired")
        print("Run: uv run jobber_auth.py")
        raise
    except NetworkError as e:
        print(f"❌ Network error: {e}")
        raise
    except GraphQLError as e:
        print(f"❌ GraphQL error: {e}")
        if e.context and "errors" in e.context:
            for error in e.context["errors"]:
                print(f"  - {error.get('message', 'Unknown error')}")
        raise

    # Step 5: Extract client data from response
    client_create = result.get("clientCreate", {})

    # Check for user errors (e.g., duplicate client)
    user_errors = client_create.get("userErrors", [])
    if user_errors:
        error_messages = [err["message"] for err in user_errors]
        raise GraphQLError(
            f"Client creation failed: {', '.join(error_messages)}",
            context={"user_errors": user_errors},
        )

    client_data = client_create.get("client", {})
    if not client_data:
        raise GraphQLError(
            "Client creation succeeded but no client data returned",
            context={"response": result},
        )

    # Step 6: Return structured result with visual confirmation URL
    return {
        "client_id": client_data["id"],
        "client_name": client_data["name"],
        "jobber_web_url": client_data["jobberWebUri"],
    }


def main() -> int:
    """
    Example usage: Create client from sample lead data.

    AI Agent Integration:
    - Replace sample_lead with actual data from:
      - Webhook event payload
      - Website form submission
      - Email parser output
      - CRM integration
    """
    # Sample lead data (replace with actual source)
    sample_lead = {
        "firstName": "Jane",
        "lastName": "Smith",
        "email": "jane.smith@example.com",
        "phone": "+1-555-123-4567",
        "companyName": "Smith Roofing Co.",
        "street1": "123 Main St",
        "city": "Vancouver",
        "province": "BC",
        "postalCode": "V6B 1A1",
        "country": "CA",
    }

    print("🔄 Creating Jobber client from lead data...")
    print(f"   Lead: {sample_lead['firstName']} {sample_lead['lastName']}")

    try:
        result = create_client_from_lead(sample_lead)

        print("✅ Client created successfully!")
        print(f"   Client ID: {result['client_id']}")
        print(f"   Client Name: {result['client_name']}")
        print(f"   🔗 View in Jobber: {result['jobber_web_url']}")

        return 0

    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return 1
    except (GraphQLError, AuthenticationError, NetworkError, ConfigurationError) as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
