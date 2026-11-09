---
name: lead-generation
description: Run the lead-generation harness to produce a traceable ranked shortlist.
---
# Lead Generation

Use the existing repository utilities as the source of truth. Do not duplicate
schemas, scoring rules, or export logic in prompts or ad-hoc scripts.

The parent Codex agent owns strategy, account prioritization, native subagent
dispatch, stopping decisions, and account-thesis wording. Use the repository's
typed JSON tool boundary and receipt journal for admission, result validation,
promotion, projection, ranking, and finalization. Python must not recreate a
planner, scheduler, retry loop, or fixed lane sequence.

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
5. Dispatch only with an explicit capability: replay is a fixture fallback,
   not live research. Non-fixture execution requires an explicit live worker;
   never relabel replay output as source-backed evidence.
6. Reuse only scope-, campaign-, profile-, adapter-, and hash-valid terminal
   outputs. Use the shared run deadline and total-attempt budget; classify
   deadline, budget, deterministic, transient, and unavailable outcomes
   explicitly instead of retrying indefinitely.
7. Preserve `Unknown`, `Partial`, `Unavailable`, and `Needs review` gaps.
   Reserve `None found` for a completed account-scoped search. Structural or
   replay evidence must not rank like source verification.
8. Bind projection and QA to the manifest-selected evidence artifact and hash.
   Preserve historical contact provenance; current runs may add observed claims
   but must not rewrite older baselines without a newer verified claim.
9. TED-only coverage is a known public-news limitation. Expanding external
   sources requires an approved policy/configuration change, not an ad-hoc
   bypass.
10. Stop when remaining gaps cannot materially change ranking, when a source or
    budget barrier is exhausted, or when strict scope/revision/hash/QA barriers
    fail. Do not run provider-backed work without explicit authorization; the
    durable production gate remains blocked until a separate live probe proves
    source verification.
11. Every native action must carry stable action/attempt identity, scope,
    contract and profile versions, request/result hashes, and budget settlement;
    append its terminal receipt before treating the handoff as complete.

## Delivery contract

The final workbook must be produced by the canonical scoring, QA, and workbook
utilities. It must include a deterministic ranked shortlist, explicit unknowns
and research gaps, claim-level provenance, contact verification state, event
identifiers, and the run-manifest hashes that bind inputs and outputs.

Personal mode may return the best defensible reserve-backed shortlist and make
partial or unavailable state visible; it cannot silently publish zero or
under-target delivery. Strict mode retains exact admitted-set, source-
verification, complete-scope, revision, hash, QA, and publication barriers.
