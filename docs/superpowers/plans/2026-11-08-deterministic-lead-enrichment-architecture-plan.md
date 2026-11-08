---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
contract_version: "1"
name: deterministic-lead-enrichment-architecture
targets:
  - config/lead_generation_schema.json
  - config/research_evidence_schema.json
  - config/research_policy.json
  - config/signal_taxonomy.json
  - scripts/lead_contract.py
  - scripts/import_discovery.py
  - scripts/normalize_dedupe.py
  - scripts/extract_website_evidence.py
  - scripts/collect_buying_signals.py
  - scripts/provider_clients.py
  - scripts/select_for_enrichment.py
  - scripts/promote_evidence.py
  - scripts/orchestrate_enrichment.py
  - scripts/score_leads.py
  - scripts/build_shortlist.py
  - scripts/qa_leads.py
  - scripts/validate_deliverables.py
  - scripts/validate_workbook.py
  - agents/
  - .agents/skills/
  - tests/
  - evidence/candidate/
  - evidence/verified/
  - evidence/research_runs/
  - evidence/manifests/
---

# Deterministic Lead Enrichment Architecture Plan

## Goal

Extend the completed PR #2 remediation into a production-ready enrichment
workflow for Berlin Hausverwaltung leads. The implementation must produce
high-quality, verified, traceable leads with complete P0/P1 data, account-level
buying signals, deterministic priority ordering, and auditable evidence.

The architecture boundary is fixed:

> Research agents gather candidate evidence. A verifier judges evidence.
> Deterministic Python promotes facts, calculates scores, ranks leads, writes
> canonical outputs, and enforces QA.

Agents must never resolve company identity, assign final scores, set `Pursue`,
mutate canonical CSV/workbook rows, or initiate outreach.

## Approved Decisions And Constraints

- Preserve the structural weights from the existing plan: service fit 35%,
  residential/WEG relevance 30%, portfolio potential 25%, and geographic or
  operational fit 10%.
- Keep eligibility, structural fit, confirmed fit, portfolio potential, buying
  signal, evidence coverage, actionability, and sales priority as separate
  fields. Do not replace them with one opaque score.
- Treat `Unknown`, `None found`, `Unavailable`, `Partial`, and `Needs review`
  as distinct states. `None found` is allowed only after completed,
  account-scoped research with zero usable results.
- Use only trusted company domains for account research. A directory,
  search-result, navigation, or unrelated host cannot become the canonical
  company domain.
- Keep raw provider data, candidate evidence, verified evidence, canonical
  projections, and generated deliverables as separate layers.
- Keep the existing CSV/workbook consumers compatible unless a schema change
  is explicitly migrated and covered by tests.
- Contact research runs after provisional P0 shortlist selection. Contact
  availability must not change structural fit or shortlist membership.
- A generic published mailbox is useful outreach data but is not a named
  decision-maker. A named owner requires independent proof of person, company
  affiliation, exact role, role relevance, and person-email ownership.
- Public professional sources only; collect the minimum data needed for sales
  qualification; record retrieval dates; do not send email or publish data.
- Preserve the untracked visualization candidate
  `lead-generation-architecture.json`; it is not a canonical implementation
  input and must not be edited by this plan.

## Consolidated Review Basis

The following findings were validated by both visible architecture reviews and
the checked-out source/output evidence:

1. `scripts/collect_buying_signals.py` performs global TED searches and then
   derives one search status for the event dataset, so `None found` is not an
   account-level conclusion.
2. `scripts/normalize_dedupe.py` can derive a canonical host from an
   untrusted discovery URL when a verified company domain is absent.
3. Fuzzy same-postcode candidates can enter review while still being admitted
   as accepted canonical companies, breaking the promotion barrier.
4. Evidence validation does not consistently enforce exact equality between a
   canonical claim, its evidence claim, and the page-local excerpt; portfolio
   evidence lacks equivalent claim-level gating.
5. Contact validation can classify a plausible-looking phrase as a person;
   capitalization and word count are not proof of a verified decision-maker.
6. The direct JSON-Schema `const` evaluator defect is correctness debt and must
   be fixed with a regression test while QA is extended; it is not described as
   a proven current data-corruption blocker without a live dependent clause.
7. Manifest, revision, and hash checks already introduced by PR #2 must remain
   enforced for every input, supporting input, verified evidence set, and
   output in the new multi-stage run.

## Implementation Outcomes

### Deterministic accepted-company universe

`import_discovery.py` and `normalize_dedupe.py` preserve provider provenance,
use only trusted domains for identity, quarantine ambiguous identities, and
emit an accepted Berlin/Hausverwaltung company universe that no research lane
can bypass.

### Linked evidence and research-run model

The repository has one versioned contract for `Company`, qualification claims,
`ResearchRun`, events/signals, contacts, candidate evidence, and verified
evidence. Every material claim carries company identity, source URL, excerpt,
retrieval time, scope, confidence, and verification state.

### Account-scoped bounded research

Signal, portfolio, and contact research receive only accepted company records
and write immutable candidate files under separate lane directories. Buying
signals are linked to the correct company and dated source; portfolio values
retain units and scope; contacts are person-first and official-source-bound.

### Evidence promotion and deterministic prioritization

The verifier and deterministic promotion barrier accept only evidence that
supports the exact claim. Scoring, actionability, `Pursue` decisions, ranking,
and canonical writes are reproducible and independent of agent completion
order or contact availability.

### Traceable deliverables and QA

Research runs, candidate/verified evidence, canonical CSVs, workbook, deck,
QA report, and manifest reconcile by run ID, commit revision, and SHA-256.
The final gate fails on schema drift, unsupported claims, unresolved identity,
unverified signals, weak contact proof, stale/missing evidence, or hash drift.

## Execution Approach

- Mode: `parallel-capable`
- Coordination: `git-tracked`
- Required skills: `skill-code-standards`, `skill-test-driven-development`,
  `skill-backend-verification`, `skill-dispatching-parallel-agents`,
  `skill-verification-before-completion`
- Isolation: `current workspace`; use isolated worktrees only for genuinely
  concurrent implementation lanes with disjoint write ownership
- Commit policy: `no commits during execution` unless a later approved
  execution plan explicitly authorizes per-task checkpoints
- Preauthorized local actions: edit the listed plan targets, add focused tests
  and fixtures, regenerate task-owned local evidence under the declared run
  directory, and run declared local verification commands
- User-approval actions: provider spend, external publication, email sending,
  Git push, PR creation, merge, destructive cleanup, and changes to unrelated
  files
- Parallel ownership: research contracts and worker-output adapters may be
  developed in disjoint files; canonical promotion, ranking, QA, and generated
  outputs are serialized by the lead controller
- Sequential fallback: complete Tasks 1–4, then run signal and portfolio lanes
  in parallel; run contact research only after Task 5 produces a shortlist;
  finish with serialized promotion, QA, and deliverable validation

## Coordination State

- Coordination owner: `single lead controller`
- Coordination schema: `2`
- Branch: `codex/lead-quality-remediation`
- Base commit: `1581c8862dca33c54479a570067c32c2f0feb4be`
- Expected workspace: `preserve the untracked lead-generation-architecture.json; no other uncommitted changes`
- Next action: `Task 1 — establish the research evidence contract and policy SSOT`
- Blockers: `none`

| Task | State | Workspace | Executor | Depends On | Required Proof | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 | `pending` | current | `unresolved` | none | contract/unit tests and JSON validation | pending |
| Task 2 | `pending` | current | `unresolved` | Task 1 | discovery and identity regression tests | pending |
| Task 3 | `pending` | current | `unresolved` | Task 1, Task 2 | page-local claim and promotion tests | pending |
| Task 4 | `pending` | current | `unresolved` | Task 1, Task 2 | queue/run-manifest tests | pending |
| Task 5 | `pending` | isolated lane or current | `unresolved` | Task 3, Task 4 | account-scoped signal/portfolio fixtures | pending |
| Task 6 | `pending` | isolated lane or current | `unresolved` | Task 3, Task 4, Task 5 | contact verification fixtures | pending |
| Task 7 | `pending` | current | `unresolved` | Task 3, Task 5, Task 6 | promotion, score, and ranking tests | pending |
| Task 8 | `pending` | current | `unresolved` | Task 7 | full QA, manifest, workbook, and deliverable validation | pending |

## Task Breakdown

### Task 1: Establish the evidence and research-run contract

**Purpose:**
- Define one shared contract for candidate evidence, verified evidence,
  research runs, events, portfolio claims, contacts, statuses, and provenance.

**Task Function:**
- Create the SSOT contract and policy surface consumed by deterministic code
  and all research roles.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: low ambiguity, cross-cutting contract risk, and required
  authority to keep schema and implementation aligned.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused unit tests provide the independent contract proof.

**Specification Coverage:**
- Linked five-object model: Company, QualificationClaim, ResearchRun, Event or
  Signal, and Contact.
- Immutable candidate evidence and verified evidence states.
- Unknown versus None found semantics, source policy, privacy minimization,
  and manifest provenance.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Inspect: `scripts/lead_contract.py:is_unknown`,
  `scripts/lead_contract.py:update_run_manifest`, and current schema enums.
- Modify: `config/lead_generation_schema.json`, add
  `config/research_evidence_schema.json`, add `config/research_policy.json`,
  add `config/signal_taxonomy.json`, and extend `scripts/lead_contract.py`.
- Add tests: `tests/test_research_contract.py` and extend
  `tests/test_lead_contract.py`.

**Dependencies:**
- None.

**Authority:**
- Preauthorized local actions: edit only the Task 1 config/helpers/tests and
  preserve current output enum compatibility through explicit projections.
- Stop for: any request to change provider credentials, publish data, or alter
  unrelated canonical outputs.

**Steps:**
- [ ] Define `EvidenceClaim` fields: `company_id`, `claim_type`, `claim_value`,
  `unit`, `scope`, `source_url`, `source_domain`, `source_kind`,
  `evidence_excerpt`, `retrieved_at`, `published_at`, `account_relationship`,
  `confidence`, `research_run_id`, and `candidate_status`.
- [ ] Define `ResearchRun` fields: `run_id`, `company_id`, `research_type`,
  `source`, `scope`, `status`, `started_at`, `completed_at`, `result_count`,
  `truncated`, `provider_status`, and `error_code`.
- [ ] Define explicit statuses: research `Not searched`, `Completed`,
  `Partial`, `Unavailable`, `Needs review`; claim `Candidate`, `Verified`,
  `Rejected`, `Needs review`; and signal output `Strong`, `Medium`, `Weak`,
  `None found`, `Unknown`.
- [ ] Add `research_policy.json` rules for allowed source kinds, official-domain
  binding, minimum evidence fields, retention fields, freshness, and lane caps.
- [ ] Add `signal_taxonomy.json` mappings for portfolio expansion,
  modernization, digitization, metering/heating-cost projects, supplier change,
  relevant hiring, and procurement events.
- [ ] Add shared validators for claim completeness, trusted source URLs,
  publication-date validity, exact company binding, person-role binding, and
  `None found` eligibility.
- [ ] Fix direct JSON-Schema `const` matching and add a regression test without
  changing existing `not: {const: ...}` semantics.

**Verification:**
- [ ] `py -3 -m unittest tests.test_lead_contract tests.test_research_contract -v`
- [ ] `py -3 -m json.tool config/lead_generation_schema.json`
- [ ] `py -3 -m json.tool config/research_evidence_schema.json`
- Expected: all contract tests pass; direct `const` matches; missing source,
  excerpt, date, unit, or company binding is rejected.

**Exit Criteria:**
- One importable contract/helper surface defines all cross-lane statuses and
  evidence requirements without duplicated enum definitions.

### Task 2: Harden discovery, domain trust, and the accepted company universe

**Purpose:**
- Prevent false merges, untrusted domains, synthetic Berlin fallbacks, and
  unresolved identities from entering any research queue or score input.

**Task Function:**
- Make identity resolution a deterministic promotion barrier that preserves raw
  records and quarantines ambiguity.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: source-authoritative P0 behavior with existing tests and
  backend/provider boundary coverage.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: deterministic fixtures and provider-client tests cover the
  accepted and rejected paths.

**Specification Coverage:**
- Berlin discovery, deduplication, normalization, domain trust,
  Hausverwaltung eligibility, and source traceability.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`,
  `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/import_discovery.py:read_rows`,
  `scripts/import_discovery.py:refresh_identity`,
  `scripts/normalize_dedupe.py:domain`, `clean_name`, `company_id`, and `main`.
- Modify: `scripts/import_discovery.py`, `scripts/normalize_dedupe.py`,
  `scripts/provider_clients.py`, `tests/test_discovery.py`,
  `tests/test_normalization.py`, and add fixtures under `tests/fixtures/`.
- Verify: `data/intermediate/discovery_quarantine_2026-11-08.csv`,
  `data/intermediate/companies_normalized_2026-11-07.csv`, and
  `evidence/entity_resolution_2026-11-07.csv` after regeneration.

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: modify only discovery, identity-resolution,
  provider normalization, and their tests/fixtures; regenerate local
  discovery evidence without external publication.
- Stop for: paid provider use, credential changes, destructive replacement of
  raw snapshots, or an identity rule that cannot preserve review provenance.

**Steps:**
- [ ] Preserve legal name, aliases, address, postal code, city, region,
  website, contact fields, source IDs, source type, actor/run IDs, extraction
  method, and retrieval time from CSV and JSON providers.
- [ ] Store `discovery_source_url` separately from `verified_company_domain`;
  derive the latter only from an explicitly trusted official or permitted
  directory record that passes identity corroboration.
- [ ] Resolve candidates in deterministic order: verified domain plus identity,
  exact legal name and postcode, exact address, then fuzzy name/location.
- [ ] Set `requires_review = True` for every fuzzy, same-host,
  missing-postcode, shared-office, branch/parent, and conflicting-identity row.
- [ ] Exclude every `requires_review` or `resolution_status != Accepted` row from
  the accepted company universe while retaining its raw row and reason.
- [ ] Keep missing location fields Unknown; never synthesize Berlin from a
  missing city, region, or postcode.
- [ ] Require positive company-level evidence for Berlin and Hausverwaltung or
  WEG eligibility before queue admission.

**Verification:**
- [ ] `py -3 -m unittest tests.test_discovery tests.test_normalization -v`
- [ ] Assert a search-result host cannot become `verified_company_domain`.
- [ ] Assert same-domain companies, fuzzy matches, and navigation-title rows are
  quarantined and never appear in accepted queue input.
- Expected: accepted rows are uniquely identified, Berlin/Hausverwaltung
  eligible, and traceable to preserved raw provider records.

**Exit Criteria:**
- A generated accepted-company file is the only legal input to all later lanes;
  every rejected or ambiguous identity has a durable review record.

### Task 3: Build claim-level website evidence and deterministic promotion barriers

**Purpose:**
- Convert official-site retrieval into page-local, claim-bound evidence that can
  be independently verified before it affects qualification or ranking.

**Task Function:**
- Separate retrieval and candidate extraction from evidence verification and
  canonical promotion.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: high correctness risk at the evidence boundary; controller
  retains ownership of promotion semantics.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: precision-oriented evidence validation is distinct from
  researcher recall and should use a stronger verifier profile at execution.

**Specification Coverage:**
- Evidence URLs, Berlin/WEG/service qualification, portfolio claim binding,
  source ownership, excerpt traceability, and verified versus review states.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`,
  `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/extract_website_evidence.py:fetch`, `process`, and `main`.
- Add: `scripts/promote_evidence.py` with `load_candidates`, `verify_claim`,
  `promote_verified_claims`, and `main`.
- Modify: `scripts/extract_website_evidence.py`, `scripts/lead_contract.py`,
  `scripts/qa_leads.py`, `tests/test_lead_contract.py`, and add
  `tests/test_evidence_promotion.py`.
- Add generated roots: `evidence/candidate/website/` and
  `evidence/verified/website/`.

**Dependencies:**
- Task 1 and Task 2 complete.

**Authority:**
- Preauthorized local actions: add claim-level evidence extraction,
  verification, and tests; write only task-owned candidate/verified evidence.
- Stop for: any evidence rule that accepts combined-page text without a
  page-local excerpt or permits a source URL outside trusted company scope.

**Steps:**
- [ ] Traverse the bounded page set including discovered contact, service,
  portfolio, team, management, and legal pages rather than only the initial
  page slice.
- [ ] Emit one candidate claim per fact with exact page URL, excerpt,
  retrieval timestamp, source kind, confidence, and claim value.
- [ ] Require explicit WEG or residential evidence; do not treat generic
  `mietverwaltung` text as WEG proof.
- [ ] Require Berlin evidence tied to the company, not only a postcode or
  navigation title.
- [ ] Validate claim/value/excerpt equality, same-company binding, URL ownership,
  and portfolio units before promotion.
- [ ] Route failures to `Needs review` or `Rejected`; never convert missing or
  contradictory evidence into a positive or zero value.

**Verification:**
- [ ] `py -3 -m unittest tests.test_evidence_promotion tests.test_lead_contract -v`
- [ ] Assert a claim supported only by an unrelated page or combined text is
  rejected.
- [ ] Assert portfolio values without unit, scope, or source do not contribute
  to confirmed fit.
- Expected: only verified claim files can feed canonical qualification fields.

**Exit Criteria:**
- The promotion barrier rejects unsupported Berlin, service, WEG, and portfolio
  claims and records every decision with a verifier reason.

### Task 4: Add deterministic orchestration, queues, and run manifests

**Purpose:**
- Make phase boundaries, worker inputs, output ownership, retries, and
  reproducibility explicit without allowing shared-state mutation.

**Task Function:**
- Create a controller that prepares bounded work queues and reconciles lane
  outputs by run ID.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: orchestration and coordination state must remain single-owner.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: queue and manifest tests are deterministic and local.

**Specification Coverage:**
- Discovery → accepted universe → P0 qualification → provisional priority →
  bounded research → verification → promotion → ranking → QA → outputs.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`

**Files And Symbols:**
- Add `scripts/select_for_enrichment.py` with `select_accounts` and `main`.
- Add `scripts/orchestrate_enrichment.py` with `create_run_manifest`,
  `write_lane_queue`, `validate_lane_output`, `reconcile_run`, and `main`.
- Modify `scripts/lead_contract.py:update_run_manifest` to hash all declared
  inputs, supporting inputs, candidate/verified evidence, and outputs.
- Add repository profile sources `agents/signal-researcher.toml`,
  `agents/portfolio-researcher.toml`, `agents/contact-researcher.toml`, and
  `agents/evidence-verifier.toml`; generate any runtime adapter view only via
  the repository sync tool.
- Add canonical shared skills `.agents/skills/lead-evidence/SKILL.md`,
  `.agents/skills/account-research/SKILL.md`, and
  `.agents/skills/contact-verification/SKILL.md`.
- Add `tests/test_orchestration.py`.
- Add run roots under `evidence/research_runs/` and `evidence/manifests/`.

**Dependencies:**
- Task 1 and Task 2 complete; Task 3 contract shape is required before final
  queue validation.

**Authority:**
- Preauthorized local actions: add queue/manifest code and deterministic tests;
  create local run directories and JSONL task files.
- Stop for: concurrency that writes canonical files from workers, ambiguous
  run ownership, or any request to bypass a promotion barrier.

**Steps:**
- [ ] Create a run ID and manifest containing Git revision, configuration hashes,
  accepted-company hash, lane scopes, caps, timestamps, and output locations.
- [ ] Write one immutable queue item per accepted company and lane, including
  `company_id`, legal name, aliases, trusted domain, location, and research scope.
- [ ] Enforce phase barriers: no lane queue before accepted identity; no contact
  queue before provisional shortlist; no canonical write before verified evidence.
- [ ] Require worker outputs to be immutable files under
  `evidence/candidate/signals/`, `evidence/candidate/portfolio/`, and
  `evidence/candidate/contacts/`, keyed by run ID and company ID.
- [ ] Configure signal, portfolio, and contact profiles for recall-oriented
  evidence collection and the verifier profile for precision-oriented review;
  all four profiles must explicitly forbid canonical writes, scoring, ranking,
  CRM mutation, and outreach.
- [ ] Put shared source-navigation, evidence-capture, account-research, and
  contact-verification procedures in the three canonical skills instead of
  duplicating them in every profile.
- [ ] Reconcile missing, duplicate, out-of-scope, stale, or malformed outputs
  into explicit run errors rather than silently skipping them.
- [ ] Keep canonical writes serialized by the controller and preserve existing
  workbook/deck manifest compatibility.

**Verification:**
- [ ] `py -3 -m unittest tests.test_orchestration -v`
- [ ] Assert a queue cannot contain a quarantined company or a contact task
  without a provisional shortlist record.
- [ ] Assert manifest verification detects changed config, revision, input,
  candidate, verified, and output hashes.
- Expected: the same inputs, revision, and worker outputs produce the same
  queue membership and reconciliation result.

**Exit Criteria:**
- A complete local run is replayable from its manifest and no worker has a path
  or API that writes canonical lead data.

### Task 5: Implement account-scoped signal and portfolio research lanes

**Purpose:**
- Replace global signal assignment and unqualified portfolio values with
  per-company candidate evidence that is bounded, dated, and traceable.

**Task Function:**
- Implement the recall-oriented signal and portfolio worker contracts and their
  deterministic ingestion adapters.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: lower-cost, medium-reasoning research profile is sufficient
  for recall-oriented public-source collection.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: Task 3 verifier and Task 7 promotion tests provide the
  independent precision gate.

**Specification Coverage:**
- Buying signals, account-specific research completion, event URLs and dates,
  portfolio value/unit/scope, provider outage handling, and no global status
  leakage.

**Required Skills:**
- `account-research`, `lead-evidence`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/collect_buying_signals.py:normalize_name` and `main`,
  `scripts/provider_clients.py:ted_search`, and existing event-link output.
- Modify: `scripts/collect_buying_signals.py`, `scripts/provider_clients.py`,
  `scripts/extract_website_evidence.py`, and `scripts/score_leads.py` adapters.
- Add: `tests/test_account_research.py`, signal and portfolio fixtures, and
  candidate output examples under `evidence/candidate/`.

**Dependencies:**
- Tasks 1–4 complete.

**Authority:**
- Preauthorized local actions: implement lane output adapters, deterministic
  fixtures, and bounded local provider tests; use only configured public
  endpoints when explicitly authorized by execution.
- Stop for: provider spend, unbounded search, credentials in files, or any lane
  output that writes scores, priority, CRM state, or canonical CSVs.

**Steps:**
- [ ] Change signal input to one accepted company at a time with legal name,
  aliases, trusted domain, Berlin location, and research scope.
- [ ] Search account-scoped combinations for procurement, modernization,
  digitization, metering/heating-cost projects, supplier change, relevant
  hiring, and portfolio expansion; retain only dated, source-bound candidates.
- [ ] Persist one `ResearchRun` per company and lane. Mark `None found` only
  when the complete required account scope finishes with zero accepted events.
- [ ] Mark provider failure as `Unavailable` or `Partial`; never emit `None
  found` for an outage or truncated search.
- [ ] Preserve event-to-company links and exact match method; ambiguous buyer
  matches remain review-only.
- [ ] Preserve portfolio units (`units`, `buildings`, `properties`, `m²`, or
  unknown), scope, as-of date, and source; values without those fields cannot
  affect scoring.

**Verification:**
- [ ] `py -3 -m unittest tests.test_account_research tests.test_provider_clients tests.test_scoring -v`
- [ ] Assert two companies receive independent search statuses and one
  company’s event cannot change another company’s signal.
- [ ] Assert dated TED events can produce a candidate signal while date-less
  positive events remain `Unknown`.
- [ ] Assert provider outage, partial search, and completed no-match produce
  different states.
- Expected: no canonical row receives a global buying-signal default.

**Exit Criteria:**
- Every accepted company has an explicit signal research outcome and portfolio
  evidence outcome, each traceable to its own run and candidate files.

### Task 6: Implement person-first contact research after shortlist selection

**Purpose:**
- Produce verified named outreach owners and separately classified published
  mailboxes without contaminating P0 selection.

**Task Function:**
- Implement the contact worker contract and deterministic contact promotion
  rules for person, role, affiliation, and email ownership.

**Template Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: lower-cost, medium-reasoning public-source research profile;
  contact verification remains evidence-gated.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: contact claims require precision review independent of the
  researcher’s plausible-name heuristic.

**Specification Coverage:**
- Named decision-makers, buying-signal-aware outreach ownership, official
  contact pages, personal business email, generic mailbox separation, and stale
  contact downgrade.

**Required Skills:**
- `contact-verification`, `lead-evidence`, `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/build_shortlist.py:fetch_contacts`,
  `fetch_hunter_contact`, `main`, and contact helpers in
  `scripts/lead_contract.py`.
- Modify: `scripts/build_shortlist.py`, `scripts/lead_contract.py`,
  `scripts/provider_clients.py`, and `scripts/qa_leads.py`.
- Add: `tests/test_contact_verification.py` and contact candidate fixtures under
  `evidence/candidate/contacts/`.

**Dependencies:**
- Tasks 1–5 complete; Task 5 must produce the provisional shortlist and run ID.

**Authority:**
- Preauthorized local actions: add contact candidate/promotion handling and
  tests; read public official contact pages and configured enrichment results.
- Stop for: personal-data collection outside public professional scope, email
  sending, paid enrichment without approval, or a contact write before
  shortlist selection.

**Steps:**
- [ ] Queue contact research only for provisional shortlist company IDs.
- [ ] Search official team, management, Impressum, and contact pages first;
  retain exact person name, company affiliation, title, role evidence, page URL,
  excerpt, and retrieval date.
- [ ] Separately validate `person_verified`, `company_affiliation_verified`,
  `role_verified`, `role_relevance`, `email_owner_match`, and
  `email_deliverability`.
- [ ] Require independent evidence for a named owner; a plausible-looking
  two-word string is never sufficient.
- [ ] Bind a personal email to the verified person and company domain. Keep
  `info@`, `kontakt@`, and equivalent mailboxes as `Published` generic contact
  data, not named decision-makers.
- [ ] Preserve stronger official evidence when Hunter or another provider
  returns weaker or `Accept-all` evidence; downgrade stale records instead of
  asserting current verification.

**Verification:**
- [ ] `py -3 -m unittest tests.test_contact_verification tests.test_lead_contract tests.test_provider_clients -v`
- [ ] Assert `Schadensmeldungen Mitgliedschaften`, navigation text, and role-only
  fragments cannot become named contacts.
- [ ] Assert person/company/role/email mismatches become `Needs review` or
  `Unverified`, while generic mailboxes remain separately usable.
- Expected: contact enrichment adds actionability metadata only after the
  structural shortlist has already been selected.

**Exit Criteria:**
- Every named owner in canonical output has person, affiliation, role,
  relevance, source, and email-owner evidence; otherwise the field is null or
  explicitly unverified.

### Task 7: Promote verified evidence and make scoring/ranking deterministic

**Purpose:**
- Convert verified claims into canonical facts and deterministic sales priority
  without allowing research order or contact availability to change structural
  fit.

**Task Function:**
- Own final promotion, score calculation, actionability transitions, shortlist
  ordering, and audit rows.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: canonical writes and priority decisions require one owner and
  deterministic behavior.

**Validator Profile:**
- Controller-selected: `none`
- Selection basis: focused scoring and promotion tests provide direct proof.

**Specification Coverage:**
- Confirmed fit, evidence coverage, buying signal, actionability, sales
  priority, lead tiers, ranking stability, and auditability.

**Required Skills:**
- `skill-code-standards`, `skill-test-driven-development`,
  `skill-backend-verification`

**Files And Symbols:**
- Inspect: `scripts/score_leads.py:main`,
  `scripts/lead_contract.py:actionability_for`,
  `sales_priority_for`, `signal_rank`, and `tier_rank`.
- Add or modify: `scripts/promote_evidence.py`, `scripts/score_leads.py`,
  `scripts/build_shortlist.py`, and their audit outputs.
- Add tests: `tests/test_promotion.py`, extend `tests/test_scoring.py` and
  `tests/test_lead_contract.py`.

**Dependencies:**
- Tasks 1–6 complete.

**Authority:**
- Preauthorized local actions: modify deterministic promotion, scoring,
  ranking, audit, and tests; regenerate local processed outputs.
- Stop for: any agent-authored score, any ranking rule that uses contact
  presence as structural fit, or a score change without an audit reason.

**Steps:**
- [ ] Promote only `Verified` claims whose source, excerpt, company binding,
  freshness, and policy checks pass.
- [ ] Calculate observed fit, confirmed weighted fit, and evidence coverage
  separately; unknown components remain unknown rather than zero.
- [ ] Derive `buying_signal` from verified account-scoped events and the
  completed research run, not from a global events file.
- [ ] Derive actionability and sales priority from explicit deterministic rules;
  only eligible, sufficiently evidenced, strong-fit accounts with meaningful
  signal may become `Pursue`.
- [ ] Keep contact evidence out of structural fit and shortlist membership;
  apply it only to outreach-owner/actionability fields after selection.
- [ ] Sort by explicit stable keys: sales priority, lead tier, confirmed fit,
  signal rank, evidence coverage, and company ID as the final tie-breaker.
- [ ] Emit scoring audit rows explaining every promoted claim, score component,
  downgrade, and priority decision.

**Verification:**
- [ ] `py -3 -m unittest tests.test_promotion tests.test_scoring tests.test_lead_contract -v`
- [ ] Assert shuffled candidate completion order produces byte-equivalent score
  and ranking outputs.
- [ ] Assert missing portfolio evidence remains unknown and cannot earn the
  portfolio weight.
- [ ] Assert contact enrichment cannot change structural fit, tier, or shortlist
  membership.
- Expected: no unsupported row reaches `Pursue` and every score is auditable.

**Exit Criteria:**
- Canonical score, priority, and shortlist outputs are deterministic functions
  of accepted companies plus verified evidence and the versioned policy.

### Task 8: Enforce final QA, manifest reconciliation, and deliverables

**Purpose:**
- Make the full run fail closed and ensure workbook, deck, QA, evidence, and
  source registers describe the same run.

**Task Function:**
- Integrate final validators and fresh artifact generation after all promotion
  decisions are complete.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: final acceptance is serialized and must reconcile all
  canonical and generated surfaces.

**Validator Profile:**
- Controller-selected: `unresolved while task is pending`
- Selection basis: fresh independent verification is required before plan
  completion.

**Specification Coverage:**
- Schema enforcement, claim-level evidence, identity quarantine, signal states,
  contact provenance, manifest hashes, workbook/deck reconciliation, and final
  run evidence.

**Required Skills:**
- `skill-verification-before-completion`, `skill-backend-verification`

**Files And Symbols:**
- Inspect and modify only where required: `scripts/qa_leads.py:main`,
  `scripts/validate_workbook.py:main`, `scripts/validate_deliverables.py:main`,
  `scripts/build_workbook.py:main`, and `scripts/build_deck.py:main`.
- Add fixtures for every accepted finding under `tests/fixtures/` and extend
  `tests/test_provider_clients.py` for provider limitation states.
- Regenerate `data/processed/`, `evidence/`, and `output/` under one run ID.

**Dependencies:**
- Task 7 complete.

**Authority:**
- Preauthorized local actions: run the complete local pipeline, regenerate
  task-owned artifacts, and update the plan’s execution evidence after fresh
  verification.
- Stop for: locked user workbooks, missing provider authorization, failed
  manifest/revision checks, or any request to mark the plan complete after a
  failed required check.

**Steps:**
- [ ] Validate every canonical row against `config/lead_generation_schema.json`
  and every candidate/verified file against `config/research_evidence_schema.json`.
- [ ] Fail on unsupported claims, unresolved identity leakage, invalid types or
  ranges, stale/missing evidence, global signal status, contact provenance
  gaps, and score/ranking mismatch.
- [ ] Verify every manifest hash for raw inputs, supporting inputs, candidate
  evidence, verified evidence, canonical CSVs, workbook, deck, QA report, and
  source registers; verify the full Git revision is reachable.
- [ ] Build the workbook once from promoted canonical outputs, run semantic QA
  against that exact workbook, validate the workbook, then build and validate
  the deck without hand-edited generated values.
- [ ] Record counts, research statuses, signal states, contact states,
  quarantines, provider limitations, retrieval dates, and unresolved cases.

**Verification:**
- [ ] `py -3 -m unittest discover -s tests -v`
- [ ] `py -3 -m json.tool config/lead_generation_schema.json`
- [ ] `py -3 -m json.tool config/research_evidence_schema.json`
- [ ] `py -3 scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/active_run.json`
- [ ] `git diff --check`
- [ ] `rg -n "APIFY_API_TOKEN|HUNTER_API_KEY|Bearer [A-Za-z0-9._-]+" data evidence output presentation --glob '!*.md'`
- Expected: tests, schema checks, QA, workbook validation, deliverable
  validation, and credential scan pass with no credential values.

**Exit Criteria:**
- The run is reproducible from its manifest, all deliverables reconcile to the
  same run and revision, and the plan remains proposed until
  `skill-verification-before-completion` returns `verified`.

## Verification

Final artifact-level verification is performed only after Tasks 1–8 are
complete and `evidence/manifests/active_run.json` points to the immutable run
manifest being accepted:

- `py -3 -m unittest discover -s tests -v`
- `py -3 -m json.tool config/lead_generation_schema.json`
- `py -3 -m json.tool config/research_evidence_schema.json`
- `py -3 scripts/orchestrate_enrichment.py verify --manifest evidence/manifests/active_run.json`
- `git diff --check`
- `git status --short --branch`

The orchestrator verification command must validate every manifest-listed input,
candidate evidence file, verified evidence file, canonical output, workbook,
deck, QA report, and source register. It must exit nonzero on any hash drift,
revision mismatch, schema error, unsupported claim, unresolved identity,
invalid signal state, missing contact provenance, or ranking inconsistency.

## Completion Criteria

The plan is ready for completion verification when:

1. Tasks 1–8 have completed in dependency order and each task-local proof is
   recorded in the plan execution record.
2. Discovery and identity promotion exclude all unresolved or untrusted rows.
3. Every accepted P0 claim is page-local, company-bound, and verifier-approved.
4. Every accepted company has an account-scoped research outcome; `None found`
   never represents an outage, partial search, or global default.
5. Portfolio values retain unit, scope, source, and as-of date before affecting
   score.
6. Named contacts satisfy person, affiliation, role, relevance, source, and
   email-owner checks; generic mailboxes remain distinct.
7. Scoring and ranking are deterministic, stable under worker completion order,
   and independent of contact availability.
8. QA fails on every known baseline defect and passes only for regenerated,
   evidence-consistent outputs.
9. Manifest hashes, Git revision, run ID, canonical CSVs, workbook, deck, QA,
   and source registers reconcile.
10. No external publication, email sending, credential exposure, or unapproved
    provider spend occurs.
11. `skill-verification-before-completion` returns `verified` before status is
    changed from `proposed` to `completed`.

## Plan Self-Review

- Spec coverage: each approved architecture boundary maps to Tasks 1–8; the
  deterministic core is owned by Tasks 2, 3, 4, 7, and 8, while bounded
  research lanes are owned by Tasks 5 and 6.
- Placeholder scan: no task contains `TODO`, `TBD`, `as needed`, unnamed
  owners, or unresolved path/function placeholders.
- Cross-task consistency: `company_id`, `research_run_id`, `research_status`,
  `candidate_status`, `verified_domain`, `evidence_excerpt`, and the three
  candidate directories are used consistently across all tasks.
- Ownership: agents write only candidate evidence; the verifier writes
  verification decisions; deterministic Python writes canonical outputs; the
  lead controller owns the run manifest and coordination state.
- Task sizing: contract, identity, evidence, orchestration, research, contact,
  promotion, and final QA are separated at their actual promotion barriers.
