# ADR-0004: URL Helpers Unit Testing

## Status

Accepted

## Context

The `url_helpers.py` module (156 LOC) provides three core functions for the visual confirmation URL pattern:

- `format_success()`: Formats success messages with web links
- `clickable_link()`: Creates ANSI OSC 8 terminal hyperlinks
- `validate_url()`: Validates jobberWebUri field presence

**Current State:**

- Module implemented with fail-fast error handling
- Type hints and docstrings present
- No automated tests to verify behavior

**Risk Without Tests:**

- Breaking changes undetected during refactoring
- Edge cases not validated (empty strings, null values, encoding errors)
- ANSI escape code formatting errors could go unnoticed
- Type validation logic not verified

**SLO Impact:**

- **Correctness (100% target)**: Cannot guarantee without tests
- **Maintainability**: Refactoring risky without test safety net
- **Observability**: No validation that errors are raised as expected

**Example Untested Scenarios:**

```python
# What happens if resource_data is None?
format_success("Client", None)  # Should raise TypeError, but is it tested?

# What if ANSI encoding fails?
clickable_link("https://example.com\x00", "Bad URL")  # Fallback tested?

# What if jobberWebUri is empty string?
validate_url({'jobberWebUri': ''})  # ValueError tested?
```

## Decision

Implement pytest-based unit tests for `jobber/url_helpers.py` covering:

1. **Happy path**: Valid inputs produce expected outputs
2. **Error cases**: Invalid inputs raise expected exceptions
3. **Edge cases**: Empty strings, None values, encoding errors
4. **ANSI formatting**: OSC 8 escape codes correctly formatted

**Test Structure:**

```
tests/
└── test_url_helpers.py  # Unit tests for url_helpers module
```

**Test Coverage Goals:**

- `format_success()`: 6+ test cases (valid, missing id, missing URL, wrong type, name fallback, custom name field)
- `clickable_link()`: 4+ test cases (valid, no text, encoding error fallback, wrong type)
- `validate_url()`: 5+ test cases (valid, missing field, null value, empty string, wrong type)

**Testing Framework:**

- **pytest**: Already in dev dependencies, minimal boilerplate
- **No mocking**: Pure functions, no external dependencies
- **Fail-fast validation**: Tests verify exceptions raised correctly

## Consequences

### Positive

**Correctness Assurance:**

- Validates fail-fast error handling works as documented
- Catches regressions during refactoring
- Documents expected behavior via tests
- Ensures type validation logic correct

**Maintainability:**

- Safe refactoring (tests catch breaking changes)
- Living documentation of edge cases
- Easier onboarding (tests show usage patterns)
- Confidence in code changes

**Development Velocity:**

- Faster debugging (failing tests pinpoint issues)
- Fewer production bugs (edge cases tested)
- Better IDE support (tests serve as examples)

**Documentation Quality:**

- Tests complement docstrings with concrete examples
- Edge cases documented via test names
- Expected exceptions verified

### Negative

**Development Cost:**

- Initial time investment (30-40 minutes to write tests)
- Maintenance burden (tests must be updated with code changes)
- Slightly longer CI runs (pytest execution)

**Complexity:**

- Additional file to maintain (tests/test_url_helpers.py)
- Test dependencies (pytest already present, no new deps)

### Mitigations

**Minimize Cost:**

- Focus on critical paths and error cases (not exhaustive testing)
- Keep tests simple (no complex setup/teardown)
- Use pytest parametrize for similar test cases (DRY)

**Maintain Quality:**

- Follow existing project patterns (tests directory, pytest framework)
- Keep tests focused (one assertion per test when possible)
- Use descriptive test names (test_format_success_raises_typeerror_when_resource_data_is_not_dict)

## Implementation Notes

### Test Organization

```python
# tests/test_url_helpers.py
import pytest
from jobber.url_helpers import format_success, clickable_link, validate_url

class TestFormatSuccess:
    """Tests for format_success() function"""

    def test_valid_input_returns_formatted_message(self):
        # Happy path

    def test_raises_typeerror_when_resource_data_not_dict(self):
        # Error case

    # ... more tests

class TestClickableLink:
    """Tests for clickable_link() function"""

class TestValidateUrl:
    """Tests for validate_url() function"""
```

### Test Execution

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_url_helpers.py

# Run with coverage
uv run pytest tests/ --cov=jobber.url_helpers

# Run with verbose output
uv run pytest tests/ -v
```

### SLO Alignment

**Availability (99.9%)**:

- Tests verify graceful fallback in clickable_link()
- No flaky tests (pure functions, no I/O)

**Correctness (100%)**:

- Tests validate all error paths raise expected exceptions
- Tests verify ANSI formatting matches OSC 8 standard
- Tests ensure type validation works correctly

**Observability**:

- Test failures provide clear error messages
- Test names document expected behavior
- Coverage reports show untested code paths

**Maintainability**:

- Tests enable safe refactoring
- Tests document edge cases
- Tests serve as usage examples

### Error Handling Validation

Tests must verify fail-fast principle:

```python
def test_format_success_raises_keyerror_when_id_missing():
    with pytest.raises(KeyError, match="missing required field: 'id'"):
        format_success("Client", {'name': 'John'})
```

### ANSI Formatting Validation

Tests must verify OSC 8 standard compliance:

```python
def test_clickable_link_produces_osc8_format():
    result = clickable_link("https://example.com", "Example")
    assert result == "\033]8;;https://example.com\033\\Example\033]8;;\033\\"
```

## Alternatives Considered

### Alternative 1: Doctest-Based Testing

Embed tests in docstrings:

```python
def format_success(resource_type, resource_data, name_field="name"):
    """
    >>> format_success("Client", {'id': '1', 'name': 'John', 'jobberWebUri': 'https://...'})
    '✅ Client created: John\n🔗 View in Jobber: https://...'
    """
```

**Pros:**

- Tests live with documentation
- No separate test file

**Cons:**

- Limited to simple cases (hard to test exceptions)
- Clutters docstrings
- Less flexible than pytest

**Decision:** Rejected. Doctest inadequate for error case testing.

### Alternative 2: Manual Testing Only

Test via examples and manual verification.

**Pros:**

- Zero development overhead
- No test maintenance burden

**Cons:**

- No regression protection
- Edge cases likely missed
- Refactoring risky
- Violates correctness SLO

**Decision:** Rejected. Manual testing insufficient for 100% correctness target.

### Alternative 3: Integration Tests Only

Test url_helpers through example scripts.

**Pros:**

- Tests real usage patterns
- No isolated unit tests needed

**Cons:**

- Slow (requires full client setup)
- Hard to test edge cases
- Failures difficult to debug
- Doesn't isolate url_helpers bugs

**Decision:** Rejected. Integration tests complement but don't replace unit tests.

### Alternative 4: Property-Based Testing (Hypothesis)

Use hypothesis for generative testing:

```python
from hypothesis import given, strategies as st

@given(st.text(), st.text())
def test_clickable_link_always_returns_string(url, text):
    result = clickable_link(url, text)
    assert isinstance(result, str)
```

**Pros:**

- Discovers edge cases automatically
- Very thorough testing

**Cons:**

- New dependency (hypothesis)
- Overkill for simple pure functions
- Slower test execution
- Harder to debug failures

**Decision:** Rejected. Standard unit tests sufficient for url_helpers complexity.

## Related Decisions

- **ADR-0001**: Jobber API Client Architecture - Fail-fast error handling principle
- **ADR-0003**: Visual Confirmation URL Pattern - url_helpers module implementation

## References

- **pytest Documentation**: https://docs.pytest.org/
- **ANSI OSC 8 Standard**: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
- **Implementation**: `/Users/terryli/own/jobber/jobber/url_helpers.py`
- **Plan**: `/Users/terryli/own/jobber/docs/plan/0004-url-helpers-unit-tests/plan.yaml`

## Metadata

- **Decision Date**: 2025-01-17
- **Author**: Terry Li
- **Scope**: Code quality, correctness SLO
- **Impact**: Low (testing infrastructure), High value (correctness assurance)
- **Implementation Plan**: `docs/plan/0004-url-helpers-unit-tests/plan.yaml`
