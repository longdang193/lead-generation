---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: personal-mode-lead-generation-hardening
targets:
  - scripts/campaign_spec.py
  - scripts/orchestrate_enrichment.py
  - scripts/select_for_enrichment.py
  - scripts/native_worker.py
  - scripts/native_verifier.py
  - scripts/promote_evidence.py
  - scripts/worker_dispatch.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/qa_leads.py
  - config/campaigns/berlin-hausverwaltung.json
  - config/research_evidence_schema.json
  - .agents/skills/lead-generation/SKILL.md
  - tests
---

# Personal-Mode Lead Generation Hardening

## Goal

Make the lead-generation harness usable for a personal Monday, November 9,
2026 delivery without weakening the existing strict evidence and audit path.
The default personal path must produce the best available leads from a reserve
pool, research only material evidence gaps, preserve provenance, expose
`Verified`, `Supported`, `Needs review`, `Unknown`, `Partial`, and `Unavailable`
states, and never fabricate evidence. Strict mode must retain exact
reproducibility, source-verification, complete-scope, and publication barriers.

The plan is based on the source-validated review of
`df05fde4d4d3f99fd346a8b411ac330089495047` and the supplied executive verdict.
The two browser reviews agreed on the verifier deadlock, canonical-admission
mismatch, replay-worker false completion, narrow source policy, serial/no-retry
dispatch, and repeated-claim projection failure. The source audit additionally
confirmed the missing `eligible` qualification field, event-envelope mismatch,
QA scope mismatch, scoring-methodology mismatch, and manifest cleanliness
conflict.

## Implementation Outcomes

### Personal delivery mode

The controller exposes an explicit personal delivery policy while preserving a
strict policy. Personal mode treats the campaign target as a goal, backfills
from a deterministic reserve pool, allows partial research, and does not block
export on missing optional facts. Strict mode keeps the current exact-set and
barrier behavior.

### Truthful evidence and source authorization

Replay outputs cannot claim completed live research. Promotion authorizes
sources by claim/source class, accepts explicitly verified company aliases and
approved external sources, and rejects or quarantines only the affected claim
when personal mode permits partial output. Production source-verification
requirements remain enforced in strict mode.

### Recoverable enrichment and projection

Workers are dispatched from material evidence gaps, reuse valid terminal
outputs, retry bounded transient failures, and preserve partial/unavailable
states. Event envelopes are normalized at adapter ingress, repeatable evidence
records are retained, and scalar projection remains deterministic.

### Consistent ranking, QA, and harness guidance

Qualification, eligibility, scoring, QA, and export consume one canonical
manifest-bound projection. Unknown handling matches the published methodology.
The repository gains a top-level `lead-generation` skill describing evidence
inspection, tool selection, gap prioritization, stop rules, worker dispatch,
and final ranked export. The skill does not replace the deterministic evidence,
scoring, or export utilities.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-code-standards`, `skill-writing-plans`, `skill-verification-before-completion`
- Isolation: `current workspace`; preserve the untracked `output/github-review/` artifacts and do not include them in commits
- Commit policy: `no commits during execution`; the lead creates one reviewed implementation commit only after final verification
- Preauthorized local actions: edit the listed source, config, skill, and test files; add focused fixtures; run repository-local tests, schema checks, compile checks, and diff checks
- User-approval actions: provider-backed research, credential changes, destructive data replacement, publication, push, merge, or changes outside the listed surfaces
- Parallel ownership: none; `campaign_spec.py`, `orchestrate_enrichment.py`, and the manifest contract are shared owners and require serialization
- Sequential fallback: complete Tasks 1–4 in order, then Tasks 5–7 in order, then run the fan-in verification in Task 8

## Task Breakdown

### Task 1: Reproduce and lock the current production blockers

**Purpose:** Create focused regression proof for the source-validated failure
conditions before changing behavior.

**Task Function:** debugging and contract characterization

**Template Profile:** unresolved

**Specification Coverage:** admission mismatch, missing `eligible`, verifier
capability deadlock, replay false completion, source-policy mismatch, event
envelope mismatch, repeated claims, serial dispatch, QA scope, scoring
methodology, and manifest cleanliness.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`

**Files And Symbols:**

- `tests/test_orchestration.py`: `OrchestrationTests`
- `tests/test_native_adapters.py`: `NativeAdapterTests`
- `tests/test_evidence_promotion.py`: `EvidencePromotionTests`
- `tests/test_buying_signals.py`: `BuyingSignalTests`
- `tests/test_canonical_projection.py`: `CanonicalProjectionTests`
- `tests/test_scoring.py`: `ScoringTests`
- `tests/test_artifact_manifest_side_effects.py`: manifest and QA side effects
- `scripts/orchestrate_enrichment.py`, `scripts/select_for_enrichment.py`, and
  the pinned campaign/data fixtures

**Dependencies:** none

**Authority:**

- Preauthorized local actions: add or extend deterministic fixtures and tests
  that reproduce only the listed failures; run focused tests and inspect source
  and committed data.
- Stop for: any test that requires external provider credentials, a production
  run, deletion of committed data, or a behavioral decision not stated in this
  plan.

**Steps:**

1. Add a fixture with a 30-row shortlist whose canonical location evidence
   disagrees with the priority surface and assert the current strict gate
   rejects it.
2. Add a selector fixture whose qualification records omit `eligible` and
   assert the current contract does not silently infer eligibility.
3. Add tests proving that a non-fixture structural verifier cannot cross the
   source-verification promotion gate, and that a replay worker cannot claim a
   live completed search.
4. Add fixtures for an approved external source, an alias domain, a wrapped
   buying-events payload, two valid events for one company, one failed lane
   item, and an unrelated non-shortlist QA row.
5. Record the exact current failure messages in test names and assertions so
   later changes cannot hide the original root causes.

**Verification:**

```powershell
py -3 -m unittest tests.test_orchestration tests.test_native_adapters tests.test_evidence_promotion tests.test_buying_signals tests.test_canonical_projection tests.test_scoring tests.test_artifact_manifest_side_effects -v
```

**Exit Criteria:** Every confirmed finding has a reproducible focused test or
an explicit data-contract assertion, and no test performs provider-backed work.

### Task 2: Add a personal/strict delivery policy and one canonical admission surface

**Purpose:** Stop exact cardinality and divergent qualification surfaces from
blocking the strongest available leads while retaining strict audit behavior.

**Task Function:** contract and controller design

**Template Profile:** unresolved

**Specification Coverage:** personal mode, reserve-pool backfill, canonical
qualification, missing eligibility, exact cardinality as a strict-only rule,
and manifest-bound inputs.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**

- `scripts/campaign_spec.py`: campaign normalization and qualification contract
- `scripts/orchestrate_enrichment.py`: `create_run_manifest`, `run_pipeline`,
  `write_lane_queue`, and `validate_final_priority_rows`
- `scripts/select_for_enrichment.py`: `eligible_for_enrichment`,
  `select_accounts`, and shortlist audit output
- `scripts/run_manifest.py`: manifest policy and input binding helpers
- `config/campaigns/berlin-hausverwaltung.json`: logical input bindings and
  default personal policy
- `tests/test_campaign_spec.py`, `tests/test_orchestration.py`, and a new
  `tests/test_personal_mode.py`

**Dependencies:** Task 1

**Authority:**

- Preauthorized local actions: add the explicit personal/strict policy field,
  canonical qualification projection, reserve-pool audit, and focused tests in
  the listed files.
- Stop for: weakening strict-mode checks, changing the target definition for
  strict campaigns, or introducing a second manifest/lineage registry.

**Steps:**

1. Add one normalized policy enum, `personal` or `strict`, to the campaign/run
   contract and persist it in the manifest; default the Berlin personal-use
   campaign to `personal` while keeping strict behavior opt-in and explicit.
2. Make qualification projection emit `eligible` from the trusted canonical
   qualification predicate before selection. Keep `resolution_status`, city,
   service, residential/WEG, location, and trusted-domain evidence in the same
   manifest-bound record.
3. Change personal selection to accept a candidate pool larger than the target,
   write selected and reserve audit records, and backfill from deterministic
   reserve candidates when a selected account is unresolved or unavailable.
   Never backfill by weakening identity or source provenance requirements.
4. Make `run_pipeline` consume that projected qualification artifact instead of
   separately reconstructing location admission from the older normalized CSV.
5. Keep exact shortlist length, exact accepted-ID equality, and exact final-ID
   equality unchanged under strict mode.
6. Add tests for a 30-target campaign that selects the best available 30 from a
   larger pool, a partial result with fewer than 30 defensible candidates, and
   strict mode rejecting the same incomplete set.

**Verification:**

```powershell
py -3 -m unittest tests.test_campaign_spec tests.test_orchestration tests.test_personal_mode -v
```

**Exit Criteria:** Personal mode has one canonical qualification/eligibility
input, deterministic reserve backfill, explicit partial output behavior, and
strict mode remains fail-closed with the original exact-set semantics.

### Task 3: Separate replay, live research, and verification assurance

**Purpose:** Prevent local replay from becoming false negative research and
remove the impossible production verifier capability contract.

**Task Function:** backend contract and adapter implementation

**Template Profile:** unresolved

**Specification Coverage:** truthful research states, risk-based verification,
strict source-verification preservation, and no fabricated evidence.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**

- `scripts/native_worker.py`: `run` and `ResearchRun` construction
- `scripts/native_verifier.py`: adapter capability declaration and decisions
- `scripts/orchestrate_enrichment.py`: worker/verifier registration and
  preflight capability checks
- `scripts/promote_evidence.py`: production capability gate and promotion
- `config/research_evidence_schema.json`: research and assurance states
- `tests/test_native_adapters.py`, `tests/test_evidence_promotion.py`, and
  `tests/test_research_contract.py`

**Dependencies:** Task 2

**Authority:**

- Preauthorized local actions: add explicit adapter capability/state fields,
  preflight validation, personal-mode partial handling, and regression tests in
  the listed files.
- Stop for: claiming live provider access without an approved provider
  boundary, changing credentials, or replacing strict source verification with
  a renamed structural check.

**Steps:**

1. Model `replay`, `live_research`, `structural_validation`, and
   `source_verification` as distinct capabilities; do not infer one from a
   successful subprocess exit code.
2. Make the native replay worker emit `Not searched` or `Needs review` when it
   has no bounded provider attempt, set provider status to `Unknown` or
   `Unavailable` as appropriate, and retain replay provenance.
3. Derive the required verifier capability from the campaign policy. In strict
   mode, fail during preflight before dispatch if no actual source-verifying
   adapter is configured. In personal mode, permit structural verification only
   for claims whose policy explicitly allows it and label the assurance level
   in the output.
4. Keep promotion fail-closed for strict source-verification campaigns and
   preserve the existing hash, run, company, and verifier-registration checks.
5. Add schema tests proving empty replay cannot become `None found / Searched`
   and that capability relabeling alone cannot pass strict promotion.

**Verification:**

```powershell
py -3 -m unittest tests.test_native_adapters tests.test_evidence_promotion tests.test_research_contract -v
```

**Exit Criteria:** Personal output is truthful about replay and incomplete
research; strict output still requires a real source-verification capability;
no path promotes claims solely because a local adapter exited successfully.

### Task 4: Make source authorization claim-aware and preserve partial evidence

**Purpose:** Accept legitimate external evidence without weakening company-fact
trust boundaries or making one rejected claim abort an entire promotion.

**Task Function:** evidence-policy implementation

**Template Profile:** unresolved

**Specification Coverage:** source-class policy, verified aliases, supported
evidence, per-claim quarantine, and provenance.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**

- `scripts/promote_evidence.py`: `_source_allowed`, claim validation, and
  promotion result handling
- `scripts/orchestrate_enrichment.py`: `source_policy` construction
- `scripts/lead_contract.py`: claim/source status constants if present
- `config/campaigns/berlin-hausverwaltung.json`: source classes and aliases
- `tests/test_evidence_promotion.py` and `tests/test_campaign_spec.py`

**Dependencies:** Task 3

**Authority:**

- Preauthorized local actions: add source classes, company aliases, policy
  validation, per-claim rejection/quarantine, and focused tests in the listed
  files.
- Stop for: allowing arbitrary domains, suppressing source URLs/excerpts, or
  changing strict-mode authorization without a matching contract test.

**Steps:**

1. Define source classes for official company facts, approved procurement or
   public-signal sources, professional contact sources, and external
   corroboration.
2. Bind each claim type to an allowed source class; retain exact trusted-domain
   checks for official company facts.
3. Add explicit verified domain aliases per company and normalize redirects and
   `www` variants without accepting arbitrary lookalike domains.
4. In personal mode, keep rejected claims in an audit/quarantine surface and
   continue promotion for independent valid claims. In strict mode, preserve
   fail-closed promotion when policy is violated.
5. Test the current STRABAG/parent-domain, alias-domain, TED/public-source,
   arbitrary-domain, and mixed-validity claim cases.

**Verification:**

```powershell
py -3 -m unittest tests.test_evidence_promotion tests.test_campaign_spec -v
```

**Exit Criteria:** Legitimate external evidence is accepted only through an
   explicit source class and account relationship; invalid claims cannot poison
   personal-mode valid output or bypass strict mode.

### Task 5: Normalize event inputs and support repeatable evidence

**Purpose:** Ensure valid buying events, contacts, and multiple claims survive
adapter ingestion and canonical projection.

**Task Function:** data-contract and projection implementation

**Template Profile:** unresolved

**Specification Coverage:** event-envelope normalization, 0..N evidence, scalar
projection, and deterministic event/contact export.

**Required Skills:** `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**

- `scripts/native_worker.py`: event payload normalization and signal claims
- `scripts/canonical_projection.py`: duplicate detection and scalar/repeatable
  projection
- `scripts/score_leads.py`: event/signal consumption
- `config/research_evidence_schema.json`
- `tests/test_native_adapters.py`, `tests/test_canonical_projection.py`, and
  `tests/test_buying_signals.py`

**Dependencies:** Task 3

**Authority:**

- Preauthorized local actions: normalize supported event envelopes, change
  repeatable-claim identity, update deterministic projection, and add focused
  tests in the listed files.
- Stop for: dropping event IDs, publication dates, source URLs, or evidence
  excerpts, or changing scalar ranking semantics without a scoring test.

**Steps:**

1. Normalize list payloads and `{items: [...]}` / `{events: [...]}` envelopes at
   the native-worker boundary and validate matched event IDs before claim
   construction.
2. Emit an explicit unresolved event state when a verified link cannot find a
   complete event; never manufacture a strong signal with missing publication
   evidence.
3. Replace the global `(company_id, claim_type)` uniqueness check with stable
   claim/event identity for repeatable types. Keep scalar conflicts explicit and
   deterministic.
4. Preserve 0..N events and contacts in canonical outputs while selecting a
   deterministic scalar value only where downstream sheets require one.
5. Add regression cases for two valid events, two contacts, duplicate event IDs,
   missing event IDs, and the committed wrapped event file.

**Verification:**

```powershell
py -3 -m unittest tests.test_native_adapters tests.test_canonical_projection tests.test_buying_signals -v
```

**Exit Criteria:** The committed event envelope produces valid claims, multiple
valid repeatable facts do not abort projection, and incomplete event matches are
visible as unresolved rather than fabricated strong evidence.

### Task 6: Make dispatch gap-driven, partial, and resumable

**Purpose:** Reduce operational overhead and prevent one unavailable worker from
discarding usable leads.

**Task Function:** execution reliability implementation

**Template Profile:** unresolved

**Specification Coverage:** evidence-gap dispatch, bounded concurrency,
transient retries, terminal-result reuse, partial lanes, and explicit gaps.

**Required Skills:** `skill-test-driven-development`, `skill-backend-verification`, `skill-performance-optimization`

**Files And Symbols:**

- `scripts/worker_dispatch.py`: `NativeExecutorConfig`,
  `dispatch_native_lane`, `reconcile_lane_outputs`
- `scripts/orchestrate_enrichment.py`: lane construction and worker result
  reconciliation
- `scripts/native_worker.py`: lane-specific missing-fact handling
- `tests/test_native_adapters.py`, `tests/test_end_to_end_enrichment.py`, and
  a new `tests/test_dispatch_recovery.py`

**Dependencies:** Tasks 2, 3, and 5

**Authority:**

- Preauthorized local actions: add bounded worker pooling, retry classification,
  terminal-output reuse, gap planning, partial reconciliation, and tests in the
  listed files; run local timing comparisons only on fixture workloads.
- Stop for: introducing an unbounded scheduler, making external provider calls,
  or changing concurrency defaults without a deterministic correctness test.

**Steps:**

1. Add a gap planner that compares canonical evidence to required facts and
   emits only missing material work items; skip already verified facts and low
   value optional fields unless requested.
2. Add a small configurable worker pool with a conservative default of `3` and
   preserve per-company/per-lane ordering in the manifest.
3. Retry only classified transient failures, with at most two attempts by
   default; do not retry schema, scope, hash, or policy failures.
4. Reuse an existing output only when run ID, lane, company, scope version,
   scope hash, output hash, and payload validation all match.
5. Reconcile failed items as `Partial` or `Unavailable` in personal mode and
   continue independent companies. Keep strict mode all-or-nothing.
6. Add fixture tests proving a late failure does not erase successful results
   and a restart does not repeat valid work.

**Verification:**

```powershell
py -3 -m unittest tests.test_native_adapters tests.test_end_to_end_enrichment tests.test_dispatch_recovery -v
```

**Exit Criteria:** Personal mode completes usable independent work despite
partial failures, reruns reuse valid outputs, retries are bounded, and strict
mode remains all-or-nothing.

### Task 7: Align scoring, QA, configuration, and harness guidance

**Purpose:** Remove misleading contracts and teach the parent agent how to run
the system without forcing every optional research field through every lane.

**Task Function:** consumer, documentation, and skill integration

**Template Profile:** unresolved

**Specification Coverage:** scoring semantics, QA scope, logical inputs,
top-level agent guidance, tool selection, stop rules, and Monday output.

**Required Skills:** `skill-code-standards`, `skill-test-driven-development`, `skill-backend-verification`

**Files And Symbols:**

- `scripts/score_leads.py`: `calculate_fit` and audit fields
- `scripts/build_workbook.py`: methodology sheet and export status
- `scripts/qa_leads.py`: admitted-scope QA and evidence source selection
- `config/campaigns/berlin-hausverwaltung.json`: logical rather than
  date-specific input bindings and removal/implementation of unused profile
  fields
- `.agents/skills/lead-generation/SKILL.md`: new top-level harness skill
- `tests/test_scoring.py`, `tests/test_artifact_manifest_side_effects.py`,
  `tests/test_end_to_end_enrichment.py`

**Dependencies:** Tasks 2, 4, 5, and 6

**Authority:**

- Preauthorized local actions: align scoring/methodology, scope QA to the
  delivery contract, add the top-level skill, and update focused tests/docs in
  the listed files.
- Stop for: editing generated agent adapters without locating their canonical
  source, removing strict audit features, or adding provider-specific secrets
  or tool integrations.

**Steps:**

1. Choose and document one scoring rule: either normalize fit by observed
   weight while keeping evidence coverage separate, or revise the methodology
   to state the fixed denominator. Update `score_leads.py`, workbook
   methodology, and tests together.
2. Make delivery QA validate the admitted/backfilled set and promoted evidence
   as the publication gate; report broader source-dataset problems separately
   without silently hiding them.
3. Replace date-specific campaign bindings with logical artifact roles while
   retaining immutable run-manifest hashes for the concrete files used by a
   run.
4. Remove `scoring_profile`, `export_profile`, and `qa_profile` only if the
   baseline search confirms they remain unused; otherwise connect them to the
   actual owning validators. Add a config-contract test either way.
5. Add `.agents/skills/lead-generation/SKILL.md` with the expected-value
   research rule, tool/source selection, gap prioritization, fallback behavior,
   stop conditions, personal/strict mode choice, and final workbook contract.
6. Keep the skill descriptive and reusable; it must direct the agent to the
   existing account, evidence, contact, scoring, and export utilities rather
   than duplicate their schemas.

**Verification:**

```powershell
py -3 -m unittest tests.test_scoring tests.test_artifact_manifest_side_effects tests.test_end_to_end_enrichment -v
```

**Exit Criteria:** Published scoring semantics match implementation, QA gates
the intended delivery scope, campaign config contains no false flexibility, and
the new skill teaches the complete mission without introducing a second source
of truth.

### Task 8: Run the Monday delivery proof and strict-mode regression proof

**Purpose:** Prove the personal path end-to-end on deterministic fixtures and
prove that strict protections remain intact before any external run is
considered.

**Task Function:** integration verification and handoff

**Template Profile:** unresolved

**Specification Coverage:** final delivery contract, provenance, partial-state
visibility, strict-mode preservation, and rollback readiness.

**Required Skills:** `skill-backend-verification`, `skill-verification-before-completion`

**Files And Symbols:** all changed files from Tasks 1–7; no new production
source owner.

**Dependencies:** Tasks 1–7

**Authority:**

- Preauthorized local actions: run fixture integration tests, schema validation,
  compile checks, diff checks, and inspect generated workbook/report outputs.
- Stop for: provider-backed production execution, credential changes, failing
  strict-mode proof, missing provenance, or any requirement to publish a lead
  list without a human-approved external run.

**Steps:**

1. Run the personal fixture campaign with a reserve pool containing more than
   30 candidates, at least one partial lane, one external approved source, and
   multiple buying events.
2. Verify the output contains approximately 30 best defensible leads, explicit
   evidence provenance, explicit research gaps, deterministic rank order, and a
   usable workbook.
3. Run strict fixture regressions for exact cardinality, accepted-ID equality,
   source policy, verifier capability, manifest hashes, complete lane
   reconciliation, and publication barriers.
4. Validate every emitted `ResearchRun`, claim, promoted record, score, QA
   report, and workbook against the canonical schemas and hashes.
5. Run the full repository suite and inspect the final changed-file list,
   generated surfaces, untracked artifacts, and diff for scope drift.

**Verification:**

```powershell
py -3 -m unittest discover -s tests -p "test_*.py" -v
py -3 -m compileall -q scripts tests
git diff --check
git status --short
```

**Exit Criteria:** Personal fixture delivery and strict regression proof both
pass; no provider-backed production run is claimed without fresh external
evidence; the plan has a verified implementation result or records the exact
remaining blocker.

## Completion Criteria

- Personal mode produces a deterministic best-available shortlist from a
  reserve pool and does not require every lane or optional field to succeed.
- Strict mode retains exact cardinality, source-verification, clean/revision,
  hash, complete-scope, and publication barriers.
- No replay output is represented as completed live research.
- Source authorization is claim-aware, alias-aware, auditable, and fail-closed
  for strict mode.
- Partial and unavailable research remains visible and cannot fabricate claims.
- Event envelopes, repeated claims, scalar projection, scoring, QA, and export
  have aligned contracts and focused regression proof.
- The top-level `lead-generation` skill points to existing canonical utilities
  and provides tool-selection, gap-prioritization, fallback, and stop guidance.
- Full tests, compile checks, diff checks, and fresh fixture backend evidence
  pass; the production provider-backed run remains explicitly unverified until
  separately authorized and executed.

## Completion Evidence

- Verification result: `verified` on branch `codex/buying-signal-attribution` at implementation head `335d4a03a2f5e178de8461820d8b30082e95f832`.
- Publication: PR `#7` merged into `main` as `e4beb99783896ed367a6215be03f1c759bbbad65`; the implementation head is reachable from `origin/main`.
- Fresh proof: `94` repository tests passed; `py -3 -m compileall -q scripts tests` passed; `git diff --check` passed.
- Final review: review cycle `2/2` found duplicate fallback contacts; the fix and focused regression were committed before merge. Replay quarantine, claim-aware source authorization, contact isolation, and personal undersized-pool behavior remain covered.
- Approved deferral: provider-backed production execution remains intentionally unrun and recorded at `evidence/manifests/production-gate-blocked-2026-11-08.json:1`; no production success is claimed.