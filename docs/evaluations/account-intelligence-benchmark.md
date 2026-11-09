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
