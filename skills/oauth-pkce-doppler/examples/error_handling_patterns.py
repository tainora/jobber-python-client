#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests>=2.32.0",
#     "oauthlib>=3.2.2",
# ]
# ///
"""
Error Handling Patterns - Comprehensive Examples

Demonstrates handling all OAuth failure scenarios with proper error messages.
Based on fail-fast patterns from: /Users/terryli/own/jobber/jobber_auth.py

Usage:
    uv run error_handling_patterns.py
"""

import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests


# Custom exceptions (fail-fast design)
class AuthorizationError(Exception):
    """OAuth authorization failed"""

    pass


class ConfigurationError(Exception):
    """Configuration or setup issue"""

    pass


def demonstrate_doppler_errors():
    """Demonstrate Doppler-related error handling."""
    print("=== Doppler Error Handling ===\n")

    # Error 1: Doppler CLI not found
    try:
        result = subprocess.run(
            ["doppler", "--version"], capture_output=True, check=True, timeout=5
        )
        print("✓ Doppler CLI found")
        print(f"  Version: {result.stdout.decode().strip()}")
    except FileNotFoundError:
        print("✗ Error: Doppler CLI not found")
        print("  Resolution: brew install dopplerhq/cli/doppler")
        print("  Reference: https://docs.doppler.com/docs/install-cli")
    except subprocess.TimeoutExpired:
        print("✗ Error: Doppler CLI timeout")
        print("  Resolution: Check network connectivity")

    # Error 2: Secrets not found
    print("\n--- Secret Existence Check ---")
    try:
        result = subprocess.run(
            [
                "doppler",
                "secrets",
                "get",
                "EXAMPLE_CLIENT_ID",
                "EXAMPLE_CLIENT_SECRET",
                "--project",
                "nonexistent-project",
                "--config",
                "dev",
                "--plain",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        print("✓ Secrets found")
    except subprocess.CalledProcessError as e:
        print("✗ Error: Secrets not found or Doppler CLI failed")
        print(f"  stderr: {e.stderr.strip()}")
        print("  Resolution: doppler secrets set EXAMPLE_CLIENT_ID")

    print()


def demonstrate_port_errors():
    """Demonstrate port availability error handling."""
    print("=== Port Availability Error Handling ===\n")

    PORT_RANGE = range(3000, 3005)  # Smaller range for demo

    # Try to bind to ports
    for port in PORT_RANGE:
        try:
            server = HTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler)
            print(f"✓ Port {port} available")
            server.server_close()
            break
        except OSError as e:
            print(f"✗ Port {port} in use: {e}")

    else:
        # No ports available
        print(f"\n✗ Error: No available ports in range {PORT_RANGE.start}-{PORT_RANGE.stop - 1}")
        print("  Resolution: Close applications using these ports")
        print("  Command: lsof -i :3000-3005")
        print("  Or: Change PORT_RANGE in script")

    print()


def demonstrate_authorization_errors():
    """Demonstrate authorization-related errors."""
    print("=== Authorization Error Handling ===\n")

    # Simulate various authorization errors
    error_scenarios = [
        {
            "error": "access_denied",
            "description": "User clicked Deny",
            "resolution": "Re-run script and click Approve",
        },
        {
            "error": "unauthorized_client",
            "description": "Client not authorized for this grant type",
            "resolution": "Check OAuth app settings, enable Authorization Code grant",
        },
        {
            "error": "invalid_scope",
            "description": "Requested scopes not available",
            "resolution": "Check scope names, ensure app has required permissions",
        },
    ]

    for scenario in error_scenarios:
        print(f"Error: {scenario['error']}")
        print(f"  Description: {scenario['description']}")
        print(f"  Resolution: {scenario['resolution']}")
        print()


def demonstrate_token_exchange_errors():
    """Demonstrate token exchange error handling."""
    print("=== Token Exchange Error Handling ===\n")

    # Simulate token exchange errors
    exchange_errors = [
        {
            "status": 400,
            "cause": "Invalid authorization code (expired or already used)",
            "resolution": "Restart authorization flow (codes expire in 5-10 minutes)",
        },
        {
            "status": 400,
            "cause": "Redirect URI mismatch",
            "resolution": "Ensure redirect_uri matches authorization request exactly",
        },
        {
            "status": 400,
            "cause": "PKCE validation failed",
            "resolution": "Verify code_verifier matches code_challenge (S256)",
        },
        {
            "status": 401,
            "cause": "Invalid client credentials",
            "resolution": "Check CLIENT_ID and CLIENT_SECRET in Doppler",
        },
        {
            "status": 500,
            "cause": "Provider server error",
            "resolution": "Wait and retry, check provider status page",
        },
    ]

    for error in exchange_errors:
        print(f"HTTP {error['status']}: {error['cause']}")
        print(f"  Resolution: {error['resolution']}")
        print()


def demonstrate_network_errors():
    """Demonstrate network-related error handling."""
    print("=== Network Error Handling ===\n")

    # Connection timeout
    try:
        response = requests.get("https://api.example.com/oauth/token", timeout=5)
    except requests.Timeout:
        print("✗ Error: Connection timeout")
        print("  Resolution: Check network connectivity, increase timeout")
    except requests.ConnectionError:
        print("✗ Error: Connection failed")
        print("  Resolution: Check DNS, firewall, VPN settings")

    print()


def demonstrate_comprehensive_flow():
    """Demonstrate comprehensive error handling in OAuth flow."""
    print("=== Comprehensive Flow with Error Handling ===\n")

    def oauth_flow_with_errors():
        """OAuth flow with all error checks."""
        try:
            # Step 1: Check Doppler
            print("1. Checking Doppler CLI...")
            subprocess.run(["doppler", "--version"], check=True, capture_output=True)

            # Step 2: Load credentials
            print("2. Loading credentials from Doppler...")
            # (Simulated - would fail if secrets don't exist)
            print("   ⚠ Simulated (secrets may not exist)")

            # Step 3: Check port availability
            print("3. Finding available port...")
            for port in range(3000, 3005):
                try:
                    HTTPServer(("127.0.0.1", port), BaseHTTPRequestHandler).server_close()
                    print(f"   ✓ Port {port} available")
                    break
                except OSError:
                    continue
            else:
                raise RuntimeError("No available ports")

            # Step 4: Authorization (simulated)
            print("4. Authorization flow...")
            print("   ⚠ Would open browser here")

            # Step 5: Token exchange (simulated)
            print("5. Token exchange...")
            print("   ⚠ Would POST to token endpoint")

            # Step 6: Save to Doppler (simulated)
            print("6. Saving tokens to Doppler...")
            print("   ⚠ Would update Doppler secrets")

            print("\n✓ Flow completed successfully (simulated)")

        except FileNotFoundError as e:
            print(f"\n✗ Configuration Error: {e}")
            print("  Install Doppler CLI: brew install dopplerhq/cli/doppler")
            return 1

        except subprocess.CalledProcessError as e:
            print(f"\n✗ Doppler Error: {e.stderr}")
            print("  Check Doppler configuration and secrets")
            return 1

        except RuntimeError as e:
            print(f"\n✗ Runtime Error: {e}")
            return 1

        except requests.RequestException as e:
            print(f"\n✗ Network Error: {e}")
            print("  Check connectivity and retry")
            return 1

        return 0

    return oauth_flow_with_errors()


def main():
    """Run all error handling demonstrations."""
    print("\n" + "=" * 60)
    print("OAuth PKCE Error Handling Patterns")
    print("=" * 60 + "\n")

    demonstrate_doppler_errors()
    demonstrate_port_errors()
    demonstrate_authorization_errors()
    demonstrate_token_exchange_errors()
    demonstrate_network_errors()
    demonstrate_comprehensive_flow()

    print("\n" + "=" * 60)
    print("For complete error handling, see:")
    print("- oauth_auth_template.py (full implementation)")
    print("- references/troubleshooting.md (debugging guide)")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
