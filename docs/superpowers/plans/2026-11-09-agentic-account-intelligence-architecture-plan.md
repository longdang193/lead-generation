---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
contract_version: "1"
name: agentic-account-intelligence-architecture
targets:
  - requirements.txt
  - config/research_policy.json
  - scripts/typed_contracts.py
  - scripts/account_intelligence.py
  - scripts/harness_tools.py
  - scripts/harness.py
  - scripts/run_manifest.py
  - scripts/worker_dispatch.py
  - scripts/promote_evidence.py
  - scripts/lead_contract.py
  - scripts/collect_buying_signals.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/orchestrate_enrichment.py
  - .agents/skills/lead-generation/SKILL.md
  - .agents/skills/account-research/SKILL.md
  - .agents/skills/lead-evidence/SKILL.md
  - .agents/skills/contact-verification/SKILL.md
  - examples/berlin_hausverwaltung.py
  - tests/test_typed_contracts.py
  - tests/test_account_intelligence.py
  - tests/test_harness_tools.py
  - tests/test_harness_e2e.py
  - tests/test_evidence_promotion.py
  - tests/test_research_contract.py
  - tests/test_orchestration.py
  - tests/test_end_to_end_enrichment.py
  - tests/test_buying_signals.py
  - tests/test_scoring.py
  - tests/test_provider_clients.py
  - tests/test_native_adapters.py
  - lead-generation-architecture.json
---

# Agentic Account Intelligence Architecture Plan

## Goal

Evolve the lead-generation harness into an agent-directed, evidence-first
account-intelligence system without turning the E2E runner into a closed
application. The parent agent must choose which accounts need more research,
which bounded worker or tool to use, when evidence is sufficient, and what
account thesis to form. Deterministic Python remains authoritative for
admission, identity, budgets, evidence promotion, projections, scoring,
ranking, QA, and publication.

The account-intelligence path must support informed assumptions when direct
buying signals are absent: observed events and verified claims remain separate
from agent-authored hypotheses; each hypothesis records supporting and
counter-evidence; research gaps and stopping reasons remain explicit; and
ranking never treats an unverified hypothesis as a verified fact.

## Implementation Outcomes

### Typed agent and tool boundaries

Pydantic contracts validate parent-agent requests, worker results, evidence,
verification decisions, research coverage, dispatch budgets, account events,
hypotheses, theses, and export references at process boundaries. Existing JSON
Schema, canonical claim hashes, manifest barriers, and semantic validators
remain compatibility and authority layers rather than being replaced.

### Evidence-first account intelligence

Accepted companies receive a company-bound research ledger that records
candidate, rejected, unresolved, and verified events with supporting claim IDs,
source provenance, scope, dates, and confidence. The ledger projects an account
timeline and a separate account thesis containing structural fit, opportunity
potential, indicators, hypotheses, counterevidence, research gaps, confidence,
and a recommended next action.

### Agentic harness with deterministic kernel

The harness exposes thin callable tools for discovery, normalization,
deduplication, identity validation, evidence capture and validation, fit
calculation, ranking, and workbook export. A parent planner can select and
sequence those tools or dispatch bounded workers without inheriting a fixed
TED/portfolio/contact lane order. The reference example and E2E test exercise
the harness; they do not become the production control plane.

### Coverage, trust, and replay safety

Research runs record required checks, completed checks, coverage status, stop
reason, strategy version, and shared-budget usage. Provider payloads are shape
validated before success is counted. Manifest-bound `as_of_date` and scoring
policy versions make ranking replayable. Self-declared agent or verifier
assurance cannot promote structural or replay evidence to source-level
`Verified`.

## Consolidated Review Basis

Both sequential architecture reviews were compared against the checked-out
source at commit `c0b3428ccd527dd8cb55a9a7067a40d8227f168e` on `main`. The
following findings are accepted into this plan:

1. The parent agent owns strategy, prioritization, bounded next actions, and
   account-thesis formation; deterministic code owns barriers and final facts.
2. Pydantic belongs at process boundaries and must coexist with the existing
   JSON Schema, canonical hashes, and semantic validators.
3. `scripts/promote_evidence.py:decision_assurance_level` must not allow a
   self-declared assurance field to elevate structural or replay evidence to
   source-level `Verified`.
4. `scripts/score_leads.py:derive_account_signal` must preserve verified
   positive events when another research lane is partial or unavailable.
5. `scripts/lead_contract.py:none_found_allowed` must require account-scoped,
   completed research; a narrow successful search must not become a broad
   `None found` conclusion.
6. Event identity must be composite `(company_id, event_id)`, and candidate,
   rejected, unresolved, and verified lineage must survive projection.
7. Research coverage, stopping metadata, shared dispatch budgets, provider
   response validation, and manifest-bound dates are required for honest
   assumptions and deterministic replay.
8. Hypotheses and theses are analytical outputs, not observed facts, and must
   be excluded from deterministic fact scoring unless their supporting claims
   independently satisfy the existing promotion contract.
9. The reference runner must stay thin, while the E2E test must mock only
   external providers and execute the real validation, promotion, projection,
   scoring, QA, staging, and atomic publication kernel.
10. The existing `worker_dispatch.py` to `orchestrate_enrichment.py` import
    boundary must be refactored so dispatch does not depend on the orchestrator
    as its validation owner.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-backend-verification`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared plan-owned files, run repository-local tests and validators, inspect configured local sources, and regenerate only plan-owned derived artifacts after canonical inputs change
- User-approval actions: push, merge, publication, dependency installation, destructive cleanup, external provider writes or spend, and changes to strict-mode admission policy
- Parallel ownership: `none`; `scripts/lead_contract.py`, `scripts/orchestrate_enrichment.py`, the manifest, and shared tests require serialization
- Sequential fallback: execute Tasks 1–6 in dependency order in the current workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `main`
- Base commit: `c0b3428ccd527dd8cb55a9a7067a40d8227f168e`
- Expected workspace: `clean; preserve the existing repository state`
- Next action: `activate Task 1 only after implementation approval and resolve its executor through Planning Dispatch`
- Blockers: `none for plan creation; no live provider access or publication is authorized by this plan`
- Publication: `no publication required` for the reviewed revision; the full SHA is already reachable from `origin/main`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | typed-contract and promotion regression tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | callable-boundary and orchestration tests | pending |
| Task 3 | `pending` | current | `unresolved` | Tasks 1–2 | account-ledger, timeline, thesis, and scoring tests | pending |
| Task 4 | `pending` | current | `unresolved` | Tasks 1–3 | coverage, provider-shape, budget, and replay tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 1–4 | harness-tool contract tests | pending |
| Task 6 | `pending` | current | `unresolved` | Tasks 1–5 | real-kernel E2E, workbook validation, and full suite | pending |

## Task Breakdown

### Task 1: Establish typed boundaries and trusted assurance

**Purpose:**
- Add the minimum typed contract layer needed for agent/tool boundaries while preserving existing JSON records and trusted promotion semantics.

**Task Function:**
- Define and enforce typed process-boundary records without moving business authority out of the deterministic kernel.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can safely handle schema compatibility, trust-boundary migration, and focused backend verification.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: assign independently to a profile that can verify assurance monotonicity and compatibility regressions.

**Specification Coverage:**
- Pydantic validates process boundaries; JSON Schema and canonical hashes remain authoritative.
- Self-declared assurance cannot promote replay or structural evidence to source-level `Verified`.
- Shared contracts include evidence, verifier decisions, research attempts/runs, run context, admitted work, dispatch results, and artifact references.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/lead_contract.py:claim_requirements_met`, `scripts/lead_contract.py:verifier_decision_valid`, `scripts/promote_evidence.py:decision_assurance_level`, `config/research_evidence_schema.json`
- Modify: `requirements.txt`, `scripts/typed_contracts.py`, `scripts/promote_evidence.py:decision_assurance_level`, `scripts/lead_contract.py` only where typed-boundary adapters are required
- Verify: `tests/test_typed_contracts.py`, `tests/test_evidence_promotion.py`, `tests/test_research_contract.py`

**Dependencies:**
- Base commit `c0b3428ccd527dd8cb55a9a7067a40d8227f168e` and the existing JSON schemas are the source of truth.

**Authority:**
- Preauthorized local actions: add the declared dependency bounds, typed models, adapters, and focused regression tests without changing existing record names or promotion barriers
- Stop for: any change that would replace JSON Schema, weaken source-verification requirements, install dependencies, or alter strict-mode admission without user approval

**Steps:**
- [ ] Step 1: Map each proposed Pydantic model to its existing JSON record fields and identify fields that must remain hash- or manifest-derived.
- [ ] Step 2: Add `requirements.txt` bounds `pydantic>=2.12,<3` and `jsonschema>=4.25,<5`, then implement `scripts/typed_contracts.py` with `EvidenceClaim`, `VerifierDecision`, `ResearchAttempt`, `ResearchRun`, `RunContext`, `AdmittedWorkItem`, `DispatchResult`, and `ArtifactRef`; use strict URL/date/datetime and bounded enum/score validation where existing records support it.
- [ ] Step 3: Make `decision_assurance_level()` monotonic: only a verified source-capable verifier registry entry can yield source assurance; replay and structural paths remain lower assurance regardless of payload self-declarations.
- [ ] Step 4: Add focused tests for valid serialization, rejection of malformed boundaries, canonical-hash preservation, and the assurance-escalation regression.

**Verification:**
- [ ] `py -3 -m unittest tests.test_typed_contracts tests.test_evidence_promotion tests.test_research_contract -v`
- Expected: all focused tests pass; replay/structural decisions never receive source assurance; existing JSON-Schema validation remains green.

**Exit Criteria:**
- Typed boundary models exist, serialize to compatible records, and cannot weaken evidence promotion or assurance semantics.

### Task 2: Extract deterministic tools from the run state machine

**Purpose:**
- Expose stable callable boundaries around the existing deterministic kernel and remove the dispatch-to-orchestrator validation dependency without changing `run_pipeline()` behavior.

**Task Function:**
- Separate admission, dispatch, verification/promotion, projection/ranking, and publication validation into reusable kernel entry points.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can safely refactor shared orchestration and prove backward compatibility.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate import direction, manifest authority, atomic publication, and failure propagation.

**Specification Coverage:**
- Tools perform actions; agents decide strategy.
- Manifest state/barriers, capability/live-replay admission, budgets, verifier assurance, projection/scoring/ranking, QA, and publication remain deterministic authorities.
- No second workflow engine, scoring pipeline, or export pipeline is introduced.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`, `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:dispatch_native_lane`, `scripts/promote_evidence.py:promote_verified_claims`, `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/build_workbook.py`
- Modify: `scripts/run_manifest.py:prepare_run` (new boundary), `scripts/worker_dispatch.py:dispatch_research` (new boundary and validation ownership), `scripts/promote_evidence.py:verify_and_promote` (new boundary), `scripts/orchestrate_enrichment.py:project_and_rank` and `validate_and_publish` (new boundaries), plus imports and compatibility wrappers
- Verify: `tests/test_orchestration.py`, `tests/test_native_adapters.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:**
- Task 1 typed models and assurance rules.
- Existing `run_pipeline()` remains the compatibility integration path until Task 6 proves the harness path.

**Authority:**
- Preauthorized local actions: refactor internal imports, add callable wrappers, preserve CLI entry points, and add failure-path tests for manifest, dispatch, promotion, and atomic publication
- Stop for: deleting or renaming an existing CLI contract, introducing a second state machine, changing manifest authority, or changing publication behavior without a migration test and user approval

**Steps:**
- [ ] Step 1: Extract `prepare_run`, `dispatch_research`, `verify_and_promote`, `project_and_rank`, and `validate_and_publish` as thin functions over existing logic, with typed inputs/outputs at their boundaries.
- [ ] Step 2: Move lane-output validation ownership out of `orchestrate_enrichment.py` so `worker_dispatch.py` depends on a neutral contract/validation module rather than importing its caller.
- [ ] Step 3: Keep `run_pipeline()` as a compatibility composition of those boundaries and preserve atomic staging, manifest updates, and nonzero failure propagation.
- [ ] Step 4: Add tests for direct callable use, invalid admission, budget exhaustion, promotion failure, projection failure, QA failure, and publication rollback/idempotency.

**Verification:**
- [ ] `py -3 -m unittest tests.test_orchestration tests.test_native_adapters tests.test_end_to_end_enrichment -v`
- Expected: existing fixture pipeline behavior is unchanged; direct boundaries are callable; failures stop before publication and leave no partial final output.

**Exit Criteria:**
- The deterministic kernel is reusable through explicit boundaries, and the original pipeline remains a compatibility wrapper rather than the only control surface.

### Task 3: Add the account-event ledger and evidence-first thesis layer

**Purpose:**
- Preserve useful verified events during partial research and turn account evidence into an auditable timeline and bounded thesis without presenting assumptions as facts.

**Task Function:**
- Attribute account events to verified claims, retain decision lineage, and produce hypotheses and theses that explain why an account deserves the next research or sales action.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can model event identity, evidence lineage, analytical uncertainty, and deterministic projection safely.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate company scoping, composite event joins, partial-research preservation, and hypothesis separation.

**Specification Coverage:**
- Account Intelligence covers select company, search environment, discover candidate events, verify events, and build account timeline.
- Composite event identity is `(company_id, event_id)`.
- Candidate, rejected, unresolved, and verified outcomes remain traceable.
- Account hypotheses and theses contain supporting claims, counterevidence, confidence, gaps, and recommended action; they do not become verified facts by authorship alone.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/collect_buying_signals.py:account_research_state`, `scripts/score_leads.py:classify_signal`, `scripts/score_leads.py:derive_account_signal`, `scripts/canonical_projection.py`, `config/signal_taxonomy.json`, `config/research_policy.json`
- Modify: `scripts/account_intelligence.py`, `scripts/collect_buying_signals.py`, `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/lead_contract.py`, `scripts/build_workbook.py`
- Verify: `tests/test_account_intelligence.py`, `tests/test_buying_signals.py`, `tests/test_scoring.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:**
- Tasks 1–2 typed boundaries and callable deterministic stages.
- Existing verified claim and signal taxonomies remain the canonical fact vocabulary.

**Authority:**
- Preauthorized local actions: add the ledger, attribution, timeline, hypothesis, and thesis projections; preserve positive verified events; add account-scoped lineage and focused tests
- Stop for: treating an agent-authored hypothesis as a promoted claim, changing score weights without an explicit policy update, or dropping verified positives because another lane is partial

**Steps:**
- [ ] Step 1: Implement `scripts/account_intelligence.py` with typed `ObservedEvent`, `AccountEventAttribution`, `CandidateDecision`, `AccountHypothesis`, and `AccountThesis` records plus deterministic joins on `(company_id, event_id)`.
- [ ] Step 2: Record the search environment, candidate discovery result, verification decision, rejection or unresolved reason, supporting claim IDs, and event date/source scope for every event considered.
- [ ] Step 3: Project an account timeline and thesis from verified claims plus explicitly labeled hypotheses; include counterevidence and research gaps, and keep direct intent nullable when no direct signal is verified.
- [ ] Step 4: Update signal derivation so verified positives survive partial or unavailable lanes and so hypotheses influence recommended action only through explicit, tested policy fields rather than fact score inputs.
- [ ] Step 5: Add a canonical workbook sheet or linked account-ledger artifact with stable IDs and source references, preserving existing workbook consumers.

**Verification:**
- [ ] `py -3 -m unittest tests.test_account_intelligence tests.test_buying_signals tests.test_scoring tests.test_end_to_end_enrichment -v`
- Expected: a verified event remains present when a later lane is partial; same-named events from different companies do not collide; rejected/unresolved lineage is retained; hypotheses are visibly distinct from verified evidence.

**Exit Criteria:**
- Every accepted company can produce a traceable event ledger, timeline, and thesis that supports informed prioritization without fabricating direct buying intent.

### Task 4: Enforce research coverage, stopping, budgets, and replay determinism

**Purpose:**
- Make incomplete research and negative conclusions honest, bounded, budgeted, and reproducible.

**Task Function:**
- Define the research-run state and enforce provider, coverage, budget, and date invariants at admission and scoring boundaries.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can safely change cross-cutting research contracts and deterministic ranking behavior.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate outage/partial semantics, provider-shape rejection, shared-budget settlement, and replay stability.

**Specification Coverage:**
- `None found` is permitted only for completed account-scoped research with zero usable results.
- Agent-selected work consumes the same `DispatchBudget` and cannot bypass capability or manifest admission.
- Required checks, completed checks, coverage status, stop reason, strategy version, `as_of_date`, and scoring policy version are persisted.
- Ranking is stable under worker completion order and does not use wall-clock time implicitly.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/lead_contract.py:none_found_allowed`, `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:dispatch_native_lane`, `scripts/collect_buying_signals.py:account_research_state`, `scripts/score_leads.py:classify_signal`, `scripts/run_manifest.py:validate_manifest_revision`, `scripts/provider_clients.py:ted_search`
- Modify: `config/research_policy.json`, `scripts/collect_buying_signals.py`, `scripts/lead_contract.py`, `scripts/score_leads.py`, `scripts/run_manifest.py`, `scripts/worker_dispatch.py`, `scripts/provider_clients.py`
- Verify: `tests/test_research_contract.py`, `tests/test_provider_clients.py`, `tests/test_native_adapters.py`, `tests/test_scoring.py`, `tests/test_orchestration.py`

**Dependencies:**
- Tasks 1–3 typed run records, account ledger, and deterministic stage boundaries.

**Authority:**
- Preauthorized local actions: add explicit coverage and stopping fields, reject malformed provider responses, bind scoring to manifest dates, and route all worker/tool calls through shared budget settlement
- Stop for: live provider access, new credentials, silent schema migration, broadening `None found`, or changing score policy without a versioned configuration and regression tests

**Steps:**
- [ ] Step 1: Extend research policy and manifest records with `strategy_version`, `required_checks`, `completed_checks`, `coverage_status`, `stop_reason`, `as_of_date`, and `scoring_policy_version`.
- [ ] Step 2: Make `none_found_allowed()` inspect account scope, required/completed checks, provider status, truncation, and verified claims before allowing the negative state.
- [ ] Step 3: Validate TED, Overpass, Apify, and Hunter response shapes before recording an attempt as successful; distinguish unavailable, partial, empty, and completed-zero outcomes.
- [ ] Step 4: Make `DispatchBudget` the single settlement path for parent-selected tools and worker lanes, including retries and failed attempts, with deterministic receipts.
- [ ] Step 5: Replace implicit `date.today()` ranking inputs with manifest-bound `as_of_date` and persist the policy version used for classification and tie-breaking.
- [ ] Step 6: Add tests for narrow-search false negatives, provider HTML/error payloads, budget exhaustion, retry accounting, partial research, and repeated replay with reordered worker completion.

**Verification:**
- [ ] `py -3 -m unittest tests.test_research_contract tests.test_provider_clients tests.test_native_adapters tests.test_scoring tests.test_orchestration -v`
- Expected: malformed providers cannot create successful research runs; partial/outage states cannot become `None found`; every admitted action settles against the shared budget; identical manifest inputs produce identical scores and ranks.

**Exit Criteria:**
- Research status, stopping, budget, provider, and date semantics are explicit and enforced before evidence or ranking can claim completeness.

### Task 5: Expose bounded harness tools and update skills

**Purpose:**
- Give the parent agent a small, typed tool surface while keeping procedure in skills and strategy in the agent.

**Task Function:**
- Adapt existing deterministic functions into validated tool calls and document how the parent agent selects, dispatches, verifies, and stops work.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can design a minimal reusable adapter surface and reconcile existing skill instructions.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate that adapters do not encode lane order, duplicate scoring/export logic, or bypass contracts.

**Specification Coverage:**
- Skills decide procedure; agents decide strategy; tools perform actions; Pydantic enforces contracts; deterministic functions calculate facts.
- The harness exposes `discover_companies`, `normalize_company`, `deduplicate`, `validate_identity`, `capture_evidence`, `validate_evidence`, `calculate_fit`, `rank_leads`, and `export_workbook`.
- Existing skills are extended rather than duplicated.

**Required Skills:**
- `skill-code-standards`

**Files And Symbols:**
- Inspect: `.agents/skills/lead-generation/SKILL.md`, `.agents/skills/account-research/SKILL.md`, `.agents/skills/lead-evidence/SKILL.md`, `.agents/skills/contact-verification/SKILL.md`, `scripts/import_discovery.py`, `scripts/normalize_dedupe.py`, `scripts/extract_website_evidence.py`, `scripts/select_for_enrichment.py`, `scripts/build_workbook.py`
- Modify: `scripts/harness_tools.py`, `scripts/harness.py`, the four existing skill files, and typed contracts from Task 1 where adapter payloads need explicit models
- Verify: `tests/test_harness_tools.py`

**Dependencies:**
- Tasks 1–4 typed contracts, deterministic boundaries, account-intelligence outputs, and coverage/budget semantics.

**Authority:**
- Preauthorized local actions: add thin adapters over existing functions, update existing skill instructions, and test planner action validation with mocked deterministic tool calls
- Stop for: adding a second workflow engine, embedding fixed TED/portfolio/contact order, bypassing manifest or budget checks, or creating duplicate skill hierarchies

**Steps:**
- [ ] Step 1: Implement `scripts/harness_tools.py` as thin adapters that accept typed inputs, call existing deterministic functions, validate typed outputs, and return artifact/evidence references rather than raw unbounded provider payloads.
- [ ] Step 2: Implement `scripts/harness.py:run_agent_harness(goal, planner, tools)` so the planner can request bounded actions, dispatch optional workers, inspect typed results, choose to stop, and produce an account thesis; reject unknown actions, invalid arguments, budget violations, and out-of-scope company IDs.
- [ ] Step 3: Update the existing skills to describe account selection, environment search, event discovery, verification, timeline/thesis formation, research stopping, and evidence-backed assumptions without prescribing a fixed lane sequence.
- [ ] Step 4: Add adapter tests that verify contract validation, deterministic delegation, budget use, stop decisions, and preservation of source/evidence references.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_tools -v`
- Expected: planner actions are validated and bounded; adapters reuse existing kernel functions; no adapter implements a second score, export, or orchestration path.

**Exit Criteria:**
- A parent agent can use the harness through a small typed tool surface and can decide research strategy without taking ownership of deterministic facts or publication.

### Task 6: Add a thin reference runner and real-kernel E2E proof

**Purpose:**
- Demonstrate and test the architecture end to end while keeping orchestration out of the example script.

**Task Function:**
- Exercise goal intake, parent planning, bounded worker dispatch, typed evidence, hypothesis/thesis generation, deterministic ranking, and export through the real kernel.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can integrate the harness, preserve existing fixture E2E behavior, and verify final artifacts.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate that the test mocks only external providers and proves final state, side effects, and failure propagation.

**Specification Coverage:**
- `examples/berlin_hausverwaltung.py` is a thin reference runner, not a hard-coded workflow.
- `tests/test_harness_e2e.py` validates Goal → parent agent → worker dispatch → typed evidence → hypothesis → ranking → export.
- The real deterministic validation, promotion, projection, scoring, QA, staging, and atomic publication kernel runs in the test.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`, `tests/test_end_to_end_enrichment.py`, `scripts/validate_workbook.py`, `scripts/qa_leads.py`, `scripts/validate_deliverables.py`
- Modify: `examples/berlin_hausverwaltung.py`, `tests/test_harness_e2e.py`, `tests/test_end_to_end_enrichment.py` only for compatibility coverage, and `lead-generation-architecture.json` only when final callable boundaries or authority labels changed
- Verify: `tests/test_harness_e2e.py`, `tests/test_end_to_end_enrichment.py`, `scripts/validate_workbook.py`, the full test suite, and the final manifest

**Dependencies:**
- Tasks 1–5 complete and accepted by the lead controller.
- No live provider access, email send, external publication, or credential exposure.

**Authority:**
- Preauthorized local actions: add the thin example and fixture-backed E2E test, mock external provider boundaries only, run local validators, and reconcile architecture documentation with the final callable boundaries
- Stop for: live provider calls, external writes, publication, email sending, broad fixture changes that hide kernel failures, or marking the plan complete without fresh final verification

**Steps:**
- [ ] Step 1: Implement `examples/berlin_hausverwaltung.py` as `goal = load_goal(...)`, `result = run_agent_harness(goal, planner, tools)`, and `export(result)` with no hard-coded TED → portfolio → contacts → verify → score → export sequence.
- [ ] Step 2: Build `tests/test_harness_e2e.py` with a planner that chooses bounded work based on typed results and mocked provider responses; run real identity validation, evidence promotion, account ledger/thesis projection, scoring, QA, staging, and atomic publication.
- [ ] Step 3: Assert final workbook rows, timeline/thesis lineage, manifest hashes, ranking determinism, and no final publication after a forced provider, verifier, QA, or workbook-validation failure.
- [ ] Step 4: Run the existing E2E suite and update `lead-generation-architecture.json` only if its canonical architecture facts no longer match the implemented boundaries.

**Verification:**
- [ ] `py -3 -m unittest tests.test_harness_e2e tests.test_end_to_end_enrichment -v`
- [ ] `py -3 -m unittest discover -s tests -v`
- [ ] `$workbook = (Get-Content evidence/manifests/active_run.json | ConvertFrom-Json).outputs.workbook.path; py -3 scripts/validate_workbook.py --workbook $workbook`
- [ ] `git diff --check`
- Expected: the harness E2E passes through the real deterministic kernel; external providers are mocked; workbook and manifest are valid; all existing tests pass; failure paths leave no partially published final artifact.

**Exit Criteria:**
- The architecture is demonstrated by a thin reference runner and regression-tested by a real-kernel E2E flow, with no production dependence on a fixed E2E sequence.

## Verification

Final artifact-level verification occurs only after Tasks 1–6 are complete and
the implementation is committed or otherwise reconciled to a clean reviewed
revision:

- `py -3 -m unittest discover -s tests -v`
- `py -3 -m json.tool config/research_policy.json`
- `$workbook = (Get-Content evidence/manifests/active_run.json | ConvertFrom-Json).outputs.workbook.path; py -3 scripts/validate_workbook.py --workbook $workbook`
- `py -3 scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/active_run.json`
- `git diff --check`
- `git status --short --branch`

The final workbook path must be read from the manifest rather than invented in
the plan. The validation command above resolves that path from
`evidence/manifests/active_run.json`. The verify command must cover the exact manifest, evidence hashes,
account ledger/timeline, thesis lineage, canonical projections, workbook, QA,
and publication barrier. It must fail on assurance escalation, unresolved
identity, out-of-scope negative research, invalid provider success,
unsettled budget usage, date/policy drift, ranking inconsistency, schema
errors, or partial final publication.

## Completion Criteria

The plan is ready for completion verification when:

1. The parent agent selects research strategy and bounded next actions without
   owning deterministic facts or publication.
2. Pydantic boundary contracts coexist with and defer to the existing JSON
   Schema, canonical hashes, manifest barriers, and semantic validators.
3. Source-level assurance cannot be self-declared, and replay/structural
   evidence remains visibly lower assurance.
4. Accepted companies have account-scoped coverage and stopping metadata;
   `None found` never represents an outage, partial search, or narrow global
   default.
5. Verified positive events survive partial research, event joins use
   `(company_id, event_id)`, and candidate/rejected/unresolved lineage remains
   auditable.
6. Account timelines and theses explain evidence-backed assumptions with
   supporting claims, counterevidence, gaps, confidence, and next action;
   hypotheses are not promoted facts.
7. All agent-selected work consumes the shared dispatch budget, provider
   response shapes are validated, and ranking is replay-stable under a
   manifest-bound `as_of_date` and scoring policy version.
8. The thin reference runner and real-kernel E2E test prove the typed path
   without encoding a closed lane sequence or duplicating scoring/export.
9. Existing fixture behavior, workbook validation, QA, manifest hashes, and
   atomic publication remain green.
10. No live provider spend, external publication, email sending, credential
    exposure, or unapproved dependency installation occurs.
11. `skill-verification-before-completion` returns `verified` before the plan
    status changes from `proposed` to `completed`.

## Plan Self-Review

- Spec coverage: the account-intelligence focus is covered by Tasks 3 and 4;
  the tools/subagents/Pydantic architecture is covered by Tasks 1, 2, and 5;
  thin example and E2E validation are covered by Task 6.
- Completeness scan: no unresolved owner or template token is used. The
  workbook validation command resolves its runtime path from
  `active_run.json` instead of guessing a filename.
- Cross-task consistency: `company_id`, `event_id`, `claim_id`,
  `research_run_id`, `coverage_status`, `stop_reason`, `as_of_date`, and
  `scoring_policy_version` are used consistently across contracts, ledger,
  manifest, scoring, tests, and export.
- Ownership: agents and external providers write only bounded candidate
  results; verifier boundaries decide promotion; deterministic Python writes
  canonical projections and outputs; the lead controller owns coordination
  state and accepts proof.
- Task sizing: contract/trust, callable kernel, account intelligence,
  coverage/replay, harness adapters, and E2E proof are separate vertical
  outcomes with ordered dependencies.

## Execution Record

- 2026-11-09: completed sequential GPT-5.6-Sol High and GPT-6 High reviews in
  one authenticated dedicated GitHub-review context; both agreed on the
  deterministic-kernel boundary, typed process contracts, evidence-first
  account intelligence, and thin-runner architecture.
- 2026-11-09: reviewed revision `c0b3428ccd527dd8cb55a9a7067a40d8227f168e`
  from `origin/main`; publication was `no publication required` because no
  source changes were made for the review.
- 2026-11-09: saved this proposed plan only; no implementation code, runtime
  artifacts, provider calls, or external publication were performed.



