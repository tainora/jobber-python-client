#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.0",
#     "oauthlib>=3.2.2",
# ]
# ///
"""
Jobber OAuth 2.0 Authorization Script

One-time authentication to obtain and store OAuth tokens in Doppler.

Usage:
    uv run jobber_auth.py

Requirements:
    - Doppler CLI installed and configured
    - JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET in Doppler
    - Browser access for authorization

Errors:
    - Raises on any failure (no retry, no fallback)
    - Check exit code: 0 = success, 1 = failure
"""

import hashlib
import base64
import os
import webbrowser
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from typing import Optional, Tuple

import requests
from oauthlib.oauth2 import WebApplicationClient


# Configuration
JOBBER_AUTH_URL = "https://api.getjobber.com/api/oauth/authorize"
JOBBER_TOKEN_URL = "https://api.getjobber.com/api/oauth/token"
PORT_RANGE = range(3000, 3011)
DOPPLER_PROJECT = "claude-config"
DOPPLER_CONFIG = "dev"


class AuthorizationError(Exception):
    """OAuth authorization failed"""

    pass


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle single OAuth callback request"""

    authorization_code: Optional[str] = None
    error: Optional[str] = None
    state: Optional[str] = None

    def do_GET(self) -> None:
        """Process OAuth callback GET request"""
        query = parse_qs(urlparse(self.path).query)

        # Store values at class level for retrieval after server shuts down
        if "code" in query:
            OAuthCallbackHandler.authorization_code = query["code"][0]
            OAuthCallbackHandler.state = query.get("state", [None])[0]

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <html><body>
                <h1>Authorization Successful</h1>
                <p>You can close this window and return to the terminal.</p>
                <script>window.close();</script>
                </body></html>
            """)
        elif "error" in query:
            OAuthCallbackHandler.error = query["error"][0]
            error_desc = query.get("error_description", ["Unknown error"])[0]

            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"""
                <html><body>
                <h1>Authorization Failed</h1>
                <p>Error: {error_desc}</p>
                </body></html>
            """.encode()
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        """Suppress HTTP server logs"""
        pass


def generate_pkce_pair() -> Tuple[str, str]:
    """
    Generate PKCE code_verifier and code_challenge.

    Returns:
        (code_verifier, code_challenge)

    Raises:
        No exceptions (uses os.urandom which is always available)
    """
    # Generate code_verifier (43-128 characters, URL-safe)
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8").rstrip("=")

    # Generate code_challenge (SHA256 hash of verifier)
    challenge_bytes = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode("utf-8").rstrip("=")

    return code_verifier, code_challenge


def find_available_port() -> Tuple[HTTPServer, int]:
    """
    Find an available port in PORT_RANGE and create HTTP server.

    Returns:
        (server, port)

    Raises:
        RuntimeError: No available ports in range
    """
    for port in PORT_RANGE:
        try:
            server = HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
            return server, port
        except OSError:
            continue

    raise RuntimeError(
        f"No available ports in range {PORT_RANGE.start}-{PORT_RANGE.stop - 1}. "
        f"Close applications using these ports or specify different range."
    )


def load_client_credentials() -> Tuple[str, str]:
    """
    Load client ID and secret from Doppler.

    Returns:
        (client_id, client_secret)

    Raises:
        RuntimeError: Doppler CLI failed or credentials not found
    """
    try:
        result = subprocess.run(
            [
                "doppler",
                "secrets",
                "get",
                "JOBBER_CLIENT_ID",
                "JOBBER_CLIENT_SECRET",
                "--project",
                DOPPLER_PROJECT,
                "--config",
                DOPPLER_CONFIG,
                "--plain",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )

        lines = result.stdout.strip().split("\n")
        if len(lines) != 2:
            raise RuntimeError(
                f"Expected 2 lines from Doppler, got {len(lines)}. "
                f"Ensure JOBBER_CLIENT_ID and JOBBER_CLIENT_SECRET exist."
            )

        return lines[0], lines[1]

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Doppler CLI failed: {e.stderr}. "
            f"Ensure Doppler is installed and configured for project={DOPPLER_PROJECT}, config={DOPPLER_CONFIG}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("Doppler CLI timeout after 10s") from e


def exchange_code_for_token(
    code: str, code_verifier: str, client_id: str, client_secret: str, redirect_uri: str
) -> dict:
    """
    Exchange authorization code for access/refresh tokens.

    Args:
        code: Authorization code from callback
        code_verifier: PKCE code verifier
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: Callback URI (must match authorization request)

    Returns:
        Token response dict with keys: access_token, refresh_token, expires_in

    Raises:
        requests.HTTPError: Token exchange failed
    """
    response = requests.post(
        JOBBER_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def save_tokens_to_doppler(access_token: str, refresh_token: str, expires_in: int) -> None:
    """
    Save tokens to Doppler secrets.

    Args:
        access_token: OAuth access token
        refresh_token: OAuth refresh token
        expires_in: Token lifetime in seconds

    Raises:
        RuntimeError: Doppler CLI failed to save tokens
    """
    expires_at = int(time.time()) + expires_in

    secrets = {
        "JOBBER_ACCESS_TOKEN": access_token,
        "JOBBER_REFRESH_TOKEN": refresh_token,
        "JOBBER_TOKEN_EXPIRES_AT": str(expires_at),
    }

    for name, value in secrets.items():
        try:
            subprocess.run(
                [
                    "doppler",
                    "secrets",
                    "set",
                    name,
                    "--project",
                    DOPPLER_PROJECT,
                    "--config",
                    DOPPLER_CONFIG,
                    "--silent",
                ],
                input=value,
                text=True,
                check=True,
                capture_output=True,
                timeout=10,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to save {name} to Doppler: {e.stderr}") from e


def main() -> int:
    """
    Run OAuth authorization flow.

    Returns:
        Exit code: 0 = success, 1 = failure
    """
    print("Jobber OAuth 2.0 Authorization")
    print("=" * 50)

    try:
        # Load credentials from Doppler
        print("Loading client credentials from Doppler...")
        client_id, client_secret = load_client_credentials()
        print(f"✓ Client ID: {client_id[:8]}...")

        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        print("✓ Generated PKCE parameters")

        # Start HTTP server
        print("Starting local callback server...")
        server, port = find_available_port()
        redirect_uri = f"http://localhost:{port}/callback"
        print(f"✓ Server listening on port {port}")

        # Build authorization URL
        client = WebApplicationClient(client_id)
        auth_url = client.prepare_request_uri(
            JOBBER_AUTH_URL,
            redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )

        # Open browser
        print("\nOpening browser for authorization...")
        print(f"If browser doesn't open, visit:\n{auth_url}\n")
        webbrowser.open_new(auth_url)

        # Wait for callback (blocks until one request received)
        print("Waiting for authorization (approve in browser)...")
        server.handle_request()
        server.server_close()

        # Check for errors
        if OAuthCallbackHandler.error:
            raise AuthorizationError(f"Authorization failed: {OAuthCallbackHandler.error}")

        if not OAuthCallbackHandler.authorization_code:
            raise AuthorizationError("No authorization code received in callback")

        print("✓ Received authorization code")

        # Exchange code for tokens
        print("Exchanging code for tokens...")
        token_data = exchange_code_for_token(
            OAuthCallbackHandler.authorization_code,
            code_verifier,
            client_id,
            client_secret,
            redirect_uri,
        )
        print("✓ Received access and refresh tokens")

        # Save to Doppler
        print("Saving tokens to Doppler...")
        save_tokens_to_doppler(
            token_data["access_token"],
            token_data["refresh_token"],
            token_data.get("expires_in", 3600),  # Default to 1 hour if not provided
        )
        print("✓ Tokens saved to Doppler")

        print("\n" + "=" * 50)
        print("✓ Authorization complete!")
        print(f"Tokens stored in Doppler (project={DOPPLER_PROJECT}, config={DOPPLER_CONFIG})")
        print("AI agents can now use JobberClient.from_doppler()")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
