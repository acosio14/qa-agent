# Takes a question and the parsed files' chunks, and returns the top-k most
# relevant chunks using BM25 lexical ranking.
from dataclasses import asdict

import bm25s
import numpy as np

from .file_types import ParsedFile


def retrieve_top_k_chunks(
    parsed_files: list[ParsedFile], question: str, k: int
) -> np.ndarray:
    """Return the ``k`` chunks most relevant to ``question``.

    The result is shaped ``(1, n)`` — a single query row of chunk dicts, ranked
    best-first — matching what ``formatter.format_prompts`` consumes. ``n`` is
    ``min(k, number_of_chunks)``, so asking for more chunks than exist returns
    all of them rather than raising. When there is nothing to search (no files,
    only failed parses, or ``k <= 0``) an empty ``(1, 0)`` array is returned.
    """
    # Only successfully parsed files contribute searchable chunks.
    chunks = [
        asdict(chunk)
        for file in parsed_files
        if file.ok
        for chunk in file.chunks
    ]

    if not chunks or k <= 0:
        return np.empty((1, 0), dtype=object)

    k = min(k, len(chunks))  # never ask BM25 for more docs than the corpus has

    question_tokens = bm25s.tokenize(question, stopwords="en", show_progress=False)
    chunk_tokens = bm25s.tokenize(
        [chunk["text"] for chunk in chunks], stopwords="en", show_progress=False
    )

    bm25 = bm25s.BM25(corpus=chunks)
    bm25.index(chunk_tokens, show_progress=False)

    return bm25.retrieve(
        question_tokens, k=k, return_as="documents", show_progress=False
    )
