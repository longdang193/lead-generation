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

## Temporal interpretation

Choose the temporal strategy that matches the trigger family; do not treat
every signal as a point event. A single dated observation proves only the
activity stated on that source. Repeated comparable observations may support a
pattern, and an increasing pattern may support acceleration, but neither may
be inferred from one posting or from missing history.

- one hiring posting -> hiring activity
- repeated comparable postings -> possible capacity pressure
- increasing comparable postings -> possible hiring acceleration
- portfolio size or service footprint -> current snapshot unless a dated
  baseline exists
- acquisitions, leadership changes, launches, or procurement -> dated event
- modernization or software replacement -> dated event sequence when multiple
  milestones are available

For trend or sequence work, capture the explicit lookback window, comparison
basis, observation dates, source coverage, and deduplicated observation IDs.
Compare like with like (same company identity, trigger definition, geography,
and source family where possible). Record `Unknown` when the baseline,
comparable coverage, or date is insufficient. Never convert provider limits,
search truncation, or no matching result into a claim that no trigger exists.

For every candidate, capture the exact company-bound page-local excerpt, source
URL, publication or event date, retrieval time, source family, and why the
signal matches an immutable offer criterion. TED/procurement is one optional
source family; absence there is not absence of commercial need.

Return separate indicators for `direct_intent`, `trigger`, `need_indicator`, and
`change_readiness`. Do not resolve contacts, score, rank, promote evidence, or
choose a follow-up action.
