#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.0",
#     "oauthlib>=3.2.2",
# ]
# ///
"""
Custom Callback Server - Advanced Patterns

Demonstrates custom HTML pages, timeouts, logging, and state validation.
Based on production implementation: /Users/terryli/own/jobber/jobber_auth.py

Usage:
    uv run custom_callback_server.py
"""

import hashlib
import base64
import os
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from oauthlib.oauth2 import WebApplicationClient

# Configuration
AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
CLIENT_ID = "your_client_id_here"
CALLBACK_PORT = 3000
CALLBACK_TIMEOUT = 300  # 5 minutes

# Callback state
callback_data = {
    'code': None,
    'error': None,
    'state': None,
    'received': False
}


class CustomCallbackHandler(BaseHTTPRequestHandler):
    """Advanced callback handler with custom HTML and logging."""

    # Custom HTML templates
    SUCCESS_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authorization Successful</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #4CAF50; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>✓ Authorization Successful!</h1>
        <p>You can now close this window and return to the terminal.</p>
        <script>
            // Auto-close after 2 seconds
            setTimeout(() => window.close(), 2000);
        </script>
    </body>
    </html>
    """

    ERROR_HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authorization Failed</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 50px; }
            h1 { color: #f44336; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <h1>✗ Authorization Failed</h1>
        <p><strong>Error:</strong> {error}</p>
        <p>{description}</p>
    </body>
    </html>
    """

    def do_GET(self):
        """Handle OAuth callback with detailed logging."""
        query = parse_qs(urlparse(self.path).query)

        # Log callback details
        print(f"\n[Callback] Received request: {self.path}")
        print(f"[Callback] Query params: {list(query.keys())}")

        # Success path
        if 'code' in query:
            callback_data['code'] = query['code'][0]
            callback_data['state'] = query.get('state', [None])[0]
            callback_data['received'] = True

            print(f"[Callback] ✓ Authorization code received")
            print(f"[Callback]   Code: {callback_data['code'][:20]}...")
            if callback_data['state']:
                print(f"[Callback]   State: {callback_data['state'][:20]}...")

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.SUCCESS_HTML.encode())

        # Error path
        elif 'error' in query:
            callback_data['error'] = query['error'][0]
            error_desc = query.get('error_description', ['Unknown error'])[0]
            callback_data['received'] = True

            print(f"[Callback] ✗ Authorization error")
            print(f"[Callback]   Error: {callback_data['error']}")
            print(f"[Callback]   Description: {error_desc}")

            html = self.ERROR_HTML_TEMPLATE.format(
                error=callback_data['error'],
                description=error_desc
            )

            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode())

        # Invalid path
        else:
            print(f"[Callback] ✗ Invalid callback (no code or error)")
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP logs (we use custom logging)."""
        pass


def wait_for_callback_with_timeout(server, timeout):
    """Wait for callback with timeout."""
    def server_thread():
        server.handle_request()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        print(f"\n[Timeout] No callback received after {timeout} seconds")
        server.server_close()
        return False

    return callback_data['received']


def main():
    print("=== Custom Callback Server Example ===\n")

    # Generate PKCE + state
    print("1. Generating security parameters...")
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip('=')
    challenge_bytes = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip('=')
    state = base64.urlsafe_b64encode(os.urandom(32)).decode().rstrip('=')
    print(f"   PKCE challenge: {challenge[:20]}...")
    print(f"   State: {state[:20]}...")

    # Start server
    print("\n2. Starting callback server with timeout...")
    server = HTTPServer(('127.0.0.1', CALLBACK_PORT), CustomCallbackHandler)
    redirect_uri = f"http://localhost:{CALLBACK_PORT}/callback"
    print(f"   Listening on {redirect_uri}")
    print(f"   Timeout: {CALLBACK_TIMEOUT} seconds")

    # Build URL with state
    print("\n3. Building authorization URL...")
    client = WebApplicationClient(CLIENT_ID)
    auth_url = client.prepare_request_uri(
        AUTH_URL,
        redirect_uri=redirect_uri,
        code_challenge=challenge,
        code_challenge_method='S256',
        state=state  # CSRF protection
    )

    # Open browser
    print("\n4. Opening browser...")
    webbrowser.open_new(auth_url)
    print(f"   If browser doesn't open, visit manually")

    # Wait with timeout
    print(f"\n5. Waiting for callback (timeout: {CALLBACK_TIMEOUT}s)...")
    received = wait_for_callback_with_timeout(server, CALLBACK_TIMEOUT)
    server.server_close()

    # Validate state (CSRF protection)
    if received and callback_data['code']:
        print("\n6. Validating state parameter...")
        # Note: oauthlib handles state validation automatically
        # This is manual demonstration
        if callback_data['state'] == state:
            print("   ✓ State matches (CSRF protection passed)")
            print(f"\n✓ Success! Authorization code: {callback_data['code'][:20]}...")
            return 0
        else:
            print("   ✗ State mismatch (potential CSRF attack)")
            return 1
    elif received and callback_data['error']:
        print(f"\n✗ Authorization failed: {callback_data['error']}")
        return 1
    else:
        print("\n✗ Timeout - no callback received")
        return 1


if __name__ == '__main__':
    exit(main())
