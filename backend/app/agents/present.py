"""Safe, concise display of owner-scoped, user-entered ticket/order fields."""
from __future__ import annotations
import re
import unicodedata


def safe_display(value: object, limit: int = 160) -> str:
    """Flatten untrusted data into one bounded line before it enters an agent draft."""
    if limit < 1:
        raise ValueError("limit must be positive")
    raw = str(value) if value is not None else ""
    # Remove ASCII control, bidirectional formatting and other hidden control chars.
    visible = "".join(char for char in raw if unicodedata.category(char) not in {"Cc", "Cf", "Cs"})
    flat = re.sub(r"\s+", " ", visible).strip()
    return flat[:limit] or "(not provided)"
