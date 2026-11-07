"""Centralized, secret-safe runtime configuration for the lead pipeline."""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    path = path or ROOT / ".env"
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class RuntimeConfig:
    apify_api_token: str = ""
    hunter_api_key: str = ""
    ted_api_base_url: str = ""
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    request_timeout_seconds: int = 15
    max_pages_per_company: int = 10
    max_fetch_retries: int = 2
    apify_max_spend_usd: float = 5.0
    max_priority_accounts: int = 30

    @classmethod
    def from_env(cls, path: Path | None = None) -> "RuntimeConfig":
        values = load_dotenv(path)
        merged = {key: os.environ[key] for key in values if key in os.environ}
        merged.update(values)
        return cls(
            apify_api_token=merged.get("APIFY_API_TOKEN", ""),
            hunter_api_key=merged.get("HUNTER_API_KEY", ""),
            ted_api_base_url=merged.get("TED_API_BASE_URL", ""),
            overpass_api_url=merged.get("OVERPASS_API_URL", cls.overpass_api_url),
            request_timeout_seconds=int(merged.get("REQUEST_TIMEOUT_SECONDS", cls.request_timeout_seconds)),
            max_pages_per_company=int(merged.get("MAX_PAGES_PER_COMPANY", cls.max_pages_per_company)),
            max_fetch_retries=int(merged.get("MAX_FETCH_RETRIES", cls.max_fetch_retries)),
            apify_max_spend_usd=float(merged.get("APIFY_MAX_SPEND_USD", cls.apify_max_spend_usd)),
            max_priority_accounts=int(merged.get("MAX_PRIORITY_ACCOUNTS", cls.max_priority_accounts)),
        )

    def validate(self, provider: str | None = None, require_secrets: bool = False) -> list[str]:
        errors: list[str] = []
        if self.request_timeout_seconds <= 0 or self.max_pages_per_company <= 0 or self.max_fetch_retries < 0:
            errors.append("runtime bounds must be positive")
        if self.apify_max_spend_usd < 0 or self.max_priority_accounts <= 0:
            errors.append("spend and priority bounds are invalid")
        if provider == "apify" and require_secrets and not self.apify_api_token:
            errors.append("APIFY_API_TOKEN is required for Apify")
        if provider == "hunter" and require_secrets and not self.hunter_api_key:
            errors.append("HUNTER_API_KEY is required for Hunter")
        return errors

    def redacted(self) -> dict[str, object]:
        return {
            "apify_configured": bool(self.apify_api_token),
            "hunter_configured": bool(self.hunter_api_key),
            "ted_configured": bool(self.ted_api_base_url),
            "overpass_api_url": self.overpass_api_url,
            "request_timeout_seconds": self.request_timeout_seconds,
            "max_pages_per_company": self.max_pages_per_company,
            "max_fetch_retries": self.max_fetch_retries,
            "apify_max_spend_usd": self.apify_max_spend_usd,
            "max_priority_accounts": self.max_priority_accounts,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--check-example", type=Path)
    parser.add_argument("--provider", choices=["apify", "hunter", "ted", "overpass"])
    args = parser.parse_args()
    config = RuntimeConfig.from_env(args.check_example or args.env)
    errors = config.validate(provider=args.provider, require_secrets=False)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(config.redacted())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
