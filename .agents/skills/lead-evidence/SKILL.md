---
name: lead-evidence
description: Capture and verify page-local, company-bound lead evidence.
---

# Lead Evidence

- Treat each claim as immutable after capture; identify it with `candidate_claim_id` and `candidate_sha256`.
- Keep the exact public source URL, retrieval timestamp, source kind, company relationship, confidence, and a page-local excerpt.
- Require `published_at` for time-sensitive signals, `unit`/`scope`/`as_of_date` for quantitative portfolio claims, and person/role/affiliation for contact claims.
- Directory or search-result hosts may support discovery but cannot become the canonical company domain.
- Researchers write candidate records. The verifier writes decisions. Deterministic Python owns promotion, scoring, ranking, QA, and canonical outputs.
