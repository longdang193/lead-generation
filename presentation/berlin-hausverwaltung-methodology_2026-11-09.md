# Berlin Hausverwaltung Lead Generation MVP
- Objective: turn public market discovery into an evidence-backed sales shortlist.
- Funnel: Market (302 raw records) → Qualified Accounts (302) → Priority Leads (30) → Published business emails (26).

# Discovery and Evidence
- Primary discovery: VDIV Berlin-Brandenburg public member directory; 302 raw records imported.
- Canonical universe: 302 rows after deterministic normalization; source URLs and retrieval dates retained.
- Official website pass: 279 domains fetched; unavailable domains remain explicit in the capture index.
- Optional Apify, Overpass, and TED lanes were not configured and did not block the workbook.

# Qualification Logic
- Structural Lead Fit: Service/ICP 35%; residential/WEG 30%; portfolio potential 25%; geography 10%.
- Lead Fit excludes Buying Signal and Actionability; observed-weight scoring preserves Unknown rather than encoding zero.
- Evidence Coverage gates confidence: A ≥75%; B/C ≥50%; Research below 50%.
- Current tier distribution: A 178; B 0; C 0; Research 124.

# Results and Contacts
- Shortlist is capped at 30 accounts and ordered by structural fit, evidence coverage, and priority.
- Tier distribution: A 178; B 0; C 0; Research 124.
- 26 contacts have published business emails with source URLs; no inferred address is marked Verified.
- Buying events remain separate; no account-specific event link was asserted without a verified match.

# Validation and Phase 2
- Current workflow: VDIV → bounded official-site evidence → deterministic scoring → shortlist → workbook.
- QA controls: duplicate checks, source URLs, Unknown handling, tier reconciliation, contact provenance, and five-tab workbook validation.
- Phase 2: Macro/Regulation → Competitors → Intermarkets → Account Events → Buying Signals → Automated Prioritization → CRM Feedback.
- Deferred by design: PostgreSQL, predictive conversion models, full-universe enrichment, continuous monitoring, and CRM automation.
