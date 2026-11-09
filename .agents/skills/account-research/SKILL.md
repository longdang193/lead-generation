---
name: account-research
description: Run bounded research for one accepted company at a time.
---

# Account Research

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
