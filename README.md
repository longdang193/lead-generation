# Berlin Hausverwaltung Lead-Generation Harness

This repository contains a Codex-native lead-generation harness for finding,
researching, validating, prioritizing, and exporting property-management leads.
It is designed to answer the stakeholder question:

> **Why is this account worth selecting next?**

The output is intentionally more than a directory or generic scraper result. A
lead is prioritized only when the available account evidence explains its fit,
operating context, uncertainty, and recommended next action.

## Current Deliverables

- [Final stakeholder workbook](output/berlin-hausverwaltungen-task1-2026-11-10-account-validation-final.xlsx)
- [Task 3 methodology presentation](output/berlin-hausverwaltungen-task3-approach-revised.pptx)
- [Semantic rerank evidence](evidence/account_validation_rerank_2026-11-10.json)
- [Normalized account-validation records](data/processed/account_validation_2026-11-10.jsonl)

The workbook contains the 30-lead ranked view, qualification KPIs, semantic
account explanations, evidence references, research gaps, bounded validation
records, and controller QA results.

## Research Approach

The controller-owned workflow is:

```text
Discovery
  -> identity and Berlin-service verification
  -> duplicate/entity resolution
  -> structural qualification
  -> bounded account research
  -> evidence verification
  -> semantic prioritization
  -> workbook and QA validation
```

Discovery sources and tools include public directories, Apify, public web
search, company websites, and optional location data. Official company sources
are used to support company-bound claims. Search results and directory entries
are treated as candidates, not proof.

Python tooling provides normalization, entity resolution, evidence capture,
ranking, workbook generation, and validation. The Codex parent controller owns
the research loop: it selects the next bounded action for an account, reviews
the returned evidence, and stops or continues based on the remaining decision
gaps.

## Semantic Qualification

The ranking model separates structural fit from commercial relevance:

| Dimension | Weight | Question answered |
| --- | ---: | --- |
| Structural fit | 30% | Is this a Berlin-relevant property-management account? |
| Opportunity / complexity | 20% | Is there a meaningful operating surface to investigate? |
| Account-specific need | 15% | Is there evidence of a concrete operating problem? |
| Change context | 15% | Is there a dated change, growth, hiring, or modernization context? |
| Direct intent | 10% | Is there a verified procurement, vendor, or purchase signal? |
| Access | 5% | Is there a credible route to the relevant buying center? |
| Evidence confidence | 5% | How strong, current, company-bound, and corroborated is the evidence? |

Unknown values receive no positive credit and remain visible. The system does
not turn provider failure, missing history, or a marketing claim into a buying
signal.

Each researched account should explain:

- why the company fits the target profile;
- what account-specific need, workflow, or complexity is evidenced;
- what change context is present;
- what remains a hypothesis or unresolved decision gap;
- what evidence would reverse the conclusion; and
- what bounded next action should be taken.

## Evidence States

The stakeholder view distinguishes:

- **Fit-led research candidate** — structural fit is supported, but account-specific validation is incomplete;
- **Problem-evidenced account** — a company-bound workflow or problem signal is supported, but change or buying intent is unresolved;
- **Change-ready account** — a dated change context is supported, but the internal project or vendor decision is not proven;
- **Sales-ready account** — requires need evidence plus current change/trigger evidence and appropriate access.

For the current delivery, 30 accounts are semantically ranked, 10 received the
latest bounded account-validation round, and 0 crossed the sales-ready gate.
The remaining rows are visibly downgraded rather than presented as confirmed
opportunities. Direct intent remains `Unknown` where it was not verified.

## Validation

Run the workbook validator:

```powershell
py -3 scripts/validate_workbook.py --workbook output/berlin-hausverwaltungen-task1-2026-11-10-account-validation-final.xlsx
```

Run the full test suite:

```powershell
py -3 -m unittest discover -s tests -p "test_*.py" -v
```

The current verification run passed the workbook validator and all 287
automated tests.

## Limitations

This is a personal-use research harness, not a production CRM or autonomous
sales system. Public research cannot reliably prove budget, internal ownership,
vendor evaluation, or current purchase intent for every account. Those gaps are
kept explicit so stakeholders can decide where the next research or outreach
minute is worth spending.
