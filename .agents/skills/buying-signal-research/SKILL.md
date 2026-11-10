---
name: buying-signal-research
description: Collect offer-bound commercial triggers without treating procurement as the only intent source.
---

# Buying Signal Research

This is a signal-domain playbook, not an orchestration loop. Execute only the
parent-selected company and action.

## Capability selection by gap

- broad trigger discovery -> `web_search` or `news_search`
- known company or official URL -> `official_source_fetch`
- procurement, RFP, or tender -> `procurement_search`
- hiring, leadership, or operating-model change -> `jobs_search` followed by
  `official_source_fetch` when a company page is found
- modernization or expansion -> discovery first, then company-bound source fetch

Discovery output is `DISCOVERY`; it is never a verified claim. A matched TED
event is `CANDIDATE_EVIDENCE` for direct intent until exact company identity,
page-local support, date, and offer relevance are verified. Always capture the
company-bound excerpt, URL, publication/event date, retrieval time, source
family, and offer-specific relevance. The parent Codex runtime selects the next
gap-driven action; this skill does not run a provider sequence.

## Query families

- portfolio expansion, new mandates, acquisitions, and managed-unit growth
- modernization, digitalization, automation, and operating-model change
- supplier or software change, implementation, and transformation projects
- relevant hiring, leadership change, and organizational growth
- references, client announcements, public projects, and procurement/RFPs

For every candidate, capture the exact company-bound page-local excerpt, source
URL, publication or event date, retrieval time, source family, and why the
signal matches an immutable offer criterion. TED/procurement is one optional
source family; absence there is not absence of commercial need.

Return separate indicators for `direct_intent`, `trigger`, `need_indicator`, and
`change_readiness`. Do not resolve contacts, score, rank, promote evidence, or
choose a follow-up action.
