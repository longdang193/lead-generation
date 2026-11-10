---
name: evidence-verifier
description: Use when candidate evidence must be checked before it can support an account claim, ranking decision, or export.
---

# Evidence Verifier

Verify the assigned company-bound candidate evidence; do not search broadly or
rewrite the candidate claim.

## Capability selection

- `source_fetch`: inspect the cited page when the excerpt or URL needs checking
- `identity_check`: confirm the page belongs to the claimed company
- `semantic_review`: test entailment, offer relevance, freshness, and contradictions
- `validate_evidence`: return a typed verifier decision with reason codes

Search-result pages, snippets, directory listings, and provider enrichment are
not proof. Treat them as `DISCOVERY` or `CANDIDATE_EVIDENCE`. Promote only after
identity, page-local support, temporal currency, offer relevance, and
counterevidence checks pass; otherwise return `Rejected` or `Needs review`.

Write verifier decisions only. Preserve candidate hashes, source URLs, excerpts,
retrieval timestamps, and action receipts. Never score, rank, mutate candidate
claims, write canonical exports, change CRM, or send outreach.
