import pytest

from qa_agent_cli.file_types import ParsedFile, Chunk
from qa_agent_cli.retriever import retrieve_top_k_chunks


def make_file(name, *texts):
    """Build a ParsedFile whose chunks carry the given texts."""
    chunks = [
        Chunk(filename=f"{name}.txt", text=text, section=chr(ord("A") + i))
        for i, text in enumerate(texts)
    ]
    return ParsedFile(name=name, extension=".txt", chunks=chunks)


class TestRetrieveTopK:
    def test_returns_most_relevant_chunk_first(self):
        # Arrange
        pf = make_file(
            "doc",
            "The cat sat on the mat",
            "Python is a programming language",
            "The weather is sunny today",
        )

        # Act
        results = retrieve_top_k_chunks([pf], "python programming language", k=1)

        # Assert
        assert results[0][0]["text"] == "Python is a programming language"

    def test_returns_exactly_k_chunks(self):
        # Arrange
        pf = make_file("doc", "alpha text", "beta text", "gamma text")

        # Act
        results = retrieve_top_k_chunks([pf], "beta", k=2)

        # Assert
        assert results.shape == (1, 2)
        assert len(results[0]) == 2

    def test_ranks_relevant_chunk_above_irrelevant_one(self):
        # Arrange
        pf = make_file(
            "doc",
            "python programming tutorial",
            "the ocean is deep and blue",
        )

        # Act
        results = retrieve_top_k_chunks([pf], "python programming", k=2)

        # Assert
        assert results[0][0]["text"] == "python programming tutorial"

    def test_combines_chunks_across_multiple_files(self):
        # Arrange
        pf1 = make_file("a", "cats and dogs are pets")
        pf2 = make_file("b", "distributed systems and databases")

        # Act
        results = retrieve_top_k_chunks([pf1, pf2], "databases", k=1)

        # Assert
        assert results[0][0]["filename"] == "b.txt"
        assert results[0][0]["text"] == "distributed systems and databases"

    def test_result_chunk_carries_full_dataclass_fields(self):
        # Arrange
        pf = make_file("doc", "only chunk here")

        # Act
        results = retrieve_top_k_chunks([pf], "chunk", k=1)

        # Assert
        assert set(results[0][0].keys()) == {
            "filename",
            "text",
            "line_num",
            "page",
            "section",
        }


class TestRetrieveErrors:
    def test_k_larger_than_corpus_raises(self):
        # Arrange
        pf = make_file("doc", "first chunk", "second chunk")

        # Act / Assert
        with pytest.raises(ValueError):
            retrieve_top_k_chunks([pf], "chunk", k=5)
