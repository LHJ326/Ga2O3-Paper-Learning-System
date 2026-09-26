"""Parser adapter interfaces and tool-specific adapter placeholders."""

from .base import ParserAdapter
from .mineru_adapter import MinerUAdapter

__all__ = ["MinerUAdapter", "ParserAdapter"]
