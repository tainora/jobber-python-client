#!/usr/bin/env python3
"""
Example webhook handler for Jobber GraphQL API events.

This example demonstrates how to:
1. Validate webhook signatures using HMAC-SHA256
2. Parse webhook event payloads
3. Route events to different handlers based on event type
4. Handle specific events (QUOTE_APPROVED, INVOICE_PAID)

Prerequisites:
- Flask installed: pip install flask
- Webhook secret stored in Doppler: JOBBER_WEBHOOK_SECRET
- Webhook URL configured in Jobber Developer Portal: https://your-domain.com/webhook

For local development:
1. Install ngrok: brew install ngrok
2. Start this webhook handler: python examples/webhook_handler.py
3. Start ngrok tunnel: ngrok http 5000
4. Configure webhook URL in Jobber: https://abc123.ngrok.io/webhook
5. Test with curl:
   curl -X POST http://localhost:5000/webhook \
     -H "Content-Type: application/json" \
     -H "X-Jobber-Signature: sha256=$(echo -n '{"event_type":"quote.approved"}' | \
        openssl dgst -sha256 -hmac 'your_secret' | cut -d' ' -f2)" \
     -d '{"event_type":"quote.approved","data":{"id":"123"}}'

Production deployment:
- Deploy to Heroku, Railway, or Fly.io
- Configure HTTPS (required by Jobber)
- Set JOBBER_WEBHOOK_SECRET environment variable
- Update webhook URL in Jobber Developer Portal
"""

# /// script
# dependencies = [
#   "flask>=3.0.0",
# ]
# ///

import os
import subprocess

from flask import Flask, jsonify, request

from jobber.webhooks import (
    CLIENT_CREATE,
    INVOICE_PAID,
    QUOTE_APPROVED,
    VISIT_COMPLETE,
    parse_event,
    validate_signature,
)

app = Flask(__name__)


def get_webhook_secret() -> str:
    """Get webhook secret from Doppler secrets manager."""
    try:
        result = subprocess.run(
            ["doppler", "secrets", "get", "JOBBER_WEBHOOK_SECRET", "--plain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Warning: Failed to fetch JOBBER_WEBHOOK_SECRET from Doppler")
        print("Using environment variable as fallback")
        return os.getenv("JOBBER_WEBHOOK_SECRET", "")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Webhook endpoint that receives and processes Jobber events.

    Validates signature, parses event, and routes to appropriate handler.
    """
    # Get webhook secret
    secret = get_webhook_secret()
    if not secret:
        return jsonify({"error": "Webhook secret not configured"}), 500

    # Get signature from header
    signature = request.headers.get("X-Jobber-Signature", "")
    if not signature:
        return jsonify({"error": "Missing X-Jobber-Signature header"}), 400

    # Validate signature
    payload = request.get_data()
    try:
        if not validate_signature(payload, signature, secret):
            print(f"❌ Invalid webhook signature: {signature[:20]}...")
            return jsonify({"error": "Invalid signature"}), 401
    except ValueError as e:
        print(f"❌ Signature validation error: {e}")
        return jsonify({"error": str(e)}), 400

    print("✅ Webhook signature validated")

    # Parse event
    try:
        event = parse_event(payload)
        event_type = event.get("event_type", "unknown")
        event_data = event.get("data", {})
    except Exception as e:
        print(f"❌ Failed to parse webhook event: {e}")
        return jsonify({"error": "Invalid event payload"}), 400

    # Route to event handlers
    print(f"📬 Received webhook event: {event_type}")

    if event_type == QUOTE_APPROVED:
        handle_quote_approved(event_data)
    elif event_type == INVOICE_PAID:
        handle_invoice_paid(event_data)
    elif event_type == VISIT_COMPLETE:
        handle_visit_complete(event_data)
    elif event_type == CLIENT_CREATE:
        handle_client_create(event_data)
    else:
        print(f"⚠️  Unhandled event type: {event_type}")

    return jsonify({"status": "ok"}), 200


def handle_quote_approved(data: dict) -> None:
    """
    Handle QUOTE_APPROVED event.

    When a quote is approved in Jobber Client Hub:
    1. Log the approval
    2. Create visit/job for the approved quote
    3. Send confirmation email to client
    4. Notify team via Slack/email
    """
    quote_id = data.get("id", "unknown")
    client_name = data.get("client", {}).get("name", "unknown")

    print(f"✅ Quote approved: {quote_id}")
    print(f"   Client: {client_name}")
    print("   Next steps: Create visit, send confirmation email")

    # TODO: Implement business logic
    # - Create visit via GraphQL mutation
    # - Send client confirmation email
    # - Notify team via Slack


def handle_invoice_paid(data: dict) -> None:
    """
    Handle INVOICE_PAID event.

    When an invoice is paid via Jobber Client Hub:
    1. Log the payment
    2. Update accounting system
    3. Send thank-you email to client
    4. Trigger follow-up workflow (satisfaction survey, renewal quote)
    """
    invoice_id = data.get("id", "unknown")
    client_name = data.get("client", {}).get("name", "unknown")
    amount = data.get("total", 0)

    print(f"💰 Invoice paid: {invoice_id}")
    print(f"   Client: {client_name}")
    print(f"   Amount: ${amount}")
    print("   Next steps: Update accounting, send thank-you email")

    # TODO: Implement business logic
    # - Update QuickBooks/Xero
    # - Send thank-you email
    # - Schedule satisfaction survey (30 days)


def handle_visit_complete(data: dict) -> None:
    """
    Handle VISIT_COMPLETE event.

    When a visit is marked complete:
    1. Log completion
    2. Create invoice from completed visit
    3. Send invoice to client
    """
    visit_id = data.get("id", "unknown")
    client_name = data.get("client", {}).get("name", "unknown")

    print(f"🏁 Visit completed: {visit_id}")
    print(f"   Client: {client_name}")
    print("   Next steps: Create invoice, send to client")

    # TODO: Implement business logic
    # - Create invoice via GraphQL mutation
    # - Send invoice to client


def handle_client_create(data: dict) -> None:
    """
    Handle CLIENT_CREATE event.

    When a new client is created:
    1. Log the new client
    2. Send welcome email
    3. Add to CRM/marketing automation
    """
    client_id = data.get("id", "unknown")
    client_name = data.get("name", "unknown")
    email = data.get("email", "unknown")

    print(f"👤 New client created: {client_id}")
    print(f"   Name: {client_name}")
    print(f"   Email: {email}")
    print("   Next steps: Send welcome email, add to CRM")

    # TODO: Implement business logic
    # - Send welcome email
    # - Add to Mailchimp/ActiveCampaign
    # - Create CRM record


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Jobber Webhook Handler")
    print("=" * 70)
    print()
    print("Webhook endpoint: http://localhost:5000/webhook")
    print("Health check: http://localhost:5000/health")
    print()
    print("For local development with ngrok:")
    print("  1. Start this handler: python examples/webhook_handler.py")
    print("  2. Start ngrok: ngrok http 5000")
    print("  3. Configure webhook URL in Jobber: https://abc123.ngrok.io/webhook")
    print()
    print("=" * 70)
    print()

    app.run(host="0.0.0.0", port=5000, debug=True)
