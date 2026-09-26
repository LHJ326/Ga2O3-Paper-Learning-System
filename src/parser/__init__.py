"""Parser interfaces and registry for future parser adapters."""

from .base import BaseParser
from .registry import ParserRegistry, parser_registry

__all__ = ["BaseParser", "ParserRegistry", "parser_registry"]
