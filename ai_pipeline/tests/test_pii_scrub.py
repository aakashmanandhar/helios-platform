import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pii_scrub import scrub_pii


def test_email_is_redacted():
    text = "reach me at john.doe82@gmail.com please"
    scrubbed, was_scrubbed = scrub_pii(text)
    assert was_scrubbed
    assert "[REDACTED_EMAIL]" in scrubbed
    assert "john.doe82@gmail.com" not in scrubbed


def test_phone_is_redacted():
    text = "call me back at 555-234-8891 anytime"
    scrubbed, was_scrubbed = scrub_pii(text)
    assert was_scrubbed
    assert "[REDACTED_PHONE]" in scrubbed
    assert "555-234-8891" not in scrubbed


def test_clean_text_untouched():
    text = "the package arrived a day late but otherwise fine"
    scrubbed, was_scrubbed = scrub_pii(text)
    assert not was_scrubbed
    assert scrubbed == text


def test_none_passthrough():
    scrubbed, was_scrubbed = scrub_pii(None)
    assert scrubbed is None
    assert not was_scrubbed
