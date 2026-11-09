from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from campaign_spec import qualification_eligibility
from lead_contract import actionability_for, parse_evidence_urls, sales_priority_for, signal_rank
from typed_contracts import RankAudit, RankContribution

WEIGHTS = {"service_fit": 35, "residential_weg": 30, "portfolio_potential": 25, "geographic_fit": 10}
COMMERCIAL_WEIGHTS = {
    "fit": 30.0,
    "opportunity": 20.0,
    "need": 15.0,
    "change": 15.0,
    "direct_intent": 10.0,
    "access": 5.0,
    "evidence_confidence": 5.0,
}


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def value(field: str, record: dict[str, object]) -> float | None:
    field_assurance = record.get("field_assurance")
    assurance_field = "portfolio_size" if field == "portfolio_potential" else field
    if isinstance(field_assurance, dict) and assurance_field in field_assurance and str(field_assurance[assurance_field]) != "source":
        return None
    raw = record.get(field)
    if field == "portfolio_potential":
        size = record.get("portfolio_size")
        if size is None or size == "":
            return None
        try:
            return min(100.0, 40.0 + float(size) / 10.0)
        except (TypeError, ValueError):
            return None
    if raw in ("Confirmed", "Primary"):
        return 100.0
    if raw == "Probable":
        return 70.0
    if raw in ("Not evident", "Secondary"):
        return 0.0
    return None


def parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _commercially_strong_event(event: dict[str, object]) -> bool:
    assurance = str(event.get("assurance_level") or "")
    verification = str(event.get("verification_status") or event.get("match_confidence") or "")
    if assurance != "source" and verification != "Verified":
        return False
    required = ("event_type", "buyer", "title", "deadline")
    if any(event.get(field) in (None, "", "Unknown") for field in required):
        return False
    return bool(event.get("source_url") not in (None, "", "Unknown"))


def classify_signal(event_rows: list[dict[str, object]], as_of_date: date | None = None) -> str:
    if not event_rows:
        return "None found"
    today = as_of_date or datetime.now(timezone.utc).date()
    ranks = []
    for event in event_rows:
        published = parse_date(event.get("publication_date"))
        deadline = parse_date(event.get("deadline"))
        if deadline and deadline < today:
            ranks.append(2)
            continue
        if published is None:
            ranks.append(0)
        elif published >= today - timedelta(days=180):
            ranks.append(4 if _commercially_strong_event(event) else 3)
        elif published >= today - timedelta(days=365):
            ranks.append(3)
        else:
            ranks.append(2)
    rank = max(ranks)
    if rank == 4 and not any(_commercially_strong_event(event) for event in event_rows):
        return "Medium"
    return {4: "Strong", 3: "Medium", 2: "Weak", 0: "Unknown"}[rank]


def calculate_fit(record: dict[str, object]) -> tuple[float | None, int]:
    inputs = {
        "service_fit": value("service_fit", record),
        "residential_weg": value("residential_weg", record),
        "portfolio_potential": value("portfolio_potential", record),
        "geographic_fit": value("berlin_relevance", record),
    }
    observed_weight = sum(WEIGHTS[field] for field, item in inputs.items() if item is not None)
    fit = sum(WEIGHTS[field] * item for field, item in inputs.items() if item is not None) / 100 if observed_weight else None
    return fit, observed_weight


def _commercial_dimension_value(record: dict[str, object], dimension: str) -> float:
    aliases = {
        "fit": "structural_lead_fit",
        "opportunity": "opportunity_score",
        "need": "need_score",
        "change": "change_score",
        "direct_intent": "direct_intent_score",
        "access": "access_score",
        "evidence_confidence": "evidence_confidence_score",
    }
    raw = record.get(aliases[dimension], 0)
    if dimension == "direct_intent" and raw in (None, "", 0, "0"):
        raw = {"Verified trigger": 100, "Strong": 80, "Medium": 60, "Weak": 30}.get(str(record.get("buying_signal") or ""), 0)
    try:
        return max(0.0, min(100.0, float(raw)))
    except (TypeError, ValueError):
        return 0.0


def priority_reason(record: dict[str, object]) -> str:
    why_account = str(record.get("why_this_account") or "Offer fit is not stated")
    why_now = str(record.get("why_now") or "Timing is not established")
    claims = ", ".join(str(value) for value in record.get("strongest_claim_ids", []) if value)
    return f"{why_account}; {why_now}; supporting claims: {claims or 'none'}"


def build_rank_audit(record: dict[str, object], offer_id: str, offer_version: str) -> RankAudit:
    if record.get("semantic_review_approved") is not True:
        raise ValueError("semantic review approval is required before ranking")
    if record.get("offer_id") != offer_id or record.get("offer_version") != offer_version:
        raise ValueError("rank record offer context does not match requested offer")
    claim_ids = [str(value) for value in record.get("strongest_claim_ids", []) if value]
    if not claim_ids:
        raise ValueError("rank record requires supporting claim IDs")
    dimensions = {
        name: _commercial_dimension_value(record, name)
        for name in COMMERCIAL_WEIGHTS
    }
    contributions = [
        RankContribution(
            dimension=name,
            value=value,
            weight=COMMERCIAL_WEIGHTS[name],
            contribution=round(value * COMMERCIAL_WEIGHTS[name] / 100.0, 6),
            supporting_claim_ids=claim_ids,
            offer_criterion=name,
        )
        for name, value in dimensions.items()
    ]
    signal = str(record.get("buying_signal") or "")
    fit = dimensions["fit"]
    if signal == "Verified trigger":
        state = "Priority — verified trigger"
    elif fit >= 70 and signal == "No trigger found":
        state = "Priority — strong fit, no trigger"
    elif fit < 40:
        state = "Disqualify"
    elif signal in {"Research incomplete", "Unavailable", "Unknown"}:
        state = "Research required"
    else:
        state = "Nurture"
    return RankAudit(
        company_id=str(record.get("company_id") or ""),
        offer_id=offer_id,
        offer_version=offer_version,
        priority_state=state,
        total_score=round(sum(item.contribution for item in contributions), 6),
        contributions=contributions,
        rationale_claim_ids=claim_ids,
    )


def rank_account(record: dict[str, object], offer_id: str, offer_version: str) -> RankAudit:
    return build_rank_audit(record, offer_id, offer_version)


def derive_account_signal(company_audit: dict[str, str], matched_events: list[dict[str, object]], default_search_status: str) -> tuple[str, str]:
    if not company_audit:
        return "Unknown", "Unknown"
    research_status = company_audit.get("research_status", company_audit.get("search_status", ""))
    search_status = company_audit.get("search_status") or {"Completed": "Searched", "Partial": "Unknown", "Needs review": "Unknown"}.get(research_status, default_search_status)
    coverage_status = company_audit.get("coverage_status")
    if not matched_events and company_audit.get("signal_state") in {"None found", "No trigger found"}:
        complete_legacy = research_status == "Completed" and coverage_status in (None, "complete")
        if coverage_status == "unavailable":
            return "Unavailable", "Unknown"
        if not complete_legacy:
            return "Research incomplete", "Unknown"
        return "No trigger found" if coverage_status == "complete" else "None found", search_status
    if research_status in {"Unavailable", "Not searched", "Partial", "Needs review"}:
        if matched_events:
            return classify_signal(matched_events), search_status
        return "Unknown", search_status
    if company_audit.get("signal_state") == "None found":
        return "None found", search_status
    if not matched_events and (
        company_audit.get("signal_state") in {"Strong", "Medium", "Weak"}
        or str(company_audit.get("verified_claim_count") or "0") not in {"", "0"}
    ):
        return "Unknown", "Unknown"
    return classify_signal(matched_events), search_status


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--event-links", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--signal-audit", type=Path)
    parser.add_argument("--delivery-policy", choices=("personal", "strict"), default="strict")
    parser.add_argument("--as-of-date", type=date.fromisoformat)
    args = parser.parse_args()
    records = []
    for line in args.qualification.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("resolution_status", "Accepted") != "Review":
            records.append(record)
    event_payload = json.loads(args.events.read_text(encoding="utf-8")) if args.events.exists() else []
    if isinstance(event_payload, dict):
        events = event_payload.get("items") or event_payload.get("events") or []
        provider_unavailable = str(event_payload.get("status", "")).lower() in {"unavailable", "partial"}
    else:
        events = event_payload if isinstance(event_payload, list) else []
        provider_unavailable = False
    events_by_id = {str(event.get("event_id")): event for event in events if isinstance(event, dict) and event.get("event_id")}
    links = list(csv.DictReader(args.event_links.open(encoding="utf-8-sig", newline=""))) if args.event_links.exists() else []
    links_by_company: dict[str, list[dict[str, object]]] = {}
    for link in links:
        if link.get("match_confidence") == "Verified":
            links_by_company.setdefault(link.get("company_id", ""), []).append(events_by_id.get(link.get("event_id", ""), link))
    signal_audit: dict[str, dict[str, str]] = {}
    if args.signal_audit and args.signal_audit.exists():
        for row in csv.DictReader(args.signal_audit.open(encoding="utf-8-sig", newline="")):
            if row.get("company_id"):
                signal_audit[row["company_id"]] = row
    default_search_status = "Unavailable" if provider_unavailable else "Searched" if args.events.exists() else "Not searched"
    scores: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for record in records:
        inputs = {
            "service_fit": value("service_fit", record),
            "residential_weg": value("residential_weg", record),
            "portfolio_potential": value("portfolio_potential", record),
            "geographic_fit": value("berlin_relevance", record),
        }
        fit, observed_weight = calculate_fit(record)
        coverage = observed_weight
        if coverage < 50 or fit is None or not qualification_eligibility(record, args.delivery_policy, recompute=True):
            tier = "Research"
        elif fit >= 70 and coverage >= 75:
            tier = "A"
        elif fit >= 55:
            tier = "B"
        else:
            tier = "C"
        matched_events = links_by_company.get(record.get("company_id", ""), [])
        company_audit = signal_audit.get(str(record.get("company_id") or ""), {})
        signal, search_status = derive_account_signal(company_audit, matched_events, default_search_status)
        if matched_events and signal not in {"Unknown", "None found"}:
            signal = classify_signal(matched_events, args.as_of_date)
        actionability = actionability_for(tier, coverage, signal)
        sales_priority = sales_priority_for(actionability, tier)
        signal_urls = [str(event.get("source_url")) for event in matched_events if event.get("source_url") not in (None, "", "Unknown")]
        signal_event_ids = [str(event.get("event_id")) for event in matched_events if event.get("event_id")]
        scores.append({
            "company_id": record.get("company_id", ""),
            "company_name": record.get("company_name", ""),
            "domain": record.get("domain", ""),
            "source_url": record.get("source_url", ""),
            "service_fit": record.get("service_fit", "Unknown"),
            "residential_weg": record.get("residential_weg", "Unknown"),
            "portfolio_size": record.get("portfolio_size", ""),
            "portfolio_potential": round(inputs["portfolio_potential"], 2) if inputs["portfolio_potential"] is not None else "Unknown",
            "berlin_relevance": record.get("berlin_relevance", "Unknown"),
            "structural_lead_fit": round(fit, 2) if fit is not None else None,
            "evidence_coverage": coverage,
            "buying_signal": signal,
            "signal_search_status": search_status,
            "actionability": actionability,
            "sales_priority": sales_priority,
            "assurance_level": record.get("assurance_level", "unknown"),
            "provider_status": record.get("provider_status", "Unknown"),
            "research_gap": record.get("research_gap", "None"),
            "next_action": "Research" if record.get("research_gap", "None") != "None" else actionability,
            "lead_tier": tier,
            "evidence_urls": " | ".join(parse_evidence_urls(record.get("evidence_urls"))),
            "buying_signal_event_ids": " | ".join(signal_event_ids),
            "buying_signal_evidence_urls": " | ".join(signal_urls),
            "retrieved_at": record.get("retrieved_at", stamp()),
        })
        audits.append({"company_id": record.get("company_id", ""), "service_weight": 35, "residential_weight": 30, "portfolio_weight": 25, "geography_weight": 10, "observed_weight": observed_weight, "structural_lead_fit": fit if fit is not None else "Unknown", "evidence_coverage": coverage, "tier": tier, "buying_signal": signal, "signal_search_status": search_status, "actionability": actionability, "sales_priority": sales_priority, "signal_rank": signal_rank(signal), "calculated_at": stamp()})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(scores[0]) if scores else ["company_id", "lead_tier"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(scores)
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    with args.audit_output.open("w", encoding="utf-8", newline="") as handle:
        fields = list(audits[0]) if audits else ["company_id", "observed_weight", "structural_lead_fit"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(audits)
    print(json.dumps({"rows": len(scores), "tiers": {tier: sum(row["lead_tier"] == tier for row in scores) for tier in ["A", "B", "C", "Research"]}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
