---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: proposed
name: berlin-hausverwaltung-lead-generation
targets:
  - .env.example
  - .gitignore
  - config/lead_generation_schema.json
  - scripts/runtime_config.py
  - scripts/import_discovery.py
  - scripts/normalize_dedupe.py
  - scripts/extract_website_evidence.py
  - scripts/score_leads.py
  - scripts/build_shortlist.py
  - scripts/build_workbook.py
  - scripts/qa_leads.py
  - scripts/validate_deliverables.py
  - output/berlin-hausverwaltung-leads_2026-11-09.xlsx
  - output/berlin-hausverwaltung-methodology_2026-11-09.pptx
---

# Berlin Hausverwaltung Lead Generation Implementation Plan

## Goal

Deliver an evidence-backed, sales-usable Berlin Hausverwaltung lead dataset by
Monday, November 9, 2026. Produce a deduplicated company universe,
transparent qualification and scoring, evidence-backed buying signals, targeted
contact enrichment, a validated workbook, and a five-slide methodology deck.

Optimize for **maximum verified, usable leads per hour**. This is an MVP lead-
generation system, not a full market-intelligence platform.

The current workspace contains no Git checkout, source files, tests, or existing
plan template. This plan defines new intended paths and requires the execution
owner to attach or initialize the real implementation workspace before creating
code. No existing helper, schema, or generated surface may be assumed.

## Implementation Outcomes

### Evidence-backed company universe

Create a canonical Berlin-relevant Hausverwaltung dataset from VDIV Berlin-
Brandenburg, permitted directories, official company websites, search discovery,
Apify exports, and supplementary Overpass/OpenStreetMap results. Normalize
company names, domains, addresses, Berlin relevance, and parent/branch identity;
retain provenance for every imported record; and target approximately 100–200
unique companies where source coverage permits.

### Deterministic qualification and prioritization

Implement Lead Fit with service/ICP fit 30%, residential/WEG relevance 25%,
portfolio potential 25%, geographic/operational fit 10%, and buying/growth
signals 10%. Keep Lead Fit, Opportunity Potential, Buying Signal, Actionability,
and Evidence Coverage separate. Represent missing evidence as `Unknown`, never
as zero, and emit a score audit that can recalculate every tier.

### Targeted contact enrichment

Research named decision-makers only for the highest-priority 20–30 accounts.
Capture role relevance, public source URL, email provenance, verification status,
LinkedIn URL when available, and last-verified date. Use team/Impressum pages
first and Hunter only for shortlisted professional-email discovery or verification.

### Centralized runtime configuration

Use one repository-root `.env` file for provider credentials and runtime settings.
Track `.env.example` with variable names, safe defaults, and blank secret values;
ignore `.env` through `.gitignore`; and require all provider scripts to load
configuration through `scripts/runtime_config.py`. API keys must never appear in
CLI arguments, source files, raw data, evidence, workbooks, presentations, or
logs.

### Submission-ready deliverables

Produce `output/berlin-hausverwaltung-leads_2026-11-09.xlsx` with tabs
`01_All_Leads`, `02_Qualification`, `03_Priority_Leads`, `04_Contacts`, and
`05_Methodology_Sources`. Produce
`output/berlin-hausverwaltung-methodology_2026-11-09.pptx` with five slides:
objective, discovery, qualification logic, results, and validation plus the
Phase 2 roadmap. Final QA must cover duplicates, evidence coverage, links,
unsupported claims, score consistency, and contact provenance.

### Explicitly deferred scope

Do not build PostgreSQL, predictive conversion models, continuous competitor or
intermarket monitoring, enrichment for the entire universe, elaborate n8n
orchestration, or a production CRM feedback loop before November 9. Show these
capabilities only as Phase 2 architecture.

## Execution Approach

- Mode: `inline sequential`
- Coordination: `none`
- Required skills: `skill-executing-plans`, `spreadsheets:Spreadsheets`, `presentations:Presentations`, `browser-use`, `skill-verification-before-completion`
- Isolation: `current workspace` after a real implementation checkout is attached; until then, plan-only workspace
- Commit policy: `no commits during execution`
- Preauthorized local actions: Read and write task-owned files under `config/`, `scripts/`, `data/`, `evidence/`, `presentation/`, and `output/`; run declared local validation commands; read public source data without bypassing access controls
- User-approval actions: Authentication, paid Apify/Hunter usage beyond available free allowance, external writes, email sending, third-party export, destructive deletion, or scope expansion
- Parallel ownership: `none`; all tasks share the canonical schema and dataset
- Sequential fallback: Execute Tasks 1–9 in order; record unavailable sources as `Unknown` and continue without unsupported substitutions
- Runtime configuration: Load provider credentials and runtime settings only from the repository-root `.env` through `scripts/runtime_config.py`; never duplicate secrets in task inputs or generated artifacts

## Task Breakdown

### Task 1: Establish the workspace and canonical data contract

**Purpose:**
- Create the minimum directory structure, runtime configuration contract, and schema used by every later task.

**Task Function:**
- Establish the durable contract for environment variables, company, evidence, signal, score, and contact records.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: The workspace is empty, so the lead controller must establish canonical paths before implementation.

**Specification Coverage:**
- Single source of truth, explicit provenance, `Unknown` handling, centralized environment variables, and no invented existing code paths.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: repository root and this plan
- Modify: `.env.example`, `.gitignore`, `config/lead_generation_schema.json`, `scripts/runtime_config.py`, `data/raw/`, `data/intermediate/`, `data/processed/`, `evidence/`, `presentation/`, `scripts/`, `output/`
- Verify: `.env.example`, `.gitignore`, `scripts/runtime_config.py`, `config/lead_generation_schema.json`

**Dependencies:**
- None; attach or initialize a real Git checkout before code creation.

**Authority:**
- Preauthorized local actions: Create the declared directories, `.env.example`, `.gitignore`, runtime loader, and schema; run parsing, secret-hygiene, and path checks.
- Stop for: Unsafe workspace identity, unrelated-file overwrite, authentication, external writes, or unapproved data fields.

**Steps:**
- [ ] Confirm the execution root is a real Git checkout and preserve unrelated changes.
- [ ] Create `config/`, `data/raw/`, `data/intermediate/`, `data/processed/`, `evidence/`, `presentation/`, `scripts/`, and `output/`.
- [ ] Create root `.env.example` with `APIFY_API_TOKEN`, `HUNTER_API_KEY`, `TED_API_BASE_URL`, `OVERPASS_API_URL`, `REQUEST_TIMEOUT_SECONDS`, and `MAX_PRIORITY_ACCOUNTS`; leave secrets blank and provide safe non-secret defaults.
- [ ] Copy `.env.example` to local root `.env` only during execution; keep credentials blank until explicitly supplied by the user and never commit the file.
- [ ] Add `.env` and `.env.*.local` to `.gitignore` while keeping `.env.example` tracked.
- [ ] Implement `scripts/runtime_config.py` with a standard-library `.env` parser, typed accessors, required-key validation per provider, and no secret values in exceptions or logs.
- [ ] Define `config/lead_generation_schema.json` with company identity, source provenance, qualification, evidence, signals, scores, tiers, contacts, and timestamps.
- [ ] Define allowed values for Berlin relevance, management type, residential/WEG, signal strength, actionability, lead tier, email status, and verification.
- [ ] Require a source URL for every non-`Unknown` qualification claim and an evidence URL plus verification status for every contact email.

**Verification:**
- [ ] Run `python -m json.tool config/lead_generation_schema.json`.
- Expected: JSON parses and contains the field and enum contract used by Tasks 2–8.
- [ ] Run `python scripts/runtime_config.py --check-example .env.example`.
- Expected: The example file parses, secret values are blank, and all declared non-secret defaults are valid.
- [ ] Run `git check-ignore -q .env` after a Git checkout is attached.
- Expected: Exit code `0`; `.env` is ignored and `.env.example` remains trackable.
- [ ] Run `Test-Path config/lead_generation_schema.json, data/raw, data/intermediate, data/processed, evidence, presentation, scripts, output`.
- Expected: Every path returns `True`.

**Exit Criteria:**
- The real execution workspace is identified, canonical directories exist, and the schema is the only authoritative field contract.

### Task 2: Collect and register raw discovery sources

**Purpose:**
- Build a broad raw company universe without spending shortlist-level effort on contacts.

**Task Function:**
- Import and register VDIV, Apify, permitted-directory, search, Overpass, and TED extracts while preserving provenance.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Source access and evidence boundaries are sensitive; one controller keeps collection and provenance consistent.

**Specification Coverage:**
- VDIV P0 discovery, Apify bulk extraction, Overpass/OpenStreetMap supplementary discovery, TED buying-signal coverage, and traceable URLs.

**Required Skills:**
- `browser-use`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: VDIV pages, permitted directory exports, Apify dataset export, Overpass result, TED result, and discovery searches
- Modify: `data/raw/vdiv_2026-11-07.csv`, `data/raw/apify_2026-11-07.json`, `data/raw/overpass_2026-11-07.json`, `data/raw/ted_2026-11-07.json`, `evidence/source_register_2026-11-07.csv`, `scripts/import_discovery.py`
- Runtime dependency: `scripts/import_discovery.py` must load `APIFY_API_TOKEN`, `TED_API_BASE_URL`, `OVERPASS_API_URL`, and `REQUEST_TIMEOUT_SECONDS` through `scripts/runtime_config.py`; no credential CLI flags.
- Verify: `data/intermediate/discovery_raw_2026-11-07.csv` and the source register

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: Read public source pages, import available exports, write raw snapshots and source-register rows, and run `scripts/import_discovery.py` locally.
- Stop for: Login or CAPTCHA bypass, paid usage beyond available free credits, prohibited scraping, external state changes, or data outside the approved scope.

**Steps:**
- [ ] Export VDIV Berlin-Brandenburg results to `data/raw/vdiv_2026-11-07.csv` with original listing URLs.
- [ ] Run the approved Apify collection within available free allowance and save `data/raw/apify_2026-11-07.json`; stop before paid execution.
- [ ] Run the bounded Overpass/OpenStreetMap supplementary query and save `data/raw/overpass_2026-11-07.json`.
- [ ] Run the bounded TED Search API query for metering, heating-cost billing, meter replacement, and remote-meter procurement and save `data/raw/ted_2026-11-07.json`.
- [ ] Register source type, retrieval date, query/export identifier, access limitation, and source URL in `evidence/source_register_2026-11-07.csv`.
- [ ] Confirm `scripts/import_discovery.py` reads provider credentials and endpoints only through `scripts/runtime_config.py` and redacts them from import reports.
- [ ] Run `python scripts/import_discovery.py --vdiv data/raw/vdiv_2026-11-07.csv --apify data/raw/apify_2026-11-07.json --overpass data/raw/overpass_2026-11-07.json --ted data/raw/ted_2026-11-07.json --output data/intermediate/discovery_raw_2026-11-07.csv`.

**Verification:**
- [ ] Confirm every available raw file is non-empty and every imported row retains a source URL.
- Expected: The import report gives row counts by source and records unavailable providers explicitly.

**Exit Criteria:**
- A broad raw discovery file exists and every source gap is explicit.

### Task 3: Normalize entities and resolve duplicates

**Purpose:**
- Produce one canonical company row per real organization while retaining duplicate and branch review evidence.

**Task Function:**
- Normalize names, domains, addresses, legal suffixes, and Berlin/Brandenburg labels; resolve exact and ambiguous matches.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Entity resolution changes the downstream universe and must be reviewed before qualification.

**Specification Coverage:**
- Domain-first identity hierarchy, company-name and address fallback, branch/parent handling, and raw provenance preservation.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/discovery_raw_2026-11-07.csv`, `config/lead_generation_schema.json`
- Modify: `scripts/normalize_dedupe.py`, `data/intermediate/companies_normalized_2026-11-07.csv`, `data/intermediate/dedupe_review_2026-11-07.csv`, `evidence/entity_resolution_2026-11-07.csv`
- Verify: canonical company output and dedupe review queue

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: Run deterministic normalization and deduplication locally; write canonical rows and review queues under `data/intermediate/` and `evidence/`.
- Stop for: Destructive raw-row removal, unresolved legal-entity ambiguity affecting ownership, or unsupported branch collapse.

**Steps:**
- [ ] Normalize domains by lowercasing, removing schemes, stripping `www.`, removing tracking parameters, and retaining the registrable host.
- [ ] Normalize names by trimming whitespace, standardizing punctuation, and retaining the legal name separately.
- [ ] Normalize addresses into street, postal code, city, and region; classify Berlin versus Brandenburg without inferring portfolio geography from office address alone.
- [ ] Deduplicate by exact domain, then normalized legal/company name, then normalized address; send conflicts to `data/intermediate/dedupe_review_2026-11-07.csv`.
- [ ] Preserve branch/parent relationships and record the resolution reason in `evidence/entity_resolution_2026-11-07.csv`.
- [ ] Run `python scripts/normalize_dedupe.py --input data/intermediate/discovery_raw_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/companies_normalized_2026-11-07.csv --review-output data/intermediate/dedupe_review_2026-11-07.csv --evidence-output evidence/entity_resolution_2026-11-07.csv`.

**Verification:**
- [ ] Assert `Company ID` uniqueness and exact-domain uniqueness in the canonical output.
- Expected: Ambiguous records remain in the review queue and are not silently merged.

**Exit Criteria:**
- The canonical company universe is deduplicated, traceable to raw sources, and ready for qualification.

### Task 4: Extract and validate website qualification evidence

**Purpose:**
- Determine whether each company is a relevant Hausverwaltung and capture evidence for service, residential/WEG, portfolio, and geography fields.

**Task Function:**
- Fetch permitted official website pages, extract structured claims, and preserve claim-level URLs and retrieval dates.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Website evidence is the primary qualification boundary and requires source-first validation.

**Specification Coverage:**
- Official website verification, LLM-assisted structured extraction, source-backed qualification, and `Unknown` for missing evidence.

**Required Skills:**
- `browser-use`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/companies_normalized_2026-11-07.csv`, official company websites, `config/lead_generation_schema.json`, `.env`
- Modify: `scripts/extract_website_evidence.py`, `data/intermediate/website_evidence_2026-11-08.jsonl`, `evidence/website_capture_index_2026-11-08.csv`
- Verify: the website evidence JSONL and capture index

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: Read public official websites within published access boundaries; write evidence, retrieval dates, and failed-fetch records locally; use LLM extraction only as an assistant to human or rule validation.
- Stop for: Authentication, robots or terms violations, CAPTCHA bypass, unsupported inference, or any request to label an unverified claim as fact.

**Steps:**
- [ ] Fetch homepage, services, WEG/residential, portfolio/references, news/projects, and Impressum pages when public.
- [ ] Extract service fit, residential/WEG relevance, visible portfolio indicators, Berlin/operational relevance, and evidence snippets.
- [ ] Store each claim with `value`, `confidence`, `evidence_url`, `evidence_excerpt`, `retrieved_at`, and `Unknown` when evidence is absent.
- [ ] Classify management type and reject clearly irrelevant businesses without deleting the raw row.
- [ ] Use the LLM only to propose structured fields from captured text; require a source URL and human review for shortlisted claims.
- [ ] Confirm website fetching uses `OVERPASS_API_URL` only for the Overpass provider, `REQUEST_TIMEOUT_SECONDS` for request limits, and never writes `.env` values to evidence files.
- [ ] Run `python scripts/extract_website_evidence.py --input data/intermediate/companies_normalized_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/website_evidence_2026-11-08.jsonl --capture-index evidence/website_capture_index_2026-11-08.csv`.

**Verification:**
- [ ] Assert every non-`Unknown` qualification value has an evidence URL and retrieval date.
- Expected: Missing pages are recorded as `Unknown` with fetch status; no missing evidence becomes zero.
- [ ] Manually audit all intended shortlist candidates and a random non-shortlist sample against official source pages.

**Exit Criteria:**
- Every canonical account has qualification fields, evidence status, and a reproducible source trail.

### Task 5: Classify buying signals and calculate the lead score

**Purpose:**
- Rank accounts transparently without confusing contact accessibility or unsupported predictive probability with commercial fit.

**Task Function:**
- Convert qualification evidence and TED/news/project signals into weighted scores, evidence coverage, and actionability fields.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Scoring is a shared decision rule; one owner prevents inconsistent weights and tiers.

**Specification Coverage:**
- Five KPI weights, separate Lead Fit/Opportunity/Buying Signal/Actionability, narrow signals, evidence coverage, and deterministic tiers.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/website_evidence_2026-11-08.jsonl`, `data/raw/ted_2026-11-07.json`, company news/projects evidence, `config/lead_generation_schema.json`
- Modify: `scripts/score_leads.py`, `data/processed/lead_scores_2026-11-08.csv`, `evidence/scoring_audit_2026-11-08.csv`
- Verify: score output and scoring audit

**Dependencies:**
- Task 4 complete; TED and other signal inputs are available or explicitly unavailable.

**Authority:**
- Preauthorized local actions: Apply the approved deterministic weights, classify observable signals, write score outputs and audits, and run recalculation checks.
- Stop for: Predictive conversion probabilities, unrecorded weight changes, or use of contact availability to raise Lead Fit.

**Steps:**
- [ ] Normalize each qualification dimension to a documented 0–100 input while preserving the original evidence state.
- [ ] Calculate `Lead Fit = 0.30*service_fit + 0.25*residential_weg + 0.25*portfolio_potential + 0.10*geographic_fit + 0.10*buying_growth_signal`.
- [ ] Calculate `Evidence Coverage = usable-evidence KPI weight / total KPI weight` and preserve `Unknown` inputs in the audit.
- [ ] Classify signals as `Strong`, `Medium`, `Weak`, `None found`, or `Unknown` using only observable tenders, provider changes, meter projects, growth, modernization, digitalization, or relevant hiring.
- [ ] Calculate Actionability separately using named-contact availability, role relevance, verified email status, and evidence completeness.
- [ ] Assign `A` for Lead Fit >= 75 and Evidence Coverage >= 75%; `B` for Lead Fit >= 60 and Evidence Coverage >= 50%; `C` for Lead Fit >= 45; `Research` otherwise or when evidence is insufficient.
- [ ] Tie-break by Evidence Coverage, then Portfolio Potential, then signal strength; never use arbitrary row order.
- [ ] Run `python scripts/score_leads.py --qualification data/intermediate/website_evidence_2026-11-08.jsonl --ted data/raw/ted_2026-11-07.json --schema config/lead_generation_schema.json --output data/processed/lead_scores_2026-11-08.csv --audit-output evidence/scoring_audit_2026-11-08.csv`.

**Verification:**
- [ ] Independently recalculate at least 20 rows from raw score inputs.
- Expected: Stored scores, coverage, actionability, and tiers match the independent calculation; no `Unknown` input is silently encoded as zero.

**Exit Criteria:**
- Every qualified account has a reproducible score, tier, evidence coverage, signal classification, and separate actionability status.

### Task 6: Enrich the priority shortlist with named contacts

**Purpose:**
- Produce sales-actionable contacts without enriching low-fit accounts.

**Task Function:**
- Research named responsibilities, public business emails, verification status, and source evidence for the top 20–30 accounts.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Contact work is a bounded P1 lane restricted to accounts selected by the score output.

**Specification Coverage:**
- Team/Impressum-first discovery, Hunter shortlist enrichment, role relevance, email provenance, and no inferred-email claims.

**Required Skills:**
- `browser-use`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/processed/lead_scores_2026-11-08.csv`, official team/Impressum pages, Hunter results for shortlisted domains, `.env`
- Modify: `scripts/build_shortlist.py`, `data/processed/priority_leads_2026-11-08.csv`, `data/processed/contacts_2026-11-08.csv`, `evidence/contact_sources_2026-11-08.csv`
- Verify: priority and contact CSVs

**Dependencies:**
- Task 5 complete.

**Authority:**
- Preauthorized local actions: Read public team/Impressum pages, use account-available Hunter lookup or verification for shortlisted domains, and write contact records and provenance locally.
- Stop for: Paid enrichment beyond allowance, email sending, out-of-scope personal-data collection, or inferred addresses labeled verified.

**Steps:**
- [ ] Generate the shortlist from A-tier accounts first, then highest-evidence B-tier accounts until 20–30 accounts are covered.
- [ ] Search team, management, contact, and Impressum pages for Geschäftsführer/in, Inhaber/in, Technische Leitung, Einkauf/Procurement, Leitung WEG-Verwaltung, and Head of Property Management.
- [ ] Verify that each named person is associated with the company at retrieval time.
- [ ] Use Hunter only for shortlisted domains and store `email_source`, `verification_status`, `last_verified`, and the source URL or result identifier.
- [ ] Confirm Hunter authentication is read from `HUNTER_API_KEY` through `scripts/runtime_config.py` and never passed on the command line.
- [ ] Record no contact as `Unknown` and do not lower Lead Fit because contact data is missing.
- [ ] Run `python scripts/build_shortlist.py --scores data/processed/lead_scores_2026-11-08.csv --schema config/lead_generation_schema.json --priority-output data/processed/priority_leads_2026-11-08.csv --contacts-output data/processed/contacts_2026-11-08.csv --evidence-output evidence/contact_sources_2026-11-08.csv --max-priority-accounts 30`.

**Verification:**
- [ ] Assert every email row has a source, verification status, and last-verified date.
- Expected: No inferred pattern is labeled `Verified`; shortlist size is no more than 30 unless the scope decision is recorded.
- [ ] Manually inspect the top 10 contacts against a source page or verification record.

**Exit Criteria:**
- The shortlist contains 20–30 deeply reviewed accounts where feasible, and the contact file contains 10–20 relevant named contacts where evidence supports them.

### Task 7: Build the workbook and methodology source register

**Purpose:**
- Turn canonical data and evidence into a business-facing workbook with reproducible methodology.

**Task Function:**
- Assemble the five required tabs, formatting, source links, calculations, and limitations.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Workbook construction consumes only accepted canonical files from Tasks 3–6.

**Specification Coverage:**
- Five-tab workbook, Sales usability, evidence traceability, methodology documentation, and quality-over-row-count target.

**Required Skills:**
- `spreadsheets:Spreadsheets`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: normalized companies, scores, priority leads, contacts, and evidence registers
- Modify: `scripts/build_workbook.py`, `output/berlin-hausverwaltung-leads_2026-11-09.xlsx`, `evidence/workbook_build_2026-11-09.json`
- Verify: all five workbook tabs and build report

**Dependencies:**
- Tasks 3–6 complete.

**Authority:**
- Preauthorized local actions: Create and format the workbook from accepted local inputs; write formulas, hyperlinks, filters, frozen headers, and methodology content; run workbook validation.
- Stop for: Manual edits bypassing canonical inputs, unsupported claims added during formatting, or unapproved external export.

**Steps:**
- [ ] Build `01_All_Leads` from the canonical universe with primary source links.
- [ ] Build `02_Qualification` with score inputs, Lead Fit, Evidence Coverage, tier, signal strength, and evidence URLs.
- [ ] Build `03_Priority_Leads` with priority reason, key evidence, research gap, actionability, and next action.
- [ ] Build `04_Contacts` with person, role, relevance, email, evidence, verification, LinkedIn, and last-verified fields.
- [ ] Build `05_Methodology_Sources` with KPI definitions, weights, thresholds, source policy, `Unknown` handling, limitations, retrieval dates, and QA notes.
- [ ] Add filters, frozen headers, readable widths, source hyperlinks, and conditional formatting without changing source values.
- [ ] Run `python scripts/build_workbook.py --companies data/intermediate/companies_normalized_2026-11-07.csv --scores data/processed/lead_scores_2026-11-08.csv --priority data/processed/priority_leads_2026-11-08.csv --contacts data/processed/contacts_2026-11-08.csv --sources evidence/source_register_2026-11-07.csv --output output/berlin-hausverwaltung-leads_2026-11-09.xlsx --build-report evidence/workbook_build_2026-11-09.json`.

**Verification:**
- [ ] Confirm exactly five required tabs exist with non-empty headers.
- Expected: Every priority row maps to one canonical `Company ID`; source URLs are clickable; tiers and scores match processed CSVs.
- [ ] Run `python scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json`.
- Expected: No missing columns, duplicate IDs, invalid enums, or unsupported email states.

**Exit Criteria:**
- The workbook is readable by Sales, traceable to evidence, and reproducible from accepted local inputs.

### Task 8: Produce the five-slide methodology presentation

**Purpose:**
- Explain the objective, evidence model, results, limitations, and scalable next phase without overstating the MVP.

**Task Function:**
- Create a concise deck whose counts, tiers, and claims derive from the final workbook.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Presentation content depends on accepted workbook counts and QA results.

**Specification Coverage:**
- Five-slide submission structure and Phase 2 competitor/intermarket/regulatory/buying-signal architecture.

**Required Skills:**
- `presentations:Presentations`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `output/berlin-hausverwaltung-leads_2026-11-09.xlsx`, `evidence/qa_report_2026-11-09.md`
- Modify: `presentation/berlin-hausverwaltung-methodology_2026-11-09.md`, `scripts/build_deck.py`, `output/berlin-hausverwaltung-methodology_2026-11-09.pptx`
- Verify: all five rendered slides

**Dependencies:**
- Task 7 complete.

**Authority:**
- Preauthorized local actions: Create and export the five-slide deck from the final workbook and QA report; correct layout and copy without changing source data.
- Stop for: Unreconciled results, unsupported market claims, publication, or an unrecorded slide-count change.

**Steps:**
- [ ] Create the exact five-slide source at `presentation/berlin-hausverwaltung-methodology_2026-11-09.md`.
- [ ] Slide 1: objective and funnel `Market → Qualified Accounts → Priority Leads → Contacts`.
- [ ] Slide 2: discovery sources, raw count, duplicates removed, final unique count, and source coverage.
- [ ] Slide 3: five KPI weights, Lead Fit versus Evidence Coverage, and `Unknown ≠ 0`.
- [ ] Slide 4: final lead counts, A/B/C/Research distribution, top prospects, signal examples, and named-contact coverage.
- [ ] Slide 5: validated current workflow plus Phase 2 architecture `Macro/Regulation → Competitors → Intermarkets → Account Events → Buying Signals → Automated Prioritization → CRM Feedback`.
- [ ] Run `python scripts/build_deck.py --content presentation/berlin-hausverwaltung-methodology_2026-11-09.md --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --output output/berlin-hausverwaltung-methodology_2026-11-09.pptx`.

**Verification:**
- [ ] Render and inspect all five slides at standard presentation size.
- Expected: No clipped text, unreadable URLs, unsupported counts, or claims absent from the workbook and QA report.
- [ ] Compare every displayed count and tier distribution to the workbook.

**Exit Criteria:**
- The deck is exactly five slides, reconciles to the workbook, and distinguishes the MVP from Phase 2.

### Task 9: Run final QA and assemble the submission package

**Purpose:**
- Prove that workbook and deck are internally consistent, evidence-backed, and ready for delivery.

**Task Function:**
- Run deterministic data checks, link and provenance audits, manual sample review, and final package validation.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Final acceptance must reconcile every output to canonical data and must not rely on unchecked task boxes.

**Specification Coverage:**
- Duplicate checks, broken links, formula consistency, `Unknown` handling, email provenance, ranking anomalies, and Monday readiness.

**Required Skills:**
- `browser-use`
- `skill-verification-before-completion`

**Files And Symbols:**
- Inspect: all files under `data/`, `evidence/`, `output/`, and `presentation/`
- Modify: `scripts/qa_leads.py`, `scripts/validate_deliverables.py`, `evidence/qa_report_2026-11-09.md`, `evidence/qa_sample_2026-11-09.csv`
- Verify: workbook and methodology deck

**Dependencies:**
- Tasks 7 and 8 complete.

**Authority:**
- Preauthorized local actions: Run local QA, inspect public source URLs, write QA reports and samples, and make bounded corrections to task-owned outputs before rerunning checks.
- Stop for: Failed checks that cannot be repaired from canonical inputs, external publication, destructive cleanup, or scope change.

**Steps:**
- [ ] Check duplicates on domains, canonical company IDs, priority rows, and contacts.
- [ ] Validate required columns, enums, score ranges, tier thresholds, evidence URLs, retrieval dates, and `Unknown` handling.
- [ ] Check priority-list URLs and manually inspect at least 10 priority accounts plus a non-priority sample.
- [ ] Verify every contact email has a source and status and no inferred pattern is marked verified.
- [ ] Reconcile workbook counts and tier distributions with the presentation.
- [ ] Record inaccessible sources, unresolved duplicates, missing signals, and deferred enrichment in `evidence/qa_report_2026-11-09.md`.
- [ ] Run `python scripts/qa_leads.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json --evidence-dir evidence --report evidence/qa_report_2026-11-09.md --sample-output evidence/qa_sample_2026-11-09.csv`.
- [ ] Run `python scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09.pptx --qa-report evidence/qa_report_2026-11-09.md`.

**Verification:**
- [ ] Require zero-error results from `scripts/qa_leads.py` and `scripts/validate_deliverables.py`.
- Expected: Outputs exist, workbook/deck counts reconcile, high-priority claims have sources, and remaining gaps are explicit.
- [ ] Confirm the package contains workbook, deck, QA report, source register, scoring audit, and contact-source register.

**Exit Criteria:**
- The submission package is internally consistent, evidence-backed, and ready for delivery on November 9, 2026.

## Verification

Run after Tasks 1–9; checked boxes are not proof by themselves.

- `python -m json.tool config/lead_generation_schema.json`
- `python scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json`
- `python scripts/qa_leads.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json --evidence-dir evidence --report evidence/qa_report_2026-11-09.md --sample-output evidence/qa_sample_2026-11-09.csv`
- `python scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09.pptx --qa-report evidence/qa_report_2026-11-09.md`
- `git check-ignore -q .env`
- `rg -n "APIFY_API_TOKEN|HUNTER_API_KEY|Bearer [A-Za-z0-9._-]+" data evidence output presentation --glob '!*.md'`
- Render and visually inspect all five slides.
- Reconcile final company, priority-lead, contact, and tier counts between workbook, QA report, and deck.

Expected final evidence:

- Approximately 100–200 unique Berlin-relevant companies where source coverage permits.
- Approximately 20–30 deeply reviewed priority accounts where time and evidence permit.
- Approximately 10–20 relevant named contacts where public evidence supports them.
- Evidence URLs for all important non-`Unknown` claims.
- Explicit records for inaccessible sources, unresolved entities, missing signals, and deferred work.
- No external publication, email sending, paid overage, predictive probability, or Phase 2 implementation in the deadline package.
- `.env` is ignored, `.env.example` is tracked, and no credential value appears in data, evidence, workbook, deck, or logs.

## Completion Criteria

The plan is ready for completion verification when:

1. The canonical schema, raw source register, normalized company universe, evidence files, scoring audit, shortlist, contacts, workbook, deck, and QA report exist at the declared paths.
2. Every required task has passed task-local verification and no required task remains blocked.
3. Workbook and deck counts, tier distributions, and claims reconcile to canonical processed data.
4. Missing evidence is represented as `Unknown` or an explicit limitation, never an invented zero or probability.
5. Contact emails have source and verification status; inferred patterns are excluded from verified counts.
6. `.env` is ignored, `.env.example` is the tracked configuration contract, and provider scripts load settings through `scripts/runtime_config.py`.
7. Deviations, provider gaps, unresolved duplicates, and deferred Phase 2 work are recorded in `evidence/qa_report_2026-11-09.md`.
8. Final validation commands return success and the five-slide deck has been visually inspected.
9. The plan remains `proposed` until `skill-verification-before-completion` performs fresh final verification and returns `verified`; only then may status change to `completed`.
