---
name: contact-verification
description: Verify named outreach owners and separate generic mailboxes.
---

# Contact Verification

## Capability selection

Use `official_source_fetch` for management, team, Impressum, and contact pages;
use `professional_profile_search` for public professional-source discovery and
`contact_verification` for checking the resulting company relationship; use
`contact_enrichment` only after the person and company relationship are already
verified. Provider output is supplemental `CANDIDATE_EVIDENCE`, not a named
stakeholder decision. The parent runtime chooses the next gap-driven action.

- Ownership: named-person and generic-mailbox verification. Consume the
  account/action boundary from `account-research` and the page-local claim
  inputs from `lead-evidence`; do not own account coverage, stop evidence,
  general semantic-support review, or commercial trigger collection.
- Search official team, management, Impressum, and contact pages before provider data.
- A named owner requires independent proof of person, company affiliation, exact role, role relevance, and page-local evidence.
- A plausible two-word phrase or navigation label is not a person.
- `info@`, `kontakt@`, `office@`, and equivalent addresses remain published generic mailboxes, not named decision-makers.
- Bind personal business email to the verified person and company domain;
  otherwise mark it unverified or needs review. Keep generic mailboxes as a
  separate verified contact class, never as named owners.
