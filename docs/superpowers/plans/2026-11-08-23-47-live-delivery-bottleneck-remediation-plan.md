---
layer: change
artifact_type: plan
status: active
template_id: implementation-plan
contract_version: "1"
name: live-delivery-bottleneck-remediation
targets:
  - scripts/orchestrate_enrichment.py
  - scripts/run_manifest.py
  - scripts/native_worker.py
  - scripts/runtime_config.py
  - scripts/native_verifier.py
  - scripts/promote_evidence.py
  - scripts/campaign_spec.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/select_for_enrichment.py
  - scripts/qa_leads.py
  - scripts/worker_dispatch.py
  - scripts/build_workbook.py
  - scripts/validate_deliverables.py
  - config/research_policy.json
  - config/lead_generation_schema.json
  - config/research_evidence_schema.json
  - tests
  - .gitignore
---

# Live Delivery Bottleneck Remediation Plan

## Goal

Make the personal lead-generation path practical and truthful for a Monday
delivery while preserving strict-mode safeguards. A run must distinguish
implementation cleanliness from generated runtime artifacts, distinguish replay
from live research, preserve structural versus source assurance, dispatch only
material gaps, recover from bounded failures, and expose research gaps in the
final workbook. No output may claim provider-backed verification without a
matching current-run record.

This is a follow-up to the completed personal-mode hardening plan. It addresses
the residual defects found at reviewed revision
`8b80ef3aa71364a142e4abc5aa53b1cc0ca36d06`, whose tree is equivalent to the
current local implementation head `68d4eaa9e3cd859639a4958b157e9362866fee5f`.

## Review Resolution

Both visible, commit-pinned review responses completed successfully in the same
repository-bound profile; no run was incomplete or ambiguous.

- `GPT-5.6-Sol`, `High`: run `run-EuwQZv`, conversation
  `6af0f6d6-5e9c-83eb-a8ad-6ac2b1decd60`, response
  `output/github-review/8b80ef3a-fragile-bottlenecks/run-EuwQZv/response.md`.
- `GPT-6`, `High`: run `run-ZfIeHa`, conversation
  `6af0f795-aadc-83eb-a93a-e245a49e5f01`, response
  `output/github-review/8b80ef3a-fragile-bottlenecks/run-ZfIeHa/response.md`.
- Review context: `longdang193-lead-generation-8b80ef3a-fragile-bottlenecks-review`.
- Publication: `no publication required`; the reviewed SHA was reachable from
  GitHub `origin/main`.
- Dedicated profile: `C:\Users\HOANG PHI LONG DANG\.codex\profiles\github-review\longdang193-lead-generation`.

The following findings are accepted only because both visible responses and the
checked-out source support them:

1. The manifest cleanliness gate can reject its own newly generated runtime
   artifacts (`scripts/orchestrate_enrichment.py:28`, `:67`, `:171`, `:325`;
   `.gitignore`).
2. The default production path is replay-only, while configuration presence can
   produce provider-exercised wording (`scripts/orchestrate_enrichment.py:358`,
   `:365`; `scripts/native_worker.py:110`; `scripts/runtime_config.py:81`).
3. Structural verification is promoted as `Verified` without a distinct source
   assurance level (`scripts/native_verifier.py:27`; `scripts/promote_evidence.py:171`).
4. Accepted reserve IDs and active dispatch IDs are not consistently separated;
   verifier work can cover accounts with no admitted work item
   (`scripts/orchestrate_enrichment.py:346`, `:387`, `:418`).
5. QA can validate broader or historical evidence than the promoted current
   projection (`scripts/canonical_projection.py:94`; `scripts/qa_leads.py:240`,
   `:314`).
6. Personal-mode `Probable` eligibility conflicts with scoring, selection, and
   QA rules that effectively require `Confirmed`
   (`scripts/canonical_projection.py:105`; `scripts/score_leads.py:137`;
   `scripts/select_for_enrichment.py:30`).
7. Dispatch is not material-gap-driven or resumable and retries are not
   failure-class aware (`scripts/worker_dispatch.py:53`, `:62`, `:83`).
8. External contact-source authorization is narrower than the declared research
   policy (`scripts/promote_evidence.py:67`; `config/research_policy.json:3`).
9. Workbook output omits research-gap and assurance state
   (`scripts/score_leads.py:152`; `scripts/build_workbook.py:108`).
10. Eligibility is only recomputed when absent, so a prior `false` can remain
    after qualifying evidence changes (`scripts/canonical_projection.py:105`).
11. The committed evidence manifest records revision
    `eda64e58f70584719e1b8fa264a2065cb245b1bf`, not the reviewed revision, so it
    cannot serve as proof for the reviewed run until revision binding is fixed.

Explicitly unverified and excluded from acceptance claims: provider latency,
cost, quotas, credential validity, TED/Hunter/Apify behavior, real-world contact
accuracy, production throughput, and any live provider call. The existing
production gate remains the source of truth at
`evidence/manifests/production-gate-blocked-2026-11-08.json:1` until a separate
bounded probe is explicitly authorized.

## Implementation Outcomes

### Truthful and restartable run lifecycle

Creating a manifest and writing run-owned evidence no longer makes a valid run
fail the implementation-cleanliness gate. Runtime artifacts remain bound to
the original revision and input hashes, while source/config/test changes still
block admission. Valid terminal lane outputs survive restart and are reused only
when their scope, hashes, schema, and payload are valid.

### Consistent personal-mode delivery

Admission, projection, scoring, selection, QA, and export consume one
qualification and assurance policy. Reserve backfill operates on active
dispatch scope, personal-mode uncertainty is explicit, and the final workbook
shows assurance, provider status, research gaps, and next action without
inventing facts.

### Verifiable evidence and revision binding

Replay, structural verification, and source verification remain separate
states. Provider-exercise summaries derive from manifest attempt evidence, not
credential presence. QA and deliverable validation reject stale or mismatched
revision/hash bundles before a list is described as current.

### Bounded operational proof

Fixture-backed tests prove the local behavior and strict-mode preservation. A
provider-backed live probe is a separate, explicitly authorized task and is not
treated as complete merely because the fixture path succeeds.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-plan-document-reviewer`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve untracked `output/github-review/` evidence and do not commit it
- Commit policy: `one lead-controlled checkpoint commit after final verification`; no push, merge, provider call, or publication without explicit approval
- Preauthorized local actions: edit listed source/config/test files, add deterministic fixtures, run repository-local checks, inspect generated artifacts, and update this plan’s task ledger
- User-approval actions: provider-backed research, credential changes, publication, push, merge, destructive cleanup, or changes outside listed targets
- Parallel ownership: none; shared manifest, campaign, projection, and QA contracts require serialization
- Sequential fallback: complete Tasks 1–7 in order, then run Task 8 fan-in verification; keep the live probe blocked until separately authorized

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/buying-signal-attribution`
- Base commit: `68d4eaa9e3cd859639a4958b157e9362866fee5f`
- Expected workspace: clean implementation tree with untracked `output/github-review/` preserved and excluded from commits
- Next action: commit the completed local remediation, then run fresh personal and strict fixture bundles from that clean revision
- Blockers: provider-backed live probe is not authorized; the local remediation work is otherwise dependency-ready

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `completed` | current | `none (lead controller)` | none | real-Git manifest lifecycle regression | 20 focused tests passed; runtime artifact lifecycle and source-dirty rejection covered |
| Task 2 | `completed` | current | `none (lead controller)` | Task 1 | replay/live and assurance contract tests | 46 affected tests passed; replay, provider wording, and assurance states covered |
| Task 3 | `completed` | current | `none (lead controller)` | Tasks 1–2 | active-scope and reserve-backfill fixture proof | focused orchestration/personal/selection/end-to-end tests passed; strict barriers preserved |
| Task 4 | `completed` | current | `none (lead controller)` | Task 3 | projection/scoring/selection/QA consistency proof | canonical qualification helper, stale eligibility, personal Probable behavior, and delivered-scope QA tests passed |
| Task 5 | `completed` | current | `none (lead controller)` | Tasks 2–4 | resumable gap-driven dispatch regression | material-gap queue filtering, scope/payload/hash validation, terminal reuse, deterministic failure, attempt history, and bounded retry tests passed |
| Task 6 | `completed` | current | `none (lead controller)` | Task 4 | claim-aware contact and workbook contract proof | external professional contact authorization, affiliation validation, assurance/provider/gap export tests passed |
| Task 7 | `completed` | current | `none (lead controller)` | Tasks 1–6 | stale-revision and hash rejection proof | shared revision validator, current-HEAD rejection, full bucket hash checks, verifier input binding, and stale-revision regression passed |
| Task 8 | `pending` | current | `unresolved` | Tasks 1–7 | full fixture verification and recorded live-probe gate | pending |

## Task Breakdown

### Task 1: Separate implementation cleanliness from runtime artifacts

**Purpose:** Make the normal `create` → `verify` → `run` manifest lifecycle
work in a real Git checkout without weakening source-change admission.

**Task Function:** root-cause debugging and repository-state contract repair

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** The defect is a small, high-risk shared invariant with a
real-Git-only failure mode; keep ownership with the lead controller.

**Specification Coverage:** P0 manifest self-block and restart safety.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:implementation_status`, `create_run_manifest`, `verify_manifest`, `run_pipeline`
- Inspect: `scripts/run_manifest.py:manifest_path`, `entry`, `update`
- Modify: `scripts/orchestrate_enrichment.py`, `scripts/run_manifest.py`, `.gitignore`
- Verify: `tests/test_artifact_manifest_side_effects.py`, `tests/test_orchestration.py`

**Dependencies:** Current source at base commit and the existing manifest/hash helpers.

**Authority:**
- Preauthorized local actions: edit manifest cleanliness and runtime-ignore code plus focused tests; run local Git-backed tests
- Stop for: any request to discard or rewrite existing evidence, alter the reviewed base, or broaden ignore rules beyond run-owned paths

**Steps:**
- [ ] Step 1: Reproduce create-then-verify in a temporary real Git repository and capture the exact dirty paths.
- [ ] Step 2: Define one narrow runtime-artifact classification covering generated manifests, candidate/verifier evidence, queues, and run-owned output while continuing to reject source/config/test changes.
- [ ] Step 3: Preserve `HEAD`, campaign hash, input hashes, and output hashes in the manifest; add a regression that an implementation edit still blocks admission.

**Verification:**
- [ ] `py -3 -m unittest tests.test_artifact_manifest_side_effects tests.test_orchestration -v`
- Expected: create-then-verify succeeds with only run-owned artifacts dirty; implementation edits still fail the cleanliness gate.

**Exit Criteria:** The lifecycle is restartable in a real Git checkout and no generated runtime path is silently treated as implementation source.

### Task 2: Make execution and assurance states truthful

**Purpose:** Prevent replay or structural checks from being reported as fresh
source-verified provider research.

**Task Function:** assurance-contract correction and failure-boundary verification

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** This changes a material backend contract and must remain serialized with promotion and manifest owners.

**Specification Coverage:** Replay/live separation, provider-exercise truth, and structural/source assurance.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/native_worker.py`, `scripts/runtime_config.py:provider_limitation`, `scripts/native_verifier.py`, `scripts/promote_evidence.py`
- Modify: `scripts/native_worker.py`, `scripts/runtime_config.py`, `scripts/native_verifier.py`, `scripts/promote_evidence.py`, and `config/research_evidence_schema.json`
- Verify: `tests/test_native_adapters.py`, `tests/test_evidence_promotion.py`, `tests/test_research_contract.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:** Task 1 manifest identity and run-owned artifact handling.

**Authority:**
- Preauthorized local actions: edit replay/live, verifier, promotion, and assurance schemas plus deterministic fixture tests
- Stop for: provider authentication, live network calls, or any change that makes replay data eligible for source-verified publication

**Steps:**
- [ ] Step 1: Require an explicit live adapter/capability when a run requests fresh research; label the built-in native path as replay-only.
- [ ] Step 2: Derive provider-exercise wording from manifest `research_runs` and attempt evidence, not from credential/configuration presence.
- [ ] Step 3: Preserve separate `assurance_level` values for replay, structural support, and source verification; reserve `Verified` for source-backed claims and preflight strict-mode capability requirements before dispatch.

**Verification:**
- [ ] Fixture promotion proves replay claims remain quarantined and structural claims cannot be labeled source-verified.
- [ ] QA/report fixtures show “configured” without an executed attempt does not become “exercised”.

**Exit Criteria:** Every promoted claim carries truthful execution and assurance provenance, and strict mode fails before dispatch when required capability is absent.

### Task 3: Align active dispatch scope and reserve backfill

**Purpose:** Research only admitted active accounts, verify only dispatched work,
and deterministically replace failed accounts from the reserve pool.

**Task Function:** orchestration scope repair and backfill integration

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** The failure crosses admission, queue construction, verifier scope, and personal-mode selection; it is not safe to split ownership.

**Specification Coverage:** Accepted-universe versus active-dispatch separation and personal reserve behavior.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/orchestrate_enrichment.py:run_pipeline`, `campaign_spec.py:admit_work_item`, `select_for_enrichment.py`
- Modify: `scripts/orchestrate_enrichment.py`, `scripts/campaign_spec.py`, `scripts/select_for_enrichment.py`
- Verify: `tests/test_orchestration.py`, `tests/test_personal_mode.py`, `tests/test_selection.py`

**Dependencies:** Tasks 1–2; the manifest must distinguish admitted IDs, active work items, and completed research.

**Authority:**
- Preauthorized local actions: edit queue admission, verifier scope, and deterministic reserve selection plus fixture tests
- Stop for: changing strict-mode exact-cardinality barriers or admitting candidates without the canonical qualification and domain checks

**Steps:**
- [x] Step 1: Record `accepted_company_ids`, `active_dispatch_ids`, and `delivered_ids` as separate manifest scopes.
- [x] Step 2: Build queues only for active IDs with material gaps; make verifier input equal the dispatched scope rather than the full accepted universe.
- [x] Step 3: On a failed or unavailable active item, select the next deterministic reserve candidate, record the replacement reason, and prevent duplicate research.

**Verification:**
- [x] A 35-candidate personal fixture with a 30-account delivery target verifies only dispatched IDs and replaces failed active records deterministically.
- [x] Strict fixture proof still rejects missing accepted IDs and cardinality drift.

**Exit Criteria:** Reserve backfill is conditional, auditable, and cannot cause verifier work for accounts with no admitted queue item.

### Task 4: Use one canonical qualification policy across projection, scoring, selection, and QA

**Purpose:** Remove contradictions around `Probable`, recompute eligibility after
evidence promotion, and prevent QA from validating the wrong evidence scope.

**Task Function:** shared policy extraction and cross-consumer contract repair

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** These consumers currently duplicate policy; a reusable helper is required by the project SSOT rule.

**Specification Coverage:** Personal/strict qualification, stale eligibility, and current-scope QA.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/select_for_enrichment.py`, `scripts/qa_leads.py`
- Modify: `scripts/campaign_spec.py`, `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/select_for_enrichment.py`, `scripts/qa_leads.py`, and `config/lead_generation_schema.json`
- Verify: `tests/test_canonical_projection.py`, `tests/test_scoring.py`, `tests/test_selection.py`, `tests/test_personal_mode.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:** Task 3 active/delivered scope fields and Task 2 assurance states.

**Authority:**
- Preauthorized local actions: create one reusable qualification/tiering helper and update its consumers and focused tests
- Stop for: adding a second policy source, silently converting `Probable` to `Confirmed`, or weakening strict mode

**Steps:**
- [x] Step 1: Define explicit personal and strict qualification transitions in one helper, including whether personal `Probable` rows are selectable and how their uncertainty is shown.
- [x] Step 2: Recompute `eligible` unconditionally from post-promotion canonical facts; do not preserve a stale `false` when the facts now qualify.
- [x] Step 3: Make scoring, selection, and QA call the same helper and scope delivery errors to delivered IDs while reporting broader dataset defects separately.

**Verification:**
- [ ] A promoted Berlin/WEG upgrade changes eligibility and selection deterministically.
- [ ] A historical or non-delivered record cannot block a fresh delivered scope when current promoted evidence is valid.

**Exit Criteria:** Admission, ranking, selection, QA, and export agree on the same policy and uncertainty remains visible.

### Task 5: Make dispatch gap-driven and resumable

**Purpose:** Avoid repeated work, classify failures correctly, and recover from
interruption without introducing a second scheduler.

**Task Function:** bounded worker recovery and attempt-ledger implementation

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** Existing bounded concurrency is adequate; the smallest safe change is to repair planning, reuse, and retry semantics in place.

**Specification Coverage:** Material-gap dispatch, terminal-output reuse, transient-only retry, and recovery visibility.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/worker_dispatch.py:dispatch_native_lane`, `dispatch_fixture_lanes`, `reconcile_lane_outputs`
- Modify: `scripts/worker_dispatch.py`, `scripts/orchestrate_enrichment.py`, and manifest attempt-record helpers
- Verify: add `tests/test_dispatch_recovery.py`; also run `tests/test_orchestration.py` and `tests/test_end_to_end_enrichment.py`

**Dependencies:** Tasks 2–4 define claim gaps, scope hashes, and assurance states.

**Authority:**
- Preauthorized local actions: edit existing bounded dispatch/reconciliation logic and add deterministic failure/restart fixtures
- Stop for: adding an unbounded scheduler, retrying deterministic failures, deleting valid terminal evidence, or making provider calls

**Steps:**
- [x] Step 1: Compute lane work from material claim gaps and omit already complete claims.
- [x] Step 2: Reuse a terminal output only after validating company ID, lane, run scope, input hash, payload schema, and output hash; never delete it before a replacement is validated.
- [x] Step 3: Persist each attempt and classify deterministic failures, transient provider failures, cancellation, and timeout; allow one bounded timeout retry and bounded retries only for classified transient failures.

**Verification:**
- [x] Restarting a fixture run reuses valid terminal output and dispatches only missing gaps.
- [x] Deterministic failure is attempted once; timeout and transient failure follow the declared bounded retry policy; the manifest records all attempts.

**Exit Criteria:** Repeated runs are cheaper and resumable, while failure states remain explicit and auditable.

### Task 6: Authorize contact evidence by claim and expose research gaps in export

**Purpose:** Allow legitimate public-professional contact evidence without broad
external-domain trust, and make research completeness visible in the workbook.

**Task Function:** claim-aware source policy and delivery projection

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** Contact authorization and workbook projection are independent consumers of the same claim-level evidence and can be repaired in one serialized task.

**Specification Coverage:** Contact-source authorization, affiliation checks, research-gap export, and assurance visibility.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`

**Files And Symbols:**
- Inspect: `scripts/promote_evidence.py:_source_allowed`, `config/research_policy.json`, `scripts/score_leads.py`, `scripts/build_workbook.py`
- Modify: `scripts/promote_evidence.py`, `config/research_policy.json`, `scripts/score_leads.py`, `scripts/build_workbook.py`, `config/lead_generation_schema.json`, and `config/research_evidence_schema.json`
- Verify: `tests/test_evidence_promotion.py`, `tests/test_contact_verification.py`, `tests/test_scoring.py`, `tests/test_end_to_end_enrichment.py`

**Dependencies:** Task 2 assurance contract and Task 4 canonical projection.

**Authority:**
- Preauthorized local actions: edit claim-aware authorization, affiliation validation, score projection, workbook columns, schemas, and focused tests
- Stop for: allowing arbitrary external domains, promoting a generic mailbox as a named owner, or inventing missing research facts

**Steps:**
- [x] Step 1: Add an explicit approved contact-source class and per-company alias/affiliation rules; retain source URL, source kind, person identity, and company binding.
- [x] Step 2: Project `assurance_level`, `provider_status`, `research_gap`, and `next_action` into the priority rows and workbook without changing deterministic structural scoring weights.
- [x] Step 3: Make workbook validation require these fields for delivered rows and allow explicit Unknown/Unavailable states for incomplete research.

**Verification:**
- [ ] An approved professional contact source promotes only when identity and company affiliation pass; an unrelated domain remains quarantined.
- [ ] Workbook rows distinguish fully checked, structurally supported, replay-only, and unavailable research.

**Exit Criteria:** Contact completeness improves without weakening domain trust, and the final deliverable exposes why each row is or is not ready.

### Task 7: Bind every evidence bundle to the exact source revision

**Purpose:** Prevent stale evidence, QA reports, workbooks, or decks from being
presented as proof for another commit.

**Task Function:** provenance validation and stale-artifact rejection

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** Revision and hash checks are a shared final gate and require one owner across manifest, QA, and deliverable validation.

**Specification Coverage:** Exact Git revision, complete manifest hash coverage, and current-run proof.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/run_manifest.py`, `scripts/qa_leads.py`, `scripts/validate_deliverables.py`, `scripts/build_workbook.py`
- Modify: `scripts/run_manifest.py`, `scripts/qa_leads.py`, `scripts/validate_deliverables.py`, `scripts/build_workbook.py`, `tests/test_artifact_manifest_side_effects.py`, `tests/test_end_to_end_enrichment.py`, and `tests/test_research_contract.py`; do not edit generated historical evidence as a substitute for validation
- Verify: `tests/test_artifact_manifest_side_effects.py`, `tests/test_end_to_end_enrichment.py`, `tests/test_research_contract.py`

**Dependencies:** Tasks 1–6 produce the fields and output graph that must be bound.

**Authority:**
- Preauthorized local actions: strengthen revision reachability, full-bundle hash, and source/output reconciliation checks plus regression fixtures
- Stop for: accepting `evidence/run_manifest_2026-11-09.json` for a different revision, bypassing hash failures, or rewriting historical evidence to make it pass

**Steps:**
- [x] Step 1: Require a full 40-character reachable Git revision and record it for every generated run bundle.
- [x] Step 2: Hash and validate all inputs, supporting inputs, outputs, QA artifacts, and workbook/deck references used by the final deliverable.
- [x] Step 3: Reject stale/mismatched bundles with an actionable error naming the expected and observed revision; keep older evidence explicitly historical.

**Verification:**
- [x] A fixture with a reachable prior revision is rejected when the current checkout is bound to a different HEAD; the regression names expected and observed revisions.
- [x] A fresh same-run bundle passes QA and deliverable validation with matching hashes.

**Exit Criteria:** No stale artifact can satisfy the current-run delivery gate.

### Task 8: Run final fixture proof and preserve the bounded live-probe gate

**Purpose:** Verify the integrated local behavior and document exactly what
remains unverified before any provider-backed execution.

**Task Function:** integration verification and operational handoff

**Template Profile:** Controller-selected: `none (lead controller)`

**Selection basis:** Final evidence must be produced by the lead controller after all shared contracts settle.

**Specification Coverage:** Monday-delivery readiness, strict-mode preservation, and explicit production limitation.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:** `scripts/orchestrate_enrichment.py`, `scripts/run_manifest.py`, `scripts/native_worker.py`, `scripts/runtime_config.py`, `scripts/native_verifier.py`, `scripts/promote_evidence.py`, `scripts/campaign_spec.py`, `scripts/canonical_projection.py`, `scripts/score_leads.py`, `scripts/select_for_enrichment.py`, `scripts/qa_leads.py`, `scripts/worker_dispatch.py`, `scripts/build_workbook.py`, `scripts/validate_deliverables.py`, and the focused tests; no new production source owner.

**Dependencies:** Tasks 1–7.

**Authority:**
- Preauthorized local actions: run fixture campaigns, full tests, schema/compile/diff checks, workbook/deliverable validation, and update evidence/plan status
- Stop for: provider-backed research, credential changes, external publication, a missing current-run revision, or any claim of production readiness without live evidence

**Steps:**
- [ ] Step 1: Run personal and strict fixture campaigns with reserve candidates, replay-only lanes, structural-only evidence, transient failure, timeout, valid external contact evidence, and a partial contact lane.
- [ ] Step 2: Verify deterministic selection, research-gap projection, assurance labels, manifest hashes, active/dispatched/delivered scope, and strict barriers.
- [ ] Step 3: Record the live-probe requirement and current blocker at `evidence/manifests/production-gate-blocked-2026-11-08.json:1`; do not execute the probe in this plan without separate authorization.

**Verification:**
- [ ] `py -3 -m unittest discover -s tests -p "test_*.py" -v`
- [ ] `py -3 -m compileall -q scripts tests`
- [ ] `git diff --check`
- [ ] `py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx --schema config/lead_generation_schema.json`
- [ ] `py -3 scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09-final.pptx --qa-report evidence/qa_report_2026-11-09.md --run-manifest evidence/run_manifest_2026-11-09.json --workbook-only`
- Expected: all local checks pass on a freshly generated, same-revision fixture bundle; production-backed success remains explicitly unverified.

**Exit Criteria:** Local implementation proof is fresh and complete, strict-mode protections remain intact, untracked review evidence is preserved, and the live-provider gate is recorded rather than overstated.

## Verification

Final artifact-level verification after Tasks 1–8:

```powershell
py -3 -m unittest discover -s tests -p "test_*.py" -v
py -3 -m compileall -q scripts tests
git diff --check
py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx --schema config/lead_generation_schema.json
py -3 scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09-reviewed.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09-final.pptx --qa-report evidence/qa_report_2026-11-09.md --run-manifest evidence/run_manifest_2026-11-09.json --workbook-only
git status --short
```

The final evidence must include fresh test output, the exact generated run
manifest revision, matching SHA-256 entries for the complete bundle, counts for
accepted/active/dispatched/delivered IDs, assurance and research-gap counts,
and the explicit production-gate limitation. Do not mark this plan completed
until `skill-verification-before-completion` returns `verified`.

## Completion Criteria

The plan is ready for completion verification when:

1. The create/verify/run lifecycle passes in a real Git checkout while source,
   config, and test modifications remain blocked.
2. Replay, structural, and source verification are distinct in promotion,
   projection, QA, and export; provider-exercise text is evidence-derived.
3. Active dispatch scope, reserve backfill, eligibility, scoring, selection, and
   QA use one canonical policy and no stale `eligible` value survives a changed
   evidence projection.
4. Dispatch is material-gap-driven, bounded, resumable, and failure-class aware.
5. Contact authorization is claim-aware and workbook rows expose assurance,
   provider status, research gap, and next action.
6. Every final artifact is bound to the exact reachable Git revision and full
   input/output hash set; mismatched historical evidence is rejected.
7. Focused regressions and the full local suite pass with fresh output.
8. No provider-backed production success, real-world contact accuracy, or
   throughput claim is made without the separately authorized live probe.

The plan remains `proposed` until explicitly approved for execution. During
execution it becomes `active`; only `skill-verification-before-completion` may
authorize the terminal `completed` status.
