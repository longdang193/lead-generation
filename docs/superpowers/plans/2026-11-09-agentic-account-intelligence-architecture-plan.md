---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: agentic-account-intelligence-architecture
targets:
  - requirements.txt
  - config/research_policy.json
  - scripts/typed_contracts.py
  - scripts/action_receipts.py
  - scripts/account_intelligence.py
  - scripts/harness_tools.py
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
  - agents/contact-researcher.toml
  - agents/evidence-verifier.toml
  - agents/portfolio-researcher.toml
  - agents/signal-researcher.toml
---

# Agentic Account Intelligence Architecture Plan

## Goal

Evolve the lead-generation harness into a Codex-native, evidence-first
account-intelligence system without turning the E2E runner into a closed
application or adding a repository-owned planner. The parent Codex agent must
choose which accounts need more research,
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

### Codex-native orchestration with deterministic kernel

  The repository exposes thin callable tools for discovery, normalization,
  deduplication, identity validation, evidence capture and validation, fit
  calculation, ranking, finalization, and workbook export. The parent Codex
  agent selects and sequences those tools, dispatches native subagents, decides
  when evidence is sufficient, and forms the account thesis. Repository Python
  does not implement a second planner, scheduler, retry loop, or production
  agent runtime. The reference example and E2E test exercise the typed
  boundaries; they do not become the production control plane.

### Coverage, trust, and replay safety

  Research runs record required checks, completed checks, coverage status, stop
  reason, strategy version, and shared-budget usage. Codex owns the continue /
  stop decision; policy owns mandatory checks and coverage computation.
  Provider payloads are shape validated before success is counted.
  Manifest-bound `as_of_date` and scoring policy versions make ranking
  replayable. Self-declared agent or verifier assurance cannot promote
  structural or replay evidence to source-level `Verified`.

## Consolidated Review Basis

Both sequential architecture reviews were compared against the checked-out
source at commit `57cfbcc89eede14f7598f8e0553e8fdcaf2878a4` on `main`. The
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
      boundary must be refactored so dispatch does not depend on the
      orchestrator as its validation owner.
  11. Native subagent scheduling, fan-out, retry choice, and concurrency remain
      Codex runtime responsibilities. Python may admit work, validate results,
      and settle receipts, but must not recreate the agent loop.
  12. One controller-owned `finalize_run(manifest_ref)` barrier is the only
      final-delivery path. Draft, ranking, and workbook staging are not final
      publication.
  13. Native handoff and action receipts must preserve parent/worker identity,
      company scope, contract version, artifact hashes, provenance, budget
      settlement, validation, and the stopping decision for replay and audit.
  14. Existing `run_pipeline()` remains legacy/fixture compatibility only; the
      Codex-native path must prove that it does not invoke the fixed
      signals-to-portfolio-to-contacts sequence.
  15. Existing agent profiles and skills are reconciled in place; no second
      instruction hierarchy or duplicate role taxonomy is introduced.
16. The legacy CLI cannot launch live native workers on the Codex-native path;
    compatibility execution is fixture-only or explicitly marked legacy and
    delegates terminal publication/recovery to the shared finalizer.
17. Native action receipts use stable, idempotent identities and an append-only
    persisted journal so restart/replay reconstructs action and budget history.
18. Finalization eligibility is policy-aware: strict mode requires complete
    policy coverage; personal mode may finalize a defensible partial result with
    explicit gaps, but neither mode may turn partial/unavailable research into
    `None found`.
19. At least one Codex-native acceptance probe proves the runtime handoff path;
    offline replay remains the deterministic-kernel regression suite.

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
- Next action: `branch finishing and independent PR review; no further architecture task remains in this plan`
- Blockers: `none for the implemented deterministic kernel; live-provider behavior remains deferred operational proof`
- Publication: `no publication required` for the reviewed revision; the full SHA is already reachable from `origin/main`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `lead controller` | none | typed-contract and promotion regression tests | full suite |
| Task 2 | `completed` | current | `lead controller` | Task 1 | callable-boundary and orchestration tests | full suite |
| Task 3 | `completed` | current | `lead controller` | Tasks 1–2 | account-ledger, timeline, thesis, and scoring tests | full suite |
| Task 4 | `completed` | current | `lead controller` | Tasks 1–3 | coverage, provider-shape, budget, and replay tests | full suite |
| Task 5 | `completed` | current | `lead controller` | Tasks 1–4 | harness-tool contract tests | `tests.test_harness_tools` and full suite |
| Task 6 | `completed` | current | `lead controller` | Tasks 1–5 | real-kernel E2E, workbook validation, and full suite | `tests.test_harness_e2e`, `tests.test_end_to_end_enrichment`, full suite |

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
- Shared contracts include `Goal`, evidence, verifier decisions, research attempts/runs, run context, admitted work, native handoffs, worker results, action receipts, stop decisions, finalization requests, account hypotheses/theses, and artifact references.

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
- [x] Step 1: Map each proposed Pydantic model to its existing JSON record fields and identify fields that must remain hash- or manifest-derived.
- [x] Step 2: Add `requirements.txt` bounds `pydantic>=2.12,<3` and `jsonschema>=4.25,<5`, then implement `scripts/typed_contracts.py` with `Goal`, `EvidenceClaim`, `VerifierDecision`, `ResearchAttempt`, `ResearchRun`, `RunContext`, `NativeActionRequest`, `WorkerResult`, `ActionReceipt`, `StopDecision`, `AccountHypothesis`, `AccountThesis`, `FinalizationRequest`, and `ArtifactRef`. Require stable `run_id`, `action_id`, `attempt_id`, optional `parent_action_id`, company/scope, contract/strategy/profile versions, request/result/artifact hashes, provenance, terminal validation, budget settlement, coverage delta, idempotency key, and stop/finalization linkage.
- [x] Step 3: Add `scripts/action_receipts.py` with an append-only JSONL journal under `evidence/action_receipts/<run_id>.jsonl`; make append idempotent by `action_id` + `attempt_id`, reject conflicting duplicates, and provide deterministic replay of settled budget/coverage state after restart.
- [x] Step 3: Make `decision_assurance_level()` monotonic: only a verified source-capable verifier registry entry can yield source assurance; replay and structural paths remain lower assurance regardless of payload self-declarations.
- [x] Step 4: Add focused tests for valid serialization, rejection of malformed boundaries, canonical-hash preservation, assurance-escalation regression, idempotent duplicate callbacks, conflicting receipt rejection, and restart/replay reconstruction.

**Verification:**
- [x] `py -3 -m unittest tests.test_typed_contracts tests.test_evidence_promotion tests.test_research_contract -v`
- Expected: all focused tests pass; replay/structural decisions never receive source assurance; existing JSON-Schema validation remains green.

**Exit Criteria:**
- Typed boundary models exist, serialize to compatible records, and cannot weaken evidence promotion or assurance semantics.

### Task 2: Extract deterministic boundaries without owning native scheduling

**Purpose:**
- Expose stable callable boundaries around the existing deterministic kernel and remove the dispatch-to-orchestrator validation dependency without moving native-agent orchestration into Python or changing `run_pipeline()` behavior.

**Task Function:**
- Separate admission, result validation/receipt settlement, verification/promotion, projection/ranking, and finalization into reusable kernel entry points. Native subagent scheduling remains outside the repository.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can safely refactor shared orchestration and prove backward compatibility.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate import direction, manifest authority, atomic publication, and failure propagation.

**Specification Coverage:**
- Tools perform actions; the parent Codex agent decides strategy and native subagent dispatch.
- Manifest state/barriers, capability/live-replay admission, budgets, verifier assurance, projection/scoring/ranking, QA, and publication remain deterministic authorities.
- No second planner, scheduler, workflow engine, scoring pipeline, or export pipeline is introduced.
- `finalize_run(manifest_ref)` is the only final-delivery barrier; draft and staged outputs cannot be reported as final.

**Required Skills:**
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`, `scripts/worker_dispatch.py:DispatchBudget`, `scripts/worker_dispatch.py:dispatch_native_lane`, `scripts/promote_evidence.py:promote_verified_claims`, `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/build_workbook.py`
- Modify: `scripts/run_manifest.py:prepare_run` (new boundary), `scripts/worker_dispatch.py:admit_research_action`, `scripts/worker_dispatch.py:record_worker_result`, `scripts/worker_dispatch.py:settle_action_receipt` (new neutral boundaries), `scripts/promote_evidence.py:verify_and_promote` (new boundary), `scripts/orchestrate_enrichment.py:project_and_rank` and `finalize_run` (new boundaries), plus imports and compatibility wrappers
- Verify: `tests/test_orchestration.py`, `tests/test_native_adapters.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:**
- Task 1 typed models and assurance rules.
- Existing `run_pipeline()` remains an explicitly legacy/fixture compatibility path; it is not the Codex-native production entry point.

**Authority:**
- Preauthorized local actions: refactor internal imports, add callable wrappers, preserve CLI entry points, and add failure-path tests for manifest, dispatch, promotion, and atomic publication
- Stop for: deleting or renaming an existing CLI contract, introducing a second state machine, changing manifest authority, or changing publication behavior without a migration test and user approval

**Steps:**
- [x] Step 1: Extract `prepare_run`, `admit_research_action`, `record_worker_result`, `settle_action_receipt`, `verify_and_promote`, `project_and_rank`, and `finalize_run` as thin functions over existing logic, with typed inputs/outputs at their boundaries.
- [x] Step 2: Move lane-output validation ownership out of `orchestrate_enrichment.py` so `worker_dispatch.py` depends on a neutral contract/validation module rather than importing its caller; retain `dispatch_native_lane` only as an explicitly legacy/fixture compatibility path.
- [x] Step 3: Keep `run_pipeline()` only for fixture/legacy compatibility; fail closed when the normal CLI requests non-fixture live execution without an explicit legacy opt-in, and require both legacy publication and `recover_publication()` to delegate to `finalize_run(manifest_ref)` so no second publication authority remains.
- [x] Step 4: Add tests for direct callable use, invalid admission, budget exhaustion, receipt settlement, promotion failure, projection failure, QA failure, publication rollback/idempotency, rejection of live legacy CLI execution, shared finalizer use by recovery, and the absence of a native-path call to `run_pipeline()`.

**Verification:**
- [x] `py -3 -m unittest tests.test_orchestration tests.test_native_adapters tests.test_end_to_end_enrichment -v`
- Expected: existing fixture pipeline behavior is unchanged; direct boundaries are callable; failures stop before publication and leave no partial final output.

**Exit Criteria:**
- The deterministic kernel is reusable through explicit boundaries; native Codex orchestration owns scheduling, while the original pipeline remains a legacy compatibility wrapper rather than the control surface.

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
- Codex authors account hypotheses and theses; Python validates company scope, claim IDs, dates, confidence, provenance, counterevidence, gaps, and persistence. They do not become verified facts or deterministic fact-score inputs by authorship or persistence alone.

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
- [x] Step 1: Implement deterministic event-ledger and timeline helpers in `scripts/account_intelligence.py` using the Task 1 boundary models; accept Codex-authored `AccountHypothesis` and `AccountThesis` payloads only through validation functions, with deterministic joins on `(company_id, event_id)`.
- [x] Step 2: Record the search environment, candidate discovery result, verification decision, rejection or unresolved reason, supporting claim IDs, and event date/source scope for every event considered.
- [x] Step 3: Project an account timeline from verified claims and validate/persist the Codex-authored thesis separately; include counterevidence and research gaps, and keep direct intent nullable when no direct signal is verified.
- [x] Step 4: Update signal derivation so verified positives survive partial or unavailable lanes and so hypotheses influence recommended action only through explicit, tested policy fields rather than fact score inputs.
- [x] Step 5: Add a canonical workbook sheet or linked account-ledger artifact with stable IDs and source references, preserving existing workbook consumers.

**Verification:**
- [x] `py -3 -m unittest tests.test_account_intelligence tests.test_buying_signals tests.test_scoring tests.test_end_to_end_enrichment -v`
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
- Agent-selected work consumes the same `DispatchBudget` through admission and settlement receipts and cannot bypass capability or manifest admission; Python does not schedule or retry native subagents.
- Required checks, completed checks, coverage status, stop reason, strategy version, `as_of_date`, and scoring policy version are persisted.
- Research termination, coverage completeness, `None found` eligibility, and finalization eligibility are separate states. Agent-supplied `required_checks` cannot shrink policy-required checks.
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
- [x] Step 1: Extend research policy and manifest records with `strategy_version`, `required_checks`, `completed_checks`, `coverage_status`, `stop_reason`, `as_of_date`, and `scoring_policy_version`.
- [x] Step 2: Make `none_found_allowed()` inspect account scope, required/completed checks, provider status, truncation, and verified claims before allowing the negative state.
- [x] Step 3: Validate TED, Overpass, Apify, and Hunter response shapes before recording an attempt as successful; distinguish unavailable, partial, empty, and completed-zero outcomes.
- [x] Step 4: Make `DispatchBudget` the single admission/settlement path for parent-selected tools and native-worker handoffs, including retries and failed attempts represented by durable receipts; do not add Python scheduling, fan-out, or retry policy.
- [x] Step 5: Replace implicit `date.today()` ranking inputs with manifest-bound `as_of_date` and persist the policy version used for classification and tie-breaking.
- [x] Step 6: Add tests for narrow-search false negatives, provider HTML/error payloads, budget exhaustion, retry accounting, partial research, policy-aware strict/personal finalization eligibility, and repeated replay with reordered worker completion.

**Verification:**
- [x] `py -3 -m unittest tests.test_research_contract tests.test_provider_clients tests.test_native_adapters tests.test_scoring tests.test_orchestration -v`
- Expected: malformed providers cannot create successful research runs; partial/outage states cannot become `None found`; every admitted action settles against the shared budget; identical manifest inputs produce identical scores and ranks.

**Exit Criteria:**
- Research status, stopping, budget, provider, coverage, finalization eligibility, and date semantics are explicit and enforced before evidence, ranking, or finalization can claim completeness; native handoffs are replay-auditable without rerunning LLM reasoning or live providers.

### Task 5: Expose bounded tool contracts and reconcile skills/profiles

**Purpose:**
- Give the parent Codex agent a small, typed tool surface while keeping procedure in skills, strategy and native-subagent orchestration in Codex, and facts/publication in the deterministic kernel.

**Task Function:**
- Adapt existing deterministic functions into validated tool calls and document how the parent agent selects, dispatches, verifies, and stops work without adding a repository planner or runtime.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can design a minimal reusable adapter surface and reconcile existing skill instructions.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate that adapters do not encode lane order, duplicate scoring/export logic, or bypass contracts.

**Specification Coverage:**
- Skills decide procedure; agents decide strategy; tools perform actions; Pydantic enforces contracts; deterministic functions calculate facts.
- The tool facade exposes `discover_companies`, `normalize_company`, `deduplicate`, `validate_identity`, `capture_evidence`, `validate_evidence`, `calculate_fit`, and draft `rank_leads`; final workbook delivery is available only through `finalize_run`, which invokes `export_workbook` after every barrier passes.
- Existing skills are extended rather than duplicated.
- The parent agent invokes the facade through one documented JSON request/response boundary: validated action name and Pydantic payload on stdin, one typed artifact/result response on stdout, nonzero exit with structured error on rejection, and no direct module import or hidden planner state.

**Required Skills:**
- `skill-code-standards`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `.agents/skills/lead-generation/SKILL.md`, `.agents/skills/account-research/SKILL.md`, `.agents/skills/lead-evidence/SKILL.md`, `.agents/skills/contact-verification/SKILL.md`, `agents/contact-researcher.toml`, `agents/evidence-verifier.toml`, `agents/portfolio-researcher.toml`, `agents/signal-researcher.toml`, `scripts/import_discovery.py`, `scripts/normalize_dedupe.py`, `scripts/extract_website_evidence.py`, `scripts/select_for_enrichment.py`, `scripts/build_workbook.py`
- Modify: `scripts/harness_tools.py`, the four existing skill files, the four existing agent profiles, and typed contracts from Task 1 where adapter payloads need explicit models
- Verify: `tests/test_harness_tools.py`

**Dependencies:**
- Tasks 1–4 typed contracts, deterministic boundaries, account-intelligence outputs, and coverage/budget semantics.

**Authority:**
- Preauthorized local actions: add thin adapters over existing functions, update existing skill/profile instructions, and test typed action validation with mocked deterministic tool calls
- Stop for: adding a second workflow engine, embedding fixed TED/portfolio/contact order, bypassing manifest or budget checks, or creating duplicate skill hierarchies

**Steps:**
- [x] Step 1: Implement `scripts/harness_tools.py` as thin adapters that accept typed inputs, call existing deterministic functions, validate typed outputs, and return artifact/evidence references rather than raw unbounded provider payloads.
- [x] Step 2: Do not implement `run_agent_harness`, a planner loop, a scheduler, or subprocess/native-agent execution in Python. Define only the tool-call contracts the parent Codex agent can invoke through a JSON stdin/stdout CLI, including action admission, worker-result recording, receipt settlement, thesis validation, draft ranking, and a `finalize_run` handoff; prevent direct export from being treated as final.
- [x] Step 3: Update the existing skills and four agent profiles to describe account selection, environment search, event discovery, verification, timeline/thesis formation, research stopping, and evidence-backed assumptions without prescribing a fixed lane sequence; add drift checks between role contracts and skill instructions.
- [x] Step 4: Add adapter tests that verify contract validation, deterministic delegation, budget use, stop-decision recording, preservation of source/evidence references, and rejection of fixed-sequence orchestration.

**Verification:**
- [x] `py -3 -m unittest tests.test_harness_tools -v`
- Expected: tool actions are validated and bounded; adapters reuse existing kernel functions; no adapter implements a second planner, score, export, or orchestration path.

**Exit Criteria:**
- A parent Codex agent can use a small typed tool surface and native subagents can return auditable results, while Python owns deterministic facts, validation, projection, ranking, and publication barriers without a duplicate runtime.

### Task 6: Add a thin reference example and native-handoff E2E proof

**Purpose:**
- Demonstrate and test the architecture end to end while keeping parent-agent orchestration and native subagent scheduling out of repository Python.

**Task Function:**
- Exercise goal intake, recorded native handoffs, typed evidence, Codex-authored hypothesis/thesis validation, deterministic ranking, finalization, and export through the real kernel.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: resolve the lowest profile that can integrate the harness, preserve existing fixture E2E behavior, and verify final artifacts.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate that the test mocks only external providers and proves final state, side effects, and failure propagation.

**Specification Coverage:**
- `examples/berlin_hausverwaltung.py` is a thin reference example that loads a goal and describes/invokes the approved typed tool surface; it is not a hard-coded workflow or production runner.
- `tests/test_harness_e2e.py` replays recorded native-agent handoffs and validates Goal → typed handoff → typed evidence → thesis validation → ranking → policy-aware finalization → export.
- The real deterministic validation, promotion, projection, scoring, QA, staging, and atomic publication kernel runs in the test.
- At least two valid action traces and an early-stop trace are covered; no trace is required to use TED → portfolio → contacts order.
- A separate Codex-native acceptance probe invokes the JSON tool boundary with one real native handoff, mocked/disabled providers, and asserts role discovery, scope propagation, receipt persistence, and finalizer admission without calling `run_pipeline()`.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`, `scripts/orchestrate_enrichment.py:finalize_run`, `tests/test_end_to_end_enrichment.py`, `scripts/validate_workbook.py`, `scripts/qa_leads.py`, `scripts/validate_deliverables.py`
- Modify: `examples/berlin_hausverwaltung.py`, `tests/test_harness_e2e.py`, `tests/test_end_to_end_enrichment.py` only for compatibility coverage, and typed handoff fixtures under `tests/fixtures/` if needed; do not add an untracked architecture registry as a second source of truth
- Verify: `tests/test_harness_e2e.py`, `tests/test_end_to_end_enrichment.py`, `scripts/validate_workbook.py`, the full test suite, and the final manifest

**Dependencies:**
- Tasks 1–5 complete and accepted by the lead controller.
- No live provider access, email send, external publication, or credential exposure.

**Authority:**
- Preauthorized local actions: add the thin example and fixture-backed E2E test, mock external provider boundaries only, run local validators, and reconcile architecture documentation with the final callable boundaries
- Stop for: live provider calls, external writes, publication, email sending, broad fixture changes that hide kernel failures, or marking the plan complete without fresh final verification

**Steps:**
- [x] Step 1: Implement `examples/berlin_hausverwaltung.py` as a thin goal loader plus typed handoff/finalization example; it must not import or call `run_agent_harness`, `run_pipeline()`, a planner loop, or a fixed lane sequence.
- [x] Step 2: Build `tests/test_harness_e2e.py` from recorded typed native-agent handoff fixtures and mocked provider responses; run real identity validation, evidence promotion, account ledger/timeline projection, thesis validation, scoring, policy-aware QA, staging, and atomic finalization. Persist the generated manifest under `evidence/manifests/native_handoff_<run_id>.json` and expose that exact path to final verification.
- [x] Step 3: Replay at least two different valid action traces plus early stop; assert final workbook rows, timeline/thesis lineage, manifest hashes, receipt settlement, ranking determinism, and no final publication after forced provider, verifier, QA, or workbook-validation failure.
- [x] Step 4: Run the existing E2E suite and add a separate Codex-native acceptance probe proving role discovery, JSON tool invocation, one native handoff, receipt settlement, and finalization without invoking `run_pipeline()` or automatically executing signals → portfolio → contacts.

**Verification:**
- [x] `py -3 -m unittest tests.test_harness_e2e tests.test_end_to_end_enrichment -v`
- [x] `py -3 -m unittest discover -s tests -v`
- [ ] `$manifest = Get-ChildItem evidence/manifests/native_handoff_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1; $workbook = (Get-Content $manifest.FullName | ConvertFrom-Json).outputs.workbook.path; py -3 scripts/validate_workbook.py --workbook $workbook`
- [x] `git diff --check`
- Expected: the harness E2E passes through the real deterministic kernel; external providers are mocked; workbook and manifest are valid; all existing tests pass; failure paths leave no partially published final artifact.

**Exit Criteria:**
- The architecture is demonstrated by a thin reference example and regression-tested by real-kernel native-handoff E2E flows, with no Python planner/runtime and no production dependence on a fixed E2E sequence.

## Verification

Final artifact-level verification occurs only after Tasks 1–6 are complete and
the implementation is committed or otherwise reconciled to a clean reviewed
revision:

- `py -3 -m unittest discover -s tests -v`
- `py -3 -m json.tool config/research_policy.json`
- `$manifest = Get-ChildItem evidence/manifests/native_handoff_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1; $workbook = (Get-Content $manifest.FullName | ConvertFrom-Json).outputs.workbook.path; py -3 scripts/validate_workbook.py --workbook $workbook`
- `py -3 scripts/orchestrate_enrichment.py verify --manifest $manifest.FullName`
- `git diff --check`
- `git status --short --branch`

The final workbook path must be read from the exact generated native-handoff
manifest rather than invented in the plan. The validation command above
resolves that path from the newest `evidence/manifests/native_handoff_*.json`.
The verify command must cover the exact manifest, evidence hashes,
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
   manifest-bound `as_of_date` and scoring policy version; stopping, coverage,
   `None found`, and finalization eligibility remain distinct.
8. The thin reference example and native-handoff E2E tests prove the typed path
   without encoding a closed lane sequence, Python planner/runtime, or
   duplicated scoring/export.
9. Existing fixture behavior, workbook validation, QA, manifest hashes, and
   atomic publication remain green.
10. Every final workbook is produced through `finalize_run(manifest_ref)`;
    draft ranking or direct export cannot bypass coverage, evidence, budget,
    QA, manifest, or atomic-publication barriers.
11. Legacy CLI execution cannot launch live workers without explicit legacy
    opt-in, and legacy publication/recovery use the shared finalizer.
12. The receipt journal is append-only, idempotent, restart-replayable, and
    binds every native handoff to budget, coverage, validation, and finalization.
13. A Codex-native acceptance probe proves the parent runtime can invoke the
    typed tool boundary and complete one handoff without the legacy pipeline.
14. No live provider spend, external publication, email sending, credential
    exposure, or unapproved dependency installation occurs.
15. `skill-verification-before-completion` returns `verified` before the plan
    status changes from `proposed` to `completed`.

## Plan Self-Review

- Spec coverage: the account-intelligence focus is covered by Tasks 3 and 4;
  the tools/native-subagents/Pydantic architecture is covered by Tasks 1, 2,
  and 5; thin example and native-handoff E2E validation are covered by Task 6.
- Completeness scan: no unresolved owner or template token is used. The
  workbook validation command resolves its runtime path from the generated
  native-handoff manifest instead of guessing a filename or using a legacy run.
- Cross-task consistency: `company_id`, `event_id`, `claim_id`,
  `research_run_id`, `coverage_status`, `stop_reason`, `as_of_date`, and
  `scoring_policy_version` are used consistently across contracts, ledger,
  manifest, scoring, tests, and export.
- Ownership: Codex owns strategy, native subagent dispatch, continue/stop
  decisions, and thesis authorship; agents and external providers write only
  bounded candidate results; verifier boundaries decide promotion;
  deterministic Python validates handoffs, writes canonical projections and
  outputs, and owns finalization; the lead controller owns coordination state
  and accepts proof.
- Architecture gate: no `run_agent_harness`, Python planner loop, Python native
  scheduler, or fixed signal/portfolio/contact sequence remains in the
  Codex-native path; `run_pipeline()` is legacy/fixture compatibility only.
- Finalization gate: `finalize_run(manifest_ref)` is the sole final-delivery
  path and applies policy-aware eligibility: strict rejects incomplete policy
  coverage, personal may accept documented partial coverage, and both reject
  unsettled receipts, invalid lineage, QA failures, manifest drift, or partial
  publication.
- Task sizing: contract/trust, callable kernel, account intelligence,
  coverage/replay, harness adapters, and E2E proof are separate vertical
  outcomes with ordered dependencies.

## Review Hardening

- Publication and crash recovery must share one mandatory, manifest-bound
  finalization gate; native publication cannot replace staged bytes when policy,
  barriers, coverage, delivery, or identity checks fail.
- The recovery marker must carry terminal status, delivery policy, registry
  updates, and barrier updates so replay settles the same durable state as the
  original publication attempt.
- Promoted evidence envelopes must adapt into the typed claim contract without
  dropping research, candidate-hash, verification, or verifier-run lineage.
- Account theses must reject foreign-company claims and hypotheses, and fact
  scoring must ignore rejected/negative/unknown claims while reusing canonical
  lead-fit semantics.
- Strict finalization must reject missing or malformed delivery evidence and
  validate policy, target count, delivered count, and shortfall consistency.
- Receipt contracts must round-trip JSON with an omitted artifact hash.
- Regression coverage must prove each item above through the native tool,
  recovery, promotion, account-intelligence, scoring, and full harness paths.

## Execution Record

- 2026-11-09: completed sequential `GPT-5.6-Sol` High and `GPT-6` High reviews
  in one authenticated, repository-bound GitHub-review context. Both returned
  `FAIL` with actionable architectural changes; no retry, resubmission, model
  switch, or effort downgrade occurred.
- 2026-11-09: reviewed revision `57cfbcc89eede14f7598f8e0553e8fdcaf2878a4`
  on `origin/main`; publication was `no publication required` for the reviewed
  source revision, and the full SHA was reachable from GitHub.
- 2026-11-09: `GPT-5.6-Sol` High — run `run-J185eH`, chat
  `https://chatgpt.com/c/6af1c953-de2c-83eb-999f-ebd1e02d461b`, response
  `C:\tmp\github-review-longdang193-lead-generation-57cfbcc-codex-native-direction-review-20261109\run-J185eH\response.md`, bounded result `completed`, visible response final/actionable and pinned to the reviewed SHA.
- 2026-11-09: `GPT-6` High — run `run-ObS9mB`, chat
  `https://chatgpt.com/c/6af1c9da-e3f8-83eb-ba0c-d4d2d63ccd8d`, response
  `C:\tmp\github-review-longdang193-lead-generation-57cfbcc-codex-native-direction-review-20261109\run-ObS9mB\response.md`, bounded result `completed`, visible response final/actionable and pinned to the reviewed SHA.
- 2026-11-09: completed the follow-up sequential `GPT-5.6-Sol` High and `GPT-6` High review of commit `86ae2aa763734605b23005e60b00ed930138c7ad`; both remained `FAIL` and independently validated the legacy-runtime, durable-receipt, policy-aware-finalization, and native-acceptance gaps. The follow-up response artifacts remain under `C:\tmp\github-review-longdang193-lead-generation-86ae2aa-plan-verdict-review-20261109`.
- 2026-11-09: patched the plan before execution to make those justified blockers executable acceptance conditions, then implemented the deterministic kernel and native facade without adding a planner, scheduler, fixed lane sequence, or replacement runtime.
- 2026-11-09: review cycle 1 of PR `#13` reproduced seven issues; patched the
  publication/recovery gate, promoted-envelope adapter, account scope checks,
  canonical fit scoring, strict delivery validation, terminal-state persistence,
  receipt round-trip, and regression tests. Full suite: `161` tests passed.
- 2026-11-09: final review cycle 2 reproduced six additional edge cases;
  patched manifest-bound artifact hashes, complete promoted portfolio/contact
  fields, wrapped claim-value normalization, exact account scope parsing,
  strict integer delivery counts, terminal publication status validation, and
  added targeted regression coverage. Two review cycles are complete; no third
  review was run.
- 2026-11-09: focused adapter proof passed (`19` tests), and the full repository
  suite passed (`176` tests) on the reconciled workspace. The fixture E2E path
  creates and validates real workbook artifacts; live external providers and
  CRM writes were not exercised and remain deferred operational proof.
- 2026-11-09: independent PR review cycle 1 at head `6cac7f03c9315343e8113f24d8043152467e63f0` found six source-supported lifecycle/finalization/corroboration gaps. Those gaps were patched with regression tests; the post-fix focused suite passed `41` tests and the full suite passed `181` tests. Review cycle 2 is pending on the new head.
- 2026-11-09: architecture plan reconciled to `completed`; branch finishing,
  push, PR review, and merge remain separate Git operations.
