---
name: lead-generation
description: Run the lead-generation harness to produce a traceable ranked shortlist.
---
# Lead Generation

Use the existing repository utilities as the source of truth. Do not duplicate
schemas, scoring rules, or export logic in prompts or ad-hoc scripts.

## Operating loop

1. Read the campaign config and select `personal` or `strict` delivery policy.
2. Inspect the manifest-bound discovery, qualification, source register, and
   canonical company identity before dispatching research.
3. Prioritize material evidence gaps by expected value: identity and company
   fit first, then location/service facts, buying events, contacts, and optional
   portfolio details.
4. Use approved sources for the claim class. Official company sources own
   company facts; approved procurement/news sources may support time-sensitive
   events. Preserve URLs, excerpts, timestamps, source class, and run scope.
5. Treat replay as replay. It is not live research and must remain
   `Not searched`, `Unavailable`, or `Needs review` unless a live provider
   produced the result.
6. Reuse only scope- and hash-valid terminal outputs. Retry bounded transient
   failures, continue independent personal-mode work, and expose `Partial` or
   `Unavailable` gaps instead of fabricating claims.
7. Stop when the remaining gaps cannot materially change ranking, when sources
   are unavailable, or when a strict barrier fails. Do not run provider-backed
   work without explicit authorization.

## Delivery contract

The final workbook must be produced by the canonical scoring, QA, and workbook
utilities. It must include a deterministic ranked shortlist, explicit unknowns
and research gaps, claim-level provenance, contact verification state, event
identifiers, and the run-manifest hashes that bind inputs and outputs.

Personal mode may return the best defensible reserve-backed shortlist and make
partial state visible. Strict mode retains exact admitted-set, source-
verification, complete-scope, revision, hash, QA, and publication barriers.
