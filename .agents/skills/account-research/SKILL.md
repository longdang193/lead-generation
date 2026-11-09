---
name: account-research
description: Run bounded research for one accepted company at a time.
---

# Account Research

- The parent agent chooses which account and bounded research action comes
  next; this skill never encodes a fixed TED/portfolio/contact sequence.
- Use only the assigned `company_id`, legal name, trusted company domain, and lane scope.
- Record one attempt per required query or source, including provider, cursor/page, cap, truncation, status, and candidate claim IDs.
- `None found` is valid only after every required attempt completed with no truncation, provider error, or unresolved candidate.
- Never use a global search result as an account-level conclusion without an exact verified company link.
- Keep outputs in the lane-specific candidate directory named by run ID and company ID.
- Preserve native action identity and receipt provenance when returning a result;
  hypotheses are analytical outputs and must cite supporting and counterevidence
  claim IDs without becoming verified facts.
