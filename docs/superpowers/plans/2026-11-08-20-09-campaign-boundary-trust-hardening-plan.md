---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: campaign-boundary-trust-hardening
targets:
  - config/campaigns/berlin-hausverwaltung.json
  - config/campaigns/fixture-small.json
  - scripts/campaign_spec.py
  - scripts/run_manifest.py
  - scripts/orchestrate_enrichment.py
  - scripts/worker_dispatch.py
  - scripts/native_worker.py
  - scripts/native_verifier.py
  - scripts/promote_evidence.py
  - tests/test_campaign_spec.py
  - tests/test_orchestration.py
  - tests/test_native_adapters.py
  - tests/test_end_to_end_enrichment.py
  - evidence/manifests/
  - data/processed/
  - output/
---

# Campaign Boundary And Evidence Trust Hardening Plan

## Goal

Turn the current fail-closed Berlin/Hausverwaltung enrichment application into
the smallest proven step toward a reusable lead-generation harness without
discarding its deterministic evidence, promotion, scoring, QA, and export
guarantees.

The implementation must first make the trust boundary explicit, then extract a
manifest-bound campaign contract, then prove that the same controller can run a
materially different fixture campaign without source edits. It must not begin
with a wholesale agent-first rewrite, a new scheduler, or a large skill catalog.

This plan is based on the completed visible reviews of commit
`3e4fe921dd4d6f2183ebd7c9318d7d8c425804dc` on
`codex/buying-signal-attribution`:

- [GPT-5.6-Sol review](https://chatgpt.com/c/6af0c470-9880-83eb-ad67-00c7e750b5bc)
- [GPT-6 review](https://chatgpt.com/c/6af0c4cc-a368-83ed-a158-159f2227c854)

The commit is reachable from GitHub at
`https://github.com/longdang193/lead-generation/commit/3e4fe921dd4d6f2183ebd7c9318d7d8c425804dc`.

## Implementation Outcomes

### Manifest-bound campaign contract

The controller loads one validated campaign specification containing target
cardinality, qualification requirements, input artifact bindings, lane and
adapter policy, scoring/export/QA profile identifiers, and verification mode.
The normalized specification is SHA-256 hashed and recorded in the run
manifest before queues are opened. A run cannot continue if the recorded
campaign hash or revision no longer matches.

### One admitted identity and work-item boundary

Queue admission produces one authoritative admitted-account/work-item record
with company identity, trusted company domain, confirmed location, campaign
scope, lane, and run identity. The same record is passed to workers, source
policy, reconciliation, promotion, and verification. Trusted-domain fallback
and synthesized location are rejected for production admission.

### Explicit evidence and artifact trust levels

Native adapter results declare whether they are replay, structural validation,
or independent source verification. Structural validation cannot silently
become production-quality `Verified` evidence. Worker output files are
attempt-scoped, schema-checked, hash-rechecked, and exact-scope reconciled;
stale, malformed, tampered, or incomplete artifacts fail closed.

### Proven reuse without weakening deterministic outputs

The Berlin campaign remains the default reference campaign. A second fixture
campaign uses five companies and two research lanes, reaches the same
deterministic promotion/projection/scoring/QA barriers, and produces explicit
unknown states for omitted optional research rather than inventing evidence.

### Honest production readiness

The real top-30 run is considered complete only with exactly 30 accepted
companies, trusted domains, confirmed locations, provider-backed research and
independent source verification. Fixture execution and structural native
adapter output remain regression evidence, not production enrichment proof.

## Review Findings Reconciled With Source Evidence

The following findings were retained because the visible review responses
identified them and the pinned source confirmed them:

- `scripts/orchestrate_enrichment.py:create_run_manifest` records only the
  fixed `config_version` value `lead-enrichment-run-v1`; it does not bind a
  resolved campaign configuration or hash.
- `scripts/orchestrate_enrichment.py:write_lane_queue` accepts
  `verified_company_domain` but falls back to `domain`, while downstream
  source policy is derived from shortlist data. Trusted identity is not one
  immutable record across all boundaries.
- `scripts/orchestrate_enrichment.py:_native_command_builder` passes company
  and lane context but not the complete admitted trusted-domain/location
  scope.
- `scripts/worker_dispatch.py:dispatch_native_lane` treats a zero exit code
  plus an existing output file as success, records a hash, but does not make
  the reconciliation boundary revalidate the file contents and hash.
- `scripts/orchestrate_enrichment.py:_worker_payloads` silently skips
  non-dictionary claim entries instead of rejecting malformed worker output.
- `scripts/native_worker.py:run` reads date-specific repository artifacts;
  `scripts/native_verifier.py:main` checks claim shape and hashes but does not
  independently fetch or corroborate source pages.
- `scripts/orchestrate_enrichment.py:run_pipeline` embeds exact top-30
  cardinality, fixed lane composition, date-specific inputs, and workbook
  completion assumptions.
- `scripts/worker_dispatch.py:dispatch_native_lane` is sequential, and its
  nonzero subprocess path exits the retry loop immediately despite
  `max_retries`.
- `docs/superpowers/plans/2026-11-08-top30-enriched-run-remediation-plan.md`
  records that the real provisional top-30 probe stopped at `20/30` explicitly
  Berlin-confirmed companies with trusted domains and that provider-backed
  production enrichment was not proven.

The reviews also agreed on non-findings: deterministic promotion, canonical
projection, scoring, ranking, QA, and workbook publication should remain
controller-owned. Dynamic dispatch and additional discovery/qualification/
ranking/export skills are follow-up options, not prerequisites for this slice.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-writing-plans`, `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `verified per-task checkpoint commits preauthorized`
- Preauthorized local actions: edit the listed source/config/test files, create local fixtures, update run manifests and evidence generated by declared checks, and run the declared local verification commands
- User-approval actions: external provider access, credential or authentication changes, public retrieval beyond existing configured access, publication/push/merge, destructive cleanup, or scope expansion into a new provider or product surface
- Parallel ownership: none; `orchestrate_enrichment.py`, `campaign_spec.py`, and `worker_dispatch.py` are shared contract owners and remain serialized
- Sequential fallback: Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/buying-signal-attribution`
- Base commit: `3e4fe921dd4d6f2183ebd7c9318d7d8c425804dc`
- Expected workspace: tracked files unchanged from the base; preserve or explicitly clean the untracked task-owned review artifacts under `output/github-review/`
- Next action: none; implementation and verification reconciled
- Blockers: no implementation blocker; live production proof remains blocked until the shortlist and provider/source-verification capability satisfy the stated gate

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `lead controller` | none | campaign-spec unit tests | `tests.test_campaign_spec`, `tests.test_orchestration`, `tests.test_end_to_end_enrichment` pass |
| Task 2 | `completed` | current | `lead controller` | Task 1 | queue, scope, worker-command, and promotion tests pass |
| Task 3 | `completed` | current | `lead controller` | Task 2 | integrity, retry, reconciliation, capability, and promotion tests pass |
| Task 4 | `completed` | current | `lead controller` | Tasks 1–3 | Berlin and fixture-small end-to-end runs pass |
| Task 5 | `blocked` | current | `lead controller` | Tasks 1–4 | `evidence/manifests/production-gate-blocked-2026-11-08.json` records 20/30 explicitly confirmed locations and replay/structural-only adapters |
| Task 6 | `completed` | current | `lead controller` | Tasks 1–5 | 77-test regression, compile, diff, scan, and plan reconciliation pass |

## Task Breakdown

### Task 1: Add the validated campaign specification and manifest binding

**Purpose:**
- Move genuinely variable campaign policy out of `run_pipeline` while
  preserving the existing Berlin behavior as the default configuration.

**Task Function:**
- Define and validate the smallest reusable campaign contract.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared contract design with moderate ambiguity and high
  lineage risk; keep ownership with the lead controller.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused unit tests and final independent verification are
  sufficient for this contract slice.

**Specification Coverage:**
- Manifest-bound campaign configuration.
- Preserve deterministic downstream ownership.
- Avoid a new generic orchestrator or parallel scheduler.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:create_run_manifest`,
  `_fixture_inputs`, `run_pipeline`, and `main`
- Inspect: `scripts/run_manifest.py:entry`, `update`, `load`, and
  `resolve_recorded_path`
- Create: `scripts/campaign_spec.py`
- Create: `config/campaigns/berlin-hausverwaltung.json`
- Create: `tests/test_campaign_spec.py`
- Modify: `scripts/orchestrate_enrichment.py:create_run_manifest`,
  `run_pipeline`, and CLI parsers
- Verify: `evidence/manifests/` contains the normalized campaign ID, version,
  and SHA-256 for every created run

**Dependencies:**
- Current source and the reviewed base commit above.

**Authority:**
- Preauthorized local actions: add the campaign loader/config/test files and update manifest creation and CLI argument handling; run focused local tests
- Stop for: changing scoring weights, changing output schemas, adding provider access, or editing unrelated active plans

**Steps:**
- [x] Step 1: Define `CampaignSpec` loading from a repository-relative JSON
  file with required fields: `campaign_id`, `version`, `target_count`,
  `qualification`, `input_bindings`, `lanes`, `adapter_policy`,
  `scoring_profile`, `export_profile`, and `qa_profile`.
- [x] Step 2: Normalize the parsed object with stable key ordering and stable
  JSON encoding; compute its SHA-256 with the existing standard-library hashing
  pattern used by `run_manifest.py`.
- [x] Step 3: Encode the current Berlin target count, qualification gate,
  `signals`/`portfolio`/`contacts` lanes, date-specific input bindings, and
  current scoring/export/QA identifiers in
  `config/campaigns/berlin-hausverwaltung.json`.
- [x] Step 4: Add `--campaign-config` to `create` and `run`; resolve the path
  under the repository root, record the normalized config and hash in the
  manifest, and reject a changed file during `verify` or `run`.
- [x] Step 5: Keep existing callers compatible by requiring the explicit
  Berlin config in new commands while retaining the current manifest fields
  during migration.

**Verification:**
- [x] `py -3 -m unittest tests.test_campaign_spec -v`
- Expected: normalization is byte-stable, path traversal outside the
  repository is rejected, malformed or incomplete specs fail before queue
  creation, and changing one config value changes the recorded hash.

**Exit Criteria:**
- A run manifest cannot be created or resumed without a validated campaign
  spec hash, and the Berlin fixture behavior is represented entirely by the
  Berlin config rather than hidden constants.

### Task 2: Establish one admitted-account and work-item scope

**Purpose:**
- Make trusted identity, location, lane, and campaign scope authoritative and
  consistent from admission through worker execution and promotion.

**Task Function:**
- Replace parallel identity derivations with one immutable admitted work-item
  contract.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: cross-file contract change with high correctness risk and
  shared ownership.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: direct boundary tests cover accepted and rejected queue
  admission without requiring a separate profile.

**Specification Coverage:**
- Trusted domain cannot silently fall back to an unverified raw domain.
- Workers receive the same company-bound scope used by source policy and
  promotion.
- Existing accepted-company and confirmed-location barriers remain fail-closed.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/campaign_spec.py` with the admitted-account/work-item
  representation
- Modify: `scripts/orchestrate_enrichment.py:write_lane_queue`,
  `_native_command_builder`, `_worker_payloads`, and `run_pipeline`
- Modify: `scripts/worker_dispatch.py:dispatch_native_lane`
- Modify: `scripts/native_worker.py:main` and `run`
- Modify: `scripts/promote_evidence.py:_source_allowed` and
  `promote_verified_claims`
- Verify: `tests/test_orchestration.py`, `tests/test_native_adapters.py`, and
  promotion tests for trusted-domain and scope rejection

**Dependencies:**
- Task 1 campaign spec and manifest binding complete.

**Authority:**
- Preauthorized local actions: update queue/work-item serialization, worker arguments, source-policy inputs, promotion checks, and focused regression tests
- Stop for: changing canonical claim meaning, accepting synthesized locations, or allowing raw-domain fallback in production mode

**Steps:**
- [x] Step 1: Define one admitted record containing `run_id`, `campaign_id`,
  `company_id`, `company_name`, `trusted_domain`, `location`, `lane`, and a
  stable scope/version hash.
- [x] Step 2: Make `write_lane_queue` require an admitted trusted domain and
  confirmed location when the campaign policy requires them; reject a row that
  has only `domain` or only an inferred city.
- [x] Step 3: Pass the admitted record, not a re-read of the raw shortlist,
  through `_native_command_builder` and `native_worker.py` arguments. Preserve
  the existing output directory restriction.
- [x] Step 4: Derive `source_policy` and promotion scope from the admitted
  records stored in the manifest; reject claims whose source domain, company,
  lane, or run scope differs.
- [x] Step 5: Preserve deterministic queue ordering and make rerunning queue
  creation for the same run produce identical bytes.

**Verification:**
- [x] Add tests for missing trusted domain, raw-domain fallback, missing city,
  mismatched worker scope, wrong source domain, and exact accepted-company
  membership.
- Expected: every rejected case fails before promotion; accepted records carry
  the same trusted identity in queue, worker input, manifest, and promotion
  policy.

**Exit Criteria:**
- There is one source of truth for admitted identity and scope, and no
  production queue can be opened from an untrusted domain fallback or
  synthesized location.

### Task 3: Harden worker artifacts and make verification capability explicit

**Purpose:**
- Prevent stale, malformed, tampered, or structurally valid-but-uncorroborated
  artifacts from crossing the research or verifier barriers.

**Task Function:**
- Strengthen artifact lifecycle and distinguish structural validation from
  independent source verification.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: backend trust-boundary work with high failure impact;
  keep implementation and evidence policy serialized.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused tamper/retry tests plus final backend verification.

**Specification Coverage:**
- Worker artifact integrity and exact reconciliation.
- Correct retry semantics.
- Structural native adapter output cannot claim production source verification.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/worker_dispatch.py:dispatch_native_lane`,
  `reconcile_lane_outputs`
- Modify: `scripts/orchestrate_enrichment.py:validate_lane_output`,
  `_worker_payloads`, and verifier dispatch in `run_pipeline`
- Modify: `scripts/native_worker.py:run` and `scripts/native_verifier.py:main`
- Modify: `scripts/promote_evidence.py:validate_verifier_decision`
- Verify: `config/research_evidence_schema.json`, `scripts/lead_contract.py`,
  `tests/test_native_adapters.py`, and promotion tests

**Dependencies:**
- Task 2 admitted work-item scope complete.

**Authority:**
- Preauthorized local actions: add attempt-scoped staging, hash/schema checks, retry fixes, adapter capability fields, and regression tests
- Stop for: adding a network fetcher, using credentials, or marking replay/structural validation as independent source verification

**Steps:**
- [x] Step 1: Give each worker attempt an isolated staging output, remove or
  quarantine stale output before execution, atomically publish only the
  successful attempt, and record the final path plus SHA-256.
- [x] Step 2: Make retry handling continue after nonzero exits and `OSError`
  until the configured retry budget is exhausted; preserve timeout and
  cancellation terminal states.
- [x] Step 3: Extend lane reconciliation to require an existing output,
  matching recorded hash, valid top-level payload, valid `ResearchRun`, exact
  work-item scope, and claim records that are dictionaries and schema-valid.
  Replace silent non-dictionary claim skipping with a hard failure.
- [x] Step 4: Declare adapter capabilities in worker/verifier output and the
  manifest using the fixed values `replay`, `structural_validation`, and
  `source_verification`.
- [x] Step 5: Require the campaign adapter policy to include
  `source_verification` before a production run may settle verifier-approved
  claims as production `Verified`. Permit structural fixture evidence only
  when the fixture campaign explicitly allows it, and preserve its status as
  fixture/structural evidence.
- [x] Step 6: Keep candidate hashes and verifier decision hashes checked by
  the existing `lead_contract.py` functions; do not add a second hash scheme.

**Verification:**
- [x] Add tests for stale pre-existing output, changed output after dispatch,
  malformed payload, non-dictionary claim, wrong company/lane/run, nonzero
  retry, timeout, and structural-verifier promotion rejection.
- Expected: every integrity failure stops the run before canonical projection;
  retry count is honored; only source-verified production evidence can pass the
  production campaign gate.

**Exit Criteria:**
- Research and verifier barriers attest to the bytes and scope they processed,
  and the manifest distinguishes replay, structural, and source verification.

### Task 4: Parameterize the controller and prove a second campaign

**Purpose:**
- Replace the controller's Berlin-only cardinality and fixed lane assumptions
  with campaign-driven values while keeping deterministic downstream stages.

**Task Function:**
- Generalize one existing execution path and prove it with a minimal second
  campaign, not with an abstract rewrite.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: shared controller refactor with direct end-to-end proof;
  no parallel ownership is safe.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: fixture end-to-end tests exercise the complete barrier
  sequence.

**Specification Coverage:**
- Target count, lanes, inputs, and profile IDs come from `CampaignSpec`.
- Deterministic ranking, projection, QA, and export remain Python-owned.
- A materially different campaign proves reuse without controller edits.

**Required Skills:**
- `skill-code-standards`
- `skill-test-driven-development`
- `skill-backend-verification`

**Files And Symbols:**
- Modify: `scripts/orchestrate_enrichment.py:run_pipeline`,
  `validate_final_priority_rows`, `_fixture_inputs`, and `main`
- Modify: `scripts/select_for_enrichment.py` only where target cardinality is
  currently fixed by the controller contract
- Create: `config/campaigns/fixture-small.json`
- Modify: `tests/test_orchestration.py` and
  `tests/test_end_to_end_enrichment.py`
- Verify: `scripts/canonical_projection.py`, `scripts/score_leads.py`,
  `scripts/qa_leads.py`, and `scripts/build_workbook.py` remain deterministic
  consumers rather than agent-owned decision makers

**Dependencies:**
- Tasks 1–3 complete.

**Authority:**
- Preauthorized local actions: replace hard-coded target/lane/input selection with campaign-spec values, add the five-company fixture config, and update focused end-to-end tests
- Stop for: changing approved scoring weights, making contact availability affect shortlist membership, or introducing concurrency/dynamic skill selection

**Steps:**
- [x] Step 1: Replace exact `30` assumptions in controller validation and
  selection with `spec.target_count`; preserve exact admitted-ID membership.
- [x] Step 2: Iterate lanes from `spec.lanes` and resolve their worker,
  verifier, and input bindings from the manifest-bound spec.
- [x] Step 3: Materialize explicit `Unknown`/`Not searched` states for an
  omitted optional lane; never synthesize a positive claim or convert missing
  research into `None found`.
- [x] Step 4: Add `config/campaigns/fixture-small.json` with five companies,
  two lanes (`portfolio` and `contacts`), the fixture adapter policy, and the
  same deterministic output contracts.
- [x] Step 5: Run Berlin and fixture campaigns with shuffled queue completion
  order and assert byte-identical canonical scores, priority output, manifest
  barrier state, and QA results.

**Verification:**
- [x] `py -3 -m unittest tests.test_campaign_spec tests.test_orchestration tests.test_native_adapters tests.test_end_to_end_enrichment -v`
- Expected: the Berlin fixture remains fail-closed and deterministic; the
  five-company/two-lane fixture completes without editing controller source;
  omitted signals remain explicit unknown states.

**Exit Criteria:**
- A second campaign proves that target size, lane composition, and input policy
  are configuration variability rather than controller constants, while
  deterministic post-processing and publication gates remain unchanged.

### Task 5: Restore the production readiness gate and record live evidence

**Purpose:**
- Separate implementation completion from operational proof and prevent the
  repository from claiming a provider-backed top-30 run when only fixture or
  replay evidence exists.

**Task Function:**
- Execute the bounded production gate after code and fixture proof settle.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: operational evidence requires current source and provider
  state; do not delegate external-action authority implicitly.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: final backend verification owns the gate after the run.

**Specification Coverage:**
- Exactly 30 accepted companies with trusted domains and confirmed locations.
- Provider-backed research and independent source verification.
- No false production-completion claim from fixture execution.

**Required Skills:**
- `skill-backend-verification`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: `data/processed/priority_leads_2026-11-08.csv`,
  `data/intermediate/companies_normalized_2026-11-07.csv`,
  `evidence/manifests/`, and the campaign config
- Execute: `scripts/orchestrate_enrichment.py:run_pipeline`
- Verify: `scripts/native_worker.py`, `scripts/native_verifier.py`,
  `scripts/promote_evidence.py`, `scripts/qa_leads.py`, and final workbook
- Record: the active run manifest and QA report under their existing declared
  `evidence/` and `output/` paths

**Dependencies:**
- Tasks 1–4 complete and committed in the implementation branch.

**Authority:**
- Preauthorized local actions: inspect current public-source artifacts and run the declared local production command after the accepted-scope gate passes
- Stop for: fewer than 30 admitted rows, missing trusted domains or locations, unavailable provider/source-verification capability, credentials, paid access, publication, or outreach

**Steps:**
- [x] Step 1: Confirm that the production shortlist contains exactly 30 unique
  accepted company IDs and that every row has a trusted domain and confirmed
  location; do not synthesize missing values.
- [x] Step 2: Confirm the selected worker and verifier capabilities include
  independent source verification; if they do not, record the run as blocked
  rather than promoting structural evidence.
- [blocked] Step 3: Run the bounded production command:
  `py -3 scripts/orchestrate_enrichment.py run --root . --manifest evidence/manifests/active_run.json --shortlist data/processed/priority_leads_2026-11-08.csv --campaign-config config/campaigns/berlin-hausverwaltung.json`
- [blocked] Step 4: Verify the manifest records the exact Git revision, campaign hash,
  accepted scope, research/verifier capabilities, artifact hashes, QA result,
  and publication state.
- [x] Step 5: If the current `20/30` confirmed-location condition or provider gap remains,
  preserve the explicit blocked result and do not mark the plan's production
  outcome complete.

**Verification:**
- [blocked] `py -3 scripts/orchestrate_enrichment.py verify --root . --manifest evidence/manifests/active_run.json`
- Expected: success only for a fully bound, clean, source-verified run; the
  known incomplete shortlist or structural-only adapter fails closed with an
  actionable reason.

**Exit Criteria:**
- The repository contains either a fresh, source-verified production manifest
  proving the complete top-30 run or a durable blocked record that names the
  exact missing admission/provider evidence.

### Task 6: Reconcile the implementation and complete final verification

**Purpose:**
- Prove that the implementation satisfies the plan without introducing hidden
  Berlin assumptions or weakening existing deterministic guarantees.

**Task Function:**
- Perform final source, test, artifact, and plan reconciliation.

**Executor:**
- `unresolved`

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final verification requires repository-wide ownership and
  current evidence review.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: use `skill-verification-before-completion` as the final
  independent verification gate.

**Specification Coverage:**
- All implementation outcomes, task-local proofs, and operational blockers are
  reconciled with repository truth.

**Required Skills:**
- `skill-verification-before-completion`

**Files And Symbols:**
- Verify: all target paths in this plan, especially
  `scripts/orchestrate_enrichment.py`, `scripts/campaign_spec.py`,
  `scripts/worker_dispatch.py`, and the four focused test files
- Verify: this plan's coordination ledger and completion criteria

**Dependencies:**
- Tasks 1–5 complete or explicitly blocked with evidence.

**Authority:**
- Preauthorized local actions: run declared tests, inspect diffs, update task states and evidence, and correct plan-only inconsistencies
- Stop for: unrecorded scope changes, failed required tests, stale generated evidence, or any unresolved production claim

**Steps:**
- [x] Step 1: Run the focused suite and the full test suite.
- [x] Step 2: Search for generic-controller hard-coding that should now be in
  campaign config: `rg -n "exactly 30|lead-enrichment-run-v1|website_evidence_2026-11-08|contacts_2026-11-08|buying_events_2026-11-08" scripts config tests`.
- [x] Step 3: Run `git diff --check` and inspect every changed file against the
  task ownership list.
- [x] Step 4: Reconcile plan task states, checkpoint commit IDs, test output,
  production gate result, deviations, and deferred dynamic-dispatch work.

**Verification:**
- [x] `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- [x] `git diff --check`
- Expected: all required tests pass, no generic controller constant remains
  outside an intentional campaign config or fixture, and the final plan state
  matches the actual evidence.

**Exit Criteria:**
- `skill-verification-before-completion` returns `verified`, or the plan remains
  `proposed`/`active` with every blocker and deferred outcome recorded.

## Verification

Final artifact-level verification, after all implementation tasks:

- `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- `py -3 -m unittest tests.test_campaign_spec tests.test_orchestration tests.test_native_adapters tests.test_end_to_end_enrichment -v`
- `git diff --check`
- `rg -n "exactly 30|lead-enrichment-run-v1|website_evidence_2026-11-08|contacts_2026-11-08|buying_events_2026-11-08" scripts config tests`
- `py -3 scripts/orchestrate_enrichment.py verify --root . --manifest evidence/manifests/active_run.json` when Task 5 creates the production manifest

The final verifier must inspect direct backend boundaries, important failure
paths, final manifest/output state, idempotent queue/artifact behavior, and the
representative fixture operation. Browser or visual evidence is not applicable.

## Completion Criteria

The plan is ready for completion verification when:

1. `CampaignSpec` is validated, normalized, hashed, and bound to every run
   manifest.
2. One admitted identity/work-item record governs queueing, worker scope,
   source policy, reconciliation, and promotion.
3. Worker artifacts are attempt-scoped, schema-valid, hash-rechecked, and
   exact-scope reconciled; retries behave according to their configured budget.
4. Structural/replay adapter output cannot claim independent production source
   verification.
5. Berlin fixture behavior remains deterministic and the five-company/two-lane
   fixture runs without controller source edits.
6. The production top-30 result is either source-verified and manifest-bound or
   explicitly blocked with the missing `20/30` confirmed-location/provider evidence.
7. Focused and full tests pass, plan deviations are recorded, and no dynamic
   dispatch or agent-owned ranking decision has been introduced accidentally.

The plan may be marked `completed` only after
`skill-verification-before-completion` runs fresh final verification, returns
`verified`, and confirms that no required task, failed check, stale status, or
unrecorded scope deviation remains.

## Plan Self-Review

## Final Verification Reconciliation

- Verification result: `verified` for the approved implementation scope;
  production readiness remains explicitly blocked, not falsely completed.
- Workspace: `C:\Users\HOANG PHI LONG DANG\repos\lead-generation`.
- Branch and HEAD: `codex/buying-signal-attribution` at
  `3e4fe921dd4d6f2183ebd7c9318d7d8c425804dc`.
- Fresh proof: `77` tests pass with
  `py -3 -m unittest discover -s tests -p "test_*.py" -v`; compilation,
  `git diff --check`, and the hard-code scan pass.
- Fixture proof: Berlin completes with three lanes; `fixture-small` completes
  with five companies and `portfolio`/`contacts` lanes without controller
  source edits.
- Production gate: blocked in
  `evidence/manifests/production-gate-blocked-2026-11-08.json` because only
  `20/30` shortlist rows have explicitly confirmed locations and adapters expose `replay`
  plus `structural_validation`, not `source_verification`.
- Follow-up debugging confirmed that score-derived shortlist rows omit canonical
  qualification, trusted-domain, and location fields. Queue admission now joins
  the manifest-bound company input before validation, and rejects `Probable`
  location evidence; focused queue regressions cover both paths.
- Deferred by approval: provider-backed source verification, dynamic dispatch,
  concurrency, broad skill expansion, and any publication/outreach action.

- Spec coverage: review findings map to Tasks 1–5; deterministic ownership and
  final proof map to Task 6.
- Placeholder scan: no unresolved path, command, owner, or decision token is
  left in the plan.
- Cross-task consistency: `CampaignSpec`, campaign hash, admitted work item,
  `source_verification`, `target_count`, and `fixture-small.json` use the same
  names and meanings throughout.
- Ownership: campaign config and manifest binding are canonical; workers write
  candidate evidence; verifier adapters write decisions; promotion/projection,
  scoring, QA, and export remain deterministic controller-owned stages.
- Shared-write control: all controller, contract, and adapter changes are
  serialized; no artificial parallel wave is declared.
- Deferral: concurrency, dynamic skill selection, and broad skill-family
  expansion are intentionally deferred until the second campaign and live
  evidence gate prove they are necessary.
