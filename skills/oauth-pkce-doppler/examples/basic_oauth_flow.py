#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.0",
#     "oauthlib>=3.2.2",
# ]
# ///
"""
Basic OAuth 2.0 PKCE Flow - Minimal Example

Demonstrates core OAuth flow without advanced features.
For production use, see: /Users/terryli/own/jobber/skills/oauth-pkce-doppler/assets/oauth_auth_template.py

Usage:
    uv run basic_oauth_flow.py
"""

import hashlib
import base64
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from oauthlib.oauth2 import WebApplicationClient

# Configuration - CUSTOMIZE for your provider
AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
CLIENT_ID = "your_client_id_here"  # In production, load from Doppler
CALLBACK_PORT = 3000

# Shared state for callback
auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)

        if "code" in query:
            auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Success! Close this window.</h1>")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logs


def main():
    print("=== Basic OAuth PKCE Flow ===\n")

    # Step 1: Generate PKCE parameters
    print("1. Generating PKCE parameters...")
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
    challenge_bytes = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip("=")
    print(f"   Code verifier: {verifier[:20]}...")
    print(f"   Code challenge: {challenge[:20]}...")

    # Step 2: Start callback server
    print("\n2. Starting callback server...")
    server = HTTPServer(("127.0.0.1", CALLBACK_PORT), CallbackHandler)
    redirect_uri = f"http://localhost:{CALLBACK_PORT}/callback"
    print(f"   Listening on {redirect_uri}")

    # Step 3: Build authorization URL
    print("\n3. Building authorization URL...")
    client = WebApplicationClient(CLIENT_ID)
    auth_url = client.prepare_request_uri(
        AUTH_URL, redirect_uri=redirect_uri, code_challenge=challenge, code_challenge_method="S256"
    )
    print(f"   URL: {auth_url[:80]}...")

    # Step 4: Open browser
    print("\n4. Opening browser for authorization...")
    webbrowser.open_new(auth_url)
    print("   Waiting for user approval...")

    # Step 5: Wait for callback
    server.handle_request()
    server.server_close()

    if auth_code:
        print(f"\n✓ Success! Received authorization code: {auth_code[:20]}...")
        print("\nNext steps:")
        print("1. Exchange code for tokens using code_verifier")
        print("2. Store tokens in Doppler")
        print("\nSee oauth_auth_template.py for complete implementation")
    else:
        print("\n✗ Failed to receive authorization code")

    return 0 if auth_code else 1


if __name__ == "__main__":
    exit(main())
