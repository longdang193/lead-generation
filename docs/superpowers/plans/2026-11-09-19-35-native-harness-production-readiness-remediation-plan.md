---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
contract_version: "1"
name: native-harness-production-readiness-remediation
targets:
  - scripts/action_lifecycle.py
  - scripts/orchestrate_enrichment.py
  - scripts/run_manifest.py
  - scripts/worker_dispatch.py
  - scripts/typed_contracts.py
  - scripts/harness_tools.py
  - scripts/qa_leads.py
  - scripts/promote_evidence.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/account_intelligence.py
  - scripts/native_worker.py
  - scripts/native_verifier.py
  - tests/test_action_lifecycle.py
  - tests/test_native_adapters.py
  - tests/test_harness_tools.py
  - tests/test_harness_e2e.py
  - tests/test_artifact_manifest_side_effects.py
  - tests/test_typed_contracts.py
  - tests/test_canonical_projection.py
  - tests/test_account_intelligence.py
  - tests/test_scoring.py
  - docs/superpowers/plans/2026-11-09-16-56-native-harness-trust-boundary-remediation-plan.md
---

# Native Harness Production-Readiness Remediation Plan

## Goal

Make the production lead-generation path executable, evidence-bound, and operationally maintainable at the native harness boundary without introducing a custom planner, scheduler, CRM writer, or closed end-to-end application. The existing Codex runtime, worker wrappers, lifecycle journal, typed contracts, ranking pipeline, and `finalize_run` publication barrier remain the system owners.

The plan addresses only findings validated by both completed read-only reviews and repository source evidence at commit `d70d56bdf3a368961227f167d9ae13a4357687c4`:

- `create_run_manifest` omits the `budget_limit` required by `admit_action`, while production dispatch does not consistently record admission, result validation, and settlement.
- `qa_leads.py` writes the canonical QA sample as CSV, while `_validate_finalization_artifacts` parses it as JSON.
- Structural-only verification can populate score-bearing qualification fields.
- Admission and evidence promotion are not fully bound to the admitted company set, scope, versions, and canonical request hash.
- Finalization still accepts manifest-authored coverage and delivery summaries without deriving all material facts from durable artifacts.
- The native worker/verifier wire format diverges from the public typed facade.
- Dispatch retry/backfill capacity and lifecycle journal replay can become unstable or expensive at larger campaign sizes.
- Buying-signal freshness and corroboration semantics can bias prioritization or confidence display.
- The current E2E test uses fixture shortcuts that bypass the production QA, promotion, ranking, and finalization path.

Preserve these boundaries: provider and CRM I/O remain fixture-backed in automated tests; provider-unavailable and unresolved evidence remain explicit; only `finalize_run` publishes; structural claims remain available for audit/context but cannot silently become source-proven ranking facts.

## Implementation Outcomes

### Production lifecycle is one authoritative execution contract

Production native actions receive a manifest-created run context, are authorized against the admitted company/action/version scope, use one canonical request hash, consume one reconciled budget ledger, and settle terminal success, failure, timeout, rejection, or partial outcomes durably. Duplicate admission remains idempotent and conflicting reuse remains rejected.

### Finalization validates real artifacts and durable facts

The QA sample has one CSV contract end to end. Finalization validates its fields and company scope, binds promoted evidence to candidate/verifier records, derives coverage and delivery from durable lifecycle and artifact IDs, and rejects internally consistent but unsupported summaries.

### Evidence and ranking preserve lead quality

Native worker and verifier records pass through one maintained typed boundary. Structural assurance can inform audit and research context but cannot write decisive score-bearing facts without source assurance. Buying-signal strength separates freshness from actionable demand, and corroboration metrics count verified supporting material separately from rejected or unresolved material.

### Regression proof covers the production path

Focused backend tests cover lifecycle authorization, budget/retry settlement, artifact validation, typed round trips, assurance-gated projection, signal/corroboration semantics, and failure recovery. A non-fixture integration trace uses mocked provider boundaries but real manifest creation, native dispatch, promotion, scoring, QA, finalization, and restart/replay behavior.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-backend-verification`, `skill-test-driven-development`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`; same-workspace writes are serialized and unrelated changes are preserved
- Commit policy: `verified per-task checkpoint commits preauthorized`; the lead creates a checkpoint only after task-local proof and ledger update are accepted
- Preauthorized local actions: inspect and edit the listed repository files, add or update focused tests and maintained documentation, run the declared local verification commands, and update this plan's task state and evidence
- User-approval actions: push, merge, publication, external provider or CRM writes, destructive cleanup, branch/base changes, force operations, or any schema migration outside the listed repository contracts
- Parallel ownership: none; `action_lifecycle.py`, `orchestrate_enrichment.py`, `run_manifest.py`, and `worker_dispatch.py` are shared contract owners and force serialization
- Sequential fallback: complete Tasks 1 through 6 in order in one lead workspace; do not start a later task until the prior task's focused proof and ledger checkpoint are accepted

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/native-harness-remediation`
- Base commit: `d70d56bdf3a368961227f167d9ae13a4357687c4`
- Expected workspace: clean at plan creation; preserve any later unrelated user changes
- Next action: obtain plan approval, then activate Task 1 after confirming the base and workspace are still unchanged
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | manifest/lifecycle contract tests | source review and current clean base |
| Task 2 | `pending` | current | `unresolved` | Task 1 | production dispatch settlement and budget tests | Task 1 checkpoint |
| Task 3 | `pending` | current | `unresolved` | Tasks 1-2 | QA/finalization boundary tests | Task 2 checkpoint |
| Task 4 | `pending` | current | `unresolved` | Task 3 | typed round trip and assurance/ranking tests | Task 3 checkpoint |
| Task 5 | `pending` | current | `unresolved` | Tasks 1-4 | scaling and signal/corroboration tests | Task 4 checkpoint |
| Task 6 | `pending` | current | `unresolved` | Tasks 1-5 | production-mode E2E and full suite | Task 5 checkpoint |

## Task Breakdown

### Task 1: Establish the manifest-bound run context and admission contract

**Purpose:**
- Make every production action admissible from the real manifest factory rather than from hand-built test state.

**Task Function:**
- Define the canonical run authorization and budget inputs used by all native actions.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost; Codex is the default because the task owns shared contracts and acceptance.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller owns the shared contract proof.

**Specification Coverage:**
- Fix the missing `budget_limit` integration.
- Bind company, action type, scope, contract version, strategy version, profile version, idempotency key, and canonical request hash to the admitted run context.
- Preserve idempotent duplicate admission and reject conflicting duplicates.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:create_run_manifest`, `scripts/orchestrate_enrichment.py:run_pipeline`
- Inspect: `scripts/action_lifecycle.py:_manifest_budget`, `scripts/action_lifecycle.py:admit_action`
- Inspect: `scripts/typed_contracts.py:NativeActionRequest`, `scripts/campaign_spec.py`
- Modify: `scripts/orchestrate_enrichment.py:create_run_manifest`
- Modify: `scripts/action_lifecycle.py:_manifest_budget`, `scripts/action_lifecycle.py:admit_action`
- Modify: `scripts/typed_contracts.py:NativeActionRequest` only when the canonical serialized request needs a maintained field or alias
- Verify: `tests/test_action_lifecycle.py`, `tests/test_harness_e2e.py`

**Dependencies:**
- None; base source and the completed review evidence are the inputs.

**Authority:**
- Preauthorized local actions: edit the listed manifest, lifecycle, and typed-request owners; add focused authorization tests; run the declared unit tests.
- Stop for: changing public campaign semantics without a recorded contract decision, adding a second lifecycle registry, external writes, or branch/base changes.

**Steps:**
- [ ] Step 1: Add the canonical manifest fields required for action authorization: `budget_limit`, admitted company IDs, permitted lane/action scopes, and the contract/strategy/profile versions used by the run. Derive the initial budget from the actual queued worker and verifier work plus explicit retry and reserve capacity; do not hard-code the current `30 × 3` campaign shape.
- [ ] Step 2: Add one canonical request serializer/hash routine owned by the lifecycle contract. Recompute the request hash at admission from the request fields excluding the supplied hash, then reject forged hashes before writing an admission event.
- [ ] Step 3: Validate that `company_id`, `action_type`, `scope`, and version fields are authorized by the manifest before reserving budget. Keep duplicate `(action_id, attempt_id)` replay idempotent only when the full admitted contract matches.
- [ ] Step 4: Build the manifest through `create_run_manifest` in tests and remove hand-fabricated budget/context assumptions from the lifecycle regression setup.

**Verification:**
- [ ] `py -3 -m unittest tests.test_action_lifecycle -v`
- Expected: first admission succeeds from a factory-created manifest; foreign company, wrong scope, wrong version, forged hash, over-budget, and conflicting duplicate requests are rejected; identical duplicate admission is idempotent.

**Exit Criteria:**
- Production-created manifests contain all required action context and budget data, and the lifecycle boundary rejects unauthorized or non-canonical requests before durable admission.

### Task 2: Integrate native dispatch, retries, and settlement with one budget ledger

**Purpose:**
- Ensure production worker execution cannot bypass the lifecycle or leave an admitted action orphaned when runtime capacity or retries fail.

**Task Function:**
- Reconcile durable action state with bounded subprocess execution and runtime attempt capacity.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct lifecycle and dispatch tests provide the required boundary proof.

**Specification Coverage:**
- Production `run_pipeline` must use admission, result validation, and settlement for native worker actions.
- Dispatch retries, timeouts, deterministic failures, and reserve backfills must have durable terminal outcomes and consistent budget accounting.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:admit_research_action`, `scripts/worker_dispatch.py:dispatch_native_lane`
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`
- Modify: `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:admit_research_action`, `scripts/worker_dispatch.py:dispatch_native_lane`
- Modify: `scripts/orchestrate_enrichment.py:run_pipeline`
- Verify: `tests/test_native_adapters.py`, `tests/test_action_lifecycle.py`, `tests/test_harness_e2e.py`

**Dependencies:**
- Task 1 complete; the manifest authorization and canonical request hash must exist first.

**Authority:**
- Preauthorized local actions: edit the listed dispatch/orchestration owners; add mocked subprocess tests for success, timeout, deterministic failure, retry exhaustion, reserve backfill, and restart; run focused backend tests.
- Stop for: live provider/CRM I/O, a new scheduler, unbounded concurrency, destructive process cleanup, or changes to external adapter protocols not covered by the repository contracts.

**Steps:**
- [ ] Step 1: Route every production queue item through the shared lifecycle adapter. Admission must happen before worker execution, worker output must pass `validate_result`, and every terminal path must emit `settle_action` with the recorded result/artifact hashes and coverage delta.
- [ ] Step 2: Make runtime reservation and durable admission use one bounded reservation helper. If runtime capacity is reserved before durable admission, release exactly that reservation when admission fails; if durable admission succeeds, a later scheduler failure must settle a terminal failed/unavailable action rather than leave an unsettled admission.
- [ ] Step 3: Account budget in `budget_units` consistently for first attempts, retries, verifier actions, and reserve-company actions. Preserve the existing terminal failure classes and cache reuse, but make retry/backfill headroom explicit in the run budget.
- [ ] Step 4: Keep worker wrappers responsible for subprocess deadline, cancellation, descendant cleanup, and output receipts; keep lifecycle responsible for authorization, settlement, and finalization eligibility.

**Verification:**
- [ ] `py -3 -m unittest tests.test_native_adapters tests.test_action_lifecycle -v`
- Expected: every production-shaped dispatch result has a matching admitted, validated, and settled lifecycle trace; reservation failure leaves no orphan admission; retries consume declared capacity; terminal failures remain replayable and idempotent.
- [ ] Run a mocked representative operation trace through `run_pipeline` and inspect the generated journal under `evidence/action_lifecycle/` for one settled event per admitted action.

**Exit Criteria:**
- The production dispatch path can reach a settled terminal state for success and all important failure paths without a second budget ledger disagreeing with the lifecycle journal.

### Task 3: Make QA and finalization validate one artifact contract and durable readiness

**Purpose:**
- Remove the deterministic QA publication blocker and prevent mutable summaries from overstating readiness.

**Task Function:**
- Reconcile artifact writers, finalization validators, coverage reconstruction, evidence lineage, and delivery counts.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: finalization tests and the production E2E trace cover the direct boundary.

**Specification Coverage:**
- Keep CSV as the canonical QA sample because `qa_leads.py` already writes CSV and the orchestration path names `qa.csv`.
- Validate QA rows, company scope, and required fields from real artifact bytes.
- Derive finalization coverage, evidence lineage, ranked IDs, and delivery counts from durable records rather than trusting flags alone.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/qa_leads.py:main`, `scripts/run_manifest.py:_validate_finalization_artifacts`, `scripts/run_manifest.py:reconstruct_finalization_readiness`, `scripts/run_manifest.py:finalization_eligibility`
- Inspect: `scripts/promote_evidence.py:promote_verified_claims`
- Modify: `scripts/run_manifest.py:_validate_finalization_artifacts`, `scripts/run_manifest.py:reconstruct_finalization_readiness`, `scripts/run_manifest.py:finalization_eligibility`
- Modify: `scripts/promote_evidence.py:promote_verified_claims` and `scripts/harness_tools.py:invoke` so production promotion requires a manifest-bound context
- Verify: `tests/test_harness_tools.py`, `tests/test_artifact_manifest_side_effects.py`, `tests/test_harness_e2e.py`

**Dependencies:**
- Tasks 1 and 2 complete; lifecycle coverage deltas and admitted scope must be available before readiness can be reconstructed.

**Authority:**
- Preauthorized local actions: edit finalization, promotion, and facade owners; add real-artifact tests; run focused backend and artifact-boundary checks.
- Stop for: accepting a second QA format, weakening strict delivery policy, allowing unbound production promotion, or publishing artifacts outside `finalize_run`.

**Steps:**
- [ ] Step 1: Parse `qa_sample` with `csv.DictReader`, require `company_id`, validate row IDs against admitted scope and the expected priority/qualification relationship, and retain the existing zero-error report requirement.
- [ ] Step 2: Bind promoted evidence to candidate hashes, verifier decisions, verifier run IDs, source policy, and admitted company IDs. Keep standalone compatibility behavior separate from production-authorized output so it cannot be mistaken for verified production evidence.
- [ ] Step 3: Reconstruct required lane coverage from settled lifecycle statuses and `coverage_delta`; require promoted evidence and ranked rows to be supported by the corresponding durable records; compare delivered IDs and counts with ranked IDs and campaign policy.
- [ ] Step 4: Treat manifest barrier, coverage, and delivery fields as cached summaries that must agree with reconstructed facts. Reject empty or partial evidence when the selected policy requires complete coverage.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_tools tests.test_artifact_manifest_side_effects -v`
- Expected: a real CSV QA sample passes; JSON or malformed CSV fails; foreign IDs, stale hashes, unbound promotion, false coverage, ranked/delivery mismatches, and incomplete lifecycle evidence fail finalization.

**Exit Criteria:**
- A production-shaped run cannot finalize unless its actual QA, evidence, ranking, coverage, delivery, lifecycle, and workbook artifacts agree under the selected policy.

### Task 4: Converge native wire contracts and gate score-bearing facts by assurance

**Purpose:**
- Remove the mismatch between native worker/verifier records and the typed facade, and stop structurally verified claims from inflating lead quality.

**Task Function:**
- Establish one maintained normalization/validation boundary and apply assurance rules before canonical projection and scoring.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: typed round-trip and scoring tests are the direct contract proof.

**Specification Coverage:**
- Native records using `candidate_claim_id`/`claim_value`, procurement sources, replay statuses, and native verifier decisions must pass through the typed boundary without scattered ad hoc adapters.
- Structural assurance remains visible for audit/context but only source assurance can mutate decisive score-bearing fields.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/typed_contracts.py:ContractModel`, `EvidenceClaim`, `VerifierDecision`, `ResearchRun`, `ResearchAttempt`
- Inspect: `scripts/native_worker.py:make_claim`, `scripts/native_verifier.py:main`, `scripts/account_intelligence.py:_claim_model`
- Inspect: `scripts/canonical_projection.py:project_verified_evidence`, `scripts/score_leads.py:calculate_fit`
- Modify: `scripts/typed_contracts.py` and one shared native-to-typed normalization owner; remove duplicate field/status conversions from consumers
- Modify: `scripts/canonical_projection.py:project_verified_evidence`, `scripts/score_leads.py:calculate_fit`, and `scripts/account_intelligence.py:build_account_timeline`
- Verify: `tests/test_typed_contracts.py`, `tests/test_canonical_projection.py`, `tests/test_account_intelligence.py`, `tests/test_scoring.py`, `tests/test_harness_tools.py`

**Dependencies:**
- Task 3 complete; promotion and finalization must agree on the same candidate/verifier identity fields.

**Authority:**
- Preauthorized local actions: edit the listed typed-contract, adapter, projection, and scoring owners; migrate affected tests to the single schema; run focused contract and ranking tests.
- Stop for: silently accepting unknown fields, weakening Pydantic validation, changing score weights without explicit evidence, or changing public source-policy semantics without a documented decision.

**Steps:**
- [ ] Step 1: Select the native candidate/verifier record shape as the inter-process contract and implement one compatibility boundary that maps it to in-process typed models. Support the actual `candidate_claim_id`, `claim_value`, `candidate_sha256`, `procurement`, `Not searched`, and `Unavailable` values through one maintained owner.
- [ ] Step 2: Add round-trip tests that feed an actual `native_worker.py` claim and `native_verifier.py` decision through the facade and back without loss of identity, hash, status, assurance, or provenance.
- [ ] Step 3: In projection, allow structural claims to remain in evidence/audit output but require `assurance_level == source` before writing `service_fit`, `residential_weg`, `berlin_relevance`, `management_type`, or `portfolio_size` values used by scoring.
- [ ] Step 4: Keep `calculate_fit` deterministic and explicit about missing/source-only inputs; add ranking regressions proving an unsupported structural claim cannot promote a lead into a higher tier.
- [ ] Step 5: Separate event freshness from buying intent using the existing signal taxonomy. Preserve publication age as one input, but require event category/relevance, buyer/opportunity evidence, deadline state, and verification status before classifying a signal as commercially strong.
- [ ] Step 6: In account-intelligence projection, retain rejected/unresolved lineage but compute `corroboration_count` only from independently verified supporting claims; expose rejected, unresolved, and contradictory counts separately.

**Verification:**
- [ ] `py -3 -m unittest tests.test_typed_contracts tests.test_canonical_projection tests.test_account_intelligence tests.test_scoring -v`
- Expected: native records validate through the shared boundary; structural-only claims cannot change decisive score fields; freshness-only events do not become strong buying signals; rejected/unresolved sources do not increase verified corroboration.

**Exit Criteria:**
- Typed consumers and native workers share one tested wire contract, and the ranking pipeline cannot treat structural or unresolved evidence as source-proven demand or fit.

### Task 5: Bound lifecycle replay cost and make retry/backfill capacity observable

**Purpose:**
- Prevent lifecycle journal growth and hidden attempt arithmetic from becoming operational bottlenecks as campaigns scale.

**Task Function:**
- Preserve the append-only journal as audit truth while making state reconstruction and capacity accounting bounded and inspectable.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic trace and bounded-read tests are sufficient for this maintenance task.

**Specification Coverage:**
- Avoid repeated full-journal scans for every transition.
- Make worker, verifier, retry, timeout, and reserve capacity consistent with the run deadline and configured concurrency.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/action_lifecycle.py:_read`, `admit_action`, `validate_result`, `settle_action`, `replay_lifecycle`
- Inspect: `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:dispatch_native_lane`
- Inspect: `scripts/runtime_config.py:RuntimeConfig`, `scripts/orchestrate_enrichment.py:run_pipeline`
- Modify: `scripts/action_lifecycle.py` with a validated per-run state snapshot or equivalent indexed state under the existing run lock
- Modify: `scripts/worker_dispatch.py:DispatchBudget` and `scripts/runtime_config.py` only where capacity accounting needs one canonical formula
- Verify: `tests/test_action_lifecycle.py`, `tests/test_native_adapters.py`, and a bounded synthetic lifecycle trace

**Dependencies:**
- Tasks 1 and 2 complete; the snapshot and capacity formula must represent the final lifecycle event types and budget units.

**Authority:**
- Preauthorized local actions: edit lifecycle state and dispatch budget owners; add deterministic scaling/consistency tests; run local timing and correctness probes.
- Stop for: deleting or rewriting the append-only journal, changing retention or cleanup policy, adding a distributed scheduler, or claiming a performance improvement without before/after evidence.

**Steps:**
- [ ] Step 1: Add a versioned per-run derived state file or equivalent indexed state updated under the existing run lock. Rebuild it from the append-only journal on missing/stale state, but use it for normal admission, validation, and settlement reads.
- [ ] Step 2: Preserve `replay_lifecycle` as the recovery/audit path and assert that snapshot state and journal replay produce identical reserved, settled, terminal, coverage, and idempotency results.
- [ ] Step 3: Instrument the synthetic trace to prove transition operations do not parse the full journal on every event; verify output equivalence for at least 1,000 admissions/results/settlements.
- [ ] Step 4: Expose attempted, retried, timed-out, verifier-reserved, reserve-backfill, reused, and remaining capacity in dispatch reconciliation so a 30-company/three-lane campaign cannot silently promise retries it cannot fund.

**Verification:**
- [ ] Run the synthetic 1,000-transition lifecycle trace and compare snapshot-backed state with a clean full replay.
- Expected: identical final state and receipts; normal transitions use bounded derived state; budget reconciliation reports explicit remaining retry/backfill capacity and never becomes negative.
- [ ] `py -3 -m unittest tests.test_action_lifecycle tests.test_native_adapters -v`

**Exit Criteria:**
- Lifecycle audit fidelity is preserved without mandatory full-journal parsing on every transition, and dispatch capacity claims are derived from actual configured work and observable in receipts/reconciliation.

### Task 6: Add a real production-mode integration trace and reconcile documentation

**Purpose:**
- Prove that the repaired contracts work together and prevent fixture-only tests from masking integration failures.

**Task Function:**
- Build the smallest provider-mocked, production-shaped campaign trace and update maintained planning evidence to match the implementation.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: resolve through Planning Dispatch from reasoning depth, ambiguity, scope, risk, and cost.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: the lead controller accepts the final backend and full-suite proof.

**Specification Coverage:**
- Exercise real manifest bootstrap, lifecycle admission/settlement, native worker/verifier adapters, evidence promotion, canonical projection, scoring/ranking, QA, finalization, and restart/replay behavior.
- Keep existing fixture tests as fast smoke tests, not as production-readiness proof.
- Reconcile stale plan claims and record deferred live-provider/CRM proof explicitly.

**Required Skills:**
- `skill-backend-verification`, `skill-test-driven-development`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `tests/test_harness_e2e.py:HarnessE2ETests._trace`, `tests/test_harness_e2e.py:test_two_valid_traces_and_early_stop_are_replayable`
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`
- Modify: `tests/test_harness_e2e.py` with a separate production-mode trace using mocked provider boundaries and real repository artifact writers/readers
- Modify: `tests/test_harness_tools.py`, `tests/test_artifact_manifest_side_effects.py`, `tests/test_action_lifecycle.py`, `tests/test_native_adapters.py`, and affected contract/ranking tests for cross-task regressions
- Modify: `docs/superpowers/plans/2026-11-09-16-56-native-harness-trust-boundary-remediation-plan.md` to remove claims that fixture shortcuts prove production readiness and to record the exact deferred live-provider/CRM boundary
- Verify: all tests under `tests/`, `git diff --check`, and the final plan/source reconciliation

**Dependencies:**
- Tasks 1 through 5 complete.

**Authority:**
- Preauthorized local actions: edit listed tests and maintained plan documentation; use deterministic provider fixtures/mocks; run focused and full repository verification.
- Stop for: live external provider or CRM writes, publication, unrelated documentation rewrites, or accepting a green fixture-only trace as production proof.

**Steps:**
- [ ] Step 1: Keep `_trace` as a fixture/replay smoke test, but add a production-mode integration test that calls the actual manifest factory and `run_pipeline` with provider subprocesses mocked at the adapter boundary.
- [ ] Step 2: Assert the real output artifacts: lifecycle journal, candidate/verifier records, promoted evidence, scores, priority rows, QA CSV/report, workbook hash, finalization proof, publication marker, and replay after a simulated restart.
- [ ] Step 3: Add failure-path assertions for QA format mismatch, failed/unavailable worker result, rejected evidence, forged admission, stale artifact hash, incomplete coverage, and ranked/delivery mismatch.
- [ ] Step 4: Update the prior remediation plan's proof ledger and deferred-capability notes so documentation distinguishes fixture proof, mocked provider proof, and unperformed live provider/CRM proof.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_e2e tests.test_harness_tools tests.test_artifact_manifest_side_effects -v`
- Expected: the production-mode mocked trace reaches final publication only through the lifecycle and artifact barriers; every listed failure is rejected with an actionable error and leaves replayable state.
- [ ] `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- Expected: the full suite passes with no test relying on hand-written production artifacts for the production-mode path.
- [ ] `git diff --check`
- Expected: no whitespace errors.

**Exit Criteria:**
- The repository has fresh direct-boundary, failure-path, final-state, idempotency/replay, and full-suite evidence for the repaired production path, with no unrecorded deferral or fixture-only readiness claim.

## Verification

Final verification is owned by the lead controller after all task-local proofs are accepted:

- `py -3 -m unittest tests.test_action_lifecycle tests.test_native_adapters tests.test_harness_tools tests.test_artifact_manifest_side_effects tests.test_typed_contracts tests.test_canonical_projection tests.test_account_intelligence tests.test_scoring tests.test_harness_e2e -v`
- `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- `git diff --check`
- Inspect one successful production-mode mocked run's lifecycle journal, finalization proof, QA CSV, promoted evidence, ranked IDs, delivery counts, workbook hash, and publication marker.
- Confirm no external provider or CRM write occurred and that only `finalize_run` published the final artifact.

## Completion Criteria

The plan is ready for completion verification when:

1. all six tasks have accepted task-local proof and completed ledger evidence
2. production dispatch reaches durable admission, validation, and settlement for every terminal action path
3. QA/finalization accepts the real CSV artifact and rejects false or unbound readiness
4. structural/unresolved evidence cannot change decisive lead ranking or verified corroboration
5. typed native worker/verifier round trips preserve identity, hashes, statuses, assurance, and provenance
6. lifecycle replay and dispatch capacity remain bounded and semantically equivalent to the journal truth
7. the production-mode mocked E2E trace proves success, failure, restart, replay, and publication barriers
8. the full test suite and `git diff --check` pass
9. documentation records fixture, mocked-provider, and deferred live-provider/CRM proof separately

This proposed plan must not be marked `completed` until `skill-verification-before-completion` returns `verified` against fresh repository evidence.
