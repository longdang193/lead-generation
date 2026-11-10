---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: account-intelligence-trust-chain-remediation
targets:
  - scripts/typed_contracts.py
  - scripts/account_intelligence.py
  - scripts/score_leads.py
  - scripts/canonical_projection.py
  - scripts/select_for_enrichment.py
  - scripts/harness_tools.py
  - scripts/build_workbook.py
  - scripts/build_task1_workbook.mjs
  - scripts/build_shortlist.py
  - scripts/qa_leads.py
  - scripts/lead_contract.py
  - scripts/action_receipts.py
  - scripts/run_manifest.py
  - scripts/promote_evidence.py
  - config/research_policy.json
  - config/signal_taxonomy.json
  - config/research_evidence_schema.json
  - config/lead_generation_schema.json
  - tests
  - docs/evaluations/account-intelligence-benchmark.md
---

# Account-Intelligence Trust-Chain Remediation Plan

## Goal

Make the validated account-intelligence dossier the enforced source of
commercial prioritization and stakeholder delivery. A priority lead must have
an offer-bound, company-bound, semantically reviewed explanation of why the
account fits, why the timing matters or why it is a strong proactive account,
what evidence supports the conclusion, what weakens it, what remains unknown,
who should be approached, and what action should happen next.

Keep Codex as the only planner and strategy owner. Do not add a repository
planner, scheduler, retry loop, CRM application, or hidden chain-of-thought
store. Python remains a deterministic kernel for typed admission, evidence
promotion, validation, projection, ranking, QA, and export.

## Review Basis

The reviewed revision is `93e46d845b8f78749cc36292a6222482917e1cd3` on
`longdang193/lead-generation`; it is published at
`origin/codex/account-intelligence-trust-chain` and the full SHA is reachable
from GitHub. The review was read-only; no external provider or CRM write was
performed.

Both requested reviews completed in one authenticated repository-bound context
with `High` effort and fresh tabs:

- `GPT-5.6-Sol`, `High`, run `run-qspcJk`, chat
  `6af2742c-88d4-83ed-aac5-2030018e5be9`; bounded result `completed`, visible
  response final and pinned to the reviewed SHA; cleanup completed.
- `GPT-6`, `High`, run `run-QouaOE`, chat
  `6af274fe-6ee8-83ed-92b8-042fbcaf071c`; bounded result `completed`, visible
  response final and pinned to the reviewed SHA; cleanup completed.

No run was timed out, incomplete, ambiguous, or retried. Both chats were
submitted exactly once in the dedicated profile
`C:\Users\HOANG PHI LONG DANG\.codex\profiles\github-review\longdang193-lead-generation`.
The consolidated source-validated findings are:

1. Every production ranking/export path must close over the canonical chain
   `validated dossier → dimension projection → rank audit → shortlist → workbook → strict QA`;
   structural-only paths remain compatibility views and a structural-only
   priority workbook must be rejected.
2. Source assurance must be bound to a promoted claim identity, candidate hash,
   verifier decision, active run, and manifest-bound artifact; caller-supplied
   `assurance_level="source"` is not sufficient.
3. Scoring needs a versioned deterministic policy with admissible evidence,
   transformations, recency, contradiction, confidence, and missing-data rules;
   commercial attractiveness must be separated from observability/actionability.
4. Semantic review needs stable instance identity and supersession semantics;
   material thesis assertions must be explicit typed members rather than
   reconstructed only from prose.
5. Research completeness must be receipt-authoritative and task ordering must
   make selection gates depend on `action_receipts.py`, `run_manifest.py`, and
   `promote_evidence.py`; all signal-state consumers migrate together.
6. Signal precedence must distinguish direct intent, environmental trigger,
   need/change, and research completeness; incomplete research remains
   uncertainty, not negative intent.
7. A durable, versioned dossier artifact keyed by company, offer, run, and
   manifest revision must be registered and resolved by workbook/QA lineage.
8. Native runtime proof must include one real Codex execution trace showing
   parent-selected actions/stopping plus a guard against repository scheduler
   or planner loops; fixture tests remain boundary proof.
9. Benchmark gates must use blinded same-cohort comparison, declared
   non-inferiority/uplift thresholds, denominators, zero-observation handling,
   adjudication, usable-contact coverage, and separate local/semantic/live
   acceptance states. Blocked live probes block production-readiness claims.
10. Priority theses require receipt-backed bounded disconfirmation before
    claiming no counterevidence.
11. Workbook provenance must be manifest-derived; no hard-coded retrieval or
    execution dates remain.
12. Benchmark samples must be stratified by structural fit, trigger
    availability, and evidence completeness before outcomes are observed.
13. The native `qa_workbook` facade must forward production mode and dossier
    identity; otherwise strict QA is optional in the very path the skills tell
    Codex to use.
14. Normal score output must carry offer identity into commercial ranking, and
    production mode must reject compatibility fallback rather than mixing
    dossier-backed and flat-score rows.
15. Workbook priority sheets must derive their own headers so validated
    dossier/rank lineage is physically delivered to stakeholders.
16. Identity normalization, review selection, dossier hashing, event merging,
    and event strength must be deterministic and conflict-aware.
17. The production acceptance gate remains blocked until native execution,
    blinded benchmark, and live-provider/CRM boundary evidence are recorded;
    unavailable external proof must not be represented as successful.

Unverified claims are excluded from this plan. In particular, no exact lead
count discrepancy is treated as a defect, no direct procurement event is
required for every good lead, no commercial-uplift claim is made without the
benchmark, no live-provider/CRM readiness claim is made without a probe, and
no new orchestration runtime is proposed.

## Implementation Outcomes

### Assertion-bound semantic trust

Every material thesis assertion has immutable content, company and offer
identity, supporting and counterevidence claim IDs, and a matching approved
semantic review. Candidate, replay-only, foreign-company, or stale claims
cannot support a production priority thesis.

### Evidence-derived commercial ranking

Commercial dimensions are derived from validated indicators and the account
thesis. Each contribution identifies the claims, semantic decision, offer
criterion, confidence adjustment, and calculation input that produced it.
Ranking fails closed without a validated dossier and cannot silently fall back
to structural ranking on the production account-intelligence path.

### Correct account-scoped research

Event identity is composite and collision-safe. Environmental triggers are
independent from direct buying intent. Negative intent states are emitted only
when the immutable offer-specific research policy and its action receipts prove
complete coverage.

### Dossier-first delivery

The canonical workbook and QA path expose thesis, timeline, evidence ledger,
counterevidence, research gaps, confidence, contact owner, and recommended
action. Structural score sheets remain useful supporting views but cannot be
the only stakeholder deliverable for priority accounts.

### Measured product acceptance

A bounded 10–20-account benchmark records claim support, thesis support,
account attribution, ranking agreement, contact usefulness, research cost, and
live boundary limitations. The release is blocked when any declared threshold
fails or when live-provider/CRM proof is unavailable but claimed as complete.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-verification-before-completion`, `skill-plan-document-reviewer`, `spreadsheets:Spreadsheets`
- Isolation: `current workspace`; preserve unrelated changes and stop if the base is no longer `93e46d845b8f78749cc36292a6222482917e1cd3`
- Commit policy: `no commits during execution`; the lead controller decides branch disposition after fresh verification
- Preauthorized local actions: edit declared files, run declared tests, inspect configured local fixtures and schemas, and produce bounded fixture artifacts
- User-approval actions: push, merge, live external provider calls, CRM writes, paid enrichment, destructive cleanup, or changing the approved product scope
- Parallel ownership: `none`; `typed_contracts.py`, `account_intelligence.py`, and the canonical projection are shared owners and are serialized
- Sequential fallback: execute Tasks 7–10 in order, then complete Tasks 5–6 only after all producer and consumer tests pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/account-intelligence-trust-chain`
- Base commit: `93e46d845b8f78749cc36292a6222482917e1cd3`
- Expected workspace: `preserve the published review commit; apply only the post-review remediation wave`
- Next action: `execute Tasks 7–10, then complete native trace and benchmark gates in Tasks 5–6`
- Blockers: `the current local suite passed before this review; post-review regressions, native Codex trace, blinded benchmark, and live-provider/CRM probe remain outstanding`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `Codex` | none | assertion-binding and claim-assurance tests | focused contracts and account-intelligence tests pass |
| Task 2 | `completed` | current | `Codex` | Tasks 1 and 3 | dossier-derived rank and fail-closed facade tests | scoring, facade, and selection tests pass |
| Task 3 | `completed` | current | `Codex` | Task 1 | collision, trigger, and coverage-policy tests | signal, projection, receipt, and evidence tests pass |
| Task 4 | `completed` | current | `Codex` | Tasks 2–3 | workbook and QA regression tests | production lineage gates, five account-intelligence sheets, and finalization tests pass |
| Task 5 | `active` | current | `Codex` | Tasks 1–4 | native trace and artifact integrity proof | fixture trace passes; actual native Codex execution trace remains outstanding |
| Task 6 | `pending` | current | `unresolved` | Task 5 | benchmark record and final verification | blocked pending native trace, blinded benchmark, and external-boundary decision |
| Task 7 | `pending` | current | `unresolved` | Tasks 1–4 | promoted-claim, offer-context, strict-QA, and facade integration tests | added from commit-pinned review; not implemented |
| Task 8 | `pending` | current | `unresolved` | Task 7 | dimension provenance, selection, trigger, and receipt regression tests | added from commit-pinned review; not implemented |
| Task 9 | `pending` | current | `unresolved` | Task 7 | deterministic identity, review mapping, conflict, and hash tests | added from commit-pinned review; not implemented |
| Task 10 | `pending` | current | `unresolved` | Tasks 7–9 | workbook lineage, portability, zero-row, and preview tests | added from commit-pinned review; not implemented |

## Task Breakdown

### Enforced review gates applied to all tasks

- `scripts/promote_evidence.py`, `scripts/action_receipts.py`, and
  `scripts/run_manifest.py` are canonical provenance owners; no caller-supplied
  assurance, coverage, or completion flag can promote a claim or close a run.
- `scripts/score_leads.py`, `scripts/select_for_enrichment.py`,
  `scripts/harness_tools.py`, `scripts/build_workbook.py`,
  `scripts/build_task1_workbook.mjs`, and `scripts/qa_leads.py` must use one
  dossier-backed production path. Structural ranking is compatibility-only and
  must be rejected when presented as a priority deliverable.
- Every priority output resolves `rank audit → material assertion → semantic
  review → promoted claim → source/artifact lineage`; missing or superseded
  links fail closed.
- Acceptance is reported in three independent states: local implementation
  verified, semantic benchmark accepted, and live-provider/CRM boundary
  verified. A blocked external probe cannot be represented as production-ready.

### Task 1: Bind semantic reviews to immutable assertions

**Purpose:**
- Prevent stale, foreign, replay-only, or semantically mismatched approvals from supporting a priority account.

**Task Function:**
- Strengthen the evidence-to-assertion contract and its validator.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: contract risk, cross-module impact, and need for precise source/claim reasoning.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently verify contract rejection and round-trip behavior.

**Specification Coverage:**
- Product Contract requirement that every material thesis assertion cites support, counterevidence, confidence, and validation evidence.
- Review findings on `SemanticReview`, `AccountThesis`, `AccountHypothesis`, and source-assurance enforcement.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/typed_contracts.py:SemanticReview`, `AccountHypothesis`, `AccountThesis`, `EvidenceClaim`
- Modify: `scripts/typed_contracts.py:MaterialAssertion`, `SemanticReview`, `AccountHypothesis`, `AccountThesis`
- Modify: `scripts/account_intelligence.py:validate_semantic_review`, `validate_account_hypothesis`, `validate_account_thesis`
- Modify: `config/research_evidence_schema.json`
- Verify: `tests/test_account_intelligence.py`, `tests/test_account_intelligence_contracts.py`, `tests/test_typed_contracts.py`

**Dependencies:**
- Current source inspection complete; preserve existing source-vs-structural-vs-replay assurance semantics.

**Authority:**
- Preauthorized local actions: edit the declared contracts, validators, schema, and focused tests; run focused unit tests
- Stop for: new external provider behavior, migration of persisted production artifacts, or any change to Codex planner authority

**Steps:**
- [x] Step 1: Add an immutable `MaterialAssertion` contract with assertion ID, kind, normalized assertion text, content hash, company ID, offer ID/version, and supporting/counterevidence claim IDs.
- [x] Step 2: Require `SemanticReview` to carry the matching assertion hash, offer criterion, reviewer/action receipt, and reviewed claim IDs; preserve the existing approved-decision predicates.
- [x] Step 3: Add `validation_step` and decision-relevant gap fields to `AccountHypothesis`; require a falsifiable validation step for unsupported speculative hypotheses used by a priority thesis.
- [x] Step 4: Make `validate_semantic_review()` and `validate_account_thesis()` reconstruct the expected material-assertion set, require exactly matching approved reviews, reject foreign-company claims, and reject replay/unknown assurance for production conclusions.
- [x] Step 5: Add regression cases for changed assertion text, reused assertion IDs, mismatched offer criteria, foreign claims, replay-only support, and missing hypothesis validation steps.
- [x] Step 6: Define stable semantic-review identity, supersession, and conflicting-active-review behavior; make `material_assertions` explicit typed thesis members.

**Verification:**
- [x] `py -3 -m unittest tests.test_typed_contracts tests.test_account_intelligence tests.test_account_intelligence_contracts -v`
- Expected: stale approvals, foreign claims, replay-only claims, and unsupported priority hypotheses fail; valid assertions round-trip with stable hashes.

**Exit Criteria:**
- No priority thesis can pass validation unless every material assertion has a matching, approved, source-supported semantic review.

### Task 2: Make dossier-derived ranking canonical

**Purpose:**
- Ensure the score that selects a lead is derived from the validated account intelligence rather than caller-supplied flat fields.

**Task Function:**
- Replace the parallel score producer with a deterministic thesis-to-commercial projection and close the native facade bypass.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: trust-boundary risk and cross-module ranking behavior.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently verify score derivation, fail-closed behavior, and ordering.

**Specification Coverage:**
- Product requirement that stakeholders can see why Account A outranks Account B.
- Review findings on `rank_account()`, `build_rank_audit()`, `_commercial_dimension_value()`, and `harness_tools.invoke("rank_leads")`.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/score_leads.py:_commercial_dimension_value`, `build_rank_audit`, `rank_account`
- Modify: `scripts/score_leads.py:project_commercial_dimensions`, `build_rank_audit`, `rank_account`
- Modify: `scripts/harness_tools.py:invoke` action `rank_leads`
- Modify: `scripts/select_for_enrichment.py:eligible_for_enrichment`, `select_accounts`
- Verify: `tests/test_scoring.py`, `tests/test_harness_tools.py`, `tests/test_selection.py`

**Dependencies:**
- Tasks 1 and 3; ranking cannot consume a thesis until receipt-authoritative completeness and signal precedence are enforced.

**Authority:**
- Preauthorized local actions: edit declared ranking, facade, selection, and focused tests; run fixture-based backend tests
- Stop for: changing the parent-agent planning boundary, introducing a custom scheduler, or publishing leads to an external system

**Steps:**
- [x] Step 1: Add one deterministic projector from validated `AccountThesis` and `AccountIndicator` records to the seven commercial dimensions already defined by `COMMERCIAL_WEIGHTS`.
- [x] Step 2: Make each `RankContribution` carry only the claims and semantic review that support that dimension; remove blanket reuse of `strongest_claim_ids`.
- [x] Step 3: Make `build_rank_audit()` accept the validated dossier/projected dimensions and reject raw caller-supplied commercial scores on the production path.
- [x] Step 4: Make `rank_leads` require a validated dossier for commercial ranking and remove the silent structural fallback from that action; preserve structural ranking only as an explicitly separate compatibility action.
- [x] Step 5: Replace the legacy A/B-only selection gate with an explicit delivery-policy check over validated rank state, thesis readiness, fit threshold, and research completeness so strong proactive accounts can enter the commercial queue.
- [x] Step 6: Add regression tests proving score tampering, missing thesis, wrong company, missing dimension evidence, and absent offer context cannot produce a priority lead.
- [x] Step 7: Record scoring-policy ID/version/hash, normalized inputs, formula, recency, contradiction, confidence, assertion IDs, review IDs, and claim IDs in every contribution; separate attractiveness from observability/actionability.
- [x] Step 8: Add a structural-only priority-workbook rejection test and a proactive-account ordering test without a TED/procurement event.

**Verification:**
- [x] `py -3 -m unittest tests.test_scoring tests.test_harness_tools tests.test_selection -v`
- Expected: identical dossiers produce identical rank audits; changing a thesis/evidence input changes the affected contribution; unsupported flat scores are rejected; selection can admit a validated strong proactive account without a TED event.

**Exit Criteria:**
- The only production commercial score is a deterministic projection of a validated account dossier, and the native facade cannot emit a commercial priority from a flat unvalidated row.

### Task 3: Harden account-scoped signals, receipts, and negative research

**Purpose:**
- Prevent cross-account evidence contamination, source-availability bias, and false negative intent states.

**Task Function:**
- Repair event identity, trigger projection, and offer-bound research coverage.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: attribution risk, policy coupling, and provider-boundary behavior.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently verify duplicate IDs, incomplete coverage, and non-TED triggers.

**Specification Coverage:**
- Zero critical account-attribution errors.
- Direct intent must accelerate priority but must not be the only commercial signal.
- `None found` must be reserved for complete account-scoped research.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `buying-signal-research`, `account-research`

**Files And Symbols:**
- Inspect: `scripts/score_leads.py:main`, `scripts/canonical_projection.py:project_verified_evidence`, `scripts/account_intelligence.py:account_signal_state`
- Modify: `scripts/score_leads.py:events_by_id` join and signal audit projection
- Modify: `scripts/canonical_projection.py:event_links`, positive signal projection, coverage binding
- Modify: `scripts/account_intelligence.py:validate_coverage_manifest`, `account_signal_state`
- Modify: `scripts/typed_contracts.py:CoverageManifest`
- Modify: `config/research_policy.json`, `config/signal_taxonomy.json`, `config/research_evidence_schema.json`
- Verify: `tests/test_scoring.py`, `tests/test_account_intelligence.py`, `tests/test_canonical_projection.py`, `tests/test_buying_signals.py`

**Dependencies:**
- Task 1 provides the receipt and claim-assurance primitives used by coverage validation.

**Authority:**
- Preauthorized local actions: edit declared signal, coverage, policy, schema, and focused tests; run fixture-based provider-adapter tests without external writes
- Stop for: live provider calls, paid enrichment, CRM writes, or changing campaign-specific source policy without explicit approval

**Steps:**
- [x] Step 1: Replace event-only indexing with `(company_id, event_id)` indexing and reject links whose company/event ownership is missing or ambiguous.
- [x] Step 2: Preserve independently verified portfolio expansion, modernization, supplier change, hiring, and organizational-change indicators even when no direct procurement/buying-signal claim exists.
- [x] Step 3: Add immutable research-policy ID/version/hash to `CoverageManifest`; validate required checks against the offer profile and require each completed check to reference a settled action receipt and attempt outcome.
- [x] Step 4: Distinguish `No trigger found in searched sources`, `Research incomplete`, `Unavailable`, and `No trigger found after required coverage`; only the last state may drive a strong negative conclusion.
- [x] Step 5: Add duplicate-event fixtures with different companies, dates, and URLs; add narrow-coverage and non-TED-trigger fixtures; assert that source availability does not become a negative buying signal.
- [x] Step 6: Include `scripts/lead_contract.py` and all signal-state consumers in the migration; require receipt-backed bounded disconfirmation before claiming no counterevidence.

**Verification:**
- [x] `py -3 -m unittest tests.test_scoring tests.test_account_intelligence tests.test_canonical_projection tests.test_buying_signals -v`
- Expected: duplicate IDs never cross accounts; non-TED verified triggers survive projection; incomplete or policy-mismatched coverage cannot emit a complete negative state.

**Exit Criteria:**
- Signal and negative-intent outputs are company-scoped, offer-policy-bound, receipt-backed, and explicit about uncertainty.

### Task 4: Make the workbook and QA dossier-first

**Purpose:**
- Deliver the account intelligence stakeholders need instead of a polished spreadsheet of structural scores.

**Task Function:**
- Integrate the canonical dossier into workbook generation and priority QA.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: cross-surface artifact integrity and stakeholder readability.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently verify workbook sheets, hyperlinks, and fail-closed QA.

**Specification Coverage:**
- Workbook must explain why an account is prioritized and preserve traceability to claims and sources.
- Structural validation must not pass a priority row that lacks a validated thesis.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`, `spreadsheets:Spreadsheets`

**Files And Symbols:**
- Inspect: `scripts/build_workbook.py:main`, `scripts/qa_leads.py:SURFACE_REQUIRED`, priority validation
- Modify: `scripts/build_workbook.py:main`, `scripts/build_task1_workbook.mjs` or retire it in favor of the canonical generator
- Modify: `scripts/qa_leads.py` priority and thesis-readiness checks
- Modify: `config/lead_generation_schema.json`
- Verify: `tests/test_harness_e2e.py`, `tests/test_artifact_manifest_side_effects.py`, workbook-specific tests under `tests`

**Dependencies:**
- Tasks 1–3 provide validated thesis, rank audit, events, coverage, and claim lineage.

**Authority:**
- Preauthorized local actions: edit declared workbook, QA, schema, and fixture tests; generate local workbook artifacts for inspection
- Stop for: external Google Sheets writes, CRM writes, destructive replacement of existing artifacts, or visual redesign outside the data contract

**Steps:**
- [x] Step 1: Add priority fields for why-this-account, why-now, problem hypothesis, strongest evidence, counterevidence, confidence, contact owner, recommended action, research gap, rank contributions, and source links.
- [x] Step 2: Add `Account Theses`, `Account Timeline`, `Evidence Ledger`, and `Research Gaps` sheets sourced from the canonical projection; keep claim IDs and source hyperlinks intact.
- [x] Step 3: Make `qa_leads.py` reject strict priority rows without a validated thesis, matching rank audit, source-backed claims, explicit uncertainty/counterevidence state, and company-bound contacts.
- [x] Step 4: Route every supported workbook generator through the same canonical projection or remove the duplicate path; do not maintain two divergent workbook schemas.
- [x] Step 5: Add a fixture E2E assertion that a stakeholder can trace a priority row from rank contribution to thesis assertion to evidence claim to source URL.
- [x] Step 6: Replace hard-coded retrieval/execution dates in `scripts/build_workbook.py` with manifest-derived offer, policy, scoring-policy, run, and retrieval revisions.
- [x] Step 7: Apply the same strict dossier gate to `scripts/build_shortlist.py`, `scripts/select_for_enrichment.py`, `scripts/build_task1_workbook.mjs`, `scripts/qa_leads.py`, and finalization readiness; compatibility sorting must not write a production priority artifact.

**Verification:**
- [x] `py -3 -m unittest tests.test_harness_e2e tests.test_artifact_manifest_side_effects -v`
- Expected: generated workbook contains all dossier sheets; strict QA rejects unexplained priority rows; artifact hashes and source links remain manifest-bound.

**Exit Criteria:**
- The canonical workbook visibly explains why each priority account is prioritized and cannot pass QA as scores-only output.

### Task 5: Prove the native runtime boundary and artifact lifecycle

**Purpose:**
- Demonstrate that Codex still owns planning while the deterministic kernel enforces the trust chain and durable outputs.

**Task Function:**
- Add representative trace and lifecycle proof across parent action selection, bounded workers, verification, projection, ranking, and export.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: cross-module execution trace and state/side-effect risk.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently verify no Python loop selects or schedules follow-up research.

**Specification Coverage:**
- Codex-native orchestration boundary and durable receipts.
- Account, offer, claim, thesis, rank, and workbook identity must share one run context.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-systematic-debugging`

**Files And Symbols:**
- Inspect: `scripts/harness_tools.py:invoke`, `scripts/action_lifecycle.py`, `scripts/action_receipts.py`, `scripts/run_manifest.py`
- Modify: only the canonical owner identified by a failing trace; do not add a new orchestration layer
- Verify: `tests/test_harness_e2e.py`, `tests/test_orchestration.py`, `tests/test_action_lifecycle.py`, `tests/test_action_receipts.py`, `tests/test_native_adapters.py`

**Dependencies:**
- Tasks 1–4 complete and focused tests pass.

**Authority:**
- Preauthorized local actions: run fixture-native traces, inspect receipts/manifests, and make narrowly scoped fixes in existing lifecycle owners
- Stop for: live external writes, unbounded retries, custom planner behavior, or any missing runtime capability that requires user action

**Steps:**
- [ ] Step 1: Execute one representative parent-selected account-research trace using the native facade and record the selected action, worker result, verifier decision, promoted claims, thesis, rank audit, and workbook artifact.
- [ ] Step 2: Assert that the parent selects the next action or stops; Python only validates, persists, projects, ranks, and exports the selected action.
- [ ] Step 2a: Capture one actual native Codex execution trace showing parent-selected action/stopping; fixture-only traces are insufficient for production-readiness claims.
- [ ] Step 3: Assert shared company ID, offer ID/version, run ID, manifest hash, claim IDs, and artifact references across the trace.
- [ ] Step 4: Verify replay is never treated as live/source assurance and that no-trigger is not emitted for incomplete research.
- [ ] Step 5: Add a static/runtime guard demonstrating no repository scheduler, planner loop, or hidden chain-of-thought persistence exists in the execution path.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_e2e tests.test_orchestration tests.test_action_lifecycle tests.test_action_receipts tests.test_native_adapters -v`
- Expected: the trace is bounded and parent-directed; all durable outputs settle consistently; no hidden scheduler or planner appears in the execution path.

**Exit Criteria:**
- A fresh fixture trace proves the intended Codex-native boundary and a manifest-bound, replay-safe artifact lifecycle.

### Task 6: Run the benchmark and reconcile acceptance evidence

**Purpose:**
- Establish whether the system produces better, more defensible leads than the prior structural shortlist.

**Task Function:**
- Execute final acceptance checks and record measured product value.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independent acceptance judgment, external-boundary risk, and evidence completeness.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independent plan and benchmark verification.

**Specification Coverage:**
- `docs/evaluations/account-intelligence-benchmark.md` thresholds and plan completion gates.
- Live-provider/CRM proof requested by product acceptance annotations.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`

**Files And Symbols:**
- Inspect: `docs/evaluations/account-intelligence-benchmark.md`, `docs/superpowers/plans/2026-11-10-account-intelligence-trust-chain-remediation-plan.md`
- Modify: `docs/evaluations/account-intelligence-benchmark.md` with measured results and explicit limitations
- Verify: all changed tests, generated workbook, run manifest, and benchmark record

**Dependencies:**
- Tasks 1–5 complete; no required test or QA failure remains.

**Authority:**
- Preauthorized local actions: run the full local suite, inspect generated artifacts, record benchmark results, and reconcile this plan
- Stop for: live-provider or CRM boundary checks requiring credentials or external writes unless explicitly approved; record the exact blocked proof instead

**Steps:**
- [ ] Step 1: Select 10–20 accounts from one campaign and one manifest revision; retain the manifest hash, offer ID/version, claim IDs, thesis IDs, and rank audits.
- [ ] Step 1a: Stratify the sample by structural fit, trigger availability, and evidence completeness before observing outcomes; define denominators and zero-observation handling.
- [ ] Step 2: Record claim-support precision, priority-thesis semantic support, critical attribution errors, top-10 pairwise ranking agreement, named-contact usefulness, and research cost against the declared thresholds.
- [ ] Step 2a: Run a blinded same-cohort comparison against the structural baseline and record a declared non-inferiority/uplift threshold plus adjudication for disagreements.
- [ ] Step 3: Run a non-destructive live-provider read probe and CRM export/dry-run boundary check when credentials and approval are available; otherwise record `blocked: external proof unavailable` and do not claim live readiness.
- [ ] Step 4: Run the full suite and reconcile actual files, test counts, benchmark results, deferred live proof, and plan status through `skill-verification-before-completion`.

**Verification:**
- [ ] `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- Expected: all local tests pass; benchmark thresholds are recorded; live-provider/CRM proof is either fresh and successful or explicitly blocked and excluded from acceptance claims.

**Exit Criteria:**
- The release decision states whether the harness meets the semantic product objective, with every failed threshold or unavailable external proof visible and no unverified claim presented as complete.

## Post-review Remediation Wave

The following tasks are added from the two completed commit-pinned reviews. They
are required before the existing completion criteria can be treated as true;
they do not add a planner, scheduler, CRM application, or alternative runtime.

### Task 7: Close production trust-chain and facade integration gaps

**Purpose:** Ensure every production dossier, rank result, and QA result is derived from the active promoted-evidence and offer context rather than caller-labelled or compatibility data.

**Task Function:** Implement the canonical production admission boundary and wire every native facade path to it.

**Template Profile:** Controller-selected from `agents/*.toml`; choose the lowest profile that can reliably handle cross-module contract changes.

**Specification Coverage:** Source assurance, dossier-first ranking, strict QA, offer binding, and structural-only compatibility behavior.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:** Inspect and modify `scripts/promote_evidence.py:promote_verified_claims`, `scripts/account_intelligence.py:validate_account_thesis/project_account_intelligence`, `scripts/harness_tools.py:invoke`, `scripts/score_leads.py:build_rank_audit/main`, `scripts/qa_leads.py:main`; add focused coverage in `tests/test_account_intelligence.py`, `tests/test_harness_tools.py`, and `tests/test_scoring.py`.

**Dependencies:** Tasks 1–4; the current promoted-evidence, run-manifest, and receipt contracts remain canonical.

**Authority:** Local source and test changes are preauthorized. Stop before any provider, CRM, or destructive write.

**Steps:**
- Add one shared production claim-set validator owned by `scripts/promote_evidence.py` that resolves every claim ID against the active manifest-bound promoted artifact, checks candidate hash, verifier decision, research run, company/offer scope, policy hash, and artifact lineage, and rejects mixed run identities.
- Make `project_account_intelligence()` require the validated parent run/manifest identity; keep any unpromoted path explicitly provisional and non-rankable.
- Make `harness_tools.invoke("rank_leads")` reject `production=true` with `compatibility_mode=true`, reject missing dossiers per company, validate dossier offer identity, and populate canonical offer fields before calling `rank_account()`.
- Make `harness_tools.invoke("qa_workbook")` forward production mode, dossier, and manifest arguments; infer the production requirement from workbook/manifest lineage when possible.
- Add regression tests that feed actual `score_leads.py` CSV output into production ranking and that prove missing promoted claims, mixed runs, missing dossiers, and non-production QA all fail closed.

**Verification:** `py -3 -m unittest tests.test_account_intelligence tests.test_harness_tools tests.test_scoring -v`

**Exit Criteria:** No production priority row can be produced from caller-labelled evidence, flat scores, mixed runs, or a QA invocation that skipped the dossier gate.

### Task 8: Make commercial ranking dimension-specific and signal-aware

**Purpose:** Make the shortlist explain why each commercial dimension is high and prevent structural observability from acting as an unintended negative intent signal.

**Task Function:** Replace generic claim/review reuse and legacy selection gates with evidence-bound projections and explicit signal precedence.

**Template Profile:** Controller-selected from `agents/*.toml`; choose the lowest profile that can reliably change scoring and selection contracts.

**Specification Coverage:** Evidence-derived commercial ranking, account intelligence explanations, independent environmental triggers, and uncertainty-preserving selection.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:** Modify `scripts/score_leads.py:project_commercial_dimensions/build_rank_audit/_commercially_strong_event/classify_signal`, `scripts/select_for_enrichment.py:eligible_for_enrichment`, and `scripts/canonical_projection.py:project_verified_evidence`; add regression coverage in `tests/test_scoring.py`, `tests/test_selection.py`, and `tests/test_canonical_projection.py`.

**Dependencies:** Task 7; promoted claims and production dossier identity must be trustworthy first.

**Authority:** Local scoring and selection changes are preauthorized. Do not claim commercial uplift until Task 11 benchmark evidence exists.

**Steps:**
- Return exact claim IDs and semantic-review IDs for each fit, opportunity, need, change, direct-intent, access, and confidence contribution; never substitute the thesis-wide strongest-claim list.
- Derive opportunity from an explicit versioned evidence rubric; distinguish identified buyer, verified contact route, and hypothetical access; return `Research required` or zero for unsupported dimensions according to the scoring policy.
- Apply each indicator’s confidence, recency, and counterevidence in the dimension transformation and record those inputs in `normalized_inputs`.
- Admit dossier-validated accounts using commercial `RankAudit` state plus delivery policy while retaining identity/geography safety checks; move structural coverage into uncertainty/actionability instead of unconditional exclusion.
- Project verified environmental event claims independently of direct buying-intent claims; direct intent remains a stronger separate signal.
- Require both source assurance and verified attribution for strong events and preserve `Research incomplete` when coverage is not receipt-complete.

**Verification:** `py -3 -m unittest tests.test_scoring tests.test_selection tests.test_canonical_projection -v`

**Exit Criteria:** Every ranked commercial contribution has dimension-specific evidence, and a verified non-procurement trigger cannot disappear merely because no duplicate direct-intent claim exists.

### Task 9: Make identity, review mapping, conflict handling, and hashes deterministic

**Purpose:** Prevent duplicate accounts, order-dependent validation, and unstable lineage from weakening dossier joins and stakeholder trust.

**Task Function:** Reuse canonical identity logic and make all semantic/event/dossier aggregation collision-aware.

**Template Profile:** Controller-selected from `agents/*.toml`; choose the lowest profile that can reliably update shared identity and lineage helpers.

**Specification Coverage:** Collision-safe account identity, semantic review stability, event integrity, and reproducible artifacts.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`.

**Files And Symbols:** Inspect `scripts/normalize_dedupe.py:main/company_id`, `scripts/harness_tools.py:_normalize_company/invoke`, `scripts/account_intelligence.py:validate_account_thesis/calculate_structural_fit/build_account_timeline/project_account_intelligence`; add tests in `tests/test_harness_tools.py`, `tests/test_account_intelligence.py`, and `tests/test_normalize_dedupe.py`.

**Dependencies:** Task 7; production claim and run identity must already be explicit.

**Authority:** Local identity and deterministic serialization changes are preauthorized. Route ambiguous identities to manual review; never silently merge them.

**Steps:**
- Expose one canonical company normalization/deduplication helper and call it from the native facade; reject or quarantine same-ID conflicting variants.
- Index approved semantic reviews as criterion-to-set, or bind each indicator to a specific review instance; reversing equivalent review input must not change validation.
- Resolve competing fact claims using explicit source precedence and effective dates; retain unresolved conflicts in the dossier instead of allowing iteration order to decide.
- Require matching company, event type, and date identity attributes before merging event corroboration.
- Require an explicit parent run ID and canonical-sort claims/reviews before dossier hashing and projection lineage generation.

**Verification:** `py -3 -m unittest tests.test_harness_tools tests.test_account_intelligence tests.test_normalize_dedupe -v`

**Exit Criteria:** Equivalent research sets produce identical IDs/hashes and every identity or evidence conflict is either resolved by policy or visible as a review state.

### Task 10: Preserve lineage and portability in the stakeholder export

**Purpose:** Deliver the evidence trail that differentiates the harness from a generic lead spreadsheet without making workbook generation machine-specific or unnecessarily expensive.

**Task Function:** Make priority-sheet schema, metadata, defaults, and preview behavior explicit and testable.

**Template Profile:** Controller-selected from `agents/*.toml`; choose the lowest profile that can reliably update the export and its regression proof.

**Specification Coverage:** Traceable workbook delivery, manifest-derived provenance, and personal-use operational stability.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:** Modify `scripts/build_task1_workbook.mjs:writeTableSheet/input metadata/preview generation`; add or extend `tests/test_task1_workbook.py` and the workbook QA fixtures.

**Dependencies:** Task 7; the workbook must consume canonical dossier and rank lineage.

**Authority:** Local export changes are preauthorized. Do not publish or write to Google Sheets/CRM as part of this task.

**Steps:**
- Give `writeTableSheet()` an explicit header list and derive Top-30 headers independently from priority rows, including rank audit, dossier hash, semantic reviews, strongest claims, projection run, and explanation columns.
- Resolve the spreadsheet dependency and default paths from the current runtime/project rather than a user-specific absolute cache path.
- Derive overview counts and retrieval metadata from the input manifest; remove the hard-coded accepted-company count.
- Make full-sheet PNG preview generation opt-in and handle zero-row overview and priority inputs without invalid ranges.
- Add an export regression that opens the generated workbook and asserts that priority lineage columns and source hyperlinks are physically present.

**Verification:** `py -3 -m unittest tests.test_task1_workbook -v`; then run the repository workbook QA command against the generated artifact.

**Exit Criteria:** The stakeholder-facing Top-30 sheet contains the exact evidence and rank lineage validated during preflight, regardless of overview schema, machine path, or row count.

## Verification

- `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- Validate the generated workbook with `scripts/qa_leads.py` and confirm all dossier sheets, source hyperlinks, rank audits, and manifest hashes are present.
- Inspect one complete native fixture trace from parent-selected action through settled workbook artifact.
- Compare benchmark judgments against computed order and record the declared thresholds in `docs/evaluations/account-intelligence-benchmark.md`.
- Confirm `git status --short` is clean except for intentional plan/implementation changes and confirm no external provider or CRM write was performed without approval.

## Completion Criteria

The plan is ready for completion verification when:

1. every priority account is dossier-backed, assertion-reviewed, source-supported, and company/offer-bound
2. commercial ranking is derived from validated thesis indicators and every contribution has dimension-specific evidence
3. event joins, trigger projection, negative research states, and coverage manifests are collision-safe and receipt-backed
4. the workbook and QA path expose and enforce account intelligence rather than scores-only output
5. the native runtime trace proves parent-agent planning authority and deterministic kernel boundaries
6. the benchmark record contains measured thresholds and explicit live-provider/CRM evidence or a clearly recorded external-proof blocker
7. all focused and full tests pass, with no unverified findings promoted to acceptance evidence

The plan may be marked `completed` only after `skill-verification-before-completion`
returns `verified` against fresh repository evidence.
