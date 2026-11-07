---
layer: change
artifact_type: plan
template_id: implementation-plan
contract_version: "1"
status: completed
name: berlin-hausverwaltung-lead-generation
targets:
  - .env.example
  - .gitignore
  - config/lead_generation_schema.json
  - scripts/runtime_config.py
  - scripts/import_discovery.py
  - scripts/normalize_dedupe.py
  - scripts/extract_website_evidence.py
  - scripts/collect_buying_signals.py
  - scripts/score_leads.py
  - scripts/build_shortlist.py
  - scripts/build_workbook.py
  - scripts/qa_leads.py
  - scripts/validate_workbook.py
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

Implement structural Lead Fit with service/ICP fit 35%, residential/WEG
relevance 30%, portfolio potential 25%, and geographic/operational fit 10%.
Keep Buying Signal, Opportunity Potential, Actionability, Evidence Coverage, and
Sales Priority separate from structural fit. Represent missing evidence as
`Unknown`, calculate observed-weight scores without silently treating unknowns as
zero, and emit a score audit that can recalculate every tier.

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
- Optional-source policy: Apify, TED, Hunter, and other external enrichment are optional inputs; manual CSV/JSON imports and partial outputs remain valid when a provider is unavailable.

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
- [ ] Create root `.env.example` with `APIFY_API_TOKEN=`, `HUNTER_API_KEY=`, `TED_API_BASE_URL=`, `OVERPASS_API_URL=https://overpass-api.de/api/interpreter`, `REQUEST_TIMEOUT_SECONDS=15`, `MAX_PAGES_PER_COMPANY=10`, `MAX_FETCH_RETRIES=2`, `APIFY_MAX_SPEND_USD=5.00`, and `MAX_PRIORITY_ACCOUNTS=30`.
- [ ] Copy `.env.example` to local root `.env` only during execution; keep credentials blank until explicitly supplied by the user and never commit the file.
- [ ] Add `.env` and `.env.*.local` to `.gitignore` while keeping `.env.example` tracked.
- [ ] Implement `scripts/runtime_config.py` with a standard-library `.env` parser, typed accessors, required-key validation per provider, and no secret values in exceptions or logs.
- [ ] Define `config/lead_generation_schema.json` with company identity, source provenance (`source_type`, `source_reuse_status`, `extraction_method`, `actor_id`, `actor_run_id`, `source_record_id`, `retrieved_at`, `evidence_level`), qualification, signals, `signal_search_status`, scores, tiers, contacts, and timestamps.
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

### Task 2: Collect and register raw company-discovery sources

**Purpose:**
- Build a broad raw company universe without spending shortlist-level effort on contacts.

**Task Function:**
- Import and register VDIV, Apify, permitted-directory, search, and Overpass company-discovery inputs while preserving provenance. Procurement events are collected separately in Task 5.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Source access and evidence boundaries are sensitive; one controller keeps collection and provenance consistent.

**Specification Coverage:**
- VDIV P0 discovery, targeted Apify actor usage, Overpass/OpenStreetMap supplementary discovery, and traceable URLs.

**Required Skills:**
- `browser-use`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: VDIV pages, permitted directory exports, Apify dataset export, Overpass result, and discovery searches
- Modify: `data/raw/vdiv_2026-11-07.csv`, `data/raw/apify_2026-11-07.json`, `data/raw/overpass_2026-11-07.json`, `evidence/source_register_2026-11-07.csv`, `scripts/import_discovery.py`
- Runtime dependency: `scripts/import_discovery.py` must load `APIFY_API_TOKEN`, `OVERPASS_API_URL`, `REQUEST_TIMEOUT_SECONDS`, and `APIFY_MAX_SPEND_USD` through `scripts/runtime_config.py`; no credential CLI flags.
- Verify: `data/intermediate/discovery_raw_2026-11-07.csv` and the source register

**Dependencies:**
- Task 1 complete.

**Authority:**
- Preauthorized local actions: Read public source pages, import available exports, write raw snapshots and source-register rows, and run `scripts/import_discovery.py` locally.
- Stop for: Login or CAPTCHA bypass, paid usage beyond available free credits, prohibited scraping, external state changes, or data outside the approved scope.

**Steps:**
- [ ] Export VDIV Berlin-Brandenburg results to `data/raw/vdiv_2026-11-07.csv` with original listing URLs.
- [ ] Run `apify/google-search-scraper` for targeted German discovery queries with one result page per query initially; save `data/raw/apify_2026-11-07.json` and record actor/run IDs.
- [ ] Use `apify/cheerio-scraper` for permitted static directory extraction; use `apify/web-scraper` only when the static extraction cannot obtain the required listing fields.
- [ ] Enforce an aggregate Apify spend cap of `$5.00` through `APIFY_MAX_SPEND_USD`; stop before any paid overage.
- [ ] Run the bounded Overpass/OpenStreetMap supplementary query and save `data/raw/overpass_2026-11-07.json`.
- [ ] Register source type, retrieval date, query/export identifier, access limitation, actor ID, actor run ID, extraction method, reuse status, and source URL in `evidence/source_register_2026-11-07.csv`.
- [ ] Confirm `scripts/import_discovery.py` reads provider credentials and endpoints only through `scripts/runtime_config.py` and redacts them from import reports.
- [ ] Run `python scripts/import_discovery.py --vdiv data/raw/vdiv_2026-11-07.csv --apify data/raw/apify_2026-11-07.json --overpass data/raw/overpass_2026-11-07.json --output data/intermediate/discovery_raw_2026-11-07.csv`.

**Verification:**
- [ ] Confirm every available raw file is non-empty and every imported row retains a source URL; allow missing optional source files when the source register records the reason.
- Expected: The import report gives row counts by source, records unavailable providers explicitly, and does not block canonical-company generation when Apify or Overpass is unavailable.

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
- Multi-field identity resolution, conservative fuzzy candidate detection, branch/parent handling, and raw provenance preservation.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/discovery_raw_2026-11-07.csv`, `config/lead_generation_schema.json`
- Modify: `scripts/normalize_dedupe.py`, `data/intermediate/companies_normalized_2026-11-07.csv`, `data/intermediate/dedupe_review_2026-11-07.csv`, `evidence/entity_resolution_2026-11-07.csv`
- Runtime dependency: Use `cleanco` for legal-form normalization, `RapidFuzz` for duplicate candidates, and `tldextract` with `urllib.parse` for registrable-domain normalization; do not add Splink or libpostal for the deadline.
- Verify: canonical company output and dedupe review queue

**Dependencies:**
- Task 2 complete.

**Authority:**
- Preauthorized local actions: Run deterministic normalization and deduplication locally; write canonical rows and review queues under `data/intermediate/` and `evidence/`.
- Stop for: Destructive raw-row removal, unresolved legal-entity ambiguity affecting ownership, or unsupported branch collapse.

**Steps:**
- [ ] Normalize domains by lowercasing, removing schemes, stripping `www.`, removing tracking parameters, and deriving the registrable host with `tldextract` and `urllib.parse`.
- [ ] Normalize names by trimming whitespace, standardizing punctuation, and removing legal-form suffixes with `cleanco` while retaining the legal name separately.
- [ ] Normalize addresses into street, postal code, city, and region; classify Berlin versus Brandenburg without inferring portfolio geography from office address alone.
- [ ] Generate duplicate candidates using this hierarchy: exact normalized domain; exact normalized company plus postcode; exact normalized address; fuzzy company name plus same postcode; fuzzy name plus similar address.
- [ ] Auto-merge only when the normalized identity and location evidence agree; send all ambiguous candidates to `data/intermediate/dedupe_review_2026-11-07.csv`.
- [ ] Do not require domain uniqueness: shared domains and addresses can represent branches or separate legal entities.
- [ ] Preserve branch/parent relationships and record the resolution reason in `evidence/entity_resolution_2026-11-07.csv`.
- [ ] Run `python scripts/normalize_dedupe.py --input data/intermediate/discovery_raw_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/companies_normalized_2026-11-07.csv --review-output data/intermediate/dedupe_review_2026-11-07.csv --evidence-output evidence/entity_resolution_2026-11-07.csv`.

**Verification:**
- [ ] Assert `Company ID` uniqueness, source-record traceability, and the absence of unresolved auto-merge conflicts in the canonical output.
- Expected: Shared domains remain possible, ambiguous candidates remain in the review queue, and no record is silently merged on domain alone.

**Exit Criteria:**
- The canonical company universe is deduplicated, traceable to raw sources, and ready for qualification.

### Task 4: Extract and validate website qualification evidence

**Purpose:**
- Determine whether each company is a relevant Hausverwaltung and capture evidence for service, residential/WEG, portfolio, and geography fields within a bounded fetch budget.

**Task Function:**
- Fetch a bounded set of official website pages locally first, use an Apify crawler only as a fallback, extract structured claims, and preserve claim-level URLs and retrieval dates.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: Website evidence is the primary qualification boundary and requires source-first validation.

**Specification Coverage:**
- Official website verification, cheap-fetch-first extraction, bounded crawler fallback, source-backed qualification, and `Unknown` for missing evidence.

**Required Skills:**
- `browser-use`
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/companies_normalized_2026-11-07.csv`, official company websites, `config/lead_generation_schema.json`, `.env`
- Modify: `scripts/extract_website_evidence.py`, `data/intermediate/website_evidence_2026-11-08.jsonl`, `evidence/website_capture_index_2026-11-08.csv`
- Runtime dependency: Use `requests` and `BeautifulSoup` first; use `apify/website-content-crawler` only when local extraction lacks sufficient content.
- Verify: the website evidence JSONL and capture index

**Dependencies:**
- Task 3 complete.

**Authority:**
- Preauthorized local actions: Read public official websites within published access boundaries; write evidence, retrieval dates, and failed-fetch records locally; use LLM extraction only as an assistant to human or rule validation.
- Stop for: Authentication, robots or terms violations, CAPTCHA bypass, unsupported inference, or any request to label an unverified claim as fact.

**Steps:**
- [ ] Fetch at most `MAX_PAGES_PER_COMPANY` pages per domain from the homepage plus services, WEG/residential, portfolio/references, news/projects, team, and Impressum paths when public.
- [ ] Use `REQUEST_TIMEOUT_SECONDS` and `MAX_FETCH_RETRIES` from `scripts/runtime_config.py`; do not recursively crawl entire sites.
- [ ] If local fetching yields insufficient text after the bounded retry policy, invoke `apify/website-content-crawler` for the same page budget and record the actor/run IDs.
- [ ] Extract service fit, residential/WEG relevance, visible portfolio indicators, Berlin/operational relevance, and evidence snippets.
- [ ] Store each claim with `value`, `confidence`, `evidence_url`, `evidence_excerpt`, `retrieved_at`, and `Unknown` when evidence is absent.
- [ ] Classify management type and reject clearly irrelevant businesses without deleting the raw row.
- [ ] Use the LLM only to propose structured fields from captured text; require a source URL and human review for shortlisted claims.
- [ ] Confirm website fetching uses `REQUEST_TIMEOUT_SECONDS`, `MAX_PAGES_PER_COMPANY`, and `MAX_FETCH_RETRIES` from `scripts/runtime_config.py`, uses the Apify fallback only after local failure, and never writes `.env` values to evidence files.
- [ ] Run `python scripts/extract_website_evidence.py --input data/intermediate/companies_normalized_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/website_evidence_2026-11-08.jsonl --capture-index evidence/website_capture_index_2026-11-08.csv`.

**Verification:**
- [ ] Assert every non-`Unknown` qualification value has an evidence URL and retrieval date.
- Expected: Missing pages are recorded as `Unknown` with fetch status; page count and retry limits are enforced; no missing evidence becomes zero.
- [ ] Manually audit all intended shortlist candidates and a random non-shortlist sample against official source pages.

**Exit Criteria:**
- Every canonical account has qualification fields, evidence status, and a reproducible source trail.

### Task 5: Collect and link buying signals, then calculate lead score

**Purpose:**
- Keep procurement events separate from company discovery while ranking accounts without confusing timing signals with structural customer fit.

**Task Function:**
- Collect account-attributable events, link them to canonical companies, and calculate structural fit, evidence coverage, actionability, and Sales Priority.

**Template Profile:**
- Controller-selected: `none (lead controller)`
- Selection basis: The event lane and score lane share a task boundary but retain separate datasets and evidence.

**Specification Coverage:**
- Separate company/event datasets, account-specific signal attribution, structural Lead Fit, `Unknown` handling, and deterministic prioritization.

**Required Skills:**
- `skill-executing-plans`

**Files And Symbols:**
- Inspect: `data/intermediate/website_evidence_2026-11-08.jsonl`, official company news/projects pages, `config/lead_generation_schema.json`
- Modify: `scripts/collect_buying_signals.py`, `scripts/score_leads.py`, `data/raw/buying_events_2026-11-08.json`, `data/processed/company_event_links_2026-11-08.csv`, `data/processed/lead_scores_2026-11-08.csv`, `evidence/buying_signal_audit_2026-11-08.csv`, `evidence/scoring_audit_2026-11-08.csv`
- Runtime dependency: TED is an optional, unauthenticated event source read through `TED_API_BASE_URL`; no event source may block company qualification or workbook generation.
- Verify: event records, company-event links, score output, and both audits

**Dependencies:**
- Task 4 complete; TED and other signal inputs are available or explicitly unavailable.

**Authority:**
- Preauthorized local actions: Collect public event evidence, link events to canonical accounts, apply approved structural weights, and run local recalculation checks.
- Stop for: Unattributed event-to-account matches, predictive conversion probabilities, unrecorded weight changes, or use of contact availability to raise Lead Fit.

**Steps:**
- [ ] Query TED for metering, heating-cost billing, meter replacement, remote-meter, and related procurement terms; store `buyer`, `event_type`, `publication_date`, `deadline`, `scope`, and `source_url` in `data/raw/buying_events_2026-11-08.json`.
- [ ] Capture directly attributable company news, projects, modernization, portfolio-growth, and relevant hiring signals in the same event schema; retain the original source URL.
- [ ] Match events to canonical companies by buyer/name/domain evidence; send ambiguous matches to the review queue and link only verified associations in `data/processed/company_event_links_2026-11-08.csv`.
- [ ] Set `signal_search_status` to `searched` or `not searched`; use `None found` only after the configured searches ran, otherwise use `Unknown`.
- [ ] Normalize service fit, residential/WEG relevance, portfolio potential, and geographic fit to documented 0–100 values while preserving evidence states.
- [ ] Calculate structural Lead Fit over observed weights only: `sum(observed_weight * observed_value) / sum(observed_weight)` using 35% service fit, 30% residential/WEG, 25% portfolio potential, and 10% geographic fit.
- [ ] Calculate Evidence Coverage as `observed_weight / 100`; require Evidence Coverage >= 75% for an A tier, >= 50% for B or C, and assign `Research` below 50% regardless of raw score.
- [ ] Classify Buying Signal separately as `Strong`, `Medium`, `Weak`, `None found`, or `Unknown`; calculate Actionability separately using role, contact, and verification evidence.
- [ ] Derive Sales Priority deterministically: `Pursue` for A tier plus Evidence Coverage >= 75% and `Actionability=Ready`; `Research` for A/B accounts lacking readiness or requiring signal/contact follow-up; `Defer` for C/Research accounts or unsupported matches.
- [ ] Tie-break equal tiers by Evidence Coverage, then Portfolio Potential, then verified signal strength; never use arbitrary row order.
- [ ] Run `python scripts/collect_buying_signals.py --companies data/intermediate/companies_normalized_2026-11-07.csv --ted-output data/raw/buying_events_2026-11-08.json --links-output data/processed/company_event_links_2026-11-08.csv --audit-output evidence/buying_signal_audit_2026-11-08.csv`.
- [ ] Run `python scripts/score_leads.py --qualification data/intermediate/website_evidence_2026-11-08.jsonl --events data/raw/buying_events_2026-11-08.json --event-links data/processed/company_event_links_2026-11-08.csv --schema config/lead_generation_schema.json --output data/processed/lead_scores_2026-11-08.csv --audit-output evidence/scoring_audit_2026-11-08.csv`.

**Verification:**
- [ ] Independently recalculate at least 20 rows from raw score inputs.
- Expected: Structural scores exclude Buying Signal and Actionability; coverage gates high-confidence tiers; no `Unknown` input is silently encoded as zero; only verified event links create account-specific signals.

**Exit Criteria:**
- Event data is separate and attributable, and every qualified account has reproducible structural fit, evidence coverage, signal classification, actionability, Sales Priority, and tier.

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
- [ ] Generate the shortlist from `Pursue` accounts first, then highest-fit `Research` accounts until 20–30 accounts are covered.
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
- [ ] Build `02_Qualification` with score inputs, structural Lead Fit, Evidence Coverage, tier, Buying Signal, Actionability, Sales Priority, and evidence URLs.
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

## Execution Record

- Completed the approved MVP on the attached `main` checkout.
- Discovery: 302 public VDIV Berlin-Brandenburg records imported; 302 canonical rows retained after deterministic normalization.
- Website evidence: 279 domains fetched successfully; 23 fetch failures remain explicit in `evidence/website_capture_index_2026-11-08.csv`.
- Shortlist: 30 accounts selected; 26 published business emails retained with source and status evidence.
- Deliverables: five-tab workbook and five-slide methodology deck generated and reconciled.
- Approved deferrals: Apify, Overpass, TED, and Hunter API integrations were not configured in the local `.env`; public/manual evidence remained sufficient for this MVP, and the gaps are recorded in QA evidence.
- Visual inspection: all five PowerPoint slides were rendered through the installed PowerPoint runtime and inspected for clipping, unreadable text, and slide-count mismatch.

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
- Company discovery records and buying-event records remain separate; only verified company-event links can create account-specific Buying Signals.
- Structural Lead Fit excludes Buying Signal and Actionability, and high-confidence tiers require the declared Evidence Coverage minimum.

## Completion Criteria

The plan is ready for completion verification when:

1. The canonical schema, raw source register, normalized company universe, evidence files, scoring audit, shortlist, contacts, workbook, deck, and QA report exist at the declared paths.
2. Every required task has passed task-local verification and no required task remains blocked.
3. Workbook and deck counts, tier distributions, and claims reconcile to canonical processed data.
4. Missing evidence is represented as `Unknown` or an explicit limitation, never an invented zero or probability.
5. Contact emails have source and verification status; inferred patterns are excluded from verified counts.
6. `.env` is ignored, `.env.example` is the tracked configuration contract, and provider scripts load settings through `scripts/runtime_config.py`.
7. Company discovery and buying-event datasets remain separate; optional provider failures and unresolved event matches are recorded without blocking the deliverable.
8. Structural Lead Fit excludes Buying Signal and Actionability; tier gates and score recalculation are proven by the scoring audit.
9. Deviations, provider gaps, unresolved duplicates, and deferred Phase 2 work are recorded in `evidence/qa_report_2026-11-09.md`.
10. Final validation commands return success and the five-slide deck has been visually inspected.
11. Fresh final verification returned `verified`; the plan status is now `completed`.
