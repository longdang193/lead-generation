from __future__ import annotations

import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from runtime_config import RuntimeConfig


def stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def claim(text: str, patterns: list[str]) -> tuple[str, str, str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            start = max(0, match.start() - 120)
            return "Confirmed", "High", re.sub(r"\s+", " ", text[start:match.end() + 180]).strip()[:420]
    return "Unknown", "None", ""


def fetch(url: str, config: RuntimeConfig) -> tuple[str, str, list[str]]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; lead-research/1.0)"}
    for attempt in range(config.max_fetch_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=config.request_timeout_seconds, allow_redirects=True)
            if response.ok and response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
                links = [urljoin(response.url, a.get("href")) for a in soup.find_all("a", href=True)]
                return response.url, text, links
        except requests.RequestException:
            pass
        if attempt < config.max_fetch_retries:
            time.sleep(0.25 * (attempt + 1))
    return url, "", []


def process(row: dict[str, str], config: RuntimeConfig) -> tuple[dict[str, object], dict[str, str]]:
    url = row.get("source_url", "")
    result: dict[str, object] = {
        "company_id": row.get("company_id", ""),
        "company_name": row.get("company_name", ""),
        "domain": row.get("domain", ""),
        "source_url": url,
        "retrieved_at": stamp(),
        "fetch_status": "Failed",
        "pages_checked": 0,
        "service_fit": "Unknown",
        "residential_weg": "Unknown",
        "management_type": "Unknown",
        "portfolio_size": None,
        "portfolio_size_status": "Unknown",
        "berlin_relevance": row.get("berlin_relevance", "Unknown"),
        "evidence_urls": [],
        "claims": [],
    }
    if not url:
        return result, {"company_id": row.get("company_id", ""), "url": url, "status": "missing URL", "pages_checked": "0", "retrieved_at": stamp()}
    pages = [url]
    seen = set()
    all_text = ""
    checked_urls: list[str] = []
    for page_url in pages[: config.max_pages_per_company]:
        if page_url in seen or urlparse(page_url).netloc != urlparse(url).netloc:
            continue
        seen.add(page_url)
        final_url, text, links = fetch(page_url, config)
        result["pages_checked"] = int(result["pages_checked"]) + 1
        if not text:
            continue
        result["fetch_status"] = "Fetched"
        checked_urls.append(final_url)
        all_text += " " + text
        keywords = ("service", "leistungen", "weg", "mietverwaltung", "hausverwaltung", "impressum", "team", "referenzen", "projekte", "portfolio", "kontakt")
        for link in links:
            low = link.lower()
            if any(word in low for word in keywords) and link not in seen and len(pages) < config.max_pages_per_company:
                pages.append(link)
    text = re.sub(r"\s+", " ", all_text).strip()
    service, confidence, excerpt = claim(text, [r"hausverwaltung", r"immobilienverwaltung", r"property management", r"verwaltung von immobilien"])
    weg, weg_conf, weg_excerpt = claim(text, [r"\bweg\b", r"wohnungseigent[üu]mergemeinschaft", r"residential property", r"mietverwaltung"])
    if service != "Unknown":
        result["service_fit"] = service
        result["management_type"] = "WEG-Verwaltung" if re.search(r"\bweg\b|wohnungseigent", text, re.I) else "Hausverwaltung"
        result["claims"].append({"field": "service_fit", "value": service, "confidence": confidence, "evidence_url": checked_urls[0] if checked_urls else url, "evidence_excerpt": excerpt})
    if weg != "Unknown":
        result["residential_weg"] = weg
        result["claims"].append({"field": "residential_weg", "value": weg, "confidence": weg_conf, "evidence_url": checked_urls[0] if checked_urls else url, "evidence_excerpt": weg_excerpt})
    portfolio = re.search(r"(?:über|mehr als|more than|verwaltet|manag(?:e|es))\s+(\d{2,5})\s+(?:einheiten|objekte|immobilien|units|properties|wohnungen)", text, re.I)
    if portfolio:
        result["portfolio_size"] = int(portfolio.group(1))
        result["portfolio_size_status"] = "Confirmed"
        result["claims"].append({"field": "portfolio_size", "value": int(portfolio.group(1)), "confidence": "High", "evidence_url": checked_urls[0] if checked_urls else url, "evidence_excerpt": portfolio.group(0)})
    result["evidence_urls"] = checked_urls
    result["text_excerpt"] = text[:900]
    capture = {"company_id": row.get("company_id", ""), "url": checked_urls[0] if checked_urls else url, "status": result["fetch_status"], "pages_checked": str(result["pages_checked"]), "retrieved_at": result["retrieved_at"]}
    return result, capture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--capture-index", type=Path, required=True)
    args = parser.parse_args()
    config = RuntimeConfig.from_env()
    with args.input.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    results: list[dict[str, object]] = []
    captures: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(process, row, config) for row in rows]
        for future in as_completed(futures):
            result, capture = future.result()
            results.append(result)
            captures.append(capture)
    results.sort(key=lambda item: str(item.get("company_id", "")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    args.capture_index.parent.mkdir(parents=True, exist_ok=True)
    with args.capture_index.open("w", encoding="utf-8", newline="") as handle:
        fields = ["company_id", "url", "status", "pages_checked", "retrieved_at"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(captures, key=lambda item: item["company_id"]))
    fetched = sum(item.get("fetch_status") == "Fetched" for item in results)
    print(json.dumps({"companies": len(results), "fetched": fetched, "failed": len(results) - fetched}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
