from __future__ import annotations

import re
from typing import Any

CONFERENCE_ABSTRACT_NUMBER = re.compile(r"^\s*(\d{1,3})\s+\S")
CONFERENCE_POSTER_CODE = re.compile(r"^\s*[A-Z]\d+\s*[^\w\s]\s*\d+\s*:")


def title_abstract_metadata_issue(
    record: dict[str, Any],
) -> tuple[str, dict[str, Any]] | None:
    title_match = CONFERENCE_ABSTRACT_NUMBER.match(str(record.get("title", "")))
    abstract_match = CONFERENCE_ABSTRACT_NUMBER.match(str(record.get("abstract", "")))
    if (
        title_match
        and abstract_match
        and title_match.group(1) != abstract_match.group(1)
    ):
        return (
            "conference_abstract_number_mismatch",
            {
                "title_abstract_number": title_match.group(1),
                "body_abstract_number": abstract_match.group(1),
            },
        )
    title = str(record.get("title", ""))
    abstract = str(record.get("abstract", "")).lstrip()
    if CONFERENCE_POSTER_CODE.match(title) and abstract[:1].islower():
        return (
            "conference_abstract_body_fragment",
            {
                "body_prefix": abstract[:40],
            },
        )
    return None
