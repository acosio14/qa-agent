from qa_agent_cli.file_parser import parse

def test_file_parser_one_file_returns_dict(filepath):
    test_file = filepath / "test_file.txt"

    test_file.write_text("This is a test file")

    result = parse(test_file)
    assert result == {"test_file": "This is a test file"}