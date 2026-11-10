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

## Provisional Blinded Run Details (2026-11-10)

- Cohort packet: `outputs/benchmark-2026-11-10/blinded_accounts.json`, SHA-256
  `31dafca95d60b3ee216bde5db5dfa3d7cbbad1987eb633611afc7b55b6493209`.
- Structural baseline mapping: `outputs/benchmark-2026-11-10/controller_baseline.json`,
  SHA-256 `cb88702389fb24517000480d9df3935d8b0a6be28a85d6ee0bcecfa5a6d8cc3f`.
- Structural order: `A02, A05, A06, A07, A09, A10, A01, A04, A03, A08`.
- Independent model-only semantic order:
  `A05, A10, A02, A09, A07, A01, A03, A04, A08, A06`.
- Pairwise preferences recorded: `A05>A10`, `A10>A02`, `A02>A09`, `A09>A07`,
  `A07>A01`, `A01>A03`, `A03>A04`, `A04>A08`, `A08>A06`.
- Adjudication identified `A06` as the critical attribution error: an aggregator
  excerpt did not entail account-specific service, WEG, or Berlin claims.
- The packet contains no typed thesis assertions, claim IDs, or named verified
  outreach owner. It is therefore useful for failure discovery and provisional
  ranking comparison only; it cannot satisfy the stakeholder benchmark gate.

## Current Acceptance Record (2026-11-10)

- Local implementation state: `verified`; the repository suite completed with
  261 passing tests on the active implementation on 2026-11-10.
- Active-plan contract state: `verified`; the scoped repository contract check
  passed for `docs/superpowers/plans/2026-11-10-account-intelligence-trust-chain-remediation-plan.md`,
  including canonical agent profiles, env protection, and publication config.
- Full repository contract state: `blocked`; unrelated historical plans still
  use the retired planning schema and must be migrated separately. This does
  not invalidate the active-plan or runtime-profile result.
- Semantic benchmark state: `provisional model-only`; the blinded same-cohort
  packet is `outputs/benchmark-2026-11-10/blinded_accounts.json` and contains
  10 accounts from one current campaign cohort. An independent native reviewer
  produced the provisional order and pairwise judgments, but no human
  stakeholder sign-off was obtained. Structural-vs-semantic top-10 pairwise
  agreement is `32/45 = 71.1%`, which clears the declared `>= 70%` numeric
  threshold only as a provisional model result. Claim-support precision is
  `22/25 = 88%`, below the declared `>= 90%` threshold. Thesis support is
  `0/0` because the blinded packet contained no thesis assertions; contact
  usefulness is `0/0` because no named outreach owner was present. One critical
  attribution error was identified. Therefore the benchmark gate is failed and
  no ranking-quality or commercial-uplift claim is accepted.
- Native runtime state: `complete for the bounded trace`; the fresh
  non-fixture trace is
  `outputs/native-parent-trace-2026-11-10/trace.json` at implementation
  revision `0242e653e8c03c333cb678b4e95d2ae52d89fd9b`. It records the parent
  controller's selected official-site action, admission, validated result,
  settled receipt, replay, explicit stop decision, unresolved buying-signal
  gap, and refusal to promote or export. The separate complete fixture chain is
  `outputs/fixture-controller-trace-2026-11-10/trace.json`; it records fresh
  dossier/rank/workbook/QA hashes but is not native-runtime or live-provider
  proof.
- External publication state: `blocked: external proof unavailable`. The active
  plan prohibits unapproved provider use and external writes. Workbook delivery
  does not require CRM/API publication, and this repository performed no
  provider call, CRM write, or other external publication. If a CRM/API
  connector is added later, it needs a separate approved, dry-run-tested
  integration contract. Provider failure or unavailable publication proof is
  not converted into a negative buying signal.
- Release decision: `blocked pending semantic benchmark and any explicitly
  approved external-publication boundary evidence`; the local implementation
  result must not be presented as production-ready account intelligence. The
  native trace gate is now evidenced; the benchmark remains failed/provisional
  and no external-publication readiness claim is made.
