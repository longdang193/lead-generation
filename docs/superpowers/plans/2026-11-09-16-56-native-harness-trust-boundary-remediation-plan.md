---
layer: change
artifact_type: plan
contract_version: "1"
status: proposed
template_id: implementation-plan
name: native-harness-trust-boundary-remediation
targets:
  - scripts/typed_contracts.py
  - scripts/worker_dispatch.py
  - scripts/action_receipts.py
  - scripts/harness_tools.py
  - scripts/account_intelligence.py
  - scripts/dispatch_contracts.py
  - scripts/run_manifest.py
  - scripts/orchestrate_enrichment.py
  - scripts/score_leads.py
  - tests/test_typed_contracts.py
  - tests/test_action_receipts.py
  - tests/test_harness_tools.py
  - tests/test_account_intelligence.py
  - tests/test_scoring.py
  - tests/test_harness_e2e.py
  - docs/superpowers/plans/2026-11-09-agentic-account-intelligence-architecture-plan.md
---

# Native Harness Trust-Boundary Remediation Plan

## Goal

Make the Codex-native lead-generation harness safe to use for production lead
ranking and delivery without adding a Python planner, scheduler, fixed lane
sequence, or second orchestration runtime.

The parent Codex agent remains responsible for company selection, research
strategy, native subagent dispatch, hypotheses, and stopping decisions. Python
remains responsible for deterministic admission, typed validation, evidence
promotion, scoring, replay, QA, and publication barriers.

This plan is based on the completed, source-checked reviews of commit
`8554d90f94f3400116abcc81e10fd8e9fd0eacda`:

- `GPT-5.6-Sol`, `High`, bounded result `completed`, conversation
  `6af1e95c-3700-83ed-83f4-20592c511304`.
- `GPT-6`, `High`, bounded result `completed`, conversation
  `6af1ea3e-5170-83ed-a0d1-849641d1c215`.

Both reviews were read-only, used the repository-bound GitHub-review profile,
and cited the pinned revision. Unverified live-provider behavior, CI claims,
and claims that Python has already recreated a planner are excluded from the
implementation scope.

## Implementation Outcomes

### One authoritative action lifecycle

Every native action is bound to a run and company scope, admitted against the
manifest and shared budget, validated against a typed result, and settled once
through an idempotent receipt. Restart replay reconstructs only transitions
that have matching admission, result, and receipt evidence.

### Evidence-safe account intelligence

Unpromoted, rejected, unresolved, and unknown claims cannot enter verified fact
scoring. Multiple independent claims can corroborate one event without losing
lineage. Structural fit is calculated by the deterministic kernel; agent-authored
opportunity hypotheses remain separate and uncertainty-aware.

### Complete native deterministic boundary

The JSON tool facade exposes thin adapters over the existing discovery,
normalization, identity, evidence, promotion, scoring, ranking, QA, and export
functions. It does not encode sequencing or scheduling, and native publication
can occur only through the validated finalization boundary.

### Replay-safe finalization and ranking

Finalization reconstructs readiness from authoritative receipts, policy-derived
coverage, promoted evidence, ranking, QA, delivery, and artifact hashes. Canonical
ranking uses a manifest-pinned date and policy version rather than wall-clock
state.

### Real integration proof and truthful coordination state

The E2E test executes the deterministic kernel with external providers mocked,
creates a genuine workbook, validates evidence lineage and receipts, exercises
failure/rollback behavior, and verifies final delivery. The earlier architecture
plan no longer presents completed implementation as pending coordination work.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-code-standards`, `skill-test-driven-development`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`; the lead controller creates one authorized checkpoint after accepted proof
- Preauthorized local actions: edit listed source/tests/docs, run listed local tests and inspection commands, and update this plan's task ledger after accepted proof
- User-approval actions: push, merge, external provider calls or writes, dependency installation, destructive cleanup, and changes to strict-mode admission policy
- Parallel ownership: `none`; shared contracts, receipt state, harness facade, manifest, and tests require serialization
- Sequential fallback: execute Tasks 1–5 in dependency order in the current workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `8554d90f94f3400116abcc81e10fd8e9fd0eacda`
- Expected workspace: `clean; preserve the existing repository state`
- Next action: `activate Task 1 after implementation approval and establish the admitted-action lifecycle`
- Blockers: `none for plan creation; implementation approval and any external publication remain outside this plan`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | admission, budget, result, receipt lifecycle tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | evidence promotion and account-intelligence regression tests | pending |
| Task 3 | `pending` | current | `unresolved` | Tasks 1–2 | native facade and finalization boundary tests | pending |
| Task 4 | `pending` | current | `unresolved` | Tasks 1–3 | replay, concurrency, status, coverage, and date determinism tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 1–4 | real-kernel E2E workbook, QA, rollback, and full-suite proof | pending |

## Task Breakdown

### Task 1: Bind admission, validation, and receipts to one lifecycle

**Purpose:**
- Make native admission and settlement authoritative, restart-safe, and idempotent without introducing a scheduler.

**Task Function:**
- Harden the shared action contract and receipt transition boundary.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve the lowest profile that can safely change shared contracts and prove failure, idempotency, and side-effect behavior.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently validate lifecycle invariants and direct boundary tests.

**Specification Coverage:**
- Native action admission must consult run context, company scope, manifest identity, idempotency, and remaining budget.
- `budget_units` must be charged exactly as declared, not as one fixed attempt.
- A worker result must be tied to the admitted request and validated artifact/result hash.
- A receipt must be accepted only for an admitted action with a settled terminal state.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/typed_contracts.py:RunContext`, `NativeActionRequest`, `WorkerResult`, `ActionReceipt`
- Inspect: `scripts/worker_dispatch.py:DispatchBudget`, `admit_research_action`, `record_worker_result`
- Inspect: `scripts/action_receipts.py:append_receipt`, `replay_receipts`
- Modify: `scripts/typed_contracts.py`, `scripts/worker_dispatch.py`, `scripts/action_receipts.py`, `scripts/harness_tools.py`
- Verify: `tests/test_typed_contracts.py`, `tests/test_action_receipts.py`, `tests/test_harness_tools.py`

**Dependencies:**
- Current Pydantic contracts and receipt JSONL format are the compatibility baseline.

**Authority:**
- Preauthorized local actions: update the listed contracts, lifecycle functions, native facade wiring, and focused tests; preserve the existing receipt format unless a compatibility adapter is added in the same task.
- Stop for: a request to add a planner/scheduler, change external-provider permissions, delete receipt history, or alter strict-mode policy without explicit approval.

**Steps:**
- [ ] Step 1: Add or extend the admission boundary so it receives the manifest/run context and rejects mismatched run, company, action scope, contract/profile/strategy versions, duplicate non-idempotent attempts, and requests over the remaining budget.
- [ ] Step 2: Reserve exactly `budget_units` atomically and return an admission record that contains the canonical request hash and idempotency identity.
- [ ] Step 3: Require `record_worker_result` and `settle_action_receipt` to reference the admitted action; recompute or verify result/artifact hashes from the recorded artifacts before settlement.
- [ ] Step 4: Make replay reject missing, conflicting, or out-of-order transitions while preserving exact duplicate idempotency.
- [ ] Step 5: Route `harness_tools.invoke` actions `admit_action`, `validate_result`, and `record_receipt` through these lifecycle functions instead of direct model-only validation.

**Verification:**
- [ ] `py -3 -m unittest tests.test_typed_contracts tests.test_action_receipts tests.test_harness_tools -v`
- Expected: over-budget, wrong-company, unknown-action, fabricated-hash, duplicate-conflict, and out-of-order transitions fail; exact replay is idempotent; declared budget units are consumed exactly once.
- [ ] Direct boundary trace through `scripts/harness_tools.py` proves admission → validated result → settled receipt → replayed state.

**Exit Criteria:**
- No native action can report admitted or settled without manifest-bound lifecycle evidence, and the existing append-only journal remains readable by current consumers.

### Task 2: Close evidence, event, and fit-authority gaps

**Purpose:**
- Prevent unverified claims and unsupported hypotheses from inflating account quality while preserving useful uncertainty and corroboration.

**Task Function:**
- Align typed evidence promotion with account timeline and deterministic scoring.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve the lowest profile that can safely change evidence semantics and preserve existing source lineage.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently validate rejected, unresolved, corroborated, and speculative paths.

**Specification Coverage:**
- Only explicit promotion-derived verification states may influence verified fact scoring.
- Rejected, negative, unknown, and unresolved claims remain visible as uncertainty rather than becoming verified facts.
- One event may retain multiple supporting claim IDs and source statuses.
- Deterministic structural fit is authoritative; opportunity potential and direct intent remain separate.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/typed_contracts.py:EvidenceClaim`, `AccountHypothesis`, `AccountThesis`
- Inspect: `scripts/account_intelligence.py:_claim_model`, `build_account_timeline`, `validate_account_hypothesis`, `calculate_structural_fit`, `project_account_intelligence`
- Inspect: `scripts/promote_evidence.py` promotion envelope and status mapping
- Modify: `scripts/typed_contracts.py`, `scripts/account_intelligence.py`, `scripts/promote_evidence.py`
- Verify: `tests/test_typed_contracts.py`, `tests/test_account_intelligence.py`, `tests/test_evidence_promotion.py`

**Dependencies:**
- Task 1 must provide the lifecycle identity used to bind verifier and promotion evidence.

**Authority:**
- Preauthorized local actions: change evidence defaults/status normalization, event aggregation, thesis validation, and focused tests in the listed files.
- Stop for: weakening evidence lineage, treating direct intent as equivalent to structural fit, or discarding counterevidence and research gaps.

**Steps:**
- [ ] Step 1: Change unpromoted evidence defaults to `unknown` and require verifier/promotion metadata for `Verified` or `Supported` scoring states.
- [ ] Step 2: Make typed and legacy claim normalization use the same candidate status; never convert missing or unrecognized status to `Verified`.
- [ ] Step 3: Aggregate multiple claims under one `(company_id, event_id)` and retain all claim IDs, source URLs, statuses, and assurance levels; derive event status without dropping corroboration.
- [ ] Step 4: Remove the agent as an independent structural-fit authority by injecting the deterministic fit into projection or rejecting a mismatched thesis value.
- [ ] Step 5: Mark hypotheses without supporting claims as speculative and keep opportunity potential separate from verified structural facts.

**Verification:**
- [ ] `py -3 -m unittest tests.test_typed_contracts tests.test_account_intelligence tests.test_evidence_promotion -v`
- Expected: unpromoted claims contribute zero verified fit; rejected/unknown claims remain non-verified; corroborating event claims produce one event with complete lineage; mismatched fit values fail; unsupported hypotheses are explicitly speculative.

**Exit Criteria:**
- Account projection and scoring cannot promote agent-supplied or ambiguous evidence by default, and corroboration no longer causes a projection exception.

### Task 3: Complete the native facade and enforce finalization ownership

**Purpose:**
- Give the parent Codex agent a complete deterministic tool surface while keeping procedure and sequencing outside Python.

**Task Function:**
- Add thin adapters and a manifest-bound finalization gate.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve the lowest profile that can map existing utilities without duplicating algorithms or orchestration.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently verify adapter coverage and publication rejection paths.

**Specification Coverage:**
- The facade must expose discovery, normalization, deduplication, identity validation, evidence capture/promotion, fit, ranking, QA, and export through typed requests and typed artifact references.
- Only `finalize_run` may perform final publication.
- Finalization must derive readiness from receipts, promoted evidence, policy coverage, ranking, QA, delivery, and artifact hashes.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/harness_tools.py:invoke`, `scripts/orchestrate_enrichment.py:project_and_rank`, `finalize_run`
- Inspect: `scripts/import_discovery.py`, `scripts/normalize_dedupe.py`, `scripts/extract_website_evidence.py`, `scripts/select_for_enrichment.py`, `scripts/build_workbook.py`, `scripts/qa_leads.py`
- Inspect: `scripts/run_manifest.py:finalization_eligibility`, `publish_staged_output`
- Modify: `scripts/harness_tools.py`, `scripts/orchestrate_enrichment.py`, `scripts/run_manifest.py`
- Verify: `tests/test_harness_tools.py`, `tests/test_orchestration.py`, `tests/test_personal_mode.py`

**Dependencies:**
- Tasks 1 and 2 provide authoritative receipts, promoted evidence, and fact scores.

**Authority:**
- Preauthorized local actions: add thin facade adapters, wire existing deterministic functions, restrict direct publication, and update focused adapter/finalization tests.
- Stop for: adding sequencing logic, a planner loop, a scheduler, a duplicate ranking/export algorithm, or direct external-provider writes.

**Steps:**
- [ ] Step 1: Define typed facade actions for the existing discovery, normalization, deduplication, identity, capture, promotion, fit, ranking, QA, and workbook functions; return bounded references and structured errors.
- [ ] Step 2: Make `project_and_rank` invoke the canonical ranking boundary or rename it to reflect projection-only behavior; prevent callers from treating projection as ranking.
- [ ] Step 3: Change `finalization_eligibility` to reconstruct readiness from replayed receipts, policy-required checks, promoted claims, ranked rows, QA results, delivery counts, and manifest-bound artifact hashes.
- [ ] Step 4: Remove or reject direct native `publish_staged_output` requests; make the facade call only `finalize_run` after the readiness result is true.
- [ ] Step 5: Preserve atomic publication, Git revision, delivery, and recovery-marker protections while adding explicit rejection messages for missing lineage or unsettled actions.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_tools tests.test_orchestration tests.test_personal_mode -v`
- Expected: the parent can invoke every documented deterministic primitive through one typed boundary; direct publication is rejected; finalization rejects plausible flags without underlying receipts/evidence/QA and accepts a fully proven run.
- [ ] Direct boundary trace proves finalization produces the final workbook only after readiness reconstruction.

**Exit Criteria:**
- Codex can complete the documented deterministic parts of a run without importing modules directly or falling back to the legacy fixed pipeline, and publication has one enforced owner.

### Task 4: Make replay, status, coverage, concurrency, and ranking deterministic

**Purpose:**
- Remove cross-process races, status mismatches, policy drift, and wall-clock dependence that make runs unstable or difficult to recover.

**Task Function:**
- Harden compatibility and replay semantics around the shared kernel.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve the lowest profile that can prove concurrency, compatibility, and deterministic replay behavior.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently validate process-boundary and historical-replay behavior.

**Specification Coverage:**
- One canonical terminal-status enum must cross worker and lane boundaries.
- Coverage must be computed from policy-required checks and validated attempts, while parent stop decisions remain strategic inputs.
- Canonical ranking must use a pinned manifest date.
- Recovery must validate immutable recorded revisions without requiring current `HEAD` when recovering a previously accepted run.
- Receipt appends must be safe across independent CLI processes.

**Required Skills:**
- `skill-backend-verification`
- `skill-code-standards`
- `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/dispatch_contracts.py:validate_lane_output`, `scripts/typed_contracts.py:ResearchStatus`, `WorkerResult`, `ActionReceipt`
- Inspect: `scripts/action_receipts.py:append_receipt`, `replay_receipts`
- Inspect: `scripts/run_manifest.py:validate_manifest_revision`, recovery paths
- Inspect: `scripts/score_leads.py:classify_signal`
- Modify: `scripts/dispatch_contracts.py`, `scripts/action_receipts.py`, `scripts/run_manifest.py`, `scripts/score_leads.py`, and compatibility adapters in `scripts/typed_contracts.py`
- Verify: `tests/test_action_receipts.py`, `tests/test_orchestration.py`, `tests/test_scoring.py`, `tests/test_typed_contracts.py`

**Dependencies:**
- Tasks 1–3 establish the lifecycle and finalization consumers of these semantics.

**Authority:**
- Preauthorized local actions: add canonical enum adapters, policy-derived coverage calculations, OS-safe receipt serialization, pinned-date scoring, and recovery tests.
- Stop for: changing historical receipt contents, weakening strict delivery requirements, or introducing a database/dependency without an approved migration decision.

**Steps:**
- [ ] Step 1: Replace mixed terminal spellings with one canonical enum and explicit lowercase/legacy adapters at the compatibility boundary.
- [ ] Step 2: Compute coverage from validated attempts and policy-required checks; retain parent stop reasons and research gaps as explanatory metadata only.
- [ ] Step 3: Add an OS-level lock or equivalent atomic append strategy with uniqueness on `(run_id, action_id, attempt_id)` and bounded journal validation cost.
- [ ] Step 4: Require `RunContext.as_of_date` for canonical signal classification and pass it through ranking; keep a clearly named exploratory-only current-date path.
- [ ] Step 5: Split fresh-execution revision validation from recovery validation so a recorded reachable revision can recover after `HEAD` advances while new admission still requires the current revision.

**Verification:**
- [ ] `py -3 -m unittest tests.test_action_receipts tests.test_orchestration tests.test_scoring tests.test_typed_contracts -v`
- Expected: concurrent duplicate appends settle once; status adapters accept canonical worker failures; coverage cannot be declared complete from a stop decision alone; identical inputs and manifest date replay to identical signal classes; recovery succeeds from a reachable recorded revision after `HEAD` changes.

**Exit Criteria:**
- Independent processes, historical replay, compatibility adapters, and recovery produce deterministic results without weakening strict delivery or evidence policy.

### Task 5: Replace synthetic E2E proof and reconcile plan state

**Purpose:**
- Prove the real native kernel path and remove stale coordination claims from the architecture plan after implementation is verified.

**Task Function:**
- Build an integration fixture around the actual deterministic pipeline and reconcile durable documentation.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve the lowest profile that can exercise the integrated kernel and validate generated workbook contents.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: independently inspect workbook, lineage, rollback, and plan-state evidence.

**Specification Coverage:**
- Native E2E proof must execute identity validation, evidence promotion, canonical fit/ranking, workbook construction, QA, receipt replay, finalization, and rollback with external providers mocked.
- Coordination state must reflect implementation truth and remain the single durable workflow source.

**Required Skills:**
- `skill-backend-verification`
- `skill-test-driven-development`
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `tests/test_harness_e2e.py`, `scripts/build_workbook.py`, `scripts/validate_workbook.py`, `scripts/validate_deliverables.py`
- Modify: `tests/test_harness_e2e.py`
- Modify after implementation proof: `docs/superpowers/plans/2026-11-09-agentic-account-intelligence-architecture-plan.md`
- Verify: `tests/test_harness_e2e.py`, generated workbook and manifest artifacts in a temporary directory

**Dependencies:**
- Tasks 1–4 must pass their focused tests before the integrated test is changed.

**Authority:**
- Preauthorized local actions: update mocked E2E fixtures, validate generated workbook contents, and reconcile the architecture plan's coordination/execution record after accepted implementation proof.
- Stop for: live provider calls, external publication, deleting historical evidence, or marking the plan completed before fresh verification returns `verified`.

**Steps:**
- [ ] Step 1: Replace manually fabricated receipts, barrier flags, and byte-string workbook fixtures with calls through the native facade and existing workbook builder.
- [ ] Step 2: Mock only external discovery/provider responses; run identity, promotion, scoring, ranking, QA, receipt settlement, finalization, and publication through real repository code.
- [ ] Step 3: Assert XLSX structure/content, evidence-to-row lineage, receipt replay totals, manifest/artifact hashes, final delivery, and rollback after a forced QA or publication failure.
- [ ] Step 4: Run the focused and full test suites and record the exact results in the active plan's execution record.
- [ ] Step 5: Update the earlier architecture plan's task states and next action so it no longer says all tasks are pending after this remediation is accepted; do not mark either plan completed without verification skill evidence.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_e2e -v`
- Expected: the test creates a genuine workbook through the kernel, rejects missing lifecycle evidence, validates lineage and QA, publishes only after finalization, and leaves no final artifact after rollback.
- [ ] `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- Expected: all repository tests pass with no unrecorded scope changes.

**Exit Criteria:**
- The native path has a representative real-kernel proof, generated output is validated, failure/rollback is covered, and coordination documents match Git and test evidence.

## Verification

- `py -3 -m unittest tests.test_typed_contracts tests.test_action_receipts tests.test_harness_tools tests.test_account_intelligence tests.test_evidence_promotion tests.test_scoring tests.test_orchestration tests.test_personal_mode tests.test_harness_e2e -v`
- `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- Inspect `git diff --check` and `git status --short --branch`.
- Verify no native facade path can publish without `finalize_run`, no unpromoted claim contributes to verified fit, and replayed receipts match the admitted lifecycle.
- Run `skill-verification-before-completion` before changing this plan's status from `proposed` to `completed`.

## Completion Criteria

The plan is ready for completion verification when:

1. native admission, result validation, receipt settlement, and replay are one authoritative lifecycle;
2. unpromoted evidence cannot affect verified fact scoring and corroborating events preserve all claim lineage;
3. the native facade exposes the documented deterministic primitives without adding orchestration;
4. finalization reconstructs readiness and is the sole publication path;
5. status, coverage, concurrency, recovery, and ranking replay are deterministic;
6. the E2E test creates and validates a genuine workbook through the native kernel;
7. all task-local and final verification commands pass;
8. the earlier architecture plan, changed code, tests, and generated artifacts reconcile with current Git state;
9. deviations, blockers, and any deferred provider/live-runtime proof are recorded explicitly.

The plan remains `proposed` until implementation approval. It may be marked
`completed` only after `skill-verification-before-completion` returns
`verified` against fresh repository evidence.

## Plan Self-Review

- Scope is limited to source-confirmed trust, evidence, finalization, replay,
  operational-stability, and E2E-proof gaps; unverified live-provider claims are
  excluded.
- The plan preserves the Codex-native ownership boundary and contains no Python
  planner, scheduler, fixed signal/portfolio/contact sequence, or replacement
  orchestration layer.
- Shared files are serialized through one lead controller; no artificial
  parallel lanes are declared.
- Canonical contracts and lifecycle state precede facade adapters, integration
  proof, and documentation reconciliation.
- Every task names exact paths, symbols, commands, expected results, and stop
  conditions; every task is executable without inventing missing details.
