---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: lead-generation-harness-bottleneck-remediation
targets:
  - scripts/orchestrate_enrichment.py
  - scripts/native_worker.py
  - scripts/worker_dispatch.py
  - scripts/promote_evidence.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/select_for_enrichment.py
  - scripts/collect_buying_signals.py
  - scripts/qa_leads.py
  - scripts/validate_deliverables.py
  - scripts/run_manifest.py
  - scripts/runtime_config.py
  - config/research_policy.json
  - .agents/skills/lead-generation/SKILL.md
  - tests
---

# Lead-Generation Harness Bottleneck Remediation Plan

This plan is the proposed implementation handoff for findings validated by two
completed, commit-pinned browser reviews and current source inspection. It is
limited to personal-use reliability and truthful delivery; it does not claim
production readiness or authorize live provider traffic.

## Goal

Make a bounded Monday delivery practical and truthful without weakening strict
mode. Replay-only execution must never present itself as live research;
personal delivery must expose partial and unavailable work; assurance,
research gaps, historical lineage, and evidence provenance must survive every
projection and ranking step; retries and lane dispatch must honor a finite
budget; and production-gate evidence must identify the exact revision,
configuration, and inputs evaluated.

## Review Resolution

Both requested model runs completed successfully. Neither timed out, was
ambiguous, or was retried or resubmitted.

- Repository: `longdang193/lead-generation`.
- Reviewed branch: `main`.
- Reviewed commit: `d7ca76219ea9e280b5a48689f94e060ae41c87df`.
- Context: `longdang193-lead-generation-d7ca7621-fragile-bottlenecks`.
- `GPT-5.6-Sol`, `High`: repository-bound dedicated review chat, fresh tab,
  visible assistant turn `0`, bounded runner completion `confirmed`.
- `GPT-6`, `High`: repository-bound dedicated review chat, fresh tab, visible
  assistant turn `0`, bounded runner completion `confirmed`.
- Dedicated profile marker matched `longdang193/lead-generation` and
  `longdang193-lead-generation`; no private profile or chat identifiers are
  stored in this public plan.
- Publication: `no publication required`; the reviewed full SHA was reachable
  from GitHub.

Validated findings, accepted only where visible responses and source agree:

1. Non-fixture execution can launch replay-only `scripts/native_worker.py` but
   label the run `live_research`.
2. Personal delivery can complete without a meaningful source-verification
   attempt or verified enrichment, including under-target output.
3. Structural assurance can be projected as `Verified` and affect ranking as
   though it were source verification.
4. Incomplete buying-signal research can become `None found` instead of
   `Unknown`.
5. QA can continue to inspect the original website-evidence path after a newer
   promoted evidence artifact becomes canonical.
6. Fixed lane matrices, serialized dispatch, generic retries, reserve rules,
   and fixed executor limits lack one global deadline and attempt budget.
7. Personal partial delivery can stamp historical contact baselines with the
   current projection run.
8. A TED-only external allowlist is a practical public-news bottleneck.
9. The checked-in production gate has inconsistent blocker counts and lacks
   revision, configuration, and input hashes.
10. Tracked campaign input churn can trigger the implementation-dirty barrier.

Explicitly excluded after current-SHA validation:

- Company-domain-only source rejection; `_source_allowed()` already supports
  approved external domains by claim and source kind.
- An exact 30-company invariant in personal mode; exact cardinality is enforced
  only in strict mode.
- A broad duplicate-claim rewrite; canonical keys already support multiple
  stable event and contact claims.
- Editing generated root `AGENTS.md`; the maintained skill already exists at
  `.agents/skills/lead-generation/SKILL.md`.
- Provider latency, cost, quota, credentials, recall, contact accuracy, and
  live-provider behavior; no live probe was run.

The durable blocker remains
`evidence/manifests/production-gate-blocked-2026-11-08.json:1`; fixture and
replay success must not close it. :codex-annotation{index="1"}

## Implementation Outcomes

### Truthful execution and delivery

Replay, structural validation, live source verification, unavailable, partial,
and needs-review states remain distinct. Non-fixture runs fail closed when the
configured worker cannot provide live research. Personal mode may deliver a
defensible reserve-backed partial shortlist, but only with explicit gaps and
attempt evidence; strict mode retains exact admitted-set barriers.

### Evidence and ranking integrity

Assurance level, provider status, source class, research status, and material
gaps remain bound to each claim and account through promotion, canonical
projection, scoring, contact output, event output, workbook export, and QA.
Incomplete searches remain `Unknown`; only an account-scoped completed search
with no matching event may produce `None found`.

### Bounded and restartable operations

Material gaps are dispatched by expected value within a single run deadline,
subprocess-attempt budget, and cancellation policy. Deterministic input,
schema, and configuration failures are not retried as transient failures.
Cache reuse requires matching scope, input, campaign, adapter, profile, and
provider fingerprints.

### Revision-bound production evidence

Contact history is immutable across projection runs. QA resolves authoritative
manifest-bound evidence rather than a stale CLI override. Production-gate
artifacts record a reachable full revision and hashes for campaign config,
admitted inputs, supporting inputs, and generated outputs, with one consistent
blocker count. Tracked campaign data changes do not masquerade as dirty
implementation code.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`, `skill-writing-skills`, `skill-executing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`
- Commit policy: `no commits during execution`
- Preauthorized local actions: edit the declared source, test, configuration, and skill files; run the declared local verification commands; preserve the durable blocker and excluded findings
- User-approval actions: push, merge, publication, live-provider calls, destructive cleanup, and any change to strict-mode admission policy
- Parallel ownership: `none`
- Sequential fallback: complete Tasks 1 through 6 in order because lifecycle semantics feed projection, dispatch budgets depend on the lifecycle contract, and documentation must describe the final behavior

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/buying-signal-attribution`
- Base commit: `97d40274b2b2ff717696c85590aabeafd2cd122e`
- Expected workspace: `declared implementation, evidence, tests, and this plan only`
- Next action: commit and publish the verified implementation; live production work remains blocked
- Blockers: live production gate remains blocked by `evidence/manifests/production-gate-blocked-2026-11-08.json`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `lead controller` | none | focused lifecycle and delivery tests | `tests/test_orchestration.py`, `tests/test_end_to_end_enrichment.py` |
| Task 2 | `completed` | current | `lead controller` | Task 1 | promotion, projection, scoring, and QA regression tests | `tests/test_canonical_projection.py`, `tests/test_scoring.py`, `tests/test_end_to_end_enrichment.py` |
| Task 3 | `completed` | current | `lead controller` | Task 1 | bounded dispatch and retry tests plus measured budget evidence | `tests/test_native_adapters.py` |
| Task 4 | `completed` | current | `lead controller` | Task 2 | historical-lineage and manifest-authoritative QA tests | `tests/test_canonical_projection.py`, `tests/test_artifact_manifest_side_effects.py`, `tests/test_personal_mode.py` |
| Task 5 | `completed` | current | `lead controller` | Tasks 1–4 | production-gate hash and clean-input regression tests | `tests/test_orchestration.py`; `python scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/production-gate-blocked-2026-11-08.json --root .` |
| Task 6 | `completed` | current | `lead controller` | Tasks 1–5 | skill inspection and end-to-end command help | `.agents/skills/lead-generation/SKILL.md`; `python scripts/orchestrate_enrichment.py --help` |

## Task 1: Fail Closed on Replay and Separate Delivery States

**Purpose:** Prevent the default native replay adapter from being mistaken for
live research and prevent personal completion from hiding missing or under-
target work.

**Task Function:** lifecycle-contract hardening

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: cross-file behavior and failure-state semantics require
  source-first controller ownership.

**Validator Profile:** Controller-selected: `none`
- Selection basis: focused local tests provide the required validation.

**Specification Coverage:** Findings 1 and 2; outcome `Truthful execution and delivery`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`,
  `complete_company_ids`, `delivery_summary`, and `validate_final_priority_rows`.
- Inspect: `scripts/native_worker.py:run` and `make_claim`.
- Modify: the same functions plus the smallest shared status/manifest helpers
  needed to carry adapter capability and meaningful-attempt evidence.
- Verify: `tests/test_orchestration.py`, `tests/test_native_adapters.py`,
  `tests/test_personal_mode.py`, `tests/test_end_to_end_enrichment.py`.

**Dependencies:** current replay and personal-mode tests are the source of truth;
strict-mode exact-scope behavior must remain unchanged.

**Authority:**
- Preauthorized local actions: edit Task 1 files and run Task 1 tests and `python -m compileall -q scripts tests`
- Stop for: any request to authorize live provider traffic or weaken strict-mode barriers

**Steps:**
- [ ] Step 1: Trace the current non-fixture command path and enumerate every
  status transition from worker output through manifest, delivery summary, and
  final priority validation.
- [ ] Step 2: Add a fail-closed capability check so replay is accepted only by
  explicit fixture/replay execution and non-fixture delivery records the live
  source-verification capability requirement.
- [ ] Step 3: Require meaningful attempts and explicit terminal evidence before
  marking a company complete; represent personal under-target output as
  `Partial` or `Unavailable` with missing company IDs and lane gaps.
- [ ] Step 4: Add regression tests for replay rejection, zero-result rejection,
  under-target personal delivery, successful partial delivery, and unchanged
  strict exact-cardinality behavior.

**Verification:**
- [ ] `python -m pytest -q tests/test_orchestration.py tests/test_native_adapters.py tests/test_personal_mode.py tests/test_end_to_end_enrichment.py`
- Expected: replay-only non-fixture runs fail closed; personal partial output is
  explicit; strict mode still rejects incomplete admitted scope.

**Exit Criteria:** every non-fixture terminal state is capability-honest and
every personal completion state is backed by meaningful attempts and explicit
target/gap accounting.

## Task 2: Preserve Assurance, Gaps, and Canonical Evidence

**Purpose:** Stop structural validation, incomplete search, and stale evidence
from being promoted or ranked as stronger source-backed facts.

**Task Function:** evidence-state propagation

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: the canonical claim contract spans promotion, projection,
  scoring, and QA and must be changed coherently.

**Validator Profile:** Controller-selected: `none`
- Selection basis: focused contract tests cover the state transitions.

**Specification Coverage:** Findings 3, 4, and 5; outcome `Evidence and ranking integrity`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `scripts/promote_evidence.py:decision_assurance_level`,
  `_source_allowed`, and `promote_verified_claims`.
- Inspect/modify: `scripts/canonical_projection.py:project_verified_evidence`.
- Inspect/modify: `scripts/collect_buying_signals.py:account_research_state`.
- Inspect/modify: `scripts/score_leads.py:derive_account_signal`,
  `classify_signal`, and score-row construction.
- Inspect/modify: `scripts/qa_leads.py:main` and manifest-bound website evidence
  resolution.
- Verify: `tests/test_evidence_promotion.py`, `tests/test_canonical_projection.py`,
  `tests/test_buying_signals.py`, `tests/test_scoring.py`,
  `tests/test_selection.py`, `tests/test_contact_verification.py`.

**Dependencies:** Task 1 status and capability fields are available to all
downstream claim and account projections.

**Authority:**
- Preauthorized local actions: edit Task 2 files and tests; run focused evidence, scoring, and QA checks
- Stop for: any schema-breaking export change not covered by existing workbook and deliverable contracts

**Steps:**
- [ ] Step 1: Use systematic debugging to trace assurance and search-state
  values from verifier decisions through promotion, canonical projection,
  scoring, contacts, events, and workbook QA.
- [ ] Step 2: Keep `structural`, `source`, `replay`, and `unknown` assurance
  distinct; prevent structural-only decisions from acquiring `Verified` source
  semantics or source-backed rank weight.
- [ ] Step 3: Make incomplete, truncated, unconfigured, and failed buying-signal
  searches produce `Unknown`; reserve `None found` for a completed,
  account-scoped search with no matching event.
- [ ] Step 4: Make QA resolve the manifest-bound canonical evidence artifact and
  validate its hash, rather than preferring an older original website-evidence
  path after promotion.
- [ ] Step 5: Add focused regressions proving state preservation, ranking
  separation, `Unknown` semantics, and promoted-evidence QA consumption.

**Verification:**
- [ ] `python -m pytest -q tests/test_evidence_promotion.py tests/test_canonical_projection.py tests/test_buying_signals.py tests/test_scoring.py tests/test_selection.py tests/test_contact_verification.py tests/test_artifact_manifest_side_effects.py`
- Expected: no structural claim is source-verified, incomplete research is not
  `None found`, and QA reads the authoritative manifest-bound evidence.

**Exit Criteria:** every exported assurance and gap value can be traced to the
correct evidence state and no stale evidence path can silently override the
canonical projection.

## Task 3: Enforce One Finite Dispatch Budget

**Purpose:** Replace fixed, serialized, and retry-heavy lane behavior with a
bounded run policy that prioritizes material gaps and stops predictably.

**Task Function:** expected-value dispatch budgeting

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: coordinated retry, timeout, cancellation, and queue
  semantics without external service access.

**Validator Profile:** Controller-selected: `none`
- Selection basis: deterministic subprocess tests and local timing evidence
  are sufficient.

**Specification Coverage:** Finding 6; outcome `Bounded and restartable operations`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**
- Inspect/modify: `scripts/worker_dispatch.py:split_material_gap_queue`,
  `dispatch_native_lane`, `dispatch_fixture_lanes`, and
  `reconcile_lane_outputs`.
- Inspect/modify: `scripts/runtime_config.py:RuntimeConfig` and
  `provider_limitation`.
- Inspect/modify: `scripts/orchestrate_enrichment.py:write_lane_queue` and
  `_native_command_builder`.
- Verify: `tests/test_native_adapters.py`, `tests/test_orchestration.py`,
  `tests/test_provider_clients.py`, and `tests/test_personal_mode.py`.

**Dependencies:** Task 1 defines meaningful terminal states and Task 2 defines
which gaps are material and rank-affecting.

**Authority:**
- Preauthorized local actions: edit Task 3 files and tests; measure only local fixture or mocked execution; run the declared performance checks
- Stop for: live provider calls, quota changes, or unbounded concurrency changes

**Steps:**
- [ ] Step 1: Record a baseline with the existing mocked/fixture dispatch for
  wall-clock duration, subprocess attempts, timeout/cancellation count, and
  material-gap completion count using the focused test suite.
- [ ] Step 2: Add one run-level deadline, total attempt budget, and cancellation
  path in `RuntimeConfig`; derive lane limits from that shared budget instead of
  independent fixed reserves.
- [ ] Step 3: Order queues by expected ranking impact and evidence value; classify
  malformed input, schema mismatch, missing executable, and configuration
  failures as deterministic terminals that do not consume transient retries.
- [ ] Step 4: Keep transient retries bounded and scope/cache fingerprints
  mandatory for reuse; expose budget exhaustion as `Partial` or `Needs review`.
- [ ] Step 5: Add regression tests for deterministic no-retry behavior, budget
  exhaustion, cancellation, rank-aware gap ordering, and cache invalidation.

**Verification:**
- [ ] `python -m pytest -q tests/test_native_adapters.py tests/test_orchestration.py tests/test_provider_clients.py tests/test_personal_mode.py`
- [ ] `python -m pytest -q tests/test_native_adapters.py -k 'budget or retry or timeout or deterministic or cache'`
- Expected: identical mocked workloads remain correct, total attempts never
  exceed the configured budget, and measured wall-clock time is bounded by the
  configured deadline plus documented process-cleanup allowance.

**Exit Criteria:** one run-level budget controls dispatch, retries, and stopping;
the performance evidence records the same workload before and after and no
live-provider claim is made.

## Task 4: Preserve Historical Lineage and Authoritative QA

**Purpose:** Prevent a current projection from rewriting historical contact
baselines and ensure partial output is validated against the evidence actually
used to produce it.

**Task Function:** historical projection integrity

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: focused state/lineage change with direct workbook and QA
  side effects.

**Validator Profile:** Controller-selected: `none`
- Selection basis: manifest and projection regression tests provide independent
  proof.

**Specification Coverage:** Findings 5 and 7; outcomes `Evidence and ranking integrity` and `Revision-bound production evidence`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `scripts/canonical_projection.py:project_verified_evidence`.
- Inspect/modify: contact projection and export paths called from
  `scripts/orchestrate_enrichment.py:run_pipeline`.
- Inspect/modify: `scripts/qa_leads.py:main`.
- Verify: `tests/test_canonical_projection.py`, `tests/test_contact_verification.py`,
  `tests/test_artifact_manifest_side_effects.py`, and
  `tests/test_end_to_end_enrichment.py`.

**Dependencies:** Task 2 establishes canonical evidence and assurance fields.

**Authority:**
- Preauthorized local actions: edit Task 4 files and tests; run local workbook/manifest QA without publishing
- Stop for: destructive migration of existing historical evidence or changes to retained output files outside the run manifest

**Steps:**
- [ ] Step 1: Identify which contact fields are baseline facts, current-run
  claims, and verified historical observations.
- [ ] Step 2: Preserve existing baseline timestamps and provenance when a new
  projection has no newer verified contact claim; write current-run metadata
  only for observed or explicitly unknown claims.
- [ ] Step 3: Bind QA to the manifest-selected evidence path and hash, while
  retaining a clear error when a caller supplies a conflicting override.
- [ ] Step 4: Add regressions for two projection runs, unchanged historical
  contact baselines, promoted evidence, and conflicting QA overrides.

**Verification:**
- [ ] `python -m pytest -q tests/test_canonical_projection.py tests/test_contact_verification.py tests/test_artifact_manifest_side_effects.py tests/test_end_to_end_enrichment.py`
- Expected: historical contact evidence remains stable across a later run and
  QA rejects stale or conflicting evidence inputs.

**Exit Criteria:** projection is append-safe for historical contact lineage and
QA validates the exact evidence artifact bound by the manifest.

## Task 5: Separate Input Churn and Strengthen Production-Gate Evidence

**Purpose:** Make implementation cleanliness and campaign-data changes distinct
concerns, and make the checked-in blocked gate reproducible and internally
consistent.

**Task Function:** provenance and gate-evidence hardening

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: source, manifest, and checked-in evidence must remain aligned
  under one controller-owned change.

**Validator Profile:** Controller-selected: `none`
- Selection basis: direct manifest and gate regression tests are sufficient.

**Specification Coverage:** Findings 9 and 10; outcome `Revision-bound production evidence`.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect/modify: `scripts/orchestrate_enrichment.py:implementation_status`,
  `create_run_manifest`, and `verify_manifest`.
- Inspect/modify: `scripts/run_manifest.py:validate_manifest_revision`,
  `update`, and `recover_publication`.
- Inspect/modify: `scripts/validate_deliverables.py:main`.
- Inspect/modify: the production-gate generator or checked-in evidence writer
  that owns `evidence/manifests/production-gate-blocked-2026-11-08.json`.
- Verify: `tests/test_artifact_manifest_side_effects.py`,
  `tests/test_orchestration.py`, `tests/test_personal_mode.py`, and the gate
  JSON against `config/campaigns/berlin-hausverwaltung.json` and its input
  artifacts.

**Dependencies:** Tasks 1–4 define the states, canonical inputs, and output
hashes that the gate records.

**Authority:**
- Preauthorized local actions: edit Task 5 files, tests, and the canonical gate-evidence producer; refresh only the checked-in gate record owned by those changes
- Stop for: claiming a live production pass, deleting the durable blocker, or changing accepted campaign scope without explicit approval

**Steps:**
- [ ] Step 1: Trace how tracked implementation files and tracked campaign
  inputs enter `implementation_status`; classify each path as code/config,
  campaign input, generated runtime artifact, or preserved output.
- [ ] Step 2: Keep code/config dirtiness as the implementation barrier while
  recording campaign-input changes as manifest-bound input churn requiring a
  fresh run, not as an implementation defect.
- [ ] Step 3: Add full reachable revision, campaign-config hash, admitted-input
  hashes, supporting-input hashes, and output hashes to production-gate
  evidence.
- [ ] Step 4: Compute blocker counts from the actual blocker list and verify the
  checked-in record reports the same count and reasons.
- [ ] Step 5: Add regressions for input-only changes, code changes, stale
  revision, hash mismatch, and inconsistent blocker-count rejection.

**Verification:**
- [ ] `python -m pytest -q tests/test_artifact_manifest_side_effects.py tests/test_orchestration.py tests/test_personal_mode.py`
- [ ] `python scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/production-gate-blocked-2026-11-08.json --root .`
- Expected: input-only churn is explicit but not misclassified as dirty
  implementation; gate evidence is hash- and revision-bound; the historical
  blocker remains blocked for existing source-verification reasons.

**Exit Criteria:** the production gate is reproducible and honest, and no code
path silently treats a changed campaign CSV as a source-code cleanliness
failure.

## Task 6: Align the Maintained Lead-Generation Skill

**Purpose:** Make operational instructions describe the final lifecycle,
expected-value dispatch, fallback, and stop rules without duplicating schemas or
inventing a second source of truth.

**Task Function:** maintained skill contract alignment

**Template Profile:** Controller-selected: `none (lead controller)`
- Selection basis: documentation-only final alignment after implementation
  semantics are settled.

**Validator Profile:** Controller-selected: `none`
- Selection basis: direct inspection and command help are sufficient.

**Specification Coverage:** Findings 1, 2, 3, 4, 6, 7, 9, and 10; maintained operational guidance.

**Required Skills:** `skill-writing-skills`

**Files And Symbols:**
- Inspect/modify: `.agents/skills/lead-generation/SKILL.md`.
- Verify against: `scripts/orchestrate_enrichment.py`,
  `scripts/worker_dispatch.py`, `scripts/promote_evidence.py`,
  `scripts/canonical_projection.py`, `scripts/score_leads.py`,
  `scripts/qa_leads.py`, and tests completed in Tasks 1–5.

**Dependencies:** Tasks 1–5 complete; documentation must reflect actual
behavior rather than planned behavior.

**Authority:**
- Preauthorized local actions: edit the maintained skill source and run local inspection and help commands
- Stop for: editing generated `AGENTS.md` or copying schemas and policy text into the skill

**Steps:**
- [ ] Step 1: Update the operating loop to require capability-aware execution,
  material-gap expected value, finite budgets, truthful fallback states, and
  manifest-bound evidence.
- [ ] Step 2: State that TED-only coverage is a known limitation and external
  source expansion requires an approved policy change, not an ad-hoc workaround.
- [ ] Step 3: State exact stop conditions for replay, unavailable sources,
  budget exhaustion, strict barriers, and the durable production-gate blocker.
- [ ] Step 4: Confirm the skill references existing utilities and does not
  duplicate schemas, scoring rules, or export logic.

**Verification:**
- [ ] `python scripts/orchestrate_enrichment.py --help`
- [ ] `rg -n "replay|live|budget|Unknown|None found|strict|Partial|manifest|production gate|TED" .agents/skills/lead-generation/SKILL.md`
- Expected: the maintained skill contains the final operational contract and
  no generated surface was edited.

**Exit Criteria:** a user following `.agents/skills/lead-generation/SKILL.md`
cannot reasonably mistake replay for live research or treat fixture success as
production evidence.

## Verification

Final artifact-level verification, after Tasks 1–6:

- `python -m pytest -q`
- `python -m compileall -q scripts tests`
- `git diff --check`
- `python scripts/orchestrate_enrichment.py --help`
- `git status --short`

Expected: all tests pass, compilation and whitespace checks pass, CLI help is
available, and final status shows only declared plan/implementation changes. A
live-provider production probe is not part of this plan; its absence must remain
visible in durable gate evidence.

## Completion Criteria

The plan is ready for completion verification when:

1. replay, structural, source, unavailable, partial, and needs-review states
   remain distinct through manifest, projection, scoring, QA, and export;
2. personal mode cannot silently publish zero or under-target delivery, while
   strict mode retains exact admitted-scope barriers;
3. retries and dispatch stop under one configured deadline and attempt budget,
   with deterministic failures not retried;
4. assurance, search gaps, contact lineage, and canonical evidence are
   preserved and tested across repeated runs;
5. production-gate evidence records one consistent blocker count plus reachable
   revision, configuration, input, supporting-input, and output hashes;
6. campaign-input churn is distinguished from implementation dirtiness;
7. the maintained skill reflects the implemented contract without generated
   surface edits;
8. focused tests, full tests, compile, diff, CLI, and final workspace checks
   have fresh output recorded by `skill-verification-before-completion`;
9. the durable production blocker remains explicitly blocked unless a separate
   authorized live probe supplies provider-backed evidence.

The plan may be marked `completed` only after
`skill-verification-before-completion` returns `verified`. Push, pull request,
review-cycle, merge, and production-publication actions remain outside this
plan until separately authorized.
