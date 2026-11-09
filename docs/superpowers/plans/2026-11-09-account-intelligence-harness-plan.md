---
layer: change
artifact_type: plan
status: proposed
template_id: implementation-plan
name: account-intelligence-harness
targets:
  - scripts/typed_contracts.py
  - scripts/lead_contract.py
  - scripts/account_intelligence.py
  - scripts/collect_buying_signals.py
  - scripts/score_leads.py
  - scripts/select_for_enrichment.py
  - scripts/build_shortlist.py
  - scripts/canonical_projection.py
  - scripts/orchestrate_enrichment.py
  - scripts/harness_tools.py
  - scripts/qa_leads.py
  - scripts/build_task1_workbook.mjs
  - config/signal_taxonomy.json
  - config/research_policy.json
  - config/lead_generation_schema.json
  - config/research_evidence_schema.json
  - agents/signal-researcher.toml
  - agents/account-intelligence-researcher.toml
  - .agents/skills/account-intelligence/SKILL.md
  - .agents/skills/buying-signal-research/SKILL.md
  - .agents/skills/account-research/SKILL.md
  - .agents/skills/lead-evidence/SKILL.md
  - .agents/skills/contact-verification/SKILL.md
  - tests
  - docs/evaluations/account-intelligence-benchmark.md
---

# Account-Intelligence Harness Plan

## Purpose

Turn the repository from a structurally validated lead-list pipeline into a
Codex-native account-intelligence harness that explains, with traceable
evidence, why one account is a better opportunity than another.

The parent Codex agent remains the strategy owner and uses the existing native
runtime, approved tools, typed contracts, and bounded workers. This plan does
not introduce a custom planner, scheduler, CRM application, or closed
end-to-end lead-generation runtime.

## Evidence Reconciliation

The two attached reviews agree with current source inspection. Their row counts
describe different dated artifacts and must not be combined into one dataset.

Validated findings:

1. `scripts/collect_buying_signals.py` is centered on four TED terms and exact
   normalized TED buyer attribution. TED is an optional procurement probe, not
   a complete prospect-intent strategy.
2. `config/signal_taxonomy.json` already names portfolio expansion,
   modernization, supplier change, and relevant hiring, but those categories
   are not first-class outputs of the research workflow.
3. `None found` can describe a narrow search rather than a researched account.
   Incomplete or unavailable research must not become negative intent.
4. `AccountHypothesis` and `AccountThesis` exist in
   `scripts/typed_contracts.py`, but indicators are only `list[str]`, thesis
   fields are not required in delivered priority rows, and
   `project_account_intelligence()` is not the workbook's canonical source.
5. `scripts/score_leads.py`, `scripts/select_for_enrichment.py`, and
   `scripts/build_shortlist.py` primarily rank structural fit, coverage, and a
   binary buying-signal field rather than opportunity hypotheses, changes,
   needs, counterevidence, and access.
6. `scripts/build_task1_workbook.mjs` has no account-thesis, timeline,
   indicator, counterevidence, or research-gap surface.
7. The current account-research and signal-researcher instructions preserve
   provenance but do not teach commercial research procedure, source choice,
   hypothesis construction, counterevidence, or stopping criteria.
8. Existing QA can pass structurally valid rows while the lead data remains
   commercially unexplained. Passing tests do not prove lead usefulness.

Not accepted as current defects without new evidence:

- The exact 191-versus-320 count difference; the next run must bind all output
  to one manifest and source revision.
- A requirement that every strong lead have direct procurement intent.
- A requirement to persist hidden chain-of-thought; export concise rationales,
  claims, counterevidence, uncertainty, and next actions only.
- A replacement of Codex's native runtime with another orchestrator.

## Product Contract

Every priority account must answer: why it fits the offer; why now, or why it
is a strong proactive account without direct intent; which facts support it;
what weakens it; who should be approached; what action is recommended; and what
unknown could change the decision.

Facts and hypotheses remain separate. Every hypothesis cites supporting claim
IDs, counterevidence claim IDs, confidence, and a validation step.

## Execution Approach

Use `subagent-ready`, followed by `inline sequential` at the shared projection
and export barrier. Research lanes may be delegated only with disjoint write
sets and account-scoped requests. Typed contracts, canonical projection,
ranking, QA, and workbook integration have one serialized owner.

Use the current workspace unless a delegated lane needs isolation. Reuse
existing action receipts, run manifests, native workers, and verifier decisions;
do not create another scheduler or manifest family.

Required skills: `skill-writing-plans`, `skill-systematic-debugging`,
`skill-test-driven-development`, `skill-backend-verification`,
`skill-dispatching-parallel-agents`, and
`skill-verification-before-completion`. Use
`skill-plan-document-reviewer` before costly execution.

## Tasks

### Task 1: Define offer and account-intelligence contracts

**Purpose:** Give the harness commercial context so opportunity reasoning is
not limited to company fit.

**Task Function:** Contract and acceptance design.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely modify shared contracts.

**Required Skills:** `skill-systematic-debugging`,
`skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:** `scripts/typed_contracts.py` (`OfferProfile`,
`AccountIndicator`, `AccountThesis`); `scripts/lead_contract.py`; both JSON
schemas under `config/`; `scripts/account_intelligence.py`; focused contract
tests under `tests/`.

**Dependencies:** None.

**Steps:**

1. Add `OfferProfile` with solution, target customer, problems solved, value
   propositions, economic-buyer roles, relevant triggers, disqualifiers, and
   incumbent or competitor signals.
2. Add typed `AccountIndicator` values for `direct_intent`, `trigger`,
   `need_indicator`, and `change_readiness`, including strength, recency,
   confidence, supporting claims, and counterevidence claims.
3. Expand `AccountThesis` with `why_this_account`, `why_now`,
   `problem_hypothesis`, strongest claim IDs, counterevidence IDs, uncertainty,
   access summary, recommended action, and research-gap impact.
4. Define explicit states: `Verified trigger`, `No trigger found`,
   `Research incomplete`, and `Unavailable`. Reserve `None found` for complete
   account-scoped research only.
5. Define visible dimensions: fit, opportunity, need, change, direct intent,
   access, and evidence confidence.

**Verification:** Write failing tests for missing offer context, invalid
indicators, unsupported hypotheses, false `None found`, and proactive leads
with strong evidence but no direct intent.

**Exit Criteria:** A complete account dossier is representable and an
unexplained priority record is rejected without requiring a tender.

### Task 2: Teach Codex account-intelligence research

**Purpose:** Make the skills executable commercial research playbooks rather
than only safety rules.

**Task Function:** Research playbook and native worker contract design.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely update skill and agent metadata.

**Required Skills:** `skill-test-driven-development` and
`skill-backend-verification`.

**Files And Symbols:** New `.agents/skills/account-intelligence/SKILL.md` and
`.agents/skills/buying-signal-research/SKILL.md`; existing
`.agents/skills/account-research/SKILL.md`, `lead-evidence/SKILL.md`, and
`contact-verification/SKILL.md`; new `agents/account-intelligence-researcher.toml`;
`agents/signal-researcher.toml`; `config/signal_taxonomy.json`.

**Dependencies:** Task 1.

**Steps:**

1. Teach the loop: known evidence → decision-relevant gap → source selection →
   claim capture → timeline → indicators → hypotheses → counterevidence →
   thesis → stop or research again.
2. Add source playbooks for official services/portfolio, news/projects,
   careers, management/Impressum, references/client announcements,
   procurement, approved external sources, and professional profiles.
3. Add query families for expansion, mandates, modernization, digitalization,
   automation, hiring, supplier change, direct RFPs, and organizational change.
4. Teach exact company binding, freshness, namesake checks, source limitations,
   negative-result semantics, and generic-mailbox handling.
5. Require every thesis to include why-this-account, why-now, support,
   counterevidence, uncertainty, confidence, access, and next action.
6. Add adaptive stopping rules: continue only when a material gap can change
   tier, action, or stakeholder.

**Verification:** Add skill evaluations for no direct signal, misleading hiring,
stale events, namesakes, contradictory sources, generic mailboxes, and
incomplete providers.

**Exit Criteria:** A fresh Codex worker request receives a concrete method and
returns a typed evidence package suitable for thesis construction.

### Task 3: Replace TED-only research with account-environment research

**Purpose:** Make intent research commercially meaningful while retaining TED
as an optional accelerator.

**Task Function:** Research orchestration and evidence promotion.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely change the research boundary.

**Required Skills:** `skill-systematic-debugging`,
`skill-test-driven-development`, `skill-backend-verification`.

**Files And Symbols:** `scripts/collect_buying_signals.py`,
`scripts/account_intelligence.py`, `scripts/orchestrate_enrichment.py`,
`scripts/worker_dispatch.py`, `scripts/harness_tools.py`,
`scripts/promote_evidence.py`, `scripts/canonical_projection.py`,
`scripts/native_verifier.py`, and focused tests for buying signals, native
adapters, account intelligence, and projection.

**Dependencies:** Tasks 1 and 2.

**Steps:**

1. Trace callers of `derive_account_signal`, `account_research_state`, and
   shortlist selection with `skill-systematic-debugging`.
2. Add account-scoped attempts for official site, public news/events, careers,
   management/contact, and optional TED/procurement.
3. Capture direct-intent, trigger, need, and change-readiness claims separately
   with claim IDs, source family, date, excerpt, and assurance.
4. Emit `Verified trigger`, `No trigger found`, `Research incomplete`, or
   `Unavailable` only from complete attempts and provider state.
5. Research a reserve pool of 40–50 structurally promising accounts, then
   deeply research 10–15 accounts whose evidence gaps can change the decision.
6. Keep research adaptive; do not force a fixed signals→portfolio→contacts
   sequence.

**Verification:** Prove that official non-TED triggers are retained, unrelated
TED events are not attributed, incomplete research remains unknown, direct TED
intent boosts but does not gate priority, and replay evidence cannot become
source assurance.

**Exit Criteria:** The collector produces meaningful indicators or an honest
no-trigger/incomplete state, with every promoted record bound to company,
source, date, and verifier decision.

### Task 4: Make thesis-backed commercial ranking canonical

**Purpose:** Rank commercial attractiveness instead of structural fit alone.

**Task Function:** Deterministic scoring, ranking, and QA.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely change canonical ranking behavior.

**Required Skills:** `skill-test-driven-development`,
`skill-systematic-debugging`, `skill-backend-verification`.

**Files And Symbols:** `scripts/score_leads.py`,
`scripts/select_for_enrichment.py`, `scripts/build_shortlist.py`,
`scripts/lead_contract.py`, `scripts/canonical_projection.py`,
`scripts/qa_leads.py`, and scoring, selection, projection, and end-to-end tests.

**Dependencies:** Tasks 1–3.

**Steps:**

1. Persist fit, opportunity, need, change, direct-intent, access, and evidence
   confidence as separate dimensions.
2. Add priority states `Priority — verified trigger`,
   `Priority — strong fit, no trigger`, `Nurture`, `Research required`, and
   `Disqualify`, with compatibility mappings for legacy exports.
3. Require verified ICP fit, complete research, a validated thesis, and either
   a current trigger or an explicit strong-fit/no-trigger rationale for priority.
4. Penalize stale, single-source, contradicted, replay-only, or uncontactable
   accounts through confidence/readiness, not invented negative intent.
5. Let deep research rerank the reserve pool instead of enriching a fixed top
   30 only.
6. Generate `priority_reason` from thesis facts and claim IDs; remove generic
   company-ID ordering as the stakeholder-facing rationale.

**Verification:** Add comparison tests where a smaller account with recent
verified change outranks a larger account with no trigger, and where direct
intent boosts but does not exclusively gate priority. Reject missing theses,
unsupported hypotheses, false contact names, and replay evidence.

**Exit Criteria:** No top lead can be emitted without an explanation, and the
ranking makes why A outranks B visible and deterministic.

### Task 5: Export account dossiers and benchmark product value

**Purpose:** Make the differentiating intelligence visible to stakeholders.

**Task Function:** Canonical projection and workbook generation.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely update the generated export.

**Required Skills:** `skill-test-driven-development`,
`skill-backend-verification`, `skill-verification-before-completion`.

**Files And Symbols:** `scripts/build_task1_workbook.mjs`, the canonical JSON
builder feeding it, `scripts/validate_workbook.py`, workbook tests, and new
`docs/evaluations/account-intelligence-benchmark.md`.

**Dependencies:** Tasks 1–4.

**Steps:**

1. Add priority columns for why-this-account, why-now, problem hypothesis,
   strongest evidence, counterevidence, confidence, contact owner, recommended
   action, and research gap.
2. Add `Account Theses`, `Account Timeline`, `Evidence Ledger`, and `Research
   Gaps` sheets with claim IDs and source hyperlinks.
3. Keep canonical JSON/CSV and typed projections authoritative; never fabricate
   evidence to fill an export cell.
4. Define a 10–20 account manual benchmark for identity, claim accuracy, event
   attribution, thesis defensibility, ranking agreement, contact usefulness,
   and research cost.
5. Run the first milestone on 10–15 Berlin Hausverwaltungen from the reserve
   pool and compare the result with the old structural shortlist.

**Verification:** Validate workbook sheets, identities, hyperlinks, thesis
completeness, source provenance, and a one-minute stakeholder read of every
priority dossier.

**Exit Criteria:** The deliverable demonstrates account intelligence rather
than a spreadsheet of fit scores, with benchmark findings recorded.

### Task 6: End-to-end verification and plan reconciliation

**Purpose:** Prove native runtime behavior and close the plan with fresh
evidence.

**Task Function:** Verification and acceptance.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can independently validate the implementation.

**Required Skills:** `skill-backend-verification`,
`skill-verification-before-completion`, and `skill-plan-document-reviewer`.

**Files And Symbols:** All changed files from Tasks 1–5; no new production
surface unless a failed acceptance proof identifies its canonical owner.

**Dependencies:** Tasks 1–5.

**Steps:**

1. Run focused contract, research, scoring, projection, and workbook tests.
2. Run `py -3 -m unittest discover -s tests -v`.
3. Execute one representative native account-research trace and verify request,
   worker result, verifier decision, action receipt, promoted claims, thesis,
   rank, and workbook row share company ID and run context.
4. Confirm replay never appears as live/source assurance and no-trigger is not
   emitted for incomplete research.
5. Compare benchmark judgments with computed order and record disagreements as
   evidence, not hidden exceptions.
6. Reconcile actual files, commands, test counts, and limitations; only then
   mark this plan completed through `skill-verification-before-completion`.

**Exit Criteria:** The harness produces a bounded set of explainable,
traceable, comparatively prioritized accounts, or clearly reports why a run is
incomplete.

## Acceptance Criteria

- `OfferProfile` is present before commercial opportunity scoring.
- Direct intent, triggers, need indicators, change readiness, access, and
  evidence confidence are separate fields.
- Every priority account has a validated thesis with support, counterevidence,
  uncertainty, confidence, and next action.
- `None found` is reserved for complete account-scoped research.
- Direct intent accelerates priority but is not required for a strong proactive
  lead.
- Deep research can change the shortlist from a reserve pool.
- The workbook exposes why-this-account, why-now, evidence, counterevidence,
  contact owner, confidence, and next action.
- A 10–20 account benchmark measures research quality, not only code quality.
- Full tests and a representative backend/native trace pass, with live-provider
  limitations explicit.

## Non-Goals

- No custom planner, scheduler, CRM integration, or outreach sender.
- No requirement that every good lead publish a tender.
- No hidden chain-of-thought persistence.
- No scaling beyond the bounded benchmark until the harness can explain why
  Account A outranks Account B.
