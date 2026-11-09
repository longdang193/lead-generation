---
layer: change
artifact_type: plan
status: completed
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
- Next action: commit and push the verified branch, open the pull request, and complete the authorized independent review cycle
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `codex` | none | manifest/lifecycle contract tests | `py -3 -m unittest tests.test_action_lifecycle tests.test_campaign_spec tests.test_orchestration -v` — 44 tests passed; `git diff --check` passed |
| Task 2 | `completed` | current | `codex` | Task 1 | production dispatch settlement and budget tests | `py -3 -m unittest tests.test_action_lifecycle tests.test_native_adapters -v` — 39 tests passed; lifecycle retry trace settled 2 attempts; `git diff --check` passed |
| Task 3 | `completed` | current | `codex` | Tasks 1-2 | QA/finalization boundary tests | `py -3 -m unittest tests.test_harness_tools tests.test_artifact_manifest_side_effects -v` — 40 tests passed; `git diff --check` passed |
| Task 4 | `completed` | current | `codex` | Task 3 | typed round trip and assurance/ranking tests | `py -3 -m unittest tests.test_typed_contracts tests.test_canonical_projection tests.test_account_intelligence tests.test_scoring tests.test_harness_tools -v` — 49 tests passed; native worker/verifier subprocess round trip passed; `git diff --check` passed |
| Task 5 | `completed` | current | `codex` | Tasks 1-4 | scaling and signal/corroboration tests | `py -3 -m unittest tests.test_action_lifecycle tests.test_native_adapters -v` — 36 tests passed; 1,000-admission snapshot/journal equivalence and capacity reconciliation passed; `git diff --check` passed |
| Task 6 | `completed` | current | `codex` | Tasks 1-5 | production-mode E2E and full suite | `tests.test_harness_e2e` — 3 tests passed; disposable committed Git fixture, non-fixture `run_pipeline`, local worker/verifier stubs, artifact/replay/failure-boundary assertions; final focused suite 97 passed and full suite 202 passed |

## Review Consolidation (2026-11-09)

The bounded `GPT-5.6-Sol` / `High` review completed against commit `69d4660172d269c12be20b60c7a9ad59bbf0c155` and the visible response was verified in the repository-bound profile. The reviewer confirmed the plan heading `Task 2: Integrate native dispatch, retries, and settlement with one budget ledger`, `action_lifecycle.validate_result`, and `ActionLifecycleTests.test_rejected_result_cannot_become_validated_or_settled` before returning findings. The review verdict was not implementation-ready: no P0, four verified P1 findings, and two verified P2 findings.

- **P1 lifecycle rejection ownership:** `WorkerResult` excludes `Rejected`; `validate_result` rejects `validation_errors` before emitting a durable validation event; and `settle_action` requires that event. Task 2 therefore must own `typed_contracts.py`, `validate_result`, `settle_action`, and the rejection regression instead of only dispatch/orchestration. Add a durable `result_rejected` transition with validation errors and artifact/hash provenance, settle it as terminal `Rejected` with zero coverage, and prove replay/idempotency.
- **P1 retry authorization and budget identity:** `create_run_manifest` runs before queues and runtime policy exist, while `dispatch_native_lane` consumes private retry units but returns one aggregate record. Add an execution-authorization sealing phase after queue materialization; give every subprocess attempt a unique lifecycle `attempt_id` under one logical action; admit and settle each actual attempt; and reduce `DispatchBudget` to deadline/concurrency enforcement or a derived view.
- **P1 false durable coverage:** `coverage_delta` is an unrestricted dictionary copied into settlement and summed during replay without terminal-status, company, action-type, or scope validation. Reconstruct authoritative coverage from authorized successful terminal records; retain `coverage_delta` only as validated diagnostics or replace it with a typed, settlement-checked structure.
- **P1 row-level assurance leakage:** projection mutates retained qualification values and stores only the maximum claim assurance, while scoring consumes scalar fields without field-level provenance. Use per-field assurance or a source-only canonical fact map; never score retained structural/base values unless their source assurance is explicitly bound; add mixed-provenance regressions.
- **P2 stale derived lifecycle state:** Task 5 needs an append-first, atomic snapshot protocol with a schema/versioned journal watermark (byte offset or event count plus last-event digest). Snapshot loads must fall back to replay on watermark mismatch, corruption, or truncation; add crash-window fault injection tests.
- **P2 non-hermetic production proof:** Task 6 must run in a disposable temporary Git repository/worktree with the minimal committed fixture tree, `require_clean=True`, deterministic local worker/verifier stubs at the adapter boundary, and assertions that no writes escape the temporary root. Do not use `require_clean=False` or the implementation checkout for this readiness proof.

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
- [x] Step 1: Add the canonical manifest fields required for action authorization: `budget_limit`, admitted company IDs, permitted lane/action scopes, and the contract/strategy/profile versions used by the run. Derive the initial budget from the actual queued worker and verifier work plus explicit retry and reserve capacity; do not hard-code the current `30 × 3` campaign shape.
- [x] Step 2: Add one canonical request serializer/hash routine owned by the lifecycle contract. Recompute the request hash at admission from the request fields excluding the supplied hash, then reject forged hashes before writing an admission event.
- [x] Step 3: Validate that `company_id`, `action_type`, `scope`, and version fields are authorized by the manifest before reserving budget. Keep duplicate `(action_id, attempt_id)` replay idempotent only when the full admitted contract matches.
- [x] Step 4: Build the manifest through `create_run_manifest` in tests and remove hand-fabricated budget/context assumptions from the lifecycle regression setup.

**Verification:**
- [x] `py -3 -m unittest tests.test_action_lifecycle tests.test_campaign_spec tests.test_orchestration -v`
- Expected: first admission succeeds from a factory-created manifest; foreign company, wrong scope, wrong version, forged hash, over-budget, and conflicting duplicate requests are rejected; identical duplicate admission is idempotent.

**Exit Criteria:**
- Production-created manifests contain all required action context and budget data, and the lifecycle boundary rejects unauthorized or non-canonical requests before durable admission.

Task 1 evidence: the factory-created manifest records accepted companies, lane scope prefixes, contract/strategy/profile versions, and a budget derived from accepted-company count times lane count. Admission recomputes the canonical request hash before acquiring the lifecycle lock or appending an event. Fresh focused proof passed 44 tests across lifecycle, campaign manifest, and orchestration boundaries; `git diff --check` passed. The lifecycle fixture now derives request hashes through the production serializer, preserving duplicate idempotency and conflict rejection.

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
- Inspect: `scripts/action_lifecycle.py:validate_result`, `scripts/action_lifecycle.py:settle_action`
- Inspect: `scripts/typed_contracts.py:WorkerResult`, `scripts/typed_contracts.py:LifecycleEvent`, `scripts/typed_contracts.py:ActionReceipt`
- Modify: `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:admit_research_action`, `scripts/worker_dispatch.py:dispatch_native_lane`
- Modify: `scripts/orchestrate_enrichment.py:run_pipeline`
- Modify: `scripts/action_lifecycle.py:validate_result`, `scripts/action_lifecycle.py:settle_action`
- Modify: `scripts/typed_contracts.py:WorkerResult`, `scripts/typed_contracts.py:LifecycleEvent`, `scripts/typed_contracts.py:ActionReceipt`
- Verify: `tests/test_native_adapters.py`, `tests/test_action_lifecycle.py`, `tests/test_harness_e2e.py`

**Dependencies:**
- Task 1 complete; the manifest authorization and canonical request hash must exist first.

**Authority:**
- Preauthorized local actions: edit the listed dispatch/orchestration owners; add mocked subprocess tests for success, timeout, deterministic failure, retry exhaustion, reserve backfill, and restart; run focused backend tests.
- Stop for: live provider/CRM I/O, a new scheduler, unbounded concurrency, destructive process cleanup, or changes to external adapter protocols not covered by the repository contracts.

**Steps:**
- [x] Step 1: Route every production queue item through the shared lifecycle adapter. Add an explicit durable rejection transition for schema/validation failures that records validation errors plus canonical/raw-artifact hash provenance, settles terminal `Rejected` with zero coverage, and remains replayable and idempotent; do not weaken `WorkerResult` validation to accept malformed results.
- [x] Step 2: Seal execution authorization after queues and runtime policy are materialized but before the first subprocess. Make runtime reservation and durable admission use one bounded helper; release a reservation when admission fails, and settle a terminal failed/unavailable/rejected action when post-admission launch or scheduling fails.
- [x] Step 3: Give each actual subprocess invocation a unique lifecycle `attempt_id` under one logical `action_id`, admit immediately before launch, and settle every attempt. Account first attempts, retries, verifier actions, and reserve-company actions in the same durable budget; reduce `DispatchBudget` to deadline/concurrency enforcement or a derived cache rather than an independent attempt ledger.
- [x] Step 4: Keep worker wrappers responsible for subprocess deadline, cancellation, descendant cleanup, and output receipts; keep lifecycle responsible for authorization, settlement, and finalization eligibility.

**Verification:**
- [ ] `py -3 -m unittest tests.test_native_adapters tests.test_action_lifecycle -v`
- Expected: every production-shaped dispatch result has a matching admitted, validated, and settled lifecycle trace; rejection is terminal and settled with zero coverage; reservation failure leaves no orphan admission; a failure-to-timeout-to-success sequence has three identifiable admissions/settlements and exactly three consumed units; terminal failures remain replayable and idempotent.
- [ ] Run a mocked representative operation trace through `run_pipeline` and inspect the generated journal under `evidence/action_lifecycle/` for one settled event per admitted action.

**Exit Criteria:**
- The production dispatch path can reach a settled terminal state for success and all important failure paths without a second budget ledger disagreeing with the lifecycle journal.

Task 2 evidence: `WorkerResult` remains strict; malformed/invalid outcomes can be recorded through the explicit `result_rejected` lifecycle transition with validation errors and raw-result hash provenance, then settled as terminal `Rejected` with zero coverage. Production-shaped native dispatch now seals runtime execution authorization, admits each subprocess attempt under one logical action, releases reservations on admission failure, and settles completed, failed, and unavailable attempts. Fresh proof passed 39 tests, including a two-attempt failure-to-success trace with two admissions, two settlements, and two consumed budget units.

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
- [ ] Step 3: Reconstruct authoritative required-lane coverage from authorized company/action/scope records and defined successful terminal statuses. Treat `coverage_delta` as diagnostic unless it is a typed structure validated by `settle_action`; require promoted evidence and ranked rows to be supported by corresponding durable records; compare delivered IDs and counts with ranked IDs and campaign policy.
- [ ] Step 4: Treat manifest barrier, coverage, and delivery fields as cached summaries that must agree with reconstructed facts. Reject empty or partial evidence when the selected policy requires complete coverage.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_tools tests.test_artifact_manifest_side_effects -v`
- Expected: a real CSV QA sample passes; JSON or malformed CSV fails; foreign IDs, stale hashes, unbound promotion, false coverage, ranked/delivery mismatches, and incomplete lifecycle evidence fail finalization.

**Exit Criteria:**
- A production-shaped run cannot finalize unless its actual QA, evidence, ranking, coverage, delivery, lifecycle, and workbook artifacts agree under the selected policy.

Task 3 evidence: QA finalization now parses the canonical CSV bytes, requires `company_id` and `lead_tier`, validates admitted scope and qualification linkage, and reconstructs coverage only from successful authorized lifecycle records. Promoted evidence and ranked/delivered IDs are checked against durable records and policy counts. Fresh focused proof passed 40 tests across harness tools and artifact-manifest side effects; `git diff --check` passed.

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
- [x] Step 1: Select the native candidate/verifier record shape as the inter-process contract and implement one compatibility boundary that maps it to in-process typed models. Support the actual `candidate_claim_id`, `claim_value`, `candidate_sha256`, `procurement`, `Not searched`, and `Unavailable` values through one maintained owner.
- [x] Step 2: Add round-trip tests that feed an actual `native_worker.py` claim and `native_verifier.py` decision through the facade and back without loss of identity, hash, status, assurance, or provenance.
- [x] Step 3: In projection, allow structural claims to remain in evidence/audit output but build a per-field assurance map or separate source-only canonical fact map. Write score-bearing `service_fit`, `residential_weg`, `berlin_relevance`, `management_type`, or `portfolio_size` values only when that specific field is source-assured; retained base/structural values remain audit context unless their source assurance is explicitly bound.
- [x] Step 4: Keep `calculate_fit` deterministic and explicit about missing/source-only inputs; add mixed-provenance ranking regressions proving an unrelated source claim or an unsupported structural claim cannot make another field score or promote a lead into a higher tier.
- [x] Step 5: Separate event freshness from buying intent using the existing signal taxonomy. Preserve publication age as one input, but require event category/relevance, buyer/opportunity evidence, deadline state, and verification status before classifying a signal as commercially strong.
- [x] Step 6: In account-intelligence projection, retain rejected/unresolved lineage but compute `corroboration_count` only from independently verified supporting claims; expose rejected, unresolved, and contradictory counts separately.

**Verification:**
- [ ] `py -3 -m unittest tests.test_typed_contracts tests.test_canonical_projection tests.test_account_intelligence tests.test_scoring -v`
- Expected: native records validate through the shared boundary; structural-only claims cannot change decisive score fields; freshness-only events do not become strong buying signals; rejected/unresolved sources do not increase verified corroboration.

**Exit Criteria:**
- Typed consumers and native workers share one tested wire contract, and the ranking pipeline cannot treat structural or unresolved evidence as source-proven demand or fit.

Task 4 evidence: `typed_contracts.py` now owns native claim, verifier-decision, and research-run normalization, including candidate identity/hash fields, procurement/official source kinds, and native unavailable/not-searched statuses. Projection retains field-level assurance and excludes non-source score inputs. Signal freshness no longer upgrades a fresh event to `Strong` without source verification, category, buyer, opportunity/title, deadline, and source evidence. Account timelines preserve rejected/unresolved/contradictory lineage while counting corroboration only for source-assured support. Fresh proof passed 49 focused tests, including actual native worker/verifier subprocess round-trip; `git diff --check` passed.

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
- [x] Step 1: Add a versioned per-run derived state file or equivalent indexed state updated under the existing run lock. Append and fsync the journal event first, then atomically replace the snapshot with a watermark containing schema version, journal byte offset or event count, and last-event digest. Rebuild from the append-only journal whenever the snapshot is missing, corrupt, truncated, or its watermark does not match the journal.
- [x] Step 2: Preserve `replay_lifecycle` as the recovery/audit path and assert that snapshot state and journal replay produce identical reserved, settled, terminal, coverage, and idempotency results, including a crash window between journal fsync and snapshot replacement.
- [x] Step 3: Instrument the synthetic trace to prove transition operations do not parse the full journal on every event; verify output equivalence for at least 1,000 admissions/results/settlements and fault-inject stale, truncated, and corrupt snapshots.
- [x] Step 4: Expose attempted, retried, timed-out, verifier-reserved, reserve-backfill, reused, and remaining capacity in dispatch reconciliation so a 30-company/three-lane campaign cannot silently promise retries it cannot fund.

**Verification:**
- [ ] Run the synthetic 1,000-transition lifecycle trace and compare snapshot-backed state with a clean full replay.
- Expected: identical final state and receipts; normal transitions use bounded derived state; budget reconciliation reports explicit remaining retry/backfill capacity and never becomes negative.
- [ ] `py -3 -m unittest tests.test_action_lifecycle tests.test_native_adapters -v`

**Exit Criteria:**
- Lifecycle audit fidelity is preserved without mandatory full-journal parsing on every transition, and dispatch capacity claims are derived from actual configured work and observable in receipts/reconciliation.

Task 5 evidence: lifecycle transitions now append and fsync the journal before atomically replacing a versioned snapshot carrying byte-offset, event-count, and last-event digest watermarks. Normal transitions use the snapshot; missing, corrupt, stale, or mismatched snapshots fall back to full journal replay, while `replay_lifecycle` remains the audit path. `DispatchBudget.reconciliation()` exposes attempted, retried, timed-out, verifier-reserved, reserve-backfill, reused, remaining capacity, and deadline seconds. Fresh proof passed 36 lifecycle/native-adapter tests, including a synthetic 1,000-admission equivalence trace and no-full-journal transition assertion; `git diff --check` passed.

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
- [x] Step 1: Keep `_trace` as a fixture/replay smoke test, and add `test_production_mode_trace_is_hermetic_and_replayable` inside a disposable temporary Git repository. The test commits the minimal campaign/input fixture tree, calls the actual manifest factory with `require_clean=True`, runs non-fixture `run_pipeline` with deterministic local worker/verifier stubs at the adapter boundary, and snapshots the implementation checkout to prove no writes escape the temporary root.
- [x] Step 2: Assert the real lifecycle journal, candidate/verifier records, promoted evidence, scores, priority rows, QA CSV/report, workbook hash, finalization readiness proof, transient publication-marker creation/removal, terminal lifecycle state, and restart/replay equivalence.
- [x] Step 3: Assert unresolved readiness, path escape/direct-publication rejection, stale workbook hash, incomplete policy coverage, and ranked/delivery mismatch in the E2E boundary test; retain the dedicated QA format, worker unavailable, rejected evidence, forged admission, and artifact-hash regressions in `tests.test_harness_tools`, `tests.test_native_adapters`, `tests.test_evidence_promotion`, `tests.test_action_lifecycle`, and `tests.test_artifact_manifest_side_effects`.
- [x] Step 4: Update the prior remediation plan's proof ledger and deferred-capability notes so documentation distinguishes fixture proof, mocked-provider proof, and unperformed live provider/CRM proof.

**Verification:**
- [x] `py -3 -m unittest tests.test_harness_e2e tests.test_harness_tools tests.test_artifact_manifest_side_effects -v`
- Expected: the production-mode mocked trace reaches final publication only through the lifecycle and artifact barriers; every listed failure is rejected with an actionable error and leaves replayable state.
- [x] `py -3 -m unittest discover -s tests -p "test_*.py" -v` — 202 tests passed
- Expected: the full suite passes with no test relying on hand-written production artifacts for the production-mode path.
- [x] `git diff --check` — passed; only Git's LF/CRLF normalization warnings were emitted
- Expected: no whitespace errors.

**Exit Criteria:**
- The repository has fresh direct-boundary, failure-path, final-state, idempotency/replay, and full-suite evidence for the repaired production path, with no unrecorded deferral or fixture-only readiness claim.

Task 6 implementation evidence: `tests.test_harness_e2e` passes a production-shaped non-fixture run entirely inside a committed temporary Git repository. The worker and verifier are deterministic local adapter stubs; the repository's manifest factory, lifecycle admission/validation/settlement, promotion, canonical projection, scoring, ranking, workbook builder, QA, finalization, and replay code execute unchanged. The test observes the transient publication marker through `atomic_write`, confirms it is removed only after successful completion, and confirms the source checkout is byte/mtime unchanged. A replay-projection compatibility regression preserves legacy fixture score values without adding source assurance, while structural claims remain visible but unscored. Focused proof is 97 tests and full proof is 202 tests. Live provider latency/credentials, real external source fetches, and CRM writes remain deferred and were not claimed as proof.

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

`skill-verification-before-completion` returned `verified` against the fresh focused/full suite, diff check, plan reconciliation, and explicit deferred live-provider/CRM proof boundary. Plan completion does not imply commit, push, merge, or publication.
