"""Conservative OCR text normalization for scientific tables."""

from __future__ import annotations

import re


_SPACE_RE = re.compile(r"\s+")
_ATTACHED_FOOTNOTE_RE = re.compile(
    r"^(?P<body>.*\d[^\s]*?)(?P<marker>[A-Da-d])$"
)
_SPACED_FOOTNOTE_RE = re.compile(
    r"^(?P<body>.*\d.*?)\s+(?P<marker>[A-Da-d])$"
)
_EMBEDDED_FOOTNOTE_RE = re.compile(
    r"^(?P<body>.*\d[^\s]*?)(?P<marker>[A-Da-d])(?P<suffix>\s+\(.*\))$"
)
_CHAR_TRANSLATION = str.maketrans(
    {
        "\u00a0": " ",
        "\u2007": " ",
        "\u202f": " ",
        "µ": "μ",
        "～": "~",
        "∼": "~",
        "˜": "~",
        "‐": "-",
        "‑": "-",
        "‒": "-",
        "–": "-",
        "—": "-",
        "−": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
)


def normalize_ocr_text(raw_text: str) -> str:
    """Normalize typography and whitespace without guessing scientific values."""
    translated = str(raw_text).translate(_CHAR_TRANSLATION)
    return _SPACE_RE.sub(" ", translated).strip()


def split_footnote_suffix(text: str) -> tuple[str, str | None]:
    """Separate a conservative A-D suffix while preserving its marker."""
    normalized = normalize_ocr_text(text)
    for pattern in (_SPACED_FOOTNOTE_RE, _ATTACHED_FOOTNOTE_RE):
        match = pattern.fullmatch(normalized)
        if match is not None:
            return match.group("body").strip(), match.group("marker").upper()
    return normalized, None


def normalize_footnote_suffix_spacing(text: str) -> str:
    """Add spacing around attached A-D markers without changing their value."""
    normalized = normalize_ocr_text(text)
    embedded = _EMBEDDED_FOOTNOTE_RE.fullmatch(normalized)
    if embedded is not None:
        return (
            f"{embedded.group('body')} {embedded.group('marker').upper()}"
            f"{embedded.group('suffix')}"
        )
    body, marker = split_footnote_suffix(normalized)
    return f"{body} {marker}" if marker is not None else normalized
