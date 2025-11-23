#!/bin/bash
# Doppler Token Flow Verification
#
# Verifies OAuth token storage and estimates refresh timing.
#
# Usage:
#     ./doppler_token_flow.sh <service_prefix> <project> <config>
#
# Example:
#     ./doppler_token_flow.sh JOBBER claude-config dev
#
# Checks:
#     - Client credentials exist
#     - Tokens exist
#     - Token format valid
#     - Expiration timing
#
# Based on: Production Jobber OAuth implementation patterns

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SERVICE_PREFIX="${1:-EXAMPLE_}"
DOPPLER_PROJECT="${2:-your-project}"
DOPPLER_CONFIG="${3:-dev}"

# Ensure trailing underscore
if [[ ! "$SERVICE_PREFIX" =~ _$ ]]; then
    SERVICE_PREFIX="${SERVICE_PREFIX}_"
fi

# ============================================================================
# Functions
# ============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

check_doppler() {
    if ! command -v doppler &> /dev/null; then
        log "ERROR: Doppler CLI not found. Install from https://docs.doppler.com/docs/install-cli"
        exit 1
    fi
    log "✓ Doppler CLI found"
}

check_secret_exists() {
    local secret_name="$1"

    if doppler secrets get "$secret_name" \
        --project "$DOPPLER_PROJECT" \
        --config "$DOPPLER_CONFIG" \
        --plain 2>/dev/null | grep -q .; then
        log "✓ $secret_name exists"
        return 0
    else
        log "✗ $secret_name NOT FOUND"
        return 1
    fi
}

get_secret_value() {
    local secret_name="$1"
    doppler secrets get "$secret_name" \
        --project "$DOPPLER_PROJECT" \
        --config "$DOPPLER_CONFIG" \
        --plain 2>/dev/null || echo ""
}

verify_credentials() {
    log "Checking client credentials..."
    check_secret_exists "${SERVICE_PREFIX}CLIENT_ID" || return 1
    check_secret_exists "${SERVICE_PREFIX}CLIENT_SECRET" || return 1

    # Display lengths (not actual values)
    local client_id
    client_id=$(get_secret_value "${SERVICE_PREFIX}CLIENT_ID")
    log "  Client ID length: ${#client_id} chars"
}

verify_tokens() {
    log "Checking tokens..."
    check_secret_exists "${SERVICE_PREFIX}ACCESS_TOKEN" || return 1
    check_secret_exists "${SERVICE_PREFIX}REFRESH_TOKEN" || return 1
    check_secret_exists "${SERVICE_PREFIX}TOKEN_EXPIRES_AT" || return 1

    # Display token lengths (not actual values)
    local access_token refresh_token
    access_token=$(get_secret_value "${SERVICE_PREFIX}ACCESS_TOKEN")
    refresh_token=$(get_secret_value "${SERVICE_PREFIX}REFRESH_TOKEN")

    log "  Access token length: ${#access_token} chars"
    log "  Refresh token length: ${#refresh_token} chars"
}

check_expiration() {
    log "Checking token expiration..."
    local expires_at
    expires_at=$(get_secret_value "${SERVICE_PREFIX}TOKEN_EXPIRES_AT")

    if [[ -z "$expires_at" ]]; then
        log "✗ TOKEN_EXPIRES_AT not found"
        return 1
    fi

    local now
    now=$(date +%s)
    local remaining=$((expires_at - now))

    if [[ $remaining -lt 0 ]]; then
        log "✗ Token EXPIRED (${remaining#-} seconds ago)"
        log "  Run authorization script to re-authenticate"
        return 1
    elif [[ $remaining -lt 300 ]]; then
        log "⚠ Token expires soon ($remaining seconds)"
        log "  TokenManager will refresh proactively"
    else
        local minutes=$((remaining / 60))
        log "✓ Token valid ($minutes minutes remaining)"
    fi

    # Show expiration time
    if command -v date &> /dev/null; then
        local expires_human
        if [[ "$OSTYPE" == "darwin"* ]]; then
            expires_human=$(date -r "$expires_at" +'%Y-%m-%d %H:%M:%S')
        else
            expires_human=$(date -d "@$expires_at" +'%Y-%m-%d %H:%M:%S')
        fi
        log "  Expires at: $expires_human"
    fi
}

test_token_injection() {
    log "Testing token injection..."

    # Test if token can be loaded into shell variable
    local token_len
    token_len=$(doppler run \
        --project "$DOPPLER_PROJECT" \
        --config "$DOPPLER_CONFIG" \
        --command="echo \${#${SERVICE_PREFIX}ACCESS_TOKEN}" 2>/dev/null || echo "0")

    if [[ "$token_len" =~ ^[0-9]+$ ]] && [[ $token_len -gt 0 ]]; then
        log "✓ Token injection works (length: $token_len chars)"
    else
        log "✗ Token injection failed"
        log "  Try: doppler run --command='env | grep ${SERVICE_PREFIX}'"
        return 1
    fi
}

# ============================================================================
# Main
# ============================================================================

main() {
    log "Verifying OAuth token flow for ${SERVICE_PREFIX%_}"
    log "Doppler: project=$DOPPLER_PROJECT config=$DOPPLER_CONFIG"
    echo ""

    check_doppler
    echo ""

    verify_credentials
    echo ""

    verify_tokens
    echo ""

    check_expiration
    echo ""

    test_token_injection
    echo ""

    log "Verification complete!"
}

main "$@"
