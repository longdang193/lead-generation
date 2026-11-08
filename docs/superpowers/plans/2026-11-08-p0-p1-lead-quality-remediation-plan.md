---
layer: change
artifact_type: plan
status: complete
template_id: implementation-plan
contract_version: "1"
name: berlin-lead-quality-remediation
targets:
  - config/lead_generation_schema.json
  - scripts/import_discovery.py
  - scripts/normalize_dedupe.py
  - scripts/extract_website_evidence.py
  - scripts/collect_buying_signals.py
  - scripts/score_leads.py
  - scripts/build_shortlist.py
  - scripts/qa_leads.py
  - scripts/lead_contract.py
  - tests/
  - evidence/
  - data/intermediate/
  - data/processed/
  - output/
---

# Berlin Lead Quality Remediation Plan

## Review Resolution

The plan review identified three blocking defects and two material risks. This
revision resolves them before execution:

- Task 2 now requires a fresh VDIV/permitted-directory backfill and quarantine
  of malformed legacy snapshots instead of merely reimporting them.
- Task 6 now builds the final workbook before semantic QA; Task 7 validates
  that same workbook and no longer rebuilds it after QA.
- Task 4 defines deterministic signal and actionability transitions. Contact
  availability does not change structural fit, actionability, or sales
  priority, so the shortlist remains selection-stable.
- The final workbook and QA gate share a run manifest containing input/output
  hashes, configuration/version metadata, and the generated run identifier.
- Task 5 and QA define public-professional-source, minimization, retention,
  stale-contact downgrade, and sales-export boundaries.

## Goal

Turn the current Berlin Hausverwaltung pipeline into an evidence-first, sales-usable workflow for the nine requested P0/P1 components: company discovery, deduplication and normalization, Berlin/Hausverwaltung validation, qualification KPIs, evidence URLs, lead ranking, named decision-makers, buying signals, and personal business email.

Preserve the approved structural weights from docs/superpowers/plans/2026-11-07-berlin-hausverwaltung-lead-generation-plan.md: service fit 35%, residential/WEG relevance 30%, portfolio potential 25%, geographic/operational fit 10%. Keep structural fit separate from buying signal, actionability, evidence coverage, and sales priority. Missing evidence remains Unknown; it is never converted to zero or a positive default.

This is a remediation plan, not an approval to publish or send outreach. External provider calls, public-site retrieval, paid enrichment, publication, and email sending remain bounded by task authority.

## Consolidated Review Basis

Accepted as validated because each item appears in both completed visible review responses and the checked-out source/generated artifacts:

- scripts/normalize_dedupe.py:82-95 auto-discards rows on (host, postcode) or host alone when postcode is missing; fuzzy candidates are reviewed but still appended to canonical output.
- scripts/normalize_dedupe.py:103-115 defaults missing city/region to Berlin and assigns Probable without positive Berlin evidence; scripts/import_discovery.py:27-39 drops address/provider metadata from JSON inputs.
- scripts/extract_website_evidence.py:76-91 iterates over a pre-sliced page list, so discovered pages are not visited. evidence/website_capture_index_2026-11-08.csv confirms pages_checked=1 for all 311 rows.
- scripts/extract_website_evidence.py:93-107 extracts combined-text keyword claims and assigns the first checked URL; mietverwaltung participates in the residential/WEG claim patterns.
- scripts/score_leads.py:39-47,68-86 accepts --events but never reads it, emits only Unknown/Unavailable signal states, hard-codes actionability, and never emits Pursue. Current artifacts show 311 Unknown buying signals, 311 Unavailable search statuses, and zero event links.
- scripts/build_shortlist.py:75-95 sorts before contact enrichment and uses loose regex contact extraction. Current contacts include non-person names such as "unseren Immobilienverwaltern" and "Immobilienfonds haben".
- scripts/build_shortlist.py:47-60 maps both Hunter valid and accept_all to Verified, selects only first names, and can replace stronger official evidence.
- scripts/qa_leads.py:33-78 accepts --schema and --evidence-dir but does not apply them. Current QA reports zero errors despite 187 A-tier rows, 124 Research rows, and the defects above.
- config/lead_generation_schema.json:30-52 disagrees with emitted values/fields: Moderate versus approved Medium, numeric sales_priority versus strings, contact_verification_status versus emitted verification_status, and weak conditional requirements.
- Current generated baseline: 311 companies, 289 URL-like names, 311 missing addresses, 308 Confirmed Berlin rows, 9 confirmed portfolio sizes, and a 30-row shortlist.

- Plan-review finding: reimporting the malformed VDIV snapshot cannot recover
  missing identity/location fields; final QA must run after final workbook
  regeneration; signal/actionability transitions and same-run provenance must
  be deterministic.

External claims in the pasted assessments about richer live VDIV content or exact live-directory counts are not treated as current implementation facts until bounded retrieval validates them. The plan recovers only fields available from permitted sources and fixtures.

## Implementation Outcomes

### Canonical company universe
Accepted companies retain legal/name/domain/address fields, explicit Berlin evidence, raw-source provenance, and a review queue for unresolved entities. No row is silently merged on domain alone.

### Evidence-backed qualification
Every non-Unknown service, WEG/residential, portfolio, or geographic claim has a matching page URL, excerpt, retrieval timestamp, and confidence. The bounded crawler visits discovered relevant pages and preserves failures explicitly.

### Signal-aware prioritization
Score and priority outputs populate buying signal, search status, actionability, sales priority, tier, coverage, and audit fields. Structural fit remains independent of signals/contact availability; final ordering is deterministic and tier-first.

### Verified outreach owners
Contact outputs distinguish named person, role, public business email, source page, and verification status. Generic mailboxes, catch-all domains, loose regex names, and unbound person/email pairs cannot count as verified personal contacts.

### Enforced QA and reconciled deliverables
QA consumes schema and evidence artifacts, validates cross-file relationships/ranking semantics, and fails on unsupported claims. Workbook, deck, QA report, and evidence registers are regenerated only after focused checks pass.

## Execution Approach

- Mode: inline sequential
- Coordination: none
- Required skills: skill-executing-plans, skill-test-driven-development, skill-backend-verification, skill-verification-before-completion
- Isolation: current workspace; preserve unrelated untracked output/~$berlin-hausverwaltung-leads_2026-11-09.xlsx
- Commit policy: no commits during execution; publication requires separate authorization
- Preauthorized local actions: edit declared source/test/schema/docs files, run bounded configured-provider reads, regenerate declared local artifacts, and run listed checks
- User-approval actions: push, publish, merge, delete raw evidence, send email, spend beyond configured caps, or change approved weights
- Parallel ownership: none; schema, scores, generated outputs, and QA are serialized shared surfaces
- Sequential fallback: execute Tasks 1–7 in order and stop at the first failed exit criterion

## Task Breakdown

### Task 1: Establish the canonical record contract and reusable quality helpers

Purpose: Remove schema/output drift before changing producers or consumers.
Task Function: Define one shared vocabulary and validation surface for identity, claims, signals, contacts, scores, and priority.
Template Profile: unresolved; resolve from agents/*.toml before execution.
Specification Coverage: SSOT schema, Unknown semantics, evidence requirements, signal states, actionability, sales priority, email status, and score auditability.
Required Skills: skill-code-standards; skill-test-driven-development.
Files And Symbols: Modify config/lead_generation_schema.json; add scripts/lead_contract.py with parse_evidence_urls, is_unknown, is_generic_mailbox, is_plausible_full_name, signal_rank, priority_rank, actionability_for, and sales_priority_for; add tests/test_lead_contract.py; update status fixtures in tests/test_provider_clients.py.
Dependencies: None.
Authority:
- Preauthorized local actions: edit schema/helper/tests and run local unit tests.
- Stop for: a required field or enum cannot be reconciled with approved scoring/contact behavior without a product decision.
Steps:
- [ ] Canonicalize buying_signal to Strong, Medium, Weak, None found, Unknown.
- [ ] Canonicalize signal_search_status to Searched, Not searched, Unavailable, Unknown; completed no-match searches use None found.
- [ ] Canonicalize actionability to Ready, Research, Monitor, Unknown and sales_priority to Pursue, Research, Defer.
- [ ] Use verification_status consistently across schema, contacts, evidence, QA, and workbook inputs; retire the mismatched alias.
- [ ] Keep logical evidence_urls as an array and centralize CSV parsing in parse_evidence_urls.
- [ ] Require evidence URL, excerpt, confidence, and retrieval time for every non-Unknown claim; require email source/status/date for non-empty emails.
- [ ] Add tests for enum drift, conditional requirements, generic mailboxes, plausible names, signal ordering, and priority ordering.
Verification:
- [ ] py -3 -m unittest tests.test_lead_contract tests.test_provider_clients -v
- [ ] py -3 -m json.tool config/lead_generation_schema.json
- [ ] Assert the tests reject current Moderate, numeric priority, missing contact evidence, and unsupported conditional records.
Exit Criteria: One importable contract/helper surface defines downstream statuses without duplicated enums.

### Task 2: Preserve discovery fields and make entity resolution conservative

Purpose: Recover source fields early and prevent false merges or unresolved duplicates from entering qualification.
Task Function: Normalize provider records while preserving legal identity, address, source provenance, and branch/parent ambiguity.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Berlin discovery, source fidelity, provider/VDIV field retention, deduplication, branch handling, and raw-to-canonical traceability.
Required Skills: skill-test-driven-development; skill-backend-verification.
Files And Symbols: Modify scripts/import_discovery.py read_rows/main, scripts/normalize_dedupe.py domain/clean_name/company_id/main, and provider normalization only where it drops fields; add tests/test_discovery.py, tests/test_normalize_dedupe.py, tests/fixtures/discovery_rich.json, and tests/fixtures/shared-host.csv; regenerate discovery, canonical, review, and entity-resolution CSVs.
Dependencies: Task 1.
Authority:
- Preauthorized local actions: read raw discovery files, run bounded configured retrievals, and write intermediate/evidence outputs.
- Stop for: raw-row deletion, unverified external access, or legal-entity ambiguity not resolvable from identity/location evidence.
Steps:
- [ ] Preserve available legal name, contact, email, phone, address, postcode, city, region, website, source ID/type, reuse status, extraction method, actor/run IDs, and retrieval time for CSV/JSON providers.
- [ ] Keep discovery_source_url separate from verified_company_domain; never use a directory/search host as company domain.
- [ ] Normalize names/legal suffixes and address components independently while retaining raw/legal names.
- [ ] Generate candidates by verified domain plus corroborating identity, exact name/postcode, exact address, then fuzzy name/location.
- [ ] Remove unconditional host/postcode merging. Shared host/domain or missing postcode creates review, not silent merge.
- [ ] Exclude ambiguous candidates from accepted scoring input while retaining every raw record and resolution reason.
- [ ] Preserve branch/parent relationships and keep missing location fields Unknown/empty rather than Berlin defaults.
- [ ] Before importing, refresh or re-extract VDIV/permitted-directory records
  when the supplied snapshot has URL-shaped names, missing addresses, or
  synthetic Berlin values; retain the malformed snapshot as quarantined input
  and record the replacement source, retrieval time, and snapshot hash.
- [ ] Add fixtures proving same-host companies remain distinct and rich provider rows retain all fields.
Verification:
- [ ] py -3 -m unittest tests.test_discovery tests.test_normalize_dedupe -v
- [ ] py -3 scripts/import_discovery.py --vdiv data/raw/vdiv_2026-11-07.csv --apify data/raw/apify_2026-11-07.json --overpass data/raw/overpass_2026-11-07.json --output data/intermediate/discovery_raw_2026-11-07.csv --source-register evidence/source_register_2026-11-07.csv --refresh-vdiv --quarantine-output data/intermediate/discovery_quarantine_2026-11-08.csv
- [ ] py -3 scripts/normalize_dedupe.py --input data/intermediate/discovery_raw_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/companies_normalized_2026-11-07.csv --review-output data/intermediate/dedupe_review_2026-11-07.csv --evidence-output evidence/entity_resolution_2026-11-07.csv
- [ ] Assert ID uniqueness, raw traceability, no host-only auto-merges, and no unresolved review candidate in accepted scoring input.
Exit Criteria: Canonical universe is conservative, source-complete, and safe for official-site qualification.

### Task 3: Repair bounded official-site qualification and claim-level evidence

Purpose: Make Berlin/Hausverwaltung qualification depend on correct official pages and exact supporting evidence.
Task Function: Crawl a bounded same-domain page queue, extract page-local claims, and preserve explicit Unknown states.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Berlin relevance, Hausverwaltung/WEG validation, portfolio evidence, claim URLs, timestamps, fetch failures, and fallback behavior.
Required Skills: skill-backend-verification; skill-test-driven-development; browser-use for manual source audits.
Files And Symbols: Modify scripts/extract_website_evidence.py claim/fetch/process/main; use runtime/provider config; update schema/claim shape; add tests/test_website_evidence.py and local HTML fixtures; regenerate website JSONL/capture index.
Dependencies: Tasks 1–2.
Authority:
- Preauthorized local actions: fetch public same-domain pages within configured limits, write evidence, and manually inspect declared samples.
- Stop for: authentication/CAPTCHA, robots/terms violations, unsupported inference, or requests to label unverified claims as fact.
Steps:
- [ ] Replace the pre-sliced for page_url in pages[:max_pages] with a bounded queue/index loop consuming appended URLs.
- [ ] Retain same verified-company-host URLs and final redirects; visit services, WEG/residential, portfolio, projects/news, team, contact, and Impressum pages within the page budget.
- [ ] Use the existing Apify fallback only after local retrieval is insufficient/JS-heavy, recording actor/run IDs and fallback reason.
- [ ] Extract claims page by page and attach each claim to the page containing its excerpt.
- [ ] Require explicit WEG/Wohnungseigentümergemeinschaft evidence for WEG Confirmed; Mietverwaltung remains separate service/management evidence.
- [ ] Derive Berlin Confirmed only from company office, explicit service area, or explicit managed-portfolio evidence.
- [ ] Require unit-bearing portfolio evidence for Confirmed; otherwise use Unknown/Probable with exact excerpt.
- [ ] Preserve failed/inaccessible pages and never replace missing evidence with a positive default.
- [ ] Add fixture tests for appended-link traversal, page-local URLs, Mietverwaltung/WEG separation, and absent Berlin evidence.
Verification:
- [ ] py -3 -m unittest tests.test_website_evidence -v
- [ ] py -3 scripts/extract_website_evidence.py --input data/intermediate/companies_normalized_2026-11-07.csv --schema config/lead_generation_schema.json --output data/intermediate/website_evidence_2026-11-08.jsonl --capture-index evidence/website_capture_index_2026-11-08.csv
- [ ] Assert every non-Unknown claim has exact URL, excerpt, confidence, and retrieval timestamp.
- [ ] Assert fixture sites with relevant links check more than one page and failures remain explicit.
- [ ] Manually inspect all final priority candidates and one non-priority sample; record unresolved cases in the QA report.
Exit Criteria: Qualification is evidence-backed, page-local, Berlin-specific, and reproducible within the fetch budget.

### Task 4: Implement attributable buying signals and reproducible structural scoring

Purpose: Populate signal fields and make score outputs reflect completed searches without contaminating structural fit.
Task Function: Collect attributable events, classify search outcomes, and calculate structural score/audit fields.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Buying signals, search status, event provenance, observed-weight KPIs, score audit, and actionability inputs.
Required Skills: skill-backend-verification; skill-test-driven-development.
Files And Symbols: Modify scripts/collect_buying_signals.py normalize_name/main and scripts/score_leads.py value/main; update schema and original methodology wording only for reconciled enums/formula; add tests/test_buying_signals.py and tests/test_scoring.py; regenerate event/link/audit/score outputs.
Dependencies: Tasks 1 and 3.
Authority:
- Preauthorized local actions: query configured public event sources within limits, collect public company-site signals, and write event/link/audit/score outputs.
- Stop for: ambiguous attribution, predictive probabilities, unrecorded weight changes, or using contact availability to raise structural fit.
Steps:
- [ ] Index normalized names as lists, not one row; disambiguate with verified domain, legal name, address, or source identity evidence.
- [ ] Send ambiguous matches to review; only unique evidence-backed links use Verified.
- [ ] Preserve event ID, buyer, type, publication date, deadline, scope, source URL, retrieval time, and match evidence.
- [ ] Distinguish completed no-match (None found), not run (Not searched), provider failure (Unavailable), and pre-search Unknown.
- [ ] When `--shortlist` is supplied, run bounded account-scoped TED searches for at most `MAX_PRIORITY_ACCOUNTS` accepted companies; without it, global searches may produce only verified positive links and must not imply account-level no-match.
- [ ] Read --events and join events/links/audit by company ID.
- [ ] Add bounded official company news, modernization, portfolio-growth, and hiring signals only with explicit attribution/source URLs.
- [ ] Keep weights 35/30/25/10 and calculate over observed weights; store coverage consistently as 0–100 percentage points.
- [ ] Apply A/B/C/Research gates and test duplicate names, stale deadlines, no-match searches, provider failures, and score recalculation.
- [ ] Use this deterministic transition table: Strong = verified attributed
  event published within 180 days with a future or unknown deadline; Medium =
  verified event published 181–365 days ago or a future deadline with weaker
  freshness; Weak = only stale/secondary company signal; None found = a
  completed search with no verified event; Unknown = not searched or
  unavailable. Actionability is Ready only for A tier, coverage >=75, and
  Strong/Medium signal; Research for A/B rows with Unknown signal; Monitor for
  A/B rows with Weak/None found; Unknown otherwise. Sales priority is Pursue
  for Ready, Research for Research/Monitor A/B rows, and Defer otherwise.
- [ ] Keep contact availability out of structural fit, actionability, and
  sales priority so enriching the provisional shortlist cannot change the
  selection rule.
Verification:
- [ ] py -3 -m unittest tests.test_buying_signals tests.test_scoring -v
- [ ] py -3 scripts/collect_buying_signals.py --companies data/intermediate/companies_normalized_2026-11-07.csv --ted-output data/raw/buying_events_2026-11-08.json --links-output data/processed/company_event_links_2026-11-08.csv --audit-output evidence/buying_signal_audit_2026-11-08.csv
- [ ] py -3 scripts/collect_buying_signals.py --companies data/intermediate/companies_normalized_2026-11-07.csv --shortlist data/processed/priority_leads_2026-11-08.csv --ted-output data/raw/buying_events_2026-11-08.json --links-output data/processed/company_event_links_2026-11-08.csv --audit-output evidence/buying_signal_audit_2026-11-08.csv
- [ ] py -3 scripts/score_leads.py --qualification data/intermediate/website_evidence_2026-11-08.jsonl --events data/raw/buying_events_2026-11-08.json --event-links data/processed/company_event_links_2026-11-08.csv --schema config/lead_generation_schema.json --output data/processed/lead_scores_2026-11-08.csv --audit-output evidence/scoring_audit_2026-11-08.csv
- [ ] Independently recalculate at least 20 rows and compare score, coverage, tier, signal, and search status to the audit.
Exit Criteria: Signals are attributable/complete and structural fit is reproducible and independent of contact availability.

### Task 5: Verify named outreach owners and personal business emails, then finalize ranking

Purpose: Make the shortlist sales-actionable without overstating generic or unbound contact data.
Task Function: Enrich only the bounded shortlist using official contact/team/Impressum pages first and Hunter as a constrained fallback.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Named decision-makers, owner verification, personal business email, contact provenance, catch-all semantics, and final priority.
Required Skills: skill-backend-verification; skill-test-driven-development; browser-use.
Files And Symbols: Modify scripts/build_shortlist.py fetch_contacts/fetch_hunter_contact/sort_key and final row construction; add tests/test_contacts_and_ranking.py; regenerate priority, contacts, and contact-source CSVs.
Dependencies: Tasks 1 and 4.
Authority:
- Preauthorized local actions: read public official contact pages, query Hunter only for shortlisted domains within configured limits, and write contact/ranking evidence.
- Stop for: email sending, inferred-address verification, catch-all promotion, paid overage, unrelated personal-data collection, or an owner that cannot be tied to the company.
Steps:
- [ ] Select up to 30 accounts provisionally using the stable signal/structure
  ranking, enrich contacts, and preserve the same ranking inputs; contact
  availability may change next_action/research_gap only, never fit, tier,
  actionability, or sales priority.
- [ ] Crawl bounded official contact/team/management/Impressum pages and retain URL/excerpt for person, role, and email claims.
- [ ] Require plausible full name, explicit role, company association, and source evidence for a verified owner.
- [ ] Prefer Geschäftsführer/in, Inhaber/in, Leitung WEG-Verwaltung, Head of Property Management, Technische Leitung, or Procurement; do not invent roles.
- [ ] Treat generic mailboxes as company channels, not personal emails.
- [ ] Restrict named contacts and personal business emails to public
  professional sources; collect only required name, role, company, email,
  source, status, and verification date; do not retain unrelated personal
  data. Downgrade or remove records whose public business provenance is no
  longer current, and keep contact exports inside the declared sales artifact
  boundary.
- [ ] Preserve Hunter full names, position/type, confidence, verification response, and source URI.
- [ ] Map Hunter valid to Verified only when individually validated; map accept_all to Unverified/Accept-all.
- [ ] Never overwrite stronger official evidence with weaker Hunter data without identity agreement.
- [ ] Keep missing owner/email Unknown; do not lower structural fit.
- [ ] Require A tier, coverage >=75, and actionability Ready for Pursue; otherwise Research for A/B follow-up or Defer for C/Research.
- [ ] Sort by sales priority, tier, coverage, portfolio potential, verified signal strength, and stable company ID; B cannot outrank A solely on fit.
- [ ] Test generic-email exclusion, catch-all handling, person/role/email binding, official-source precedence, and tier-first sorting.
Verification:
- [ ] py -3 -m unittest tests.test_contacts_and_ranking -v
- [ ] py -3 scripts/build_shortlist.py --scores data/processed/lead_scores_2026-11-08.csv --schema config/lead_generation_schema.json --priority-output data/processed/priority_leads_2026-11-08.csv --contacts-output data/processed/contacts_2026-11-08.csv --evidence-output evidence/contact_sources_2026-11-08.csv --max-priority-accounts 30
- [ ] Assert every email has source/status/date and every verified owner has full name, role, official URL, and excerpt.
- [ ] Manually inspect the top 10 contacts and every Pursue row.
Exit Criteria: No unsupported named-owner or personal-email claim remains; final priority reflects verified evidence.

### Task 6: Make QA semantic, cross-file, and regression-backed

Purpose: Replace the current zero-error false assurance with a meaningful final gate.
Task Function: Validate records, evidence joins, identity state, score math, ranking, contact semantics, and representative samples.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Schema enforcement, source/evidence traceability, dedupe leakage, URL checks, signal/search consistency, score/ranking checks, contact verification, and sampling.
Required Skills: skill-test-driven-development; skill-backend-verification.
Files And Symbols: Modify scripts/qa_leads.py main/contact_email_status_summary; add tests/test_qa_leads.py; update QA report/sample outputs.
Dependencies: Tasks 1–5; the final workbook must be regenerated before this
task's semantic QA run.
Authority:
- Preauthorized local actions: read local workbook/evidence/data files, run deterministic QA, and write QA reports/samples.
- Stop for: missing evidence artifacts, unresolved schema/output drift, or any request to downgrade a failed gate.
Steps:
- [ ] Load and apply the schema; fail on enum/type/required-field drift.
- [ ] Validate each non-Unknown claim against URL, excerpt, confidence, retrieval timestamp, and same-company evidence.
- [ ] Check duplicate IDs/domains/names/addresses, unresolved candidates, branch relationships, and source traceability.
- [ ] Reject Berlin Confirmed without company-level evidence and WEG Confirmed without explicit WEG evidence.
- [ ] Recalculate fit/coverage/tier and verify final priority ordering.
- [ ] Reject Unknown buying signal after a completed no-match search; validate event IDs, URLs, freshness, and verified match evidence.
- [ ] Reject contacts without plausible full name, role, company association, official evidence, or correct email semantics.
- [ ] Validate priority subset and choose the non-priority sample by company-ID set difference.
- [ ] Distinguish configured, queried, completed-without-match, unavailable, and usable-evidence provider states.
- [ ] Require evidence/run_manifest_2026-11-09.json; reject workbook or source
  artifacts whose hashes do not match the same successful run.
- [ ] Add fixtures for every accepted finding and assert QA exits nonzero for each invalid case.
Verification:
- [ ] py -3 -m unittest discover -s tests -v
- [ ] Build the final workbook once before running semantic QA; never rebuild it
  after QA has passed.
- [ ] py -3 scripts/build_workbook.py --companies data/intermediate/companies_normalized_2026-11-07.csv --scores data/processed/lead_scores_2026-11-08.csv --priority data/processed/priority_leads_2026-11-08.csv --contacts data/processed/contacts_2026-11-08.csv --sources evidence/source_register_2026-11-07.csv --output output/berlin-hausverwaltung-leads_2026-11-09.xlsx --build-report evidence/workbook_build_2026-11-09.json --run-manifest evidence/run_manifest_2026-11-09.json
- [ ] py -3 scripts/qa_leads.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json --evidence-dir evidence --report evidence/qa_report_2026-11-09.md --sample-output evidence/qa_sample_2026-11-09.csv
- [ ] py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json
- [ ] Require zero errors only after all semantic checks pass; missing/stale evidence fails the run.
Exit Criteria: QA catches every known baseline defect and passes only regenerated, evidence-consistent outputs.

### Task 7: Validate final business deliverables and reconcile documentation

Purpose: Validate local deliverables built from accepted canonical outputs and make displayed claims match evidence.
Task Function: Generate workbook/deck and reconcile methodology, counts, limitations, and QA evidence.
Template Profile: unresolved; resolve before execution.
Specification Coverage: Generated consumers, workbook tabs, methodology deck, source register, QA report, and final acceptance evidence.
Required Skills: skill-verification-before-completion.
Files And Symbols: Modify scripts/build_workbook.py:main, scripts/build_deck.py:main, and scripts/validate_deliverables.py:main only where canonical fields require it; update presentation/berlin-hausverwaltung-methodology_2026-11-09.md and maintained execution/verification text; regenerate workbook/deck/build report.
Dependencies: Task 6.
Authority:
- Preauthorized local actions: regenerate declared local artifacts and update maintained methodology from verified outputs.
- Stop for: any count/tier/contact discrepancy; do not hand-edit generated values.
Steps:
- [ ] Run py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json
- [ ] Run py -3 scripts/build_deck.py --content presentation/berlin-hausverwaltung-methodology_2026-11-09.md --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --output output/berlin-hausverwaltung-methodology_2026-11-09.pptx
- [ ] Run py -3 scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09.pptx --qa-report evidence/qa_report_2026-11-09.md
- [ ] Reconcile counts, tiers, signal/status counts, priority order, contact statuses, and limitations against source CSVs/evidence.
- [ ] Record unresolved duplicates, inaccessible pages, missing signals, deferred contacts, and provider limitations in the QA report.
Verification:
- [ ] Confirm exactly five workbook tabs and non-empty required headers.
- [ ] Render and inspect all five deck slides.
- [ ] rg -n "APIFY_API_TOKEN|HUNTER_API_KEY|Bearer [A-Za-z0-9._-]+" data evidence output presentation --glob '!*.md' returns no credentials.
- [ ] Run py -3 scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09.pptx --qa-report evidence/qa_report_2026-11-09.md after reconciliation.
Exit Criteria: Local deliverables agree with QA, evidence registers, and methodology without hand-edited generated values.

## Verification

Focused proof:
- py -3 -m unittest discover -s tests -v
- py -3 -m json.tool config/lead_generation_schema.json
- py -3 scripts/qa_leads.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json --evidence-dir evidence --report evidence/qa_report_2026-11-09.md --sample-output evidence/qa_sample_2026-11-09.csv
- py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --schema config/lead_generation_schema.json
- py -3 scripts/validate_deliverables.py --workbook output/berlin-hausverwaltung-leads_2026-11-09.xlsx --deck output/berlin-hausverwaltung-methodology_2026-11-09.pptx --qa-report evidence/qa_report_2026-11-09.md

Acceptance checks:
- No company is auto-merged on domain/source host alone.
- Every non-Unknown qualification claim has exact URL, excerpt, confidence, and retrieval timestamp.
- Berlin Confirmed and WEG Confirmed values have appropriate company-level evidence.
- Buying signal and search status distinguish Strong/Medium/Weak/None found/Unknown and completed no-match/unavailable/not searched.
- Structural weights remain 35/30/25/10, use observed weights, and are independently reproducible.
- Pursue is reachable only for A-tier, coverage >=75, actionability Ready rows; final sorting is tier-first and deterministic.
- Named owners require full name, role, company association, and official evidence; generic/catch-all email does not count as verified personal business email.
- QA fails on schema drift, unsupported claims, unresolved identity leakage, score/ranking mismatch, invalid signal state, missing contact provenance, or stale/missing evidence.
- Workbook, deck, QA report, and source registers reconcile without hand-edited generated values.

## Completion Criteria

1. Tasks 1–7 pass in dependency order.
2. py -3 -m unittest discover -s tests -v passes with regression coverage.
3. Final QA, workbook, and deliverable validators pass on freshly regenerated artifacts.
4. The evidence report records before/after baseline, accepted limitations, unresolved cases, and retrieval dates.
5. No external publication, email sending, credential exposure, or unapproved provider spend occurs.
6. The plan remains active until the canonical workbook is refreshed after its current Excel lock is released; completion status is set only after fresh implementation verification on the canonical output paths.

## Execution Record

- 2026-11-08: Published execution began after this plan was reviewed and patched.
- Discovery refresh completed with 323 records; malformed, same-domain, and
  unresolved identities remain in `data/intermediate/discovery_quarantine_2026-11-08.csv`
  or the review register, and are excluded from accepted scoring input.
- Bounded official-site retrieval completed for 323 companies: 290 fetched,
  33 failed, with page-local captures and multi-page traversal preserved.
- Accepted qualification excludes review rows: 201 score rows, 30 priority
  rows, and 30 contact rows. Buying signals are explicitly `None found` after
  a completed search, not `Unknown`; 18 same-domain public mailboxes remain
  Published and no named decision-maker is asserted without evidence.
- Remediated artifacts pass 17 unit tests, JSON validation, semantic QA with
  `Errors: 0`, workbook validation, five-slide deck generation, and deliverable
  validation. The canonical regenerated run is bound by
  `evidence/run_manifest_2026-11-09.json`, with run ID
  `lead-63856dbb52757423`.
- Canonical workbook promotion completed after confirming Excel was not
  running. The canonical workbook, QA report, build report, and five-slide deck
  now share the same validated input/output run manifest; no user workbook was
  terminated or discarded.
- Final local verification on 2026-11-08: 18 tests passed, `qa_errors=0`, the
  workbook has five sheets, deliverables validated, `git diff --check` passed,
  and the credential scan was clean. A native slide renderer is not installed
  in this workspace; deck structure and five-slide count were validated by the
  repository validator instead of claiming visual-render inspection.
- Review cycle 1 at PR head `985780fa012c64441d7d87fde3e6593dfd6addee`
- Final independent review at PR head `eda64e58f70584719e1b8fa264a2065cb245b1bf`
  identified five additional blockers: synthetic Berlin fallback and navigation
  title identity acceptance, same-domain ambiguity leakage, incomplete QA type/
  range/conditional enforcement, incomplete manifest revision/hash coverage,
  and positive TED signals without publication dates. The remediation commit
  removed those fallbacks, quarantined ambiguous identities, strengthened the
  schema/QA gate, added Git revision and full manifest hash verification, and
  downgraded date-less TED events to `Unknown`.
- Final regeneration on 2026-11-08: 323 raw records, 320 canonical records,
  149 review records, 297 fetched websites, 23 retrieval failures, 191 score
  rows, 85 A-tier rows, 106 Research rows, 30 priority rows, and 18 published
  mailbox contacts. Semantic QA reports `qa_errors=0`.
- Final verification: 21 unit tests passed; workbook validation passed; the
  five-slide deck was rebuilt at
  `output/berlin-hausverwaltung-methodology_2026-11-09-final.pptx`; deliverable
  validation passed; `git diff --check` passed; and the credential scan found
  no credential values. The original PowerPoint-locked deck was not touched.
  identified seven blockers. They are addressed in the follow-up commit by
  stricter contact/domain binding, explicit WEG and Berlin evidence, same-domain
  review quarantine, provider-outage state propagation, schema/score/evidence
  QA enforcement, and manifest/deck reconciliation. A fresh head-bound review
  is required before merge.
