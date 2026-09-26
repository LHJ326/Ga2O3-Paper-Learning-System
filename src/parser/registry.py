"""Registry for parser adapter classes."""

from __future__ import annotations

from .base import BaseParser


class ParserRegistry:
    """Store parser classes by stable names without choosing a default parser."""

    def __init__(self) -> None:
        self._parsers: dict[str, type[BaseParser]] = {}

    def register(self, name: str, parser_class: type[BaseParser]) -> None:
        """Register one parser class under a unique, non-empty name."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Parser name must not be empty.")
        if not issubclass(parser_class, BaseParser):
            raise TypeError("Registered parser must inherit from BaseParser.")
        if normalized_name in self._parsers:
            raise ValueError(f"Parser '{normalized_name}' is already registered.")
        self._parsers[normalized_name] = parser_class

    def get(self, name: str) -> type[BaseParser]:
        """Return a registered parser class by name."""
        try:
            return self._parsers[name]
        except KeyError as error:
            raise KeyError(f"Parser '{name}' is not registered.") from error

    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order."""
        return tuple(sorted(self._parsers))

    def create(self, name: str, *args: object, **kwargs: object) -> BaseParser:
        """Instantiate a registered parser without coupling callers to its class."""
        return self.get(name)(*args, **kwargs)


parser_registry = ParserRegistry()
