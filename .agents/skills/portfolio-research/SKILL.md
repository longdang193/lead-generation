---
name: portfolio-research
description: Use when an accepted company needs bounded portfolio, managed-unit, reference, or quantitative account evidence.
---

# Portfolio Research

Research only the parent-selected company and bounded portfolio action.

## Capability selection

- known official page -> `official_source_fetch`
- possible reference or portfolio discovery -> `web_search`
- permitted directory candidate -> `permitted_directory`, then official/source fetch

Search and directory results discover candidate references. Official or
company-bound reference pages prove the portfolio claim. Quantitative claims
must preserve unit, scope, and as-of date. Capture page-local excerpts and
return `CANDIDATE_EVIDENCE`; the verifier owns promotion to
`VERIFIED_EVIDENCE`.

Do not resolve identity, score, rank, write canonical outputs, mutate CRM, or
send outreach. Preserve action identity, scope, and receipt provenance.
