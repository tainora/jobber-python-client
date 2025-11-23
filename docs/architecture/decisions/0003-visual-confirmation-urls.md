# ADR-0003: Visual Confirmation URL Pattern

## Status

Accepted

## Context

API operations create an abstraction gap between programmatic execution and human verification. When automation creates a Jobber client via GraphQL API, users have no immediate way to visually confirm the operation succeeded in Jobber's web interface. This requires manual navigation (search by name, browse lists) which is time-consuming and error-prone.

**Current Behavior:**

```python
result = client.execute_query(CREATE_CLIENT_MUTATION, variables)
print(f"Created client ID: {result['clientCreate']['client']['id']}")
# User: "Okay... but did it work? Let me search Jobber manually..."
```

**User Needs:**

1. Immediate visual confirmation that API operations succeeded
2. Clickable links to view resources in Jobber web interface
3. Confidence that programmatic and manual views are synchronized
4. Debugging aid when operations produce unexpected results

**Available Solution (Discovered):**
Jobber's GraphQL API provides URL fields on most resources:

- `jobberWebUri` (String): Direct link to resource in Jobber web UI (team members)
- `previewUrl` (String): Client Hub link for quote approval (customers)

**Current Gap:**

- Existing examples (`basic_usage.py`, `error_handling.py`) don't query URL fields
- No documentation of URL availability or usage patterns
- No helper utilities to format success messages with links
- Terminal output uses plain URLs (not clickable in modern terminals)

**Opportunity:**
Including `jobberWebUri` in queries is zero-cost (field already computed by API) and provides immediate UX improvement. This pattern should be:

1. Documented as best practice
2. Demonstrated in all examples
3. Supported by helper utilities for consistent formatting

## Decision

Implement visual confirmation URL pattern as a core workflow for the Jobber Python client.

**Components:**

### 1. Documentation (`docs/visual-confirmation-urls.md`)

Comprehensive guide covering:

- Problem/solution framing
- Quick start patterns (always include `jobberWebUri`)
- 5 use cases: create, query, automation, validation, batch
- Best practices (ANSI hyperlinks, error context)
- Integration patterns (CLI, web, Slack)
- Troubleshooting and security considerations

### 2. Working Example (`examples/visual_confirmation_urls.py`)

Demonstrates:

- Create operations with URL feedback
- Query operations with clickable links
- Quote dual URLs (jobberWebUri + previewUrl)
- URL-based validation
- Batch operations with URL summaries

### 3. Helper Utilities (`jobber/url_helpers.py`)

Provide reusable functions:

- `format_success()`: Consistent success message formatting with URLs
- `clickable_link()`: ANSI hyperlink escape codes for terminal
- `validate_url()`: Ensure jobberWebUri present in response

### 4. Retrofit Existing Examples

Update existing code to follow pattern:

- `examples/basic_usage.py`: Include jobberWebUri in queries
- `examples/error_handling.py`: Show URL in error context
- Maintain consistency across all examples

### 5. Documentation Integration

Update project docs:

- README.md: Add "Visual Confirmation URLs (Quick Win!)" section
- CLAUDE.md: Add to features and examples
- Link to comprehensive guide

## Consequences

### Positive

**Immediate User Value:**

- Users can click links to verify API operations in Jobber web UI
- Builds trust in automation (visual confirmation)
- Reduces time spent manually searching for created resources
- Enables better debugging (see current state vs. expected state)

**Developer Experience:**

- Pattern is simple: "Always include `jobberWebUri`"
- Helper utilities provide consistent formatting
- ANSI hyperlinks work in modern terminals (iTerm2, VSCode, etc.)
- Zero performance overhead (field already computed)

**Documentation Quality:**

- Comprehensive guide with real-world use cases
- Working example demonstrates all patterns
- Integration examples (CLI, Slack, web dashboard)
- Troubleshooting section addresses common issues

**Maintainability:**

- Helper utilities centralize formatting logic (DRY)
- Existing examples updated for consistency
- Pattern scales to future API resources
- No external dependencies (ANSI codes are stdlib)

### Negative

**Terminal Compatibility:**

- ANSI hyperlinks not supported in all terminals (fallback: plain URLs)
- Users may not know links are clickable (documentation addresses this)

**API Coverage Gaps:**

- Not all Jobber resources may support `jobberWebUri` (check per-resource)
- Preview URLs only available on quotes (documented limitation)

**Code Changes:**

- Existing examples require updates (retrofit)
- New module `url_helpers.py` increases LOC (minimal: ~50 lines)
- Success messages need reformatting (use helper utilities)

**Abstraction Risk:**

- Helper utilities may be too opinionated for some use cases
- Users may want custom formatting (provide escape hatch: direct URL access)

### Mitigations

**Terminal Compatibility:**

- `clickable_link()` includes fallback: shows URL even if hyperlink fails
- Documentation shows both ANSI and plain URL patterns

**API Coverage:**

- Documentation lists known resources with `jobberWebUri`
- Introspection query pattern to check new resources
- Validation helper detects missing URLs

**Maintainability:**

- Helper utilities are optional (users can format URLs directly)
- Examples demonstrate both helper and manual patterns
- Clear documentation of design decisions

## Implementation Notes

### SLO Alignment

**Availability** (99.9%):

- URL helpers are pure functions (no I/O, no failures)
- Optional pattern (doesn't affect core client behavior)
- Graceful degradation (missing URL → show ID instead)

**Correctness** (100%):

- URL helpers validate inputs (type checking)
- ANSI escape codes follow terminal standards
- Examples tested against real Jobber API

**Observability**:

- URL presence indicates resource accessibility
- Missing URLs flag permission or API issues
- Links enable visual verification of operations

**Maintainability** (< 500 LOC target):

- url_helpers.py: ~50 LOC (6% of target)
- Total project: 867 → 917 LOC (acceptable growth)
- High value-to-code ratio (major UX improvement)

### Error Handling

Following fail-fast principle:

- `validate_url()` raises if jobberWebUri missing (caller decides recovery)
- `format_success()` raises on invalid input (TypeError)
- `clickable_link()` returns plain URL on ANSI encoding error (graceful fallback)

### Dependencies

**Zero new dependencies:**

- ANSI escape codes: stdlib string formatting
- URL validation: dict key checking
- Terminal detection: optional (ANSI codes degrade gracefully)

### Testing Strategy

**Examples as Integration Tests:**

- `visual_confirmation_urls.py` demonstrates all patterns
- Run against real API: `uv run examples/visual_confirmation_urls.py`
- Manual verification: click links, confirm resources appear

**Helper Utilities:**

- Unit tests for `format_success()`, `clickable_link()`, `validate_url()`
- Test ANSI escape code formatting
- Test error cases (missing URL, invalid types)

## Alternatives Considered

### Alternative 1: No URL Pattern (Status Quo)

**Pros:**

- No code changes required
- Users can manually navigate Jobber web UI

**Cons:**

- Poor UX (manual search required)
- No visual confirmation of API operations
- Time-consuming debugging workflow

**Decision:** Rejected. UX improvement justifies minimal implementation cost.

### Alternative 2: Client-Side URL Construction

Generate URLs from resource IDs:

```python
def build_url(resource_type: str, resource_id: str) -> str:
    return f"https://secure.getjobber.com/{resource_type}s/{resource_id}"
```

**Pros:**

- No need to query jobberWebUri field
- Works even if API doesn't return URL

**Cons:**

- URL pattern may change (fragile)
- Assumes knowledge of Jobber's URL structure
- Breaks if Jobber changes routing
- No validation that URL works

**Decision:** Rejected. Using API-provided URLs is more reliable and future-proof.

### Alternative 3: Browser Auto-Open

Automatically open URLs in browser after operations:

```python
import webbrowser
result = client.execute_query(mutation, variables)
webbrowser.open(result['client']['jobberWebUri'])
```

**Pros:**

- Immediate visual confirmation (no click required)

**Cons:**

- Intrusive for batch operations (opens many tabs)
- Not suitable for automation/CI environments
- Users lose control over when to verify

**Decision:** Rejected. Provide URLs for user-initiated verification only.

### Alternative 4: Rich Console Libraries (rich, colorama)

Use third-party libraries for better terminal formatting:

```python
from rich.console import Console
console = Console()
console.print(f"[link={url}]View Client[/link]")
```

**Pros:**

- Better terminal rendering
- Cross-platform terminal detection
- More formatting options

**Cons:**

- New dependency (violates "minimal dependencies" principle)
- Overkill for simple hyperlinks
- Increases installation complexity

**Decision:** Rejected. ANSI escape codes are sufficient and dependency-free.

## Related Decisions

- **ADR-0001**: Jobber API Client Architecture - Fail-fast error handling, minimal dependencies
- **ADR-0002**: OAuth PKCE Skill Extraction - Pattern extraction methodology

## References

- **Jobber GraphQL API**: https://developer.getjobber.com/docs/
- **ANSI Escape Codes**: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
- **Implementation Guide**: `/Users/terryli/own/jobber/docs/visual-confirmation-urls.md`
- **Example Code**: `/Users/terryli/own/jobber/examples/visual_confirmation_urls.py`
- **Plan**: `/Users/terryli/own/jobber/docs/plan/0003-visual-confirmation-urls/plan.yaml`

## Metadata

- **Decision Date**: 2025-01-17
- **Author**: Terry Li
- **Scope**: UX improvement, developer ergonomics
- **Impact**: Medium (optional pattern, high value)
- **Implementation Plan**: `docs/plan/0003-visual-confirmation-urls/plan.yaml`
