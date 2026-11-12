"""Dataset-specific adapter entry points.

Each public class is intentionally explicit. The source layouts differ and must
be implemented against a pinned release manifest instead of guessed field names.
"""

from __future__ import annotations

from pathlib import Path

from .generic_jsonl import GenericJsonlAdapter
from .source_formats import MotChallengeAdapter, ReIdListAdapter, UADetracXmlAdapter


class CityFlowAdapter(GenericJsonlAdapter):
    """CityFlow adapter contract; expects a release-normalized JSONL export."""

    dataset_name = "CityFlow"


class CityFlowV2Adapter(GenericJsonlAdapter):
    """CityFlowV2 adapter contract; expects a release-normalized JSONL export."""

    dataset_name = "CityFlowV2"


class AICityAdapter(GenericJsonlAdapter):
    """AI City Challenge adapter contract; one class per pinned track release."""

    dataset_name = "AI_City_Challenge"


class VeRi776Adapter(ReIdListAdapter):
    """VeRi-776 adapter for a release-normalized image identity list."""

    dataset_name = "VeRi-776"


class VehicleIDAdapter(ReIdListAdapter):
    """VehicleID adapter for a release-normalized image identity list."""

    dataset_name = "VehicleID"


class VehicleNetAdapter(ReIdListAdapter):
    """VehicleNet adapter; component-release provenance is required."""

    dataset_name = "VehicleNet"


class UADetracAdapter(UADetracXmlAdapter):
    """UA-DETRAC adapter for a pinned XML release."""


class MotTextAdapter(MotChallengeAdapter):
    """Generic MOT text adapter for a pinned challenge track."""


ADAPTERS = {
    "cityflow": CityFlowAdapter,
    "cityflowv2": CityFlowV2Adapter,
    "aicity": AICityAdapter,
    "veri776": VeRi776Adapter,
    "vehicleid": VehicleIDAdapter,
    "vehiclenet": VehicleNetAdapter,
    "ua-detrac": UADetracAdapter,
    "mot-text": MotTextAdapter,
}


def create_adapter(
    name: str,
    source_root: Path,
    release: str,
    filename: str | None = None,
) -> GenericJsonlAdapter | ReIdListAdapter | UADetracXmlAdapter | MotChallengeAdapter:
    """Create a named adapter without silently falling back to another dataset."""
    try:
        adapter_type = ADAPTERS[name.lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported dataset adapter: {name}") from exc
    adapter = adapter_type(source_root, release=release)
    if filename:
        if hasattr(adapter, "annotation_path"):
            adapter.annotation_path = source_root / filename  # type: ignore[attr-defined]
        elif hasattr(adapter, "annotation_filename"):
            adapter.annotation_filename = filename  # type: ignore[attr-defined]
        elif hasattr(adapter, "list_filename"):
            adapter.list_filename = filename  # type: ignore[attr-defined]
    return adapter
