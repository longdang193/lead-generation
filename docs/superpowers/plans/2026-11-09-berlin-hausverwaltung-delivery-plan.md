---
layer: change
artifact_type: plan
status: completed
template_id: implementation-plan
contract_version: "1"
name: berlin-hausverwaltung-delivery
targets:
  - scripts/import_discovery.py
  - tests/test_discovery.py
  - evidence/live-probe-2026-11-09/
  - output/berlin-hausverwaltungen-task1-2026-11-09.xlsx
---

# Berlin Hausverwaltung Delivery Plan

## Goal

Deliver the existing canonical Berlin Hausverwaltung overview as a usable Excel
workbook, preserve explicit KPI unknowns and source provenance, and add bounded
live-provider evidence without allowing provider availability to masquerade as
company verification.

## Tasks

### 1. Verify inputs and KPI contract

- Use `C:/tmp/berlin_hausverwaltungen_task1_build.json` as the canonical
  workbook input.
- Confirm the overview, ranked shortlist, KPI Definitions, and Source Notes
  sheets contain 320 accepted companies, 30 priority rows, seven KPI entries,
  and explicit limitations.
- Preserve `Unknown`, `None found`, and `Not found` values as stated by the
  canonical scoring and research policy.

### 2. Run bounded live provider probe

- Run `scripts/import_discovery.py --fetch-providers` once with
  `APIFY_MAX_SPEND_USD=3.00`, two Berlin Hausverwaltung queries, and outputs
  under `evidence/live-probe-2026-11-09/`.
- Record the Apify run ID, returned record count, spend if supplied, and the
  Overpass status in the source register.
- Do not promote live discovery candidates into qualified leads without the
  existing normalization, evidence, and verifier gates.

### 3. Fix confirmed provenance defect

- Preserve item-level `source_reuse_status` during record projection in
  `scripts/import_discovery.py`.
- Read payload-level reuse metadata for nested provider rows so fresh Overpass
  payloads can retain `New retrieval` while old exports retain `Existing export`.
- Add regression tests covering Apify item metadata, nested Overpass metadata,
  and the projected CSV output.

### 4. Build and validate deliverable

- Build `output/berlin-hausverwaltungen-task1-2026-11-09.xlsx` with
  `node scripts/build_task1_workbook.mjs C:/tmp/berlin_hausverwaltungen_task1_build.json output/berlin-hausverwaltungen-task1-2026-11-09.xlsx C:/tmp/berlin_hausverwaltungen_previews`.
- Validate workbook sheet names, row counts, KPI columns, hyperlinks, and
  rendered previews with `openpyxl` and the generated inspection output.
- Run `py -3 -m unittest discover -s tests -v` and retain failures unrelated to
  this task as explicit limitations rather than patching them opportunistically.

## Completion Evidence

- The bounded live run returned 20 Apify records under the `$3.00` ceiling;
  Overpass returned HTTP 502 and remained unavailable in
  `evidence/live-probe-2026-11-09/source-register-3usd.csv`.
- Focused discovery tests passed: `py -3 -m unittest tests.test_discovery -v`.
- Full repository tests passed: `py -3 -m unittest discover -s tests -v` (212
  tests).
- Workbook validation passed for 320 overview rows, 30 priority rows, 7 KPI
  definitions, unique company IDs, and evidence URLs on every row.

## Acceptance

- The workbook contains 320 accepted companies and a deterministic top-30 view.
- KPI definitions explain service fit, residential/WEG relevance, portfolio
  potential, Berlin relevance, evidence coverage, buying signal, and contact
  verification.
- The live probe is labeled provider evidence only; no independent verifier or
  CRM write is claimed.
- Focused and full tests pass, the provenance regression is covered, and the
  final Git diff contains no credentials or unrelated generated mutations.
