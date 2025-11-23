#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.0",
#     "oauthlib>=3.2.2",
# ]
# ///
"""
OAuth 2.0 Authorization Script with PKCE + Doppler

Generic template for one-time browser-based OAuth authentication.
Tokens stored in Doppler secrets manager for programmatic access.

CUSTOMIZATION:
    1. Set CONFIGURATION section below for your OAuth provider
    2. Update secret names in load_client_credentials() and save_tokens_to_doppler()
    3. Run: uv run oauth_auth.py

Based on production implementation: /Users/terryli/own/jobber/jobber_auth.py

Requirements:
    - Doppler CLI installed and configured
    - Client ID and secret stored in Doppler
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
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple

import requests
from oauthlib.oauth2 import WebApplicationClient


# ============================================================================
# CONFIGURATION - Customize for your OAuth provider
# ============================================================================

# OAuth Provider Endpoints
# Examples:
#   Jobber:  https://api.getjobber.com/api/oauth/authorize & /token
#   GitHub:  https://github.com/login/oauth/authorize & /access_token
#   Google:  https://accounts.google.com/o/oauth2/v2/auth & https://oauth2.googleapis.com/token
AUTH_URL = "https://api.example.com/oauth/authorize"  # CUSTOMIZE
TOKEN_URL = "https://api.example.com/oauth/token"  # CUSTOMIZE

# Callback Server Configuration
PORT_RANGE = range(3000, 3011)  # Ports to try for local callback server
CALLBACK_PATH = "/callback"  # URL path for OAuth callback

# Doppler Secrets Manager Configuration
DOPPLER_PROJECT = "your-project"  # CUSTOMIZE: Doppler project name
DOPPLER_CONFIG = "dev"  # CUSTOMIZE: Doppler config (dev/staging/prod)

# Secret Naming Convention
# Doppler secret names follow pattern: {SERVICE_PREFIX}{SUFFIX}
# Example: For SERVICE_PREFIX="GITHUB_", creates GITHUB_CLIENT_ID, GITHUB_ACCESS_TOKEN, etc.
SERVICE_PREFIX = "EXAMPLE_"  # CUSTOMIZE: Prefix for secret names (e.g., "JOBBER_", "GITHUB_")

# OAuth Scopes (optional, provider-specific)
# Examples:
#   GitHub: ["repo", "user"]
#   Google: ["openid", "email", "profile"]
#   Jobber: []  # Jobber doesn't use scopes
SCOPES = []  # CUSTOMIZE: Add scopes if required by provider

# ============================================================================
# OAuth Implementation (No changes needed below this line)
# ============================================================================


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
    Generate PKCE code_verifier and code_challenge (RFC 7636).

    Returns:
        (code_verifier, code_challenge)

    PKCE Security:
        - code_verifier: 43-128 chars, cryptographically random
        - code_challenge: SHA-256 hash of verifier
        - Prevents authorization code interception attacks
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

    Security:
        - Binds to 127.0.0.1 (localhost only)
        - Prevents network exposure of callback endpoint
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

    Secret Names:
        - {SERVICE_PREFIX}CLIENT_ID
        - {SERVICE_PREFIX}CLIENT_SECRET
    """
    client_id_key = f"{SERVICE_PREFIX}CLIENT_ID"
    client_secret_key = f"{SERVICE_PREFIX}CLIENT_SECRET"

    try:
        result = subprocess.run(
            [
                "doppler",
                "secrets",
                "get",
                client_id_key,
                client_secret_key,
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
                f"Ensure {client_id_key} and {client_secret_key} exist."
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
        code_verifier: PKCE code verifier (proves client identity)
        client_id: OAuth client ID
        client_secret: OAuth client secret
        redirect_uri: Callback URI (must match authorization request exactly)

    Returns:
        Token response dict with keys: access_token, refresh_token, expires_in

    Raises:
        requests.HTTPError: Token exchange failed (400/401/500)
            - 400: Invalid code, expired code, PKCE validation failed
            - 401: Invalid client credentials
            - 500: Provider server error
    """
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,  # PKCE proof
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

    Secret Names:
        - {SERVICE_PREFIX}ACCESS_TOKEN
        - {SERVICE_PREFIX}REFRESH_TOKEN
        - {SERVICE_PREFIX}TOKEN_EXPIRES_AT (Unix timestamp)

    Security:
        - Tokens passed via stdin (not command args)
        - Never visible in process list
    """
    expires_at = int(time.time()) + expires_in

    secrets = {
        f"{SERVICE_PREFIX}ACCESS_TOKEN": access_token,
        f"{SERVICE_PREFIX}REFRESH_TOKEN": refresh_token,
        f"{SERVICE_PREFIX}TOKEN_EXPIRES_AT": str(expires_at),
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
    Run OAuth authorization flow with PKCE.

    Flow:
        1. Load credentials from Doppler
        2. Generate PKCE parameters
        3. Start local callback server
        4. Open browser for authorization
        5. Wait for callback
        6. Exchange code for tokens
        7. Save tokens to Doppler

    Returns:
        Exit code: 0 = success, 1 = failure
    """
    print(f"OAuth 2.0 Authorization ({SERVICE_PREFIX.rstrip('_')})")
    print("=" * 50)

    try:
        # Load credentials from Doppler
        print("Loading client credentials from Doppler...")
        client_id, client_secret = load_client_credentials()
        print(f"✓ Client ID: {client_id[:8]}...")

        # Generate PKCE parameters
        code_verifier, code_challenge = generate_pkce_pair()
        print("✓ Generated PKCE parameters (S256 challenge)")

        # Start HTTP server
        print("Starting local callback server...")
        server, port = find_available_port()
        redirect_uri = f"http://localhost:{port}{CALLBACK_PATH}"
        print(f"✓ Server listening on port {port}")

        # Build authorization URL
        client = WebApplicationClient(client_id)
        auth_params = {
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        # Add scopes if configured
        if SCOPES:
            auth_params["scope"] = " ".join(SCOPES)

        auth_url = client.prepare_request_uri(AUTH_URL, **auth_params)

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
            token_data["access_token"], token_data["refresh_token"], token_data["expires_in"]
        )
        print("✓ Tokens saved to Doppler")

        print("\n" + "=" * 50)
        print("✓ Authorization complete!")
        print(f"Tokens stored in Doppler (project={DOPPLER_PROJECT}, config={DOPPLER_CONFIG})")
        print(f"Token secrets: {SERVICE_PREFIX}ACCESS_TOKEN, {SERVICE_PREFIX}REFRESH_TOKEN")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
