---
name: lead-evidence
description: Capture and verify page-local, company-bound lead evidence.
---

# Lead Evidence

## Evidence boundary

Use the deterministic `capture_evidence`, `validate_evidence`, and
`promote_evidence` boundaries for the assigned source action. This skill does
not perform general discovery. Search results are `DISCOVERY`; source excerpts
are `CANDIDATE_EVIDENCE`; only verifier decisions can promote them to
`VERIFIED_EVIDENCE`.

- Ownership: page-local claims and semantic-support review input. Consume the
  parent-selected bounded action from `account-research`; do not own action
  scope, account coverage, stop decisions, contact verification, or commercial
  trigger collection.
- Treat each claim as immutable after capture; identify it with `candidate_claim_id` and `candidate_sha256`.
- Keep the exact public source URL, retrieval timestamp, source kind, company relationship, confidence, and a page-local excerpt.
- Require `published_at` for time-sensitive signals, `unit`/`scope`/`as_of_date` for quantitative portfolio claims, and person/role/affiliation for contact claims.
- Directory or search-result hosts may support discovery but cannot become the canonical company domain.
- Researchers write candidate records and the semantic-support inputs a verifier
  can review. The verifier writes decisions. Deterministic Python owns
  promotion, scoring, ranking, QA, and canonical outputs.
- Native handoffs must use typed request/result contracts and append-only action
  receipts; never persist hidden reasoning or treat a self-declared assurance
  level as source verification.
