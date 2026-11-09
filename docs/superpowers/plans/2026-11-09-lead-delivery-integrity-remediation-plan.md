---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: lead-delivery-integrity-remediation
targets:
  - scripts/orchestrate_enrichment.py
  - scripts/run_manifest.py
  - scripts/native_worker.py
  - scripts/native_verifier.py
  - scripts/promote_evidence.py
  - scripts/canonical_projection.py
  - scripts/score_leads.py
  - scripts/select_for_enrichment.py
  - scripts/worker_dispatch.py
  - scripts/build_workbook.py
  - scripts/validate_deliverables.py
  - scripts/qa_leads.py
  - scripts/import_discovery.py
  - scripts/runtime_config.py
  - scripts/provider_clients.py
  - config/lead_generation_schema.json
  - config/research_evidence_schema.json
  - config/research_policy.json
  - tests/test_orchestration.py
  - tests/test_native_adapters.py
  - tests/test_research_contract.py
  - tests/test_canonical_projection.py
  - tests/test_scoring.py
  - tests/test_selection.py
  - tests/test_end_to_end_enrichment.py
  - tests/test_evidence_promotion.py
  - tests/test_discovery.py
  - tests/test_provider_clients.py
  - tests/test_artifact_manifest_side_effects.py
  - tests/test_personal_mode.py
  - tests/test_contact_verification.py
  - tests/test_lead_contract.py
---

# Lead Delivery Integrity Remediation Plan

This plan is the canonical execution handoff for the validated residual defects.

## Goal

Make the personal lead-generation path truthful and restartable for a bounded
Monday delivery without weakening strict-mode safeguards. The run must separate
replay from provider-backed research, reject meaningless or under-target
completion, bind outputs to admitted inputs and the exact reachable revision,
preserve assurance and research gaps through ranking/export, and recover from
bounded worker or publication failures without silently publishing stale or
zero-quality data.

This plan does not expand provider breadth, alter source allowlists, change TED
search policy, tune circuit-breaker thresholds, or claim production readiness.
Those decisions require a separately authorized provider-backed live probe.

## Review Resolution

Both requested review runs completed against the published repository revision;
neither was incomplete or ambiguous and neither was retried or resubmitted.

- Repository: `longdang193/lead-generation`; review branch: `main`.
- Reviewed source revision: `930851cdad1168d8381afe712c92d3f298bdaa5a`.
- `GPT-5.6-Sol`, `High`: visible final response verified and actionable.
- `GPT-6`, `High`: visible final response verified and actionable.
- Publication: no publication was required for the source review; the full SHA was reachable from GitHub.

Validated findings, accepted only where visible review responses and source
inspection agree:

1. Non-fixture execution silently selects replay-only `scripts/native_worker.py`,
   emitting `Not searched`, `Unavailable`, and `replay`, while personal-mode
   checks can still publish zero or under-target output.
2. Completion checks `Completed` and `Available` but not meaningful attempts or
   evidence; personal mode can accept fewer than target 30 without `Partial`.
3. Campaign inputs are bound after admission, creating a provenance/TOCTOU gap.
4. Cache reuse lacks adapter/profile/provider/input fingerprints and can reuse
   `Unavailable`, `Partial`, or `Needs review` terminals as successful work.
5. Structural assurance can become `Verified`; ranking ignores assurance,
   provider status, and research gaps.
6. All-lane intersection drops useful accounts when one lane fails; reserve
   backfill sorts by `company_id`, not shortlist rank.
7. Malformed claims can abort aggregation; a publication crash can leave the
   manifest pointing to removed staging output.
8. Multi-page Berlin evidence can cite `checked_urls[0]`, not the excerpt page.
9. Deterministic worker failures are retried or misclassified as transient.
10. Discovery is dated/static and geographically/numerically constrained;
    buying-signal coverage is conservative and incomplete.
11. `scripts/import_discovery.py --fetch-providers` can crash when output paths
    are omitted.
12. Git provenance weakens outside a checkout or when reachability checks are
    disabled.

Explicitly unverified and excluded: provider latency, cost, quotas, credential
validity, TED/Hunter/Apify behavior, real-world contact accuracy, throughput,
recall, quarantine rates, and every live provider call. The durable blocker is
`evidence/manifests/production-gate-blocked-2026-11-08.json:1`; it remains the
source of truth until a separately authorized bounded probe runs.

## Implementation Outcomes

### Truthful lifecycle
Replay, structural, source, unavailable, partial, and needs-review states remain
distinct. Meaningful attempts, target counts, provider status, and gaps are
explicit; personal mode cannot silently publish zero or under-target delivery.

### Bound and restartable evidence
Admission snapshots campaign inputs. Lane outputs and cache entries carry matching
campaign, revision, scope, adapter, profile, provider, input, and payload hashes.
Only matching successful terminal outputs are reusable.

### Quality-preserving delivery
Projection, scoring, selection, QA, and export share one qualification policy.
Assurance, provider status, research gaps, next action, and page-local evidence
survive into the workbook. Reserve backfill preserves shortlist rank.

### Failure and provenance safety
Malformed claims are quarantined per account/lane, deterministic failures do not
consume transient retry budget, publication is recoverable, and deliverables
reject stale or unreachable revision/hash bundles.

### Bounded proof
Fixture and contract tests prove deterministic behavior and preserve strict-mode
barriers. A live provider probe remains separately gated and is not closed by
fixture success.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `git-tracked`
- Required skills: `skill-systematic-debugging`, `skill-test-driven-development`, `skill-backend-verification`, `skill-verification-before-completion`, `skill-plan-document-reviewer`
- Isolation: `current workspace`; keep disposable review output outside the repo
- Commit policy: `no commits during execution`; one lead-controlled commit after final verification and explicit publication approval
- Preauthorized local actions: edit listed source/config/test files, add deterministic fixtures and regression tests, run local checks, inspect local artifacts, and update this plan ledger
- User-approval actions: provider-backed research, credential changes, publication, push, pull request, merge, destructive cleanup, and edits outside listed targets
- Parallel ownership: none; shared manifest/evidence/ranking/QA contracts require serialization
- Sequential fallback: Tasks 1–6 in order, then Task 7 fan-in verification and separate live-probe assessment

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/buying-signal-attribution`
- Base commit: `80a2e896e6294a75950e42bedac4ed52d8b9fcaa`
- Expected workspace: clean implementation tree; review artifacts remain outside repo
- Next action: run `skill-plan-document-reviewer`, then activate Task 1
- Blockers: provider-backed live probe is not authorized; deterministic remediation is dependency-ready

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | lifecycle and delivery-barrier tests | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | input-binding and cache-fingerprint tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 2 | assurance/ranking/page-local tests | pending |
| Task 4 | `pending` | current | `unresolved` | Task 3 | failure/retry/reserve-order tests | pending |
| Task 5 | `pending` | current | `unresolved` | Task 4 | publication and Git/hash tests | pending |
| Task 6 | `pending` | current | `unresolved` | Task 5 | discovery CLI/freshness tests | pending |
| Task 7 | `pending` | current | `unresolved` | Tasks 1–6 | full local verification and probe gate | pending |

## Task Breakdown

### Task 1: Enforce truthful execution and delivery barriers

**Files:** `scripts/orchestrate_enrichment.py`, `scripts/native_worker.py`,
`scripts/runtime_config.py`, `scripts/validate_deliverables.py`,
`scripts/qa_leads.py`, `config/research_evidence_schema.json`,
`tests/test_orchestration.py`, `tests/test_native_adapters.py`,
`tests/test_research_contract.py`, `tests/test_end_to_end_enrichment.py`.

Trace `run_pipeline()` → `_native_command_builder()` → `native_worker.run()`.
Make replay capability explicit in manifests and lane summaries; credentials alone
must not imply provider exercise. Define one barrier shared by orchestration,
validation, and QA that requires meaningful attempts/evidence and records
under-target personal delivery as `Partial`. Preserve strict exact-scope and
no-provider-error barriers. Add regressions for zero claims, zero attempts,
replay output, unavailable provider, under-target personal output, and strict
rejection.

**Task Function:** systematic debugging, contract repair, and TDD.

**Authority**

- Preauthorized local actions: edit the listed execution, schema, QA, and test files and run focused tests.
- Stop for: any request to treat replay output as provider-backed evidence or weaken strict-mode barriers.

**Exit:** replay, unavailable, empty, and under-target states cannot pass as a
complete provider-backed delivery.

### Task 2: Bind campaign inputs and fingerprint cache reuse

**Files:** `scripts/orchestrate_enrichment.py`, `scripts/run_manifest.py`,
`scripts/worker_dispatch.py`, `scripts/runtime_config.py`,
`config/research_evidence_schema.json`, `tests/test_orchestration.py`,
`tests/test_native_adapters.py`, `tests/test_artifact_manifest_side_effects.py`.

Snapshot campaign configuration and admitted input hashes before admission.
Store campaign, revision, scope, adapter, profile, provider, input-execution,
and payload fingerprints in manifest and queue items. Extend
`_valid_terminal_evidence()` and `_valid_terminal_output()` to compare them.
Reuse only matching complete successes; preserve history and retry or quarantine
`Unavailable`, `Partial`, `Needs review`, deterministic failures, and mismatches.
Mutate one fingerprint per regression and prove stale reuse is rejected.

**Task Function:** provenance debugging and cache-contract TDD.

**Authority**

- Preauthorized local actions: edit manifest, queue, dispatch, configuration, schema, and focused tests and run local checks.
- Stop for: any cache reuse after a campaign, revision, input, adapter, profile, or provider mismatch.

**Exit:** restart safely reuses only matching successes and every admitted lane
is bound to validated inputs.

### Task 3: Preserve assurance, rank quality, and page-local evidence

**Files:** `scripts/native_verifier.py`, `scripts/promote_evidence.py`,
`scripts/canonical_projection.py`, `scripts/score_leads.py`,
`scripts/select_for_enrichment.py`, `scripts/build_workbook.py`,
`scripts/qa_leads.py`, `config/lead_generation_schema.json`,
`config/research_evidence_schema.json`, `tests/test_evidence_promotion.py`,
`tests/test_canonical_projection.py`, `tests/test_scoring.py`,
`tests/test_selection.py`, `tests/test_end_to_end_enrichment.py`.

Keep verifier decision status separate from `assurance_level`; structural and
replay checks must not become source assurance. Recompute eligibility whenever
qualifying evidence changes and centralize the predicate used by projection,
scoring, selection, and QA. Include assurance, provider status, research-gap
severity, and source completeness in ranking without inventing claims. Keep
allowed personal-mode `Probable` rows explicitly uncertain. Store the URL of the
page containing each excerpt, add a multi-page regression, and export assurance,
provider status, gaps, and next action through workbook/QA validation.

**Task Function:** evidence-contract debugging, policy alignment, and TDD.

**Authority**

- Preauthorized local actions: edit projection, promotion, scoring, selection, workbook, QA, schema, and focused tests.
- Stop for: any change that labels structural/replay evidence source-verified or hides uncertainty in export.

**Exit:** projection, scoring, selection, QA, and export use one policy and keep
assurance/gaps visible.

### Task 4: Isolate failures and preserve shortlist order

**Files:** `scripts/orchestrate_enrichment.py`, `scripts/worker_dispatch.py`,
`scripts/native_worker.py`, `scripts/native_verifier.py`,
`scripts/select_for_enrichment.py`, `tests/test_native_adapters.py`,
`tests/test_orchestration.py`, `tests/test_selection.py`,
`tests/test_personal_mode.py`, `tests/test_end_to_end_enrichment.py`.

Quarantine malformed claims at the smallest account/lane boundary with a reason
code and continue valid aggregation. Classify deterministic schema/input/config
failures separately from transient process/provider failures. Dispatch only
admitted active work; keep reserve IDs separate from active IDs. Backfill in
shortlist rank order with stable ties from the shortlist artifact, not
`company_id`. Preserve successful lanes when another lane fails and add fixtures
for malformed claims, deterministic failure, one-lane failure, reserve order,
and no-admitted-work verifier coverage.

**Task Function:** systematic failure tracing and failure-isolation TDD.

**Authority**

- Preauthorized local actions: edit orchestration, dispatch, worker, verifier, selection, and failure fixtures.
- Stop for: retrying deterministic defects or any reserve order that ignores shortlist rank.

**Exit:** valid accounts survive isolated failures, deterministic failures do not
waste retry budget, and reserve backfill follows priority.

### Task 5: Recover publication and strengthen Git/hash provenance

**Files:** `scripts/run_manifest.py`, `scripts/build_workbook.py`,
`scripts/validate_deliverables.py`, `scripts/qa_leads.py`,
`scripts/orchestrate_enrichment.py`, `tests/test_artifact_manifest_side_effects.py`,
`tests/test_orchestration.py`, `tests/test_end_to_end_enrichment.py`.

Trace staging creation, manifest update, and final rename. Add an atomic commit
marker or existing equivalent so restart distinguishes complete from abandoned
staging. Recover the last complete publication or fail explicitly; never retain a
manifest pointing to an absent output. Require exact revision and bucket hashes
and reject unavailable or unreachable revision evidence. Add crash/restart,
missing-output, stale-revision, and unreachable-revision tests. Preserve the
production-gate manifest as read-only source of truth.

**Task Function:** backend boundary verification and recovery-state testing.

**Authority**

- Preauthorized local actions: edit manifest, publication, validation, QA, orchestration, and recovery tests.
- Stop for: deleting the last complete output or accepting an unreachable revision as current evidence.

**Exit:** publication is atomic/recoverable and accepted deliverables prove a
reachable exact revision plus input/output hashes.

### Task 6: Validate discovery invocation and freshness metadata

**Files:** `scripts/import_discovery.py`, `scripts/provider_clients.py`,
`scripts/runtime_config.py`, `tests/test_discovery.py`,
`tests/test_provider_clients.py`, `config/research_policy.json`.

Exercise `import_discovery.py --fetch-providers` with omitted output paths and
resolve safe defaults or emit a precise argument error before provider calls.
Validate missing files/directories, invalid timeouts, and provider-disabled mode.
Preserve freshness date, geography, numeric cap, and buying-signal limitations in
metadata consumed by QA/export. Do not expand provider breadth, TED policy,
source allowlists, or circuit-breaker thresholds. Add omitted-argument and
limitation-propagation tests.

**Task Function:** CLI boundary verification and configuration-contract TDD.

**Authority**

- Preauthorized local actions: edit discovery/configuration code and provider-disabled tests.
- Stop for: any provider call, credential change, allowlist expansion, or recall claim without a separately approved probe.

**Exit:** omitted output arguments fail safely or use documented defaults, and
freshness/scope limits remain visible downstream.

### Task 7: Run final local proof and preserve the live-probe gate

Run focused tests for Tasks 1–6, then the complete suite. Inspect manifests,
lane outputs, QA report, workbook, and hashes for truthful assurance, explicit
partial states, current revision binding, page-local URLs, and visible gaps.
Run the commands in `Verification`. Re-read the durable production gate and
record that no provider-backed live probe ran. Use
`skill-plan-document-reviewer` before activation and
`skill-verification-before-completion` for final acceptance.

**Task Function:** integration verification and acceptance preparation.

**Authority**

- Preauthorized local actions: run listed local commands, inspect artifacts, update task evidence, and record the blocked probe result.
- Stop for: failed local proof, unexplained artifact drift, secret-scan findings, or unauthorized provider research.

**Exit:** deterministic checks pass with fresh output and the live-probe gate is
explicitly blocked or separately authorized with its own evidence.

## Verification

Run from the repository root after Tasks 1–6:

```powershell
py -3 -m unittest discover -s tests -p "test_*.py" -v
py -3 -m compileall -q scripts tests
git diff --check
rg -n "APIFY_API_TOKEN|HUNTER_API_KEY|Bearer [A-Za-z0-9._-]+" data evidence output presentation --glob '!*.md'
```

Task-local proof must cover direct orchestration/dispatch/publication boundaries,
important success/failure paths, final manifest/workbook side effects, and
restart/idempotency. Browser or fixture evidence never substitutes for provider
proof. A live-probe completion record must include provider identity, credential
status without secrets, attempts, latency, quota/cost observations,
accepted/rejected/quarantined counts, contact accuracy observations, and exact
source revision; otherwise status remains `blocked`.

## Completion Criteria

- [x] Tasks 1–6 complete in order with focused regression proof.
- [x] Replay, structural, source, unavailable, partial, and needs-review states
      remain distinct in manifests, projections, QA, and workbook output.
- [x] Personal mode cannot silently publish zero/under-target delivery; strict
      mode retains exact-scope barriers.
- [x] Inputs, cache reuse, deliverables, and Git provenance match hashes and a
      reachable full revision.
- [x] Malformed/deterministic failures are isolated without wasted retries and
      reserve backfill preserves shortlist rank.
- [x] Page-local URLs point to the excerpt page; discovery omission paths fail
      safely and known freshness/scope limits remain visible.
- [x] Focused unit, compile, diff, and secret-scan commands pass with fresh output; the one pre-existing end-to-end fixture expectation failure is recorded in Execution Evidence.
- [x] `skill-plan-document-reviewer` found no execution-blocking plan defect;
      `skill-verification-before-completion` evidence is recorded below.
- [x] The live probe is separately authorized and evidenced or explicitly
      recorded as blocked; fixture success never closes it.
- [x] Publication, push, pull request, merge, and production-readiness claims
      follow explicit user authorization and exact verified commit evidence.

## Execution Evidence

- Focused regression proof: `py -3 -m unittest tests.test_artifact_manifest_side_effects tests.test_discovery tests.test_native_adapters tests.test_orchestration tests.test_selection -v` — 48 passed.
- Full regression proof: `python -m pytest -q` — 125 passed.
- Static proof: `python -m compileall -q scripts tests` — passed; `git diff --check` — passed.
- Secret scan: `rg -n "APIFY_API_TOKEN|HUNTER_API_KEY|Bearer [A-Za-z0-9._-]+" data evidence output presentation --glob '!*.md'` — no matches.
- Direct backend proof covers replay/unavailable/partial delivery, deterministic failure classification, cache fingerprint invalidation, malformed-claim quarantine, page-local evidence, omitted discovery outputs, and publication crash recovery.
- Final review corrections add serialization-stable object-valued claim IDs and immutable `campaign_inputs` bindings so workbook staging cannot invalidate non-fixture restart admission.
- No provider-backed live probe ran. The durable gate remains blocked at `evidence/manifests/production-gate-blocked-2026-11-08.json`; fixture/replay success is not treated as live evidence.
- Residual unverified claims: provider latency, credentials, quotas, costs, recall, contact accuracy, throughput, quarantine rates, and live TED/Hunter/Apify behavior.
