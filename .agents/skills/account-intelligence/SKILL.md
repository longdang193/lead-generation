---
name: account-intelligence
description: Compose offer-bound account dossiers from parent-selected bounded research actions.
---

# Account Intelligence

The parent Codex runtime owns the research loop. It selects one bounded action,
reviews the returned evidence, and decides whether to continue or stop. This
skill does not create a planner or scheduler.

## Capability selection

Use `official_source_fetch`, `identity_resolution`, `semantic_review`, and the
gap-specific research capabilities exposed by the registry. Select an account
when verified evidence supports a defensible commercial thesis, even when no
explicit buying event or named buyer exists. Do not treat a rank or a
discovered event as account intelligence. Discovery finds candidates;
company-bound sources support claims; semantic review promotes evidence; the
parent Codex agent chooses the next action.

## Required loop

1. Read the accepted company, immutable `offer_id`/`offer_version`, existing
   claims, coverage manifest, and open decision-relevant gaps.
2. Select one action that can change the account thesis, comparative priority,
   recommended action, or named stakeholder; record the parent action and
   bounded scope.
3. Capture page-local claims with exact company binding, source URL, excerpt,
   retrieval time, publication/as-of date, source family, and assurance.
4. Separate direct intent, triggers, need indicators, change readiness, access,
   and evidence confidence. Keep facts separate from hypotheses.
5. Run semantic review for entailment, offer relevance, temporal relevance, and
   contradiction before an assertion contributes to a thesis or rank.
6. Write `why_this_account`, `why_now`, problem hypothesis, strongest claims,
   counterevidence, uncertainty, confidence, access summary, research-gap
   impact, recommended action, and the next decision-relevant gap.
7. For every `proactive_account` or `sales_ready` thesis, provide a
   `selection_rationale` with verified observations, operational implications,
   offer-specific opportunity hypothesis, counterevidence, comparative basis,
   confidence, reversal condition, recommended action, and unresolved gaps.
   Answer what matters about this company, why it outranks a plausible
   alternative, and what would reverse the decision.
8. Return a typed result and append-only receipt. The parent runtime chooses the
   next action or records a stop decision.

## Stop rules

`No trigger found` is valid only when every check in the finite coverage
manifest completed, providers were available, the search was not truncated, and
there are no unresolved candidates. Otherwise use `Research incomplete` or
`Unavailable`; never convert missing coverage into negative intent.

## Ownership

- `account-research`: bounded action scope, coverage manifest, attempt ledger,
  and stop evidence.
- `lead-evidence`: page-local claim capture and semantic-review input.
- `contact-verification`: named-person and generic-mailbox verification.
- `buying-signal-research`: commercial trigger collection only; direct intent
  accelerates timing but is not required for account selection.

Do not score, rank, promote, write canonical exports, mutate CRM, or send
outreach from this skill.
