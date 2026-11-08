# Berlin Hausverwaltung Lead Generation MVP
- Objective: turn public market discovery into an evidence-backed sales shortlist.
- Funnel: Market (323 raw records) → Qualified Accounts (311) → Priority Leads (30) → Email-evidence contacts (28; 26 Published/Verified).

# Discovery and Evidence
- Primary discovery: VDIV Berlin-Brandenburg public member directory; 302 raw records imported.
- Discovery additions: 20 Apify records and 5 bounded Overpass elements were imported; 1 Overpass company record was usable after normalization.
- Canonical universe: 311 rows after deterministic normalization; source URLs and retrieval dates retained.
- Official website pass: 288 domains fetched; 23 unavailable domains remain explicit in the capture index.
- Apify, TED, and Hunter provider access was configured and exercised; Overpass used its public endpoint. TED events remain separate from company discovery.

# Qualification Logic
- Structural Lead Fit: Service/ICP 35%; residential/WEG 30%; portfolio potential 25%; geography 10%.
- Lead Fit excludes Buying Signal and Actionability; observed-weight scoring preserves Unknown rather than encoding zero.
- Evidence Coverage gates confidence: A ≥75%; B/C ≥50%; Research below 50%.
- Current tier distribution: A 187; B 0; C 0; Research 124.

# Results and Contacts
- Shortlist is capped at 30 accounts and ordered by structural fit, evidence coverage, and priority.
- Tier distribution: A 187; B 0; C 0; Research 124.
- 28 contacts have email evidence with source URLs: 21 Published, 5 Verified, and 2 Unverified; no inferred address is marked Verified.
- Buying events remain separate; no account-specific event link was asserted without a verified match.

# Validation and Phase 2
- Current workflow: VDIV + Apify + bounded Overpass → official-site evidence → TED signal search → deterministic scoring → shortlist + Hunter enrichment → workbook.
- QA controls: duplicate checks, source URLs, Unknown handling, tier reconciliation, contact provenance, and five-tab workbook validation.
- Phase 2: Macro/Regulation → Competitors → Intermarkets → Account Events → Buying Signals → Automated Prioritization → CRM Feedback.
- Deferred by design: PostgreSQL, predictive conversion models, full-universe enrichment, continuous monitoring, and CRM automation.
