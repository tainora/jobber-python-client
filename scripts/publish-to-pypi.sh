#!/usr/bin/env bash
set -euo pipefail

# PyPI Publishing Script (Local-Only)
# This script enforces LOCAL machine publishing only, preventing CI/CD execution
# See: pypi-doppler skill, ADR-0027

echo "🚀 Publishing to PyPI (Local Workflow)"
echo "======================================"
echo ""

# ============================================================================
# Step 0: CI Detection Guards
# ============================================================================
echo "🔐 Step 0: CI detection and credential verification..."

# Check for CI environment variables
CI_DETECTED=""
if [[ -n "${CI:-}" ]]; then
    CI_DETECTED="yes"
    echo "   ❌ CI: ${CI}"
fi
if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    CI_DETECTED="yes"
    echo "   ❌ GITHUB_ACTIONS: ${GITHUB_ACTIONS}"
fi
if [[ -n "${GITLAB_CI:-}" ]]; then
    CI_DETECTED="yes"
    echo "   ❌ GITLAB_CI: ${GITLAB_CI}"
fi
if [[ -n "${JENKINS_URL:-}" ]]; then
    CI_DETECTED="yes"
    echo "   ❌ JENKINS_URL: ${JENKINS_URL}"
fi
if [[ -n "${CIRCLECI:-}" ]]; then
    CI_DETECTED="yes"
    echo "   ❌ CIRCLECI: ${CIRCLECI}"
fi

if [[ -n "${CI_DETECTED}" ]]; then
    echo ""
    echo "❌ ERROR: This script must ONLY be run on your LOCAL machine"
    echo ""
    echo "   This project enforces LOCAL-ONLY PyPI publishing for:"
    echo "   - Security: No long-lived PyPI tokens in GitHub secrets"
    echo "   - Speed: 30 seconds locally vs 3-5 minutes in CI"
    echo "   - Control: Manual approval step before production release"
    echo ""
    echo "   See: pypi-doppler skill, ADR-0027"
    exit 1
fi

# Verify Doppler access
if ! command -v doppler &> /dev/null; then
    echo "   ❌ ERROR: Doppler CLI not found"
    echo "   Install: brew install dopplerhq/cli/doppler"
    exit 1
fi

# Verify Doppler authentication
if ! doppler whoami &> /dev/null; then
    echo "   ❌ ERROR: Not authenticated with Doppler"
    echo "   Run: doppler login"
    exit 1
fi

echo "   ✅ Local environment verified"

# ============================================================================
# Step 1: Pull Latest Release Commit
# ============================================================================
echo ""
echo "📥 Step 1: Pulling latest release commit..."

git pull origin main &> /dev/null || {
    echo "   ❌ ERROR: Failed to pull latest changes"
    exit 1
}

# Extract version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "   Current version: v${CURRENT_VERSION}"

# ============================================================================
# Step 2: Clean Old Builds
# ============================================================================
echo ""
echo "🧹 Step 2: Cleaning old builds..."

rm -rf dist/ build/ *.egg-info
echo "   ✅ Cleaned"

# ============================================================================
# Step 3: Build Package
# ============================================================================
echo ""
echo "📦 Step 3: Building package..."

if ! uv build; then
    echo "   ❌ ERROR: Build failed"
    exit 1
fi

# Verify wheel created
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -n1)
if [[ -z "${WHEEL_FILE}" ]]; then
    echo "   ❌ ERROR: No wheel file found in dist/"
    exit 1
fi

echo "   ✅ Built: ${WHEEL_FILE}"

# ============================================================================
# Step 4: Publish to PyPI
# ============================================================================
echo ""
echo "📤 Step 4: Publishing to PyPI..."

# Retrieve PyPI token from Doppler
echo "   Using PYPI_TOKEN from Doppler (claude-config/prd)"
PYPI_TOKEN=$(doppler secrets get PYPI_TOKEN \
    --project claude-config \
    --config prd \
    --plain 2>/dev/null) || {
    echo "   ❌ ERROR: Failed to retrieve PYPI_TOKEN from Doppler"
    echo "   Run: doppler secrets set PYPI_TOKEN='your-token' --project claude-config --config prd"
    exit 1
}

if [[ -z "${PYPI_TOKEN}" ]]; then
    echo "   ❌ ERROR: PYPI_TOKEN is empty"
    exit 1
fi

# Publish to PyPI
if ! UV_PUBLISH_TOKEN="${PYPI_TOKEN}" uv publish; then
    echo "   ❌ ERROR: Publish failed"
    echo "   Common issues:"
    echo "   - PyPI token expired (requires 2FA since 2024)"
    echo "   - Version already exists on PyPI"
    echo "   - Package name conflict"
    exit 1
fi

echo "   ✅ Published to PyPI"

# ============================================================================
# Step 5: Verify on PyPI
# ============================================================================
echo ""
echo "🔍 Step 5: Verifying on PyPI..."

# Extract package name from pyproject.toml
PACKAGE_NAME=$(grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')
PYPI_URL="https://pypi.org/project/${PACKAGE_NAME}/${CURRENT_VERSION}/"

# Wait a few seconds for PyPI to index
sleep 3

if curl -s -o /dev/null -w "%{http_code}" "${PYPI_URL}" | grep -q "200"; then
    echo "   ✅ Verified: ${PYPI_URL}"
else
    echo "   ⚠️  Package published but verification URL not yet available"
    echo "   Check manually: ${PYPI_URL}"
fi

# ============================================================================
# Success
# ============================================================================
echo ""
echo "✅ Complete! Published v${CURRENT_VERSION} to PyPI"
echo ""
