import pytest

from qa_agent_cli.file_parser import parse

class TestParseSingleFile:
    def test_returns_dict_keyed_by_filename_stem(self, tmp_path):
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("This is a test file")

        result = parse(test_file)

        assert result == {"test_file_txt": "This is a test file"}

    def test_empty_file_returns_empty_string_content(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = parse(test_file)

        assert result == {"empty_txt": ""}

    def test_preserves_multiline_content(self, tmp_path):
        content = "line one\nline two\nline three"
        test_file = tmp_path / "multiline.txt"
        test_file.write_text(content)

        result = parse(test_file)

        assert result == {"multiline_txt": content}


class TestParseDirectory:
    def test_multiple_files_returns_single_dict_with_all_entries(self, tmp_path):
        (tmp_path / "test_file1.txt").write_text("This is test file 1")
        (tmp_path / "test_file2.txt").write_text("This is test file 2")

        result = parse(tmp_path)

        assert result == {
            "test_file1_txt": "This is test file 1",
            "test_file2_txt": "This is test file 2",
        }

    def test_empty_directory_returns_empty_dict(self, tmp_path):
        result = parse(tmp_path)

        assert result == {}

    def test_duplicate_stems_with_different_extensions(self, tmp_path):
        # Documents current behavior when two files share a stem,
        # e.g. notes.txt and notes.md — adjust once the intended
        # behavior is decided (last-write-wins, error, keyed by full name, ...).
        (tmp_path / "notes.txt").write_text("txt content")
        (tmp_path / "notes.md").write_text("md content")

        result = parse(tmp_path)

        assert len(result) == 2
        # Need to assert that it sees notes_txt and notes_md

class TestParseErrors:
    def test_nonexistent_path_raises(self, tmp_path):
        missing = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            parse(missing)
    
    def test_nonpath_type_raises(self, tmp_path):
        missing = ""

        with pytest.raises(FileNotFoundError):
            parse(missing)