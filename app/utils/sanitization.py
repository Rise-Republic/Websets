import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

def sanitize_prompt(prompt: str) -> str:
    """Validate and escape user-provided prompt or text."""
    if len(prompt) > 4000:
        raise ValueError("Prompt too long")
    if _CONTROL_CHARS_RE.search(prompt):
        raise ValueError("Prompt contains control characters")
    return prompt.replace("{", "\\{").replace("}", "\\}").replace("`", "\\`")

