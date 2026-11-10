"""Capability-to-provider resolution for Codex-native research actions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EVIDENCE_STATUSES = frozenset({"DISCOVERY", "CANDIDATE_EVIDENCE", "VERIFIED_EVIDENCE"})


def load_capability_registry(root: Path) -> dict[str, Any]:
    path = root / "config" / "tool_capabilities.json"
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read tool capability registry: {path}") from exc
    validate_capability_registry(registry)
    return registry


def validate_capability_registry(registry: object) -> None:
    if not isinstance(registry, dict):
        raise ValueError("tool capability registry must be an object")
    statuses = registry.get("evidence_statuses")
    if not isinstance(statuses, dict) or set(statuses) != set(EVIDENCE_STATUSES):
        raise ValueError("tool capability registry must define DISCOVERY, CANDIDATE_EVIDENCE, and VERIFIED_EVIDENCE")
    for status, definition in statuses.items():
        if not isinstance(definition, dict) or not isinstance(definition.get("description"), str):
            raise ValueError(f"invalid evidence status definition: {status}")
        if not isinstance(definition.get("promotable_without_verification"), bool):
            raise ValueError(f"invalid promotion rule for evidence status: {status}")
    capabilities = registry.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        raise ValueError("tool capability registry must define capabilities")
    for capability, definition in capabilities.items():
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability names must be non-empty strings")
        if not isinstance(definition, dict):
            raise ValueError(f"invalid capability definition: {capability}")
        providers = definition.get("providers")
        if not isinstance(providers, list) or not providers or not all(isinstance(provider, str) and provider.strip() for provider in providers):
            raise ValueError(f"capability providers must be a non-empty string list: {capability}")
        if definition.get("default_evidence_status") not in EVIDENCE_STATUSES:
            raise ValueError(f"invalid default evidence status: {capability}")
        if not isinstance(definition.get("evidence_role"), str) or not definition["evidence_role"].strip():
            raise ValueError(f"capability evidence_role must be non-empty: {capability}")


def resolve_capability(root: Path, capability: str, available_providers: list[str] | None = None) -> dict[str, Any]:
    registry = load_capability_registry(root)
    definition = registry["capabilities"].get(capability)
    if definition is None:
        raise ValueError(f"unknown capability: {capability}")
    configured = list(definition["providers"])
    available = None if available_providers is None else [provider for provider in available_providers if provider in configured]
    return {
        "capability": capability,
        "providers": configured,
        "available_providers": available,
        "resolution_status": "unresolved" if available is None else ("available" if available else "unavailable"),
        "default_evidence_status": definition["default_evidence_status"],
        "evidence_role": definition["evidence_role"],
        "provider_selection": "parent_runtime",
    }


def validate_profile_capabilities(root: Path, capabilities: object) -> list[str]:
    if not isinstance(capabilities, list) or not all(isinstance(item, str) and item.strip() for item in capabilities):
        raise ValueError("agent capabilities must be a list of non-empty strings")
    registry = load_capability_registry(root)
    unknown = sorted(set(capabilities) - set(registry["capabilities"]))
    if unknown:
        raise ValueError(f"unknown agent capabilities: {', '.join(unknown)}")
    return list(capabilities)




def authorize_capability(root: Path, profile_name: str, capability: str, provider: str | None = None) -> dict[str, Any]:
    """Authorize one parent-selected capability for one registered profile."""
    if not profile_name:
        raise ValueError("capability authorization requires profile_name")
    try:
        role_contracts = json.loads((root / "config" / "agent_role_contracts.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("cannot read agent role contracts for capability authorization") from exc
    role = role_contracts.get(profile_name) if isinstance(role_contracts, dict) else None
    if not isinstance(role, dict):
        raise ValueError(f"unknown capability profile: {profile_name}")
    allowed = validate_profile_capabilities(root, role.get("capabilities") or [])
    if capability not in allowed:
        raise ValueError(f"profile {profile_name} is not allowed capability: {capability}")
    resolution = resolve_capability(root, capability)
    if provider is not None and provider not in resolution["providers"]:
        raise ValueError(f"provider {provider} is not configured for capability: {capability}")
    return {"profile_name": profile_name, "capability": capability, "provider": provider, "resolution": resolution}
