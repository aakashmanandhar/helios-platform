"""
Chunking strategy for internal KB/policy markdown documents.

Splits on level-2 (##) headers so each chunk is one semantically coherent
policy section (e.g. "Late Shipment Policy" as its own chunk, not buried
inside the whole document) - this makes retrieval much more precise than
embedding each doc as one giant blob. The doc title is prepended to every
chunk so the embedding still carries document-level context.

This is a versioned artifact on purpose: changing the header level split
on, or the chunk-overlap behavior, is a deliberate pipeline change, not a
silent config tweak - see the retrieval eval in tests/.
"""
import re


def chunk_markdown(doc_id, title, content):
    sections = re.split(r"\n(?=## )", content.strip())
    chunks = []
    idx = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue
        text = section if idx == 0 else f"{title}\n\n{section}"
        chunks.append({
            "source_id": doc_id,
            "chunk_index": idx,
            "chunk_text": text,
        })
        idx += 1
    return chunks
