---
layer: change
artifact_type: plan
status: active
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
IDs, counterevidence claim IDs, confidence, and a validation step. Structural
claim verification is not semantic thesis verification: every material thesis
assertion must also pass an offer-relevance, temporal-relevance, entailment, and
contradiction review by a separate semantic-review action.

The parent Codex runtime is the only research planner. Repository Python may
validate requests, persist receipts, run one explicitly selected action,
promote verified evidence, calculate deterministic contributions, and export
results. It may not choose the next account/action, schedule follow-up
research, own research continuation, or decide when the account is complete.

Every `OfferProfile` has an immutable `offer_id` and `offer_version`. Every
thesis, indicator, semantic-review decision, and rank audit is bound to that
version, and each commercial feature records the offer criterion it satisfies.

Negative research uses a finite account/offer coverage manifest. The manifest
declares the required source/query families for that account, records each
completed check and provider state, and permits `No trigger found` only after
all declared checks complete without truncation, unresolved candidates, or
provider failure.

## Execution Approach

Use `subagent-ready`, followed by `inline sequential` at the shared projection
and export barrier. The parent Codex runtime selects and sequences research
actions. Repository actions may be delegated only as explicitly requested,
account-scoped, idempotent operations with disjoint write sets. Typed
contracts, canonical projection, ranking, QA, and workbook integration have
one serialized owner.

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

1. Add `OfferProfile` with immutable `offer_id` and `offer_version`, solution,
   target customer, problems solved, value propositions, economic-buyer roles,
   relevant triggers, disqualifiers, and incumbent or competitor signals.
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
   access, and evidence confidence. Each opportunity, need, and change value
   must include supporting claim IDs and the offer criterion it satisfies.
6. Add a semantic-review contract separate from fact verification. It records
   assertion IDs, reviewed claim IDs, offer criterion, temporal check,
   contradiction result, decision, reason codes, and reviewer identity.
7. Add a coverage-manifest contract with declared checks, completed checks,
   provider states, truncation, unresolved-candidate counts, and the finite
   negative-state decision.

**Verification:** Write failing tests for missing offer context, invalid
indicators, unsupported hypotheses, false `None found`, and proactive leads
with strong evidence but no direct intent.

**Exit Criteria:** A complete account dossier is representable, an unrelated
claim cannot validate a material thesis assertion, offer versions bind every
commercial conclusion, and an unexplained priority record is rejected without
requiring a tender.

### Task 2: Teach Codex account-intelligence research

**Purpose:** Make the skills executable commercial research playbooks rather
than only safety rules.

**Task Function:** Research playbook and native worker contract design.

**Template Profile:** unresolved until Planning Dispatch selects the lowest
profile that can safely update skill and agent metadata.

**Required Skills:** `skill-test-driven-development` and
`skill-backend-verification`.

**Files And Symbols:** New `.agents/skills/account-intelligence/SKILL.md` as
the canonical research-loop skill; new `.agents/skills/buying-signal-research/SKILL.md`
as a signal-domain playbook only; existing `account-research/SKILL.md` becomes
the bounded action/receipt contract, `lead-evidence/SKILL.md` remains the
claim-provenance contract, and `contact-verification/SKILL.md` remains the
access/contact contract; new `agents/account-intelligence-researcher.toml`;
`agents/signal-researcher.toml`; `config/signal_taxonomy.json`.

**Dependencies:** Task 1.

**Steps:**

1. Teach the canonical loop: known evidence → decision-relevant gap → parent
   Codex selects one action → source selection → claim capture → timeline →
   indicators → hypotheses → semantic review → counterevidence → thesis →
   parent Codex stops or requests another action.
2. Add source playbooks for official services/portfolio, news/projects,
   careers, management/Impressum, references/client announcements,
   procurement, approved external sources, and professional profiles.
3. Add query families for expansion, mandates, modernization, digitalization,
   automation, hiring, supplier change, direct RFPs, and organizational change.
4. Teach exact company binding, freshness, namesake checks, source limitations,
   negative-result semantics, and generic-mailbox handling.
5. Require every thesis to include why-this-account, why-now, support,
   counterevidence, uncertainty, confidence, access, and next action.
6. Add adaptive stopping rules for the parent Codex planner: continue only when
   a material gap can change tier, action, or stakeholder. Workers and Python
   adapters cannot select the next action or stop the account.
7. Add a responsibility matrix: account-intelligence owns the loop and thesis
   semantics; buying-signal-research owns signal terminology and source
   patterns; account-research owns bounded action scope and receipts;
   lead-evidence owns immutable claims; contact-verification owns access
   validation; the parent Codex runtime owns planning and stopping.

**Verification:** Add skill evaluations for no direct signal, misleading hiring,
stale events, namesakes, contradictory sources, generic mailboxes, and
incomplete providers.

**Exit Criteria:** A fresh Codex worker request receives a concrete method and
returns a typed evidence package suitable for thesis construction, while the
skill composition has one canonical loop and no contradictory stopping owner.

### Task 3: Replace TED-only research with account-environment research

**Purpose:** Make intent research commercially meaningful while retaining TED
as an optional accelerator.

**Task Function:** Per-action tool boundary and evidence promotion.

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

**Authority:** Use only approved tools and configured source policy. No hidden
reasoning persistence. No live-provider claim from replay or structural output.
No generic industry event may become an account claim without exact company
binding and page-local evidence. Python must not plan, schedule, retry, select
the next account/action, or decide research completion; it may only execute the
single parent-selected action and return a typed result.

**Steps:**

1. Trace callers of `derive_account_signal`, `account_research_state`, and
   shortlist selection with `skill-systematic-debugging`, then split the
   existing Python orchestration into explicit parent-selected action
   boundaries without adding another planner.
2. Add account-scoped attempts for official site, public news/events, careers,
   management/contact, and optional TED/procurement.
3. Capture direct-intent, trigger, need, and change-readiness claims separately
   with claim IDs, source family, date, excerpt, and assurance.
4. Emit `Verified trigger`, `No trigger found`, `Research incomplete`, or
   `Unavailable` only from complete attempts and provider state.
5. Use a reserve pool of 40–50 and a deep-research sample of 10–15 only as
   benchmark inputs selected by the parent Codex runtime; do not encode those
   counts as Python scheduling or backfill logic.
6. Keep research adaptive; do not force a fixed signals→portfolio→contacts
   sequence. The parent Codex runtime chooses continuation, parallelism,
   retries, and stopping from returned evidence and coverage manifests.
7. Add semantic-review execution after fact verification and before thesis
   promotion. Reject assertions whose cited claims do not entail the statement,
   satisfy the bound offer criterion, remain temporally relevant, or survive
   contradiction review.

**Verification:** Prove that official non-TED triggers are retained, unrelated
TED events are not attributed, incomplete research remains unknown, direct TED
intent boosts but does not gate priority, and replay evidence cannot become
source assurance.

**Exit Criteria:** The per-action boundary produces meaningful indicators or
an honest no-trigger/incomplete state, with every promoted record bound to
company, offer version, source, date, verifier decision, semantic decision,
and coverage manifest. No Python loop owns research planning.

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
7. Require every rank audit to include immutable offer ID/version and
   deterministic per-dimension contributions so the ordering is derivable
   rather than a post-hoc narrative.
8. Require semantic-review approval for every material thesis assertion before
   it can contribute to opportunity, need, change, or priority.

**Verification:** Add comparison tests where a smaller account with recent
verified change outranks a larger account with no trigger, and where direct
intent boosts but does not exclusively gate priority. Reject missing theses,
unsupported hypotheses, false contact names, and replay evidence.

**Exit Criteria:** No top lead can be emitted without a semantically supported
explanation, offer-bound rank contributions, and a visible reason why A
outranks B.

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
   and research cost. Completion gates are at least 90% claim-support
   precision; 100% of priority thesis assertions semantically supported; zero
   critical account-attribution errors; at least 70% top-10 pairwise ranking
   agreement; and at least 80% usefulness for named contacts that the output
   claims are outreach owners. A failed threshold blocks completion.
5. Run the first milestone on 10–15 Berlin Hausverwaltungen from the reserve
   pool and compare the result with the old structural shortlist.

**Verification:** Validate workbook sheets, identities, hyperlinks, thesis
completeness, source provenance, and a one-minute stakeholder read of every
priority dossier. Record benchmark threshold results in the release manifest;
do not mark the plan complete when a threshold fails.

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
3. Execute one representative parent-Codex native account-research trace and
   verify the trace names the selected native profile and skills, records the
   parent-selected action and returned evidence, shows the parent selecting the
   next action or stopping, and proves no Python loop selected or scheduled
   subsequent research. Also verify request, worker result, verifier decision,
   semantic-review decision, action receipt, promoted claims, thesis, rank, and
   workbook row share company ID, offer ID/version, and run context.
4. Confirm replay never appears as live/source assurance and no-trigger is not
   emitted for incomplete research.
5. Compare benchmark judgments with computed order and enforce the declared
   claim, thesis, attribution, ranking, and contact thresholds. A disagreement
   below threshold is a failed acceptance gate, not merely a recorded note.
6. Reconcile actual files, commands, test counts, and limitations; only then
   mark this plan completed through `skill-verification-before-completion`.

**Exit Criteria:** The harness produces a bounded set of explainable,
traceable, comparatively prioritized accounts, or clearly reports why a run is
incomplete.

## Acceptance Criteria

- `OfferProfile` is present before commercial opportunity scoring, and every
  thesis, indicator, semantic decision, and rank audit binds to its immutable
  offer ID/version.
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
- A 10–20 account benchmark meets the declared claim-support, thesis-support,
  attribution, ranking-agreement, and contact-usefulness thresholds.
- Full tests and a representative backend/native trace pass, with live-provider
  limitations explicit.

## Non-Goals

- No custom planner, scheduler, CRM integration, or outreach sender.
- No requirement that every good lead publish a tender.
- No hidden chain-of-thought persistence.
- No scaling beyond the bounded benchmark until the harness can explain why
  Account A outranks Account B.
