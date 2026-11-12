"""Dataset adapter registry."""

from .base import DatasetAdapter
from .catalog_adapters import ADAPTERS, create_adapter

__all__ = ["ADAPTERS", "DatasetAdapter", "create_adapter"]
