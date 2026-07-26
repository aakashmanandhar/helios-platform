import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from chunk_kb import chunk_markdown

SAMPLE_DOC = """# Return Policy

## Standard Return Window
Items may be returned within 30 days.

## Refund Timing
Refunds are issued within 3-5 business days.
"""


def test_splits_into_sections():
    chunks = chunk_markdown("kb_006", "Return Policy", SAMPLE_DOC)
    assert len(chunks) == 3  # intro + 2 sections


def test_title_prepended_to_non_first_chunks():
    chunks = chunk_markdown("kb_006", "Return Policy", SAMPLE_DOC)
    assert chunks[1]["chunk_text"].startswith("Return Policy")
    assert chunks[0]["chunk_text"].startswith("# Return Policy")


def test_chunk_index_sequential():
    chunks = chunk_markdown("kb_006", "Return Policy", SAMPLE_DOC)
    assert [c["chunk_index"] for c in chunks] == [0, 1, 2]
