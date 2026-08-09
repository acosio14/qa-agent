import pytest

from qa_cli.parser import (
    parse,
    create_file_type_dataclass,
    chunk_file_content,
    CHUNK_SIZE_THRESHOLD_BYTES,
)
from qa_cli.file_types import ParsedFile


def by_name(results):
    """Index a parse() result list by file stem for order-independent asserts."""
    return {pf.name: pf for pf in results}


class TestParseSingleFile:
    def test_returns_list_with_one_parsed_file(self, tmp_path):
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file")

        # Act
        result = parse(test_file)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParsedFile)

    def test_parsed_file_carries_stem_extension_and_content(self, tmp_path):
        # Arrange
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file")

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is True
        assert pf.error is None
        assert pf.name == "test_file"
        assert pf.extension == ".txt"
        assert pf.raw_text == "This is a test file"

    def test_preserves_multiline_content(self, tmp_path):
        # Arrange
        content = "line one\nline two\nline three"
        test_file = tmp_path / "multiline.txt"
        test_file.write_text(content)

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is True
        assert pf.raw_text == content

    def test_extension_match_is_case_insensitive(self, tmp_path):
        # Arrange
        test_file = tmp_path / "shouting.TXT"
        test_file.write_text("still valid")

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is True
        assert pf.extension == ".TXT"

    def test_small_file_is_a_single_chunk(self, tmp_path):
        # Arrange
        test_file = tmp_path / "small.txt"
        test_file.write_text("short content")

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert len(pf.chunks) == 1
        assert pf.chunks[0].text == "short content"

    def test_large_file_is_split_into_multiple_chunks(self, tmp_path):
        # Arrange
        # Exceed the byte threshold and provide headers so the file is chunked.
        body_a = "word " * 400
        body_b = "more " * 400
        content = f"# Section A\n{body_a}\n# Section B\n{body_b}"
        assert len(content.encode()) > CHUNK_SIZE_THRESHOLD_BYTES
        test_file = tmp_path / "large.md"
        test_file.write_text(content)

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is True
        assert len(pf.chunks) > 1
        assert [c.section for c in pf.chunks] == ["# Section A", "# Section B"]


class TestParseFailuresAreNonFatal:
    def test_empty_file_is_recorded_as_failed(self, tmp_path):
        # Arrange
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is False
        assert pf.error == "File is empty."
        assert pf.name == "empty"

    def test_explicitly_named_unsupported_file_is_recorded_as_failed(self, tmp_path):
        # Arrange
        # Single-file mode does not pre-filter, so the validator inside
        # create_file_type_dataclass is what rejects it.
        test_file = tmp_path / "weird.xyz"
        test_file.write_text("some data")

        # Act
        pf = parse(test_file)[0]

        # Assert
        assert pf.ok is False
        assert pf.error is not None and ".xyz" in pf.error

    def test_one_bad_file_does_not_abort_the_batch(self, tmp_path):
        # Arrange
        (tmp_path / "good.txt").write_text("good content")
        (tmp_path / "empty.txt").write_text("")

        # Act
        results = by_name(parse(tmp_path))

        # Assert
        assert results["good"].ok is True
        assert results["empty"].ok is False


class TestParseDirectory:
    def test_multiple_files_all_parsed(self, tmp_path):
        # Arrange
        (tmp_path / "file1.txt").write_text("content one")
        (tmp_path / "file2.txt").write_text("content two")

        # Act
        results = by_name(parse(tmp_path))

        # Assert
        assert results.keys() == {"file1", "file2"}
        assert results["file1"].raw_text == "content one"
        assert results["file2"].raw_text == "content two"

    def test_empty_directory_returns_empty_list(self, tmp_path):
        # Arrange
        # tmp_path is an empty directory by default.

        # Act
        results = parse(tmp_path)

        # Assert
        assert results == []

    def test_same_stem_different_extensions_both_kept(self, tmp_path):
        # Arrange
        # A list result means shared stems no longer collide.
        (tmp_path / "notes.txt").write_text("txt content")
        (tmp_path / "notes.md").write_text("md content")

        # Act
        results = parse(tmp_path)

        # Assert
        assert len(results) == 2
        assert {pf.extension for pf in results} == {".txt", ".md"}

    def test_hidden_files_are_skipped(self, tmp_path):
        # Arrange
        (tmp_path / "real.txt").write_text("keep me")
        (tmp_path / ".DS_Store").write_text("system junk")

        # Act
        results = parse(tmp_path)

        # Assert
        assert len(results) == 1
        assert results[0].name == "real"

    def test_unsupported_extensions_are_skipped(self, tmp_path):
        # Arrange
        (tmp_path / "keep.md").write_text("# keep")
        (tmp_path / "skip.xyz").write_text("ignore me")

        # Act
        results = parse(tmp_path)

        # Assert
        assert len(results) == 1
        assert results[0].name == "keep"

    def test_subdirectories_are_skipped(self, tmp_path):
        # Arrange
        (tmp_path / "keep.txt").write_text("keep")
        (tmp_path / "nested").mkdir()

        # Act
        results = parse(tmp_path)

        # Assert
        assert len(results) == 1
        assert results[0].name == "keep"


class TestParseErrors:
    def test_nonexistent_path_raises(self, tmp_path):
        # Arrange
        missing = tmp_path / "does_not_exist.txt"

        # Act / Assert
        with pytest.raises(FileNotFoundError):
            parse(missing)


class TestCreateFileTypeDataclass:
    def test_unsupported_extension_returns_failed_record(self, tmp_path):
        # Arrange
        f = tmp_path / "data.bin"
        f.write_text("bytes")

        # Act
        pf = create_file_type_dataclass(f)

        # Assert
        assert pf.ok is False
        assert pf.extension == ".bin"
        assert pf.error is not None and ".bin" in pf.error

    def test_accepts_string_path(self, tmp_path):
        # Arrange
        f = tmp_path / "as_string.txt"
        f.write_text("hello")

        # Act
        pf = create_file_type_dataclass(str(f))

        # Assert
        assert pf.ok is True
        assert pf.raw_text == "hello"


class TestChunkFileContentHeaders:
    def test_content_before_first_header_kept_as_preamble(self):
        # Arrange
        filename = "test_file"
        text = "intro line\n# H1\nbody a\n## H2\nbody b"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert chunks[0].section is None
        assert chunks[0].text == "intro line"
        assert [c.section for c in chunks[1:]] == ["# H1", "## H2"]

    def test_no_preamble_when_content_starts_with_header(self):
        # Arrange
        filename = "test_file"
        text = "# H1\nbody a\n# H2\nbody b"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert [c.section for c in chunks] == ["# H1", "# H2"]
        assert chunks[0].text == "# H1\nbody a"

    def test_final_header_section_does_not_index_error(self):
        # Arrange
        # Regression: the last section previously read one past the list end.
        filename = "test_file"
        text = "# Only\nlast line"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].text == "# Only\nlast line"


class TestChunkFileContentBlankLines:
    def test_splits_paragraphs_on_blank_lines(self):
        # Arrange
        filename = "test_file"
        text = "Para one\nline two\n\nPara two"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert [c.text for c in chunks] == ["Para one\nline two", "Para two"]

    def test_leading_trailing_and_repeated_blanks_produce_no_empty_chunks(self):
        # Arrange
        filename = "test_file"
        text = "\n\nPara one\nline two\n\n\nPara two\n"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert [c.text for c in chunks] == ["Para one\nline two", "Para two"]
        assert all(c.text.strip() for c in chunks)

    def test_single_paragraph_without_trailing_newline(self):
        # Arrange
        filename = "test_file"
        text = "just one paragraph"

        # Act
        chunks = chunk_file_content(filename, text)

        # Assert
        assert len(chunks) == 1
        assert chunks[0].text == "just one paragraph"
