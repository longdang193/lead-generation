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

The reviewed revision is `7b065fa54a21a30278444306bc818e39873c41f9` on
`longdang193/lead-generation`; `origin/main` reaches the same full SHA and no
publication was required before review.

Both requested reviews completed in one authenticated repository-bound context
with `High` effort and fresh tabs:

- `GPT-5.6-Sol`, `High`, run `run-L3GaCF`, chat
  `6af25b8e-3b04-83eb-91d8-ce425f8bc7b0`; bounded result `completed`, visible
  response final and pinned to the reviewed SHA.
- `GPT-6`, `High`, run `run-vl4yc3`, chat
  `6af25c3e-9108-83eb-8685-0db3a42cab44`; bounded result `completed`, visible
  response final and pinned to the reviewed SHA.

No run was timed out, incomplete, ambiguous, or retried. The consolidated
source-validated findings are:

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

Unverified claims are excluded from this plan. In particular, no exact lead
count discrepancy is treated as a defect, no direct procurement event is
required for every good lead, and no new orchestration runtime is proposed.

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
- Isolation: `current workspace`; preserve unrelated changes and stop if the base is no longer `7b065fa54a21a30278444306bc818e39873c41f9`
- Commit policy: `no commits during execution`; the lead controller decides branch disposition after fresh verification
- Preauthorized local actions: edit declared files, run declared tests, inspect configured local fixtures and schemas, and produce bounded fixture artifacts
- User-approval actions: push, merge, live external provider calls, CRM writes, paid enrichment, destructive cleanup, or changing the approved product scope
- Parallel ownership: `none`; `typed_contracts.py`, `account_intelligence.py`, and the canonical projection are shared owners and are serialized
- Sequential fallback: execute Tasks 1–5 in order, then run Task 6 only after all producer and consumer tests pass

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `7b065fa54a21a30278444306bc818e39873c41f9`
- Expected workspace: `clean before implementation; this plan file is the only planned addition at authoring time`
- Next action: `complete Task 5 native-runtime evidence, then execute the benchmark gates in Task 6`
- Blockers: `local implementation is verified through 238 passing tests; actual native Codex trace and live-provider/CRM probe remain unavailable without the required authenticated external boundary and approval`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `Codex` | none | assertion-binding and claim-assurance tests | focused contracts and account-intelligence tests pass |
| Task 2 | `completed` | current | `Codex` | Tasks 1 and 3 | dossier-derived rank and fail-closed facade tests | scoring, facade, and selection tests pass |
| Task 3 | `completed` | current | `Codex` | Task 1 | collision, trigger, and coverage-policy tests | signal, projection, receipt, and evidence tests pass |
| Task 4 | `completed` | current | `Codex` | Tasks 2–3 | workbook and QA regression tests | production lineage gates, five account-intelligence sheets, and finalization tests pass |
| Task 5 | `active` | current | `Codex` | Tasks 1–4 | native trace and artifact integrity proof | fixture trace passes; actual native Codex execution trace remains outstanding |
| Task 6 | `pending` | current | `unresolved` | Task 5 | benchmark record and final verification | blocked pending native trace, blinded benchmark, and external-boundary decision |

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
