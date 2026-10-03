"""Shared helpers for the AI agents."""
from __future__ import annotations

import json
import re
from typing import Any

NO_INFO_MESSAGE = (
    "I couldn't find this information in the available government scheme documents."
)


def profile_summary(profile: dict[str, Any]) -> str:
    """Render a citizen profile into a compact natural-language summary."""
    flags = [
        label
        for key, label in [
            ("disability_status", "person with disability"),
            ("minority_status", "minority"),
            ("student_status", "student"),
            ("farmer_status", "farmer"),
            ("widow_status", "widow"),
            ("senior_citizen_status", "senior citizen"),
            ("bpl_status", "below poverty line (BPL)"),
        ]
        if profile.get(key)
    ]
    flag_text = f" Special status: {', '.join(flags)}." if flags else ""
    return (
        f"Name: {profile.get('full_name')}. Age: {profile.get('age')}. "
        f"Gender: {profile.get('gender')}. State: {profile.get('state')}, "
        f"District: {profile.get('district')}. Occupation: {profile.get('occupation')}. "
        f"Education: {profile.get('education')}. Annual income: Rs. {profile.get('annual_income')}. "
        f"Category: {profile.get('category')}.{flag_text}"
    )


def extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON object/array from an LLM response."""
    text = text.strip()
    # Strip markdown code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to the first {...} or [...] block.
        for opener, closer in (("{", "}"), ("[", "]")):
            start = text.find(opener)
            end = text.rfind(closer)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    continue
    return None
