---
name: account-research
description: Run bounded research for one accepted company at a time.
---

# Account Research

## Capability selection

Select capabilities from the evidence gap; do not encode a fixed provider
sequence. The runtime resolves the configured provider and the parent Codex
agent chooses the next action.

- identity gap -> `identity_resolution`, then `official_source_fetch`
- known official URL -> `official_source_fetch`
- broad company/news/hiring discovery -> `web_search`, `news_search`, or `jobs_search`
- possible procurement intent -> `procurement_search`
- location or place discovery -> `place_discovery`
- named stakeholder gap -> `contact_verification`

Before choosing a temporal research action, the parent controller must classify
the decision-relevant gap as one of:

- `snapshot` for the current state or scale;
- `dated_event` for a discrete company-bound change;
- `trend` for comparable observations across time; or
- `event_sequence` for related milestones that form a change narrative.

The parent controller owns that choice. This skill must not impose a universal
lane order. For every non-snapshot action, record the explicit lookback window,
comparison basis, minimum observation requirement, and stop condition. If the
available sources cannot meet those requirements, return `Unknown` with the
coverage limitation rather than infer stability, growth, acceleration, or
absence of a trigger.

Search and directory results are `DISCOVERY`; fetched company-bound pages are
`CANDIDATE_EVIDENCE`; only a verifier or semantic review may produce
`VERIFIED_EVIDENCE`. Search discovers. Sources prove. Verifiers promote. Codex
decides what to do next.

- Ownership: parent-selected bounded action scope, account coverage, and stop
  evidence. The parent agent chooses the account and the next bounded action;
  this skill never encodes a fixed TED/portfolio/contact sequence.
- Composition matrix:
  - `account-research`: assigns and bounds the action, tracks attempts and
    coverage, and proves the stop condition.
  - `lead-evidence`: captures page-local claims and semantic-support review
    input for the assigned action.
  - `contact-verification`: verifies named people and generic mailboxes; it
    does not own account coverage or general claim capture.
  - `buying-signal-research`: collects commercial triggers only; it does not
    resolve contacts or decide account-level completeness.
- Use only the assigned `company_id`, legal name, trusted company domain, and lane scope.
- Record one attempt per required query or source, including provider, cursor/page, cap, truncation, status, and candidate claim IDs.
- `None found` is valid only after every required attempt completed with no
  truncation, provider error, or unresolved candidate; preserve that coverage
  and stop evidence with the action receipt.
- Never use a global search result as an account-level conclusion without an exact verified company link.
- Keep outputs in the lane-specific candidate directory named by run ID and company ID.
- Preserve native action identity and receipt provenance when returning a result;
  hypotheses are analytical outputs and must cite supporting and counterevidence
  claim IDs without becoming verified facts.
