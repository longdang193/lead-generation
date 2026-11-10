# Account-Intelligence Benchmark

This is the bounded release gate for the account-intelligence harness. It is
not a claim that a lead is good merely because deterministic QA passes.

## Sample

Use 10–20 accounts from one campaign and one manifest revision. Record the
offer ID/version, source revision, account IDs, reviewer, and review date.

## Judgments

- claim-support precision: does each cited source entail the exported claim?
- thesis support: is every priority thesis assertion semantically supported?
- account attribution: are events and contacts bound to the named company?
- ranking agreement: does the computed top-10 order agree with independent
  pairwise stakeholder judgments?
- contact usefulness: can a reviewer use a named outreach owner as presented?
- research cost: actions, provider failures, truncation, and unresolved gaps.

## Release thresholds

- claim-support precision `>= 90%`
- priority thesis assertions semantically supported `100%`
- critical account-attribution errors `0`
- top-10 pairwise ranking agreement `>= 70%`
- usefulness for named contacts claimed as outreach owners `>= 80%`

Any failed threshold blocks release. A failed live provider probe is recorded as
an explicit limitation and must not be converted into a negative buying signal.

## Required evidence

The benchmark record must retain the manifest hash, offer ID/version, claim IDs,
semantic-review IDs, rank-audit contributions, stakeholder judgments, threshold
calculations, and unresolved research gaps. No hidden chain-of-thought is
persisted; exported rationale is limited to concise claims, counterevidence,
uncertainty, confidence, and recommended action.

## Current Acceptance Record (2026-11-10)

- Local implementation state: `verified`; the repository suite completed with
  238 passing tests on the active implementation.
- Semantic benchmark state: `not run`; no same-cohort 10–20-account sample,
  blinded structural-baseline comparison, stakeholder pairwise judgments, or
  adjudicated denominators are recorded here, so no ranking-quality threshold
  is claimed as met.
- Native runtime state: `incomplete`; fixture lifecycle tests prove the
  deterministic boundary, but an actual native Codex execution trace showing
  parent action selection and stopping is still required for production
  readiness.
- Live-provider/CRM state: `blocked`; the existing bounded provider probe is
  unavailable as current acceptance evidence because it lacks an independent
  source-verification decision and CRM boundary proof. Provider failure is not
  converted into a negative buying signal.
- Release decision: `blocked pending semantic benchmark, native runtime trace,
  and live-provider/CRM boundary evidence`; the local implementation result
  must not be presented as production-ready account intelligence until those
  independent gates are recorded.
