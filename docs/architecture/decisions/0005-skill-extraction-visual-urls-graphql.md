# ADR-0005: Skill Extraction - Visual Confirmation URLs & GraphQL Query Execution

## Status

Accepted

## Context

The Jobber Python client implementation includes two validated, reusable workflow patterns beyond OAuth PKCE (already extracted as ADR-0002):

1. **Visual Confirmation URL Pattern** (ADR-0003, validated)
   - Location: `docs/visual-confirmation-urls.md` (495 lines), `jobber/url_helpers.py` (156 LOC), `examples/visual_confirmation_urls.py` (147 LOC)
   - Pattern: Include `jobberWebUri` in API responses → Display clickable links → Enable visual verification
   - Validation: Production-tested, ADR-0003, plan.yaml, 19 unit tests (100% pass)
   - Reusability: API-agnostic (any API providing web UI URLs: Stripe, GitHub, Linear, Asana)

2. **GraphQL Query Execution Pattern** (ADR-0001, validated)
   - Location: `jobber/graphql.py` (189 LOC), `examples/basic_usage.py`, `examples/error_handling.py`
   - Pattern: Query construction → HTTP POST → Response parsing → Error handling → Pagination → Rate limiting
   - Validation: Production-tested, ADR-0001, working examples
   - Reusability: GraphQL-specific but applicable to Shopify, GitHub, Stripe, Linear, Contentful

**Current State:**

- Visual confirmation pattern documented in comprehensive guide (docs/visual-confirmation-urls.md)
- GraphQL execution pattern embedded in implementation (jobber/graphql.py)
- Both patterns proven reusable beyond Jobber API
- No consolidated skill for easy reference and reuse

**Problem:**
Future projects requiring:

- API visual verification will reimplement or copy-paste url_helpers
- GraphQL client functionality will reimplement executor patterns
- Knowledge scattered across docs, source code, examples
- No single source of truth for these patterns

**Opportunity:**
Both patterns are:

- **Prescriptive**: Clear steps documented
- **Stepwise**: Sequential execution phases
- **Task-like**: Actionable workflows
- **Validated**: Production-tested with ADRs, plans, tests
- **Reusable**: API-agnostic or broadly applicable across GraphQL ecosystem

## Decision

Extract both patterns as atomic project-local skills at `skills/`:

1. `skills/visual-confirmation-urls/` - Visual verification pattern
2. `skills/graphql-query-execution/` - GraphQL client pattern

**Rationale for Project-Local (not global ~/.claude/skills/)**:

- Patterns validated specifically in Jobber context
- May need future refinement before global promotion
- Keep alongside oauth-pkce-doppler skill for consistency
- Easy to version with project via semantic-release

**Skill Structure (following skill-architecture patterns):**

```
skills/{skill-name}/
├── SKILL.md                  # Hub: Overview + quick start + navigation
├── assets/                   # Templates (parameterized, API-agnostic)
├── references/               # Deep documentation (progressive disclosure)
└── examples/                 # Runnable code (PEP 723)
```

**Content Extraction Strategy (copy/move not regenerate):**

- Reuse existing validated content from docs/, jobber/, examples/
- Parameterize for API-agnostic usage
- Organize via progressive disclosure (80% tasks in SKILL.md, 20% in references/)

## Consequences

### Positive

**Knowledge Consolidation:**

- Single source of truth per pattern
- Progressive disclosure (hub → overview → details)
- Searchable via skill triggers
- Reduces scattered documentation

**Reusability:**

- Patterns available for future projects
- Templates accelerate implementation
- Examples demonstrate usage
- No need to re-discover patterns

**Maintainability:**

- Skills update independently of core library
- Clear boundaries (skill vs embedded code)
- Version control via project semantic-release
- ADR documents extraction rationale

**Documentation Quality:**

- Hub-and-spoke architecture (CLAUDE.md → SKILL.md → references/)
- No duplication (CLAUDE.md links to skills, doesn't duplicate content)
- Progressive disclosure reduces cognitive load

### Negative

**Additional Files:**

- 24 new files created (11 visual URLs + 12 GraphQL + 1 CLAUDE.md update)
- Maintenance burden (keep skills in sync with core library)
- Potential for divergence (skill templates vs actual implementation)

**Complexity:**

- New abstraction layer (skills/ directory)
- Navigation complexity (where to find information)
- Learning curve (hub-and-spoke pattern)

**Premature Extraction Risk:**

- Visual URLs pattern only validated in Jobber context
- GraphQL pattern may need refinement for other APIs
- May discover limitations when reusing

### Mitigations

**Minimize Files:**

- Focus on essential references only (3-4 per skill)
- Consolidate similar content
- Remove unused directories (scripts/ if not needed)

**Prevent Divergence:**

- Templates extracted from actual working code (jobber/url_helpers.py, jobber/graphql.py)
- Examples reference actual project examples
- Skills link back to implementation as reference

**Validate Before Global Promotion:**

- Keep project-local initially
- Test reusability in 2-3 other projects
- Promote to ~/.claude/skills/ only after broad validation

**Maintain Sync:**

- Link skills to ADRs (single source of truth for decisions)
- Update skills when core library changes significantly
- Include version references in SKILL.md

## Implementation Notes

### Skill 1: Visual Confirmation URLs

**SKILL.md Frontmatter:**

```yaml
---
name: visual-confirmation-urls
description: Get web UI links from APIs for instant visual verification. Use when creating resources via API and need clickable links to verify in web interface (Jobber, Stripe, GitHub, Linear).
---
```

**Content Sources (copy/move):**

- SKILL.md: From docs/visual-confirmation-urls.md (lines 1-100, overview + quick start)
- assets/url_helpers_template.py: From jobber/url_helpers.py (parameterize)
- references/api-integration.md: From docs/visual-confirmation-urls.md (API coverage section)
- references/terminal-hyperlinks.md: From docs/visual-confirmation-urls.md (ANSI codes section)
- references/use-cases.md: From docs/visual-confirmation-urls.md (5 use cases)
- examples/: From examples/visual_confirmation_urls.py (split by use case)

**Parameterization:**

- Remove Jobber-specific field names (use generic examples)
- Add configuration section showing Stripe, GitHub, Linear usage
- Keep fail-fast error handling intact

### Skill 2: GraphQL Query Execution

**SKILL.md Frontmatter:**

```yaml
---
name: graphql-query-execution
description: Execute GraphQL queries with error handling, pagination, and rate limiting. Use when integrating GraphQL APIs (Shopify, GitHub, Stripe) or building GraphQL clients.
---
```

**Content Sources (copy/move):**

- SKILL.md: New synthesis (GraphQL pattern overview)
- assets/graphql_executor_template.py: From jobber/graphql.py (GraphQLExecutor class)
- references/error-handling.md: From jobber/graphql.py (error parsing logic)
- references/pagination.md: From examples/error_handling.py (pagination pattern)
- references/rate-limiting.md: From jobber/graphql.py (throttle logic)
- references/query-patterns.md: From examples/ (query construction examples)
- examples/: From examples/basic_usage.py, error_handling.py (extract patterns)

**Parameterization:**

- Replace `API_URL`, `API_VERSION` with configuration parameters
- Add examples for Shopify, GitHub, Stripe GraphQL endpoints
- Keep rate limiting, error handling generic

### CLAUDE.md Integration (Minimal Link Farm)

Add two new sections to "Skills & Patterns" (after line 211):

- Visual Confirmation URLs section (~30 lines)
- GraphQL Query Execution section (~30 lines)

**Format (from agent investigation):**

```markdown
### [Skill Name]

**Skill**: Link to SKILL.md

**Pattern**: One-sentence description

**Implementation**: Links to actual code

**Key Components**: Bullet list (3-6 items)

**Reusability**: Applicability statement

**Skill Documentation**: Links to references/

**Examples**: Links to examples/
```

**Link Density Target:** ~30-40% (consistent with oauth-pkce-doppler section)

### SLO Alignment

**Availability (99.9%):**

- Skills are optional (core library unaffected)
- No breaking changes to existing code
- Progressive disclosure (load references only when needed)

**Correctness (100%):**

- Content extracted from production-validated code
- Unit tests validate url_helpers (19 tests, 100% pass)
- Working examples demonstrate patterns

**Observability:**

- Clear error messages in templates
- Examples demonstrate debugging approaches
- References document troubleshooting

**Maintainability:**

- Single source of truth per pattern (skill)
- Clear boundaries (skill vs core library)
- Progressive disclosure reduces cognitive load
- Hub-and-spoke navigation

### Error Handling

Following fail-fast principle:

- Templates preserve existing error handling (TypeError, KeyError, ValueError)
- No fallback/default/retry added
- Caller controls recovery strategy
- Examples demonstrate exception handling

### Validation

**Automated:**

```bash
# Run official skill validator
/Users/terryli/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/scripts/quick_validate.py skills/visual-confirmation-urls/
/Users/terryli/.claude/plugins/marketplaces/anthropic-agent-skills/skill-creator/scripts/quick_validate.py skills/graphql-query-execution/
```

**Manual Checklist:**

- [ ] YAML frontmatter valid (single-line description, <200 chars)
- [ ] Progressive disclosure effective (SKILL.md handles 80% tasks)
- [ ] No content duplication (hub → spoke → references)
- [ ] All links resolve (relative for project, absolute for ~/.claude/)
- [ ] Templates parameterized (no hardcoded Jobber URLs)
- [ ] Examples runnable (PEP 723 inline dependencies)

## Alternatives Considered

### Alternative 1: Keep as Documentation Only

Keep comprehensive guides in docs/ without skill extraction.

**Pros:**

- No additional abstraction layer
- Simpler project structure
- Less maintenance

**Cons:**

- Not discoverable via skill triggers
- No progressive disclosure
- Knowledge scattered across docs/, examples/, source
- Harder to reuse in other projects

**Decision:** Rejected. Skills provide better discoverability and reusability.

### Alternative 2: Extract All 6 Workflow Candidates

Extract all identified workflows (unit testing, visual URLs, fail-fast errors, GraphQL, rate limiting, token refresh).

**Pros:**

- Comprehensive skill coverage
- Maximum knowledge capture

**Cons:**

- High implementation cost (12+ hours)
- Some patterns redundant (token refresh overlaps oauth-pkce-doppler)
- Some patterns too small (rate limiting)
- Maintenance burden for 6 skills

**Decision:** Rejected. Focus on highest-value patterns (visual URLs + GraphQL).

### Alternative 3: Consolidate into Single "API Integration" Skill

Combine visual URLs + GraphQL into one skill.

**Pros:**

- Fewer skills to maintain
- Related patterns grouped

**Cons:**

- Blurs focus (URL pattern ≠ GraphQL pattern)
- Harder to discover specific pattern
- Violates atomic single-purpose principle

**Decision:** Rejected. Agent investigation recommends atomic skills.

### Alternative 4: Extract to Global Skills (~/.claude/skills/)

Create skills in global directory for maximum reusability.

**Pros:**

- Available across all projects immediately
- Matches oauth-pkce-doppler precedent (if moved to global)

**Cons:**

- Patterns only validated in Jobber context
- May need refinement before broad promotion
- Harder to version with project

**Decision:** Rejected for now. Start project-local, promote to global after validation in 2-3 other projects.

## Related Decisions

- **ADR-0001**: Jobber API Client Architecture - Fail-fast error handling, minimal dependencies
- **ADR-0002**: OAuth PKCE Skill Extraction - First skill extraction, established pattern
- **ADR-0003**: Visual Confirmation URL Pattern - Pattern being extracted
- **ADR-0004**: URL Helpers Unit Testing - Tests validate extracted code

## References

- **Skill Architecture Investigation**: Agent investigation report (4 parallel agents)
- **Workflow Analysis**: 6 workflow candidates identified, 2 selected for extraction
- **Implementation**: `/Users/terryli/own/jobber/docs/plan/0005-skill-extraction-visual-urls-graphql/plan.yaml`
- **Existing Skill**: `skills/oauth-pkce-doppler/` (extraction precedent)

## Metadata

- **Decision Date**: 2025-01-17
- **Author**: Terry Li
- **Scope**: Knowledge organization, skill extraction, reusability
- **Impact**: Medium (24 new files, documentation reorganization)
- **Implementation Plan**: `docs/plan/0005-skill-extraction-visual-urls-graphql/plan.yaml`
