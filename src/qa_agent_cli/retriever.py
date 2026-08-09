# Takes question and stored chunks -> creates top-k chunks
from .file_types import ParsedFile
from dataclasses import asdict
import bm25s


def retrieve_top_k_chunks(parsed_files: list[ParsedFile], question: str, k: int) -> dict[str]:


    question_tokens = bm25s.tokenize(question)

    chunks = [
        asdict(chunk)
        for file in parsed_files
        for chunk in file.chunks
    ]

    chunk_tokens = bm25s.tokenize(chunk["text"] for chunk in chunks)

    retriever = bm25s.BM25(corpus=chunks)
    retriever.index(chunk_tokens)

    results = retriever.retrieve(question_tokens, k=k, return_as="documents")

    return results
