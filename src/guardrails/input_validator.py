from __future__ import annotations

import re
from dataclasses import dataclass

MAX_PROMPT_LENGTH = 4_000
SUSPICIOUS_PATTERNS = (
    r"ignore\s+previous\s+instructions",
    r"system\s+prompt",
    r"reveal\s+secrets?",
    r"api\s+key",
)


@dataclass(frozen=True)
class PromptValidationResult:
    is_valid: bool
    normalized_prompt: str
    reason: str | None = None


def validate_prompt(prompt: str) -> PromptValidationResult:
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        return PromptValidationResult(False, normalized_prompt, "Prompt must not be empty.")

    if len(normalized_prompt) > MAX_PROMPT_LENGTH:
        return PromptValidationResult(False, normalized_prompt, "Prompt exceeds max length.")

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, normalized_prompt, flags=re.IGNORECASE):
            return PromptValidationResult(
                False,
                normalized_prompt,
                "Prompt contains blocked content.",
            )

    return PromptValidationResult(True, normalized_prompt)
