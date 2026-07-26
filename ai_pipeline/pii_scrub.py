"""
PII scrubbing for text destined for the vector store.

Deliberately simple regex-based detection - good enough to catch the
synthetic PII leakage injected into the ticket generator (emails, phone
numbers), and a realistic first pass for any text pipeline. A production
system would likely layer in a proper NER-based PII model on top of this.
"""
import re

EMAIL_RE = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")
PHONE_RE = re.compile(r"(\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}")


def scrub_pii(text):
    """Returns (scrubbed_text, was_scrubbed: bool). Passes through None unchanged."""
    if text is None:
        return text, False

    scrubbed = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    scrubbed = PHONE_RE.sub("[REDACTED_PHONE]", scrubbed)
    return scrubbed, scrubbed != text
