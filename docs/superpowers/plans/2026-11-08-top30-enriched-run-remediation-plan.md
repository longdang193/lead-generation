---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
contract_version: "1"
name: top30-enriched-run-remediation
targets:
  - scripts/orchestrate_enrichment.py
  - scripts/promote_evidence.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/select_for_enrichment.py
  - scripts/qa_leads.py
  - scripts/build_workbook.py
  - scripts/validate_deliverables.py
  - scripts/validate_workbook.py
  - tests/test_orchestration.py
  - tests/test_evidence_promotion.py
  - tests/test_canonical_projection.py
  - tests/test_end_to_end_enrichment.py
  - evidence/manifests/
  - data/processed/
  - output/
---

# Top-30 Enriched Run Remediation Plan

## Goal

Make one manifest-bound enriched run executable and fail-closed for the
provisional top 30 Berlin Hausverwaltung leads:

`queue -> native sub-agents -> verifier -> promotion -> canonical projection -> reranking -> readiness QA -> regenerated workbook`

The run must use only accepted shortlist companies, preserve one run identity
and Git revision through every stage, apply only verifier-approved evidence to
canonical data, produce deterministic post-enrichment ranking, and publish the
workbook only after semantic QA succeeds.

This plan consolidates the two independent reviews at commit
`bd4d236828fbd54b0d513d635b601a469fe01e50`. Consensus findings were retained
only when the visible review responses agreed and the pinned source confirmed
the behavior:

- `scripts/orchestrate_enrichment.py` has no integrated run command or worker
  dispatch path.
- Native worker completion and verifier handoff barriers are absent.
- Promoted evidence has no canonical projection edge into scoring, contacts,
  or buying-signal ranking.
- Workbook generation can replace the controller manifest, breaking lineage.
- Queue reconciliation accepts incomplete lane output.
- Final verification does not run the required semantic validators.
- Existing tests do not prove a manifest-bound top-30 end-to-end run.

The reviews also identified source-confirmed hardening required for the same
acceptance goal: active-run binding at promotion, accepted-identity and
verified-provenance enforcement in scoring, repository-root manifest path
resolution, and rejection of missing or stale workbook inputs.

## Implementation Outcomes

### Integrated controller-owned run

`orchestrate_enrichment.py` exposes one `run`/`resume` path that creates or
loads `evidence/manifests/active_run.json`, admits only the manifest-hashed
provisional shortlist, dispatches bounded native research lanes, reconciles
every queued company, dispatches the verifier only after research completion,
promotes verified evidence, projects canonical inputs, reranks, runs readiness
QA, and builds the workbook. Every phase records status, inputs, outputs, and
hashes in the same manifest.

### Single-source evidence and ranking lineage

`promote_evidence.py` requires the active run and verifies accepted-company
membership, research-run linkage, trusted-source policy, claim-specific
provenance, verifier authorization, and candidate hashes. A new
`scripts/canonical_projection.py` converts only promoted claims into the
canonical qualification, event/link, signal, and contact surfaces consumed by
scoring and workbook generation.

### Fail-closed readiness and artifact generation

Queue admission, lane reconciliation, final QA, manifest validation, and
workbook generation reject missing, stale, cross-run, unresolved, or
incomplete inputs. The workbook is built to a staging path and moved into the
manifest-recorded output only after readiness QA and deliverable validation
pass.

### Regression proof and accepted deliverable

Tests execute the real controller command against a fixture with 30 accepted
companies, mocked native workers, verifier decisions, positive and negative
research outcomes, canonical projection, reranking, QA, and workbook
validation. The fixture also proves failure on missing workers, missing
decisions, cross-run evidence, hash drift, stale inputs, and manifest lineage
breaks.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the listed source, test, plan, and generated-surface files; run repository-local Python, JSON, hash, workbook, and Git read-only verification commands
- User-approval actions: commit, push, pull-request creation, merge, provider authentication, external enrichment spend, email sending, destructive cleanup, and publication of lead data
- Parallel ownership: `none`; manifest, controller, projection, scoring, QA, and generated outputs share one ordered state machine
- Sequential fallback: execute Tasks 1–7 in dependency order in the current workspace

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/buying-signal-attribution`
- Base commit: `bd4d236828fbd54b0d513d635b601a469fe01e50`
- Expected workspace: preserve untracked `lead-generation-architecture.json` and `output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx`; do not treat either as implementation input until manifest-bound
- Next action: complete Task 1 by defining the shared run-manifest contract and repository-root path resolution
- Blockers: none

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | manifest and path-resolution regression tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | controller dispatch and barrier tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 1 | promotion and canonical-projection tests | pending |
| Task 4 | `pending` | current | `unresolved` | Task 3 | deterministic post-projection scoring tests | pending |
| Task 5 | `pending` | current | `unresolved` | Tasks 2–4 | semantic QA and workbook input-gate tests | pending |
| Task 6 | `pending` | current | `unresolved` | Tasks 1–5 | fixture-backed controller E2E test | pending |
| Task 7 | `pending` | current | `unresolved` | Task 6 | fresh top-30 run and final verification evidence | pending |

## Task Breakdown

### Task 1: Establish one authoritative run-manifest contract

**Purpose:**
- Make `evidence/manifests/active_run.json` the single source of run identity, revision, barriers, queue membership, evidence lineage, inputs, outputs, and hashes.

**Task Function:**
- Normalize manifest creation, updates, and repository-relative path resolution.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from reasoning depth, scope, risk, and cost before activation.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate manifest compatibility and hash behavior.

**Specification Coverage:**
- One immutable `run_id`, `head_sha`, `git_revision`, configuration version, and phase barrier state across all stages.
- Repository-root resolution for manifests nested under `evidence/manifests/`.
- No downstream stage may mint a replacement run identity.
- The manifest contains exact `research_runs`, `verifier_runs`, `source_policy`, and `projection` registries. Each registry entry records the company ID, lane or claim scope, status, input/output paths, hashes, producer, and terminal timestamp.
- The `projection` registry names the exact canonical output keys and repository-relative paths for qualification, events/links, buying signals, contacts, scores, shortlist, QA, and workbook artifacts; every downstream CLI receives those paths from the manifest rather than reconstructing them.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:create_run_manifest`, `scripts/orchestrate_enrichment.py:verify_manifest`
- Inspect: `scripts/validate_deliverables.py:resolve_manifest_path`, `scripts/validate_deliverables.py:verify_manifest_bucket`
- Inspect: `scripts/qa_leads.py:main`
- Modify: `scripts/orchestrate_enrichment.py:create_run_manifest`, manifest update helpers, `verify_manifest`
- Modify: `scripts/validate_deliverables.py:resolve_manifest_path`
- Modify: `scripts/qa_leads.py:main` and manifest checks
- Modify: `scripts/build_workbook.py:main` so supplied manifests are updated, never replaced
- Verify: `tests/test_orchestration.py`, `tests/test_artifact_manifest_side_effects.py`

**Dependencies:**
- Existing manifest fields and the current workbook/QA consumers are the compatibility baseline.

**Authority:**
- Preauthorized local actions: edit manifest helpers and focused tests; run local unit tests and hash checks
- Stop for: changing the public lead schema, introducing a second manifest registry, or requiring external credentials

**Steps:**
- [ ] Step 1: Define required manifest fields for `run_id`, `head_sha`, `git_revision`, `config_version`, `status`, `barriers`, `queues`, `inputs`, `supporting_inputs`, and `outputs`.
- [ ] Step 2: Add one atomic manifest-update helper that preserves existing identity, queues, barriers, and evidence references while registering new files.
- [ ] Step 3: Resolve repository-relative paths from the repository root, including manifests at `evidence/manifests/active_run.json`.
- [ ] Step 4: Change workbook and QA manifest handling to update the active manifest rather than overwrite it.
- [ ] Step 5: Add and validate the `research_runs`, `verifier_runs`, `source_policy`, and `projection` registries, including exact output key/path/format and CLI-argument records.

**Verification:**
- [ ] `py -3 -m unittest tests.test_orchestration tests.test_artifact_manifest_side_effects -v`
- Expected: nested-manifest paths resolve to repository files; workbook generation preserves the original `run_id` and `head_sha`; hash drift fails.

**Exit Criteria:**
- Every manifest consumer accepts the same schema, preserves one run identity, and resolves all recorded paths against the repository root.

### Task 2: Connect queue admission, native workers, and completion barriers

**Purpose:**
- Turn the declarative worker profiles into a controller-owned, bounded execution path with fail-closed reconciliation.

**Task Function:**
- Implement phase transitions and native worker dispatch for signal, portfolio, contact, and verifier lanes.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from execution scope, ambiguity, risk, and cost before activation.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate queue scope and completion barriers.

**Specification Coverage:**
- Only accepted, eligible, manifest-hashed provisional-shortlist companies enter queues.
- Each queued company has exactly one terminal lane outcome before verifier dispatch.
- Missing output, duplicate output, wrong run, wrong lane, or out-of-scope output blocks the run.
- The verifier starts only after every required research lane reaches a valid terminal state.
- `scripts/orchestrate_enrichment.py:main` (or a named `run_pipeline` helper called by it) owns the complete ordered sequence after queue reconciliation: verifier dispatch, promotion, canonical projection, reranking, readiness QA, workbook staging, validator invocation, and final manifest publication.
- The production native executor contract is explicit: executable/API, selected role/profile, serialized arguments, bounded concurrency, per-item timeout, cancellation behavior, exit-status capture, retry budget, and mapping of every worker result to `succeeded`, `failed`, `cancelled`, or `timed_out` terminal states. Worker output is limited to the assigned candidate-evidence directory and must satisfy the recorded JSONL schema.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:write_lane_queue`, `scripts/orchestrate_enrichment.py:validate_lane_output`, `scripts/orchestrate_enrichment.py:main`
- Inspect: `scripts/select_for_enrichment.py:eligible_for_enrichment`, `scripts/select_for_enrichment.py:select_accounts`
- Inspect: `agents/signal-researcher.toml`, `agents/portfolio-researcher.toml`, `agents/contact-researcher.toml`, `agents/evidence-verifier.toml`
- Modify: `scripts/orchestrate_enrichment.py:write_lane_queue`, `validate_lane_output`, `main`
- Add: `scripts/worker_dispatch.py:dispatch_native_lane`, `reconcile_lane_outputs`
- Verify: `tests/test_orchestration.py`

**Dependencies:**
- Task 1 manifest contract.

**Authority:**
- Preauthorized local actions: add the controller and worker-dispatch adapter, use fixture workers in tests, and run local boundary tests
- Stop for: provider authentication, external spend, email sending, or any worker write outside candidate evidence directories

**Steps:**
- [ ] Step 1: Require the accepted-company artifact, qualification artifact, and manifest-hashed provisional shortlist when writing queues; reject untrusted domain fallback and synthesized Berlin location.
- [ ] Step 2: Add `dispatch_native_lane` with bounded concurrency, explicit role/profile selection, queue-item scope, output directory, and run ID.
- [ ] Step 3: Add a fixture executor seam for tests and a production native executor seam that records worker exit status, output hash, attempts, and terminal state.
- [ ] Step 4: Make `validate_lane_output` require exact queue coverage, then record research barriers before dispatching the verifier.
- [ ] Step 5: Add a controller `run`/`resume` command and named `run_pipeline` path that invokes queue, worker, verifier, promotion, canonical projection, reranking, readiness QA, workbook staging, semantic validators, and final manifest publication in order.
- [ ] Step 6: Document and implement the native executor adapter contract, including role/profile selection, serialized CLI/API arguments, timeout/cancellation, retry limits, terminal-state mapping, and output-schema enforcement; keep the fixture executor behind the same interface.

**Verification:**
- [ ] `py -3 -m unittest tests.test_orchestration -v`
- Expected: a missing worker result, wrong company, duplicate result, wrong run, or verifier-before-research attempt exits nonzero; a complete fixture lane reaches the verifier barrier.

**Exit Criteria:**
- The controller can execute and reconcile all required worker lanes for a 30-company fixture without accepting incomplete or out-of-scope output.

### Task 3: Enforce active-run promotion and add canonical projection

**Purpose:**
- Ensure verified evidence is the only source allowed to update canonical lead facts.

**Task Function:**
- Bind promotion to the active run and project approved claims into deterministic canonical inputs.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from data-integrity risk and implementation scope.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate claim scope, policy, and projection determinism.

**Specification Coverage:**
- Candidate claims, research runs, verifier decisions, accepted companies, trusted domains, and source policy belong to the active run.
- Projection preserves claim-level URL, excerpt, retrieval date, unit, scope, as-of date, contact ownership, and verifier provenance.
- Unverified, stale, cross-run, unsupported, or out-of-scope claims never reach canonical CSVs.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/promote_evidence.py:validate_verifier_decision`, `scripts/promote_evidence.py:promote_verified_claims`
- Inspect: `scripts/lead_contract.py:verifier_decision_valid`, `scripts/lead_contract.py:candidate_sha256`
- Inspect: `config/research_evidence_schema.json`
- Modify: `scripts/promote_evidence.py:promote_verified_claims`, CLI arguments, manifest registration
- Add: `scripts/canonical_projection.py:project_verified_evidence`
- Add: `tests/test_canonical_projection.py`

**Dependencies:**
- Task 1 manifest contract; Task 2 research and verifier barriers.

**Authority:**
- Preauthorized local actions: strengthen validation, add the projection module, and run fixture-based evidence tests
- Stop for: schema changes that require migrating existing consumers or any publication of personal contact data

**Steps:**
- [ ] Step 1: Make `--run-manifest` mandatory for production promotion and validate manifest membership for every candidate, decision, research run, verifier run, company ID, and source domain.
- [ ] Step 2: Enforce claim-specific freshness and evidence requirements, including portfolio unit/scope/as-of metadata and person/email ownership agreement.
- [ ] Step 3: Implement `project_verified_evidence` to merge only `Verified` claims into canonical qualification, event/link, buying-signal, and contact inputs while preserving existing fields when no verified claim exists.
- [ ] Step 4: Register projection inputs and outputs in the same manifest and reject duplicate or conflicting claims deterministically.

**Verification:**
- [ ] `py -3 -m unittest tests.test_evidence_promotion tests.test_canonical_projection -v`
- Expected: cross-run, unaccepted-company, untrusted-source, stale, conflicting, and incomplete claims fail; approved claims project reproducibly with identical bytes regardless of input order.

**Exit Criteria:**
- Promoted evidence has one deterministic, manifest-bound path into canonical data, and no scoring consumer reads candidate or unverified evidence directly.

### Task 4: Rerank only projected canonical data

**Purpose:**
- Make post-enrichment scoring and provisional top-30 selection deterministic, accepted-identity-only, and independent of worker completion order.

**Task Function:**
- Reconcile projected qualification, signal, portfolio, and contact inputs before scoring and ranking.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from deterministic-data and business-rule scope.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate score inputs and stable ordering.

**Specification Coverage:**
- Scoring consumes projected canonical artifacts only.
- `resolution_status == Accepted` and explicit eligibility are required for qualification and priority outputs.
- Portfolio contributions require verified unit, scope, as-of date, and claim provenance.
- Stable tie-breaking remains deterministic and contact availability does not alter structural fit or shortlist membership.
- Post-enrichment reranking is restricted to the exact company IDs recorded in the manifest-bound provisional top-30 shortlist; rows outside that set are rejected or excluded before scoring, even if they are otherwise eligible.

**Required Skills:**
- `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/score_leads.py:value`, `scripts/score_leads.py:derive_account_signal`, `scripts/score_leads.py:main`
- Inspect: `scripts/select_for_enrichment.py:select_accounts`
- Modify: `scripts/score_leads.py:main`, `value`, `derive_account_signal`
- Modify: `scripts/select_for_enrichment.py:select_accounts` and audit output
- Verify: `tests/test_scoring.py`, `tests/test_selection.py`

**Dependencies:**
- Task 3 canonical projection.

**Authority:**
- Preauthorized local actions: update scoring and selection consumers and add deterministic ordering tests
- Stop for: changing approved structural weights or introducing contact-dependent shortlist criteria

**Steps:**
- [ ] Step 1: Replace direct pre-enrichment inputs with manifest-recorded projection outputs.
- [ ] Step 2: Reject non-accepted or ineligible qualification rows before score calculation.
- [ ] Step 3: Compute portfolio contribution only from projected verified quantitative claims and preserve explicit `Unknown` states.
- [ ] Step 4: Require account-scoped signal research outcomes before deriving `None found` and preserve `Partial`, `Unavailable`, and `Unknown` distinctly.
- [ ] Step 5: Pass the manifest-bound provisional top-30 company-ID set into `select_accounts()` and reject or exclude every row outside that set before score calculation and shortlist emission.
- [ ] Step 6: Sort with a documented stable key and assert byte-identical scores and shortlist output after shuffled worker completion order.

**Verification:**
- [ ] `py -3 -m unittest tests.test_scoring tests.test_selection -v`
- Expected: stale or unaccepted rows are excluded; verified claims change ranking only through projection; shuffled inputs produce identical canonical score and shortlist bytes.

**Exit Criteria:**
- The reranked provisional top 30 reflects only manifest-bound, verifier-approved projected evidence and has stable ordering.

### Task 5: Wire readiness QA and safe workbook generation

**Purpose:**
- Make the final gate prove semantic completeness and prevent incomplete or stale workbooks from being written as successful outputs.

**Task Function:**
- Integrate semantic validators and enforce staging-before-publish behavior.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from validation risk and artifact scope.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate workbook contents and manifest lineage.

**Specification Coverage:**
- Controller verification invokes `qa_leads.py`, `validate_workbook.py`, and `validate_deliverables.py` with manifest-bound paths.
- QA checks research completion for every top-30 company, promoted evidence coverage, ranking consistency, contact provenance, and workbook-to-canonical equality.
- Missing files, empty fallback sheets, stale hashes, old revisions, and wrong company sets fail before output replacement.
- `validate_deliverables.py` supports an explicit workbook-only mode for this pipeline, or the controller schedules and validates `build_deck.py` before invoking the full five-slide deliverable gate; the selected mode is recorded in the manifest and is never inferred from missing files.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/qa_leads.py:main`, `scripts/validate_workbook.py:main`, `scripts/validate_deliverables.py:main`
- Inspect: `scripts/build_workbook.py:read_csv`, `scripts/build_workbook.py:write_sheet`, `scripts/build_workbook.py:main`
- Modify: `scripts/orchestrate_enrichment.py:verify_manifest`
- Modify: `scripts/qa_leads.py:main`
- Modify: `scripts/build_workbook.py:read_csv`, `write_sheet`, `main`
- Modify: `scripts/validate_deliverables.py:main`
- Modify: `scripts/validate_workbook.py:main`
- Verify: `tests/test_artifact_manifest_side_effects.py`

**Dependencies:**
- Tasks 1–4 produce the authoritative manifest and canonical inputs.

**Authority:**
- Preauthorized local actions: edit validators and workbook staging flow; run local workbook and QA fixtures
- Stop for: overwriting the preserved workbook or publishing a workbook before the readiness gate passes

**Steps:**
- [ ] Step 1: Make the controller verify command run all three semantic validators and propagate every nonzero exit code.
- [ ] Step 2: Require exact `HEAD == manifest.head_sha == manifest.git_revision` and validate every required top-30 research outcome and promoted claim set.
- [ ] Step 3: Make missing CSV inputs, empty required surfaces, stale manifest entries, and wrong company IDs hard failures instead of `No records` fallback text.
- [ ] Step 4: Build the workbook to a staging path, validate it, then atomically replace the manifest-recorded output and register the final hash.
- [ ] Step 5: Add the explicit workbook-only validator mode and its manifest contract, or wire `build_deck.py` into the controller before the full deliverable validator; test that omitted mode cannot silently skip the deck requirement.

**Verification:**
- [ ] `py -3 -m unittest tests.test_artifact_manifest_side_effects -v`
- Expected: missing, stale, cross-run, empty, and revision-mismatched inputs fail before output replacement; valid fixture workbooks pass all validators.

**Exit Criteria:**
- Readiness QA is a real controller gate and only a fully validated enriched workbook is registered as the run output.

### Task 6: Add a fixture-backed end-to-end regression

**Purpose:**
- Prove the actual controller command, not isolated helpers, completes the full top-30 state machine and fails closed at each barrier.

**Task Function:**
- Exercise the integrated pipeline with deterministic fixture workers and artifacts.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from integration scope and test cost.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate failure-path coverage.

**Specification Coverage:**
- Successful queue, native-worker adapter, verifier, promotion, projection, reranking, QA, and workbook regeneration.
- Failure on missing worker output, missing verifier decision, cross-run evidence, hash drift, stale input, and revision mismatch.

**Required Skills:**
- `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Add: `tests/test_end_to_end_enrichment.py:test_top30_run_completes_and_is_manifest_bound`
- Add: `tests/test_end_to_end_enrichment.py:test_top30_run_fails_closed_at_each_barrier`
- Modify: `tests/fixtures/` only if an existing fixture directory is present; otherwise create fixture data under the test temporary directory
- Verify: `scripts/orchestrate_enrichment.py:main`

**Dependencies:**
- Tasks 1–5.

**Authority:**
- Preauthorized local actions: create temporary fixture data, invoke the controller with fixture workers, and assert outputs and failures
- Stop for: using live provider credentials or writing fixture data into canonical `data/`, `evidence/`, or `output/` paths

**Steps:**
- [ ] Step 1: Generate 30 accepted companies and deterministic lane queues in a temporary directory.
- [ ] Step 2: Run fixture worker adapters that emit account-scoped candidate claims, research runs, and verifier decisions in shuffled completion order.
- [ ] Step 3: Invoke the real controller command and assert the final manifest, canonical CSVs, reranked priority list, QA report, and workbook all share one run ID and revision.
- [ ] Step 4: Repeat the command with each failure mutation and assert nonzero exit plus no replacement of the prior valid workbook.

**Verification:**
- [ ] `py -3 -m unittest tests.test_end_to_end_enrichment -v`
- Expected: the success case produces a 30-company manifest-bound workbook; every declared failure case stops before publication.

**Exit Criteria:**
- The repository has fresh automated proof that the controller executes the required sequence and enforces every promotion and publication barrier.

### Task 7: Execute the provisional top-30 run and reconcile the plan

**Purpose:**
- Produce one real manifest-bound enriched run and record immutable readiness evidence.

**Task Function:**
- Run the accepted implementation against the provisional top 30, then reconcile task and artifact state.

**Template Profile:**
- Controller-selected: `unresolved`
- Selection basis: pending; resolve from live-run risk and external-action boundary.

**Validator Profile:**
- Controller-selected: `unresolved`
- Selection basis: independently validate final artifacts and manifest lineage.

**Specification Coverage:**
- One complete enriched run for the provisional top 30 using native sub-agents, verifier promotion, canonical projection, reranking, readiness QA, and regenerated workbook.
- No email sending, CRM mutation, or public lead publication.

**Required Skills:**
- `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `evidence/manifests/active_run.json`
- Inspect: `data/processed/`, `evidence/`, `output/`
- Modify: manifest-bound generated outputs only after the controller gate passes
- Verify: `scripts/orchestrate_enrichment.py`, `scripts/qa_leads.py`, `scripts/validate_deliverables.py`, `scripts/validate_workbook.py`

**Dependencies:**
- Tasks 1–6; implementation must be committed before artifact generation according to the repository’s manifest policy.

**Authority:**
- Preauthorized local actions: run the controller, inspect generated artifacts, and execute final local verification commands
- Stop for: missing native worker capability, provider authentication, provider spend, email sending, public publication, dirty implementation worktree, or any manifest/hash mismatch

**Steps:**
- [ ] Step 1: Confirm a clean implementation revision and create `evidence/manifests/active_run.json` from the accepted provisional top-30 shortlist.
- [ ] Step 2: Execute the controller’s native worker path for signal, portfolio, and contact lanes, then verifier and all deterministic downstream phases.
- [ ] Step 3: Confirm the generated workbook contains the enriched, reranked top 30 and that all evidence URLs and contact provenance are traceable.
- [ ] Step 4: Run final verification and record the immutable run ID, Git SHA, output hashes, QA report, and workbook validation result in this plan’s execution record.

**Verification:**
- [ ] `py -3 -m unittest discover -s tests -v`
- [ ] `py -3 -m json.tool config/lead_generation_schema.json`
- [ ] `py -3 -m json.tool config/research_evidence_schema.json`
- [ ] `py -3 scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/active_run.json`
- [ ] `git diff --check`
- [ ] `git status --short --branch`
- Expected: all commands pass; the active manifest points to one reachable full SHA; QA, deliverable, workbook, and hash checks all pass; no lead artifact comes from an older run.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`; only then may the plan status change from `proposed` to `completed`.

## Verification

- `py -3 -m unittest discover -s tests -v`
- `py -3 -m json.tool config/lead_generation_schema.json`
- `py -3 -m json.tool config/research_evidence_schema.json`
- `py -3 scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/active_run.json`
- `git diff --check`
- `git status --short --branch`

The final verification must confirm, from fresh output, that:

- the controller ran every required phase for exactly the manifest-bound top 30;
- every worker and verifier result is present, scoped, hashed, and terminal;
- only verified claims reached canonical projection;
- scores and ranking are deterministic and use projected canonical data;
- QA, workbook, deliverable, and source-register artifacts share the same run
  ID, Git revision, company universe, and input/output hashes;
- the workbook was regenerated after implementation changes and passed staging
  validation before replacement.

## Completion Criteria

1. Tasks 1–7 are complete with task-local proof recorded in the coordination ledger.
2. The controller exposes and executes the full top-30 sequence without manual phase stitching.
3. Native worker and verifier barriers fail closed on missing, duplicate, stale, cross-run, or out-of-scope results.
4. Canonical projection is the only route from verified evidence to qualification, signals, contacts, scores, and workbook inputs.
5. The active manifest remains one immutable run lineage from queue creation through workbook publication.
6. Final QA invokes all required validators and rejects revision, hash, evidence, identity, ranking, and workbook inconsistencies.
7. The fixture-backed E2E regression passes for success and declared failure cases.
8. One real provisional top-30 enriched run produces a fresh manifest-bound workbook with traceable evidence URLs and complete priority fields.
9. No email, CRM mutation, public publication, or unapproved provider spend occurs.
10. The plan remains `proposed` until `skill-verification-before-completion` returns `verified`.

## Execution Record

Execution date: `2026-11-08` (`Europe/Berlin`). The plan was patched after the
plan review to make controller ownership, manifest registries, native executor
behavior, shortlist scoping, and workbook-only validation explicit.

- Focused regression proof: `py -3 -m unittest tests.test_orchestration tests.test_selection tests.test_evidence_promotion tests.test_canonical_projection tests.test_artifact_manifest_side_effects -v` — passed.
- Full regression proof: `py -3 -m unittest discover -s tests -v` — `60` tests passed.
- Review-cycle-1 remediation: connected the non-fixture native worker and verifier dispatch path, made admission require the manifest-bound shortlist and accepted-company scope, enforced exact research/verifier registries and source policy during promotion, recalculated scores through `score_leads.py`, and made semantic `qa_leads.py` the readiness gate before publication.
- Added regression proof for prefix-collision run IDs, unregistered verifiers, fresh post-projection reranking, 30-row readiness QA, and final `Errors: 0` workbook publication.
- Provider-free controller proof: `lead-fixture-v3-6381fd60` executed queue, three fixture research lanes, verifier barrier, promotion, canonical projection, manifest-scoped reranking, workbook staging, workbook validation, and readiness settlement. Output: `output/lead-fixture-v3-6381fd60.xlsx`; manifest: `evidence/manifests/fixture_run_v3.json`.
- Workbook boundary proof: `py -3 scripts/validate_workbook.py --workbook output/lead-fixture-v3-6381fd60.xlsx` — passed with five required sheets.
- Deliverable boundary proof: `py -3 scripts/validate_deliverables.py --workbook output/lead-fixture-v3-6381fd60.xlsx --deck output/missing-fixture-deck.pptx --qa-report evidence/reports/lead-fixture-v3-6381fd60/qa.md --run-manifest evidence/manifests/fixture_run_v3.json --workbook-only` — passed without requiring a deck.
- Real provisional-top-30 probe: stopped fail-closed before queue creation because only `24/30` existing priority rows had confirmed city, accepted identity, and trusted domain. No Berlin location was synthesized and no external provider was called.
- Final strict manifest verification: `py -3 scripts/orchestrate_enrichment.py verify --root . --manifest evidence/manifests/fixture_run_v3.json` — rejected with `implementation worktree is dirty`; no production publication is claimed.

The fixture output is regression evidence only: it contains no provider-enriched
verified claims, so buying signals and named contacts remain explicit
`Unknown`. Task 7 remains blocked until the implementation revision is committed
and the provisional shortlist is repaired or requalified to exactly 30 accepted,
Berlin-confirmed companies with trusted domains.

## Consolidated Review Evidence

- `GPT-5.6-Sol` review context: `longdang193-lead-generation-bd4d236-top30-enriched-run`; result: `FAIL` for the mandatory end-to-end requirement.
- `GPT-6` review context: `longdang193-lead-generation-bd4d236-top30-enriched-run-gpt6`; result: `FAIL` for the mandatory end-to-end requirement.
- Both reviews verified commit `bd4d236828fbd54b0d513d635b601a469fe01e50` through commit-pinned GitHub files and independently identified the disconnected controller, missing dispatch barriers, absent canonical projection, broken manifest lineage, and missing E2E proof.
- PR #5 review cycle 1 at `2be785e08b08becdd7588626b16f937d3962803a` independently reproduced five blockers: fixture-only execution, synthetic QA, stale reranking, weak promotion authorization, and missing manifest admission. The implementation was patched on the review branch with focused regression coverage; a real provider-backed run remains blocked by the 24/30 shortlist-quality gate.
- The source-of-truth files are `scripts/orchestrate_enrichment.py`, `scripts/promote_evidence.py`, `scripts/score_leads.py`, `scripts/qa_leads.py`, `scripts/build_workbook.py`, `scripts/validate_deliverables.py`, `scripts/select_for_enrichment.py`, and the tests named in Tasks 1–6.

## Plan Self-Review

- Spec coverage: every required pipeline phase maps to Tasks 2–5 and the real-run gate in Task 7; lineage and regression proof map to Tasks 1 and 6.
- Token scan: no forbidden planning markers, unresolved path token, or unnamed task owner remains in the plan.
- Cross-task consistency: `active_run.json`, `run_id`, `head_sha`, `git_revision`, `candidate evidence`, `verified evidence`, canonical projection, and workbook staging are named consistently across tasks.
- Ownership: worker adapters write candidate evidence only; verifier writes decisions; promotion and projection write verified/canonical artifacts; scoring writes scores and priority; the controller owns the manifest and phase transitions; workbook generation writes only staged generated outputs.
- Task sizing: manifest, dispatch, projection, scoring, QA, regression, and live-run reconciliation are separated at their actual barriers and ordered by dependency.
