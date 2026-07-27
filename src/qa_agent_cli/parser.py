# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import ParsedFile
from docx import Document
from markitdown import MarkItDown

SMALL_FILE_SIZE_BYTES = 5000

def convert_to_markdown(filepath):
    md = MarkItDown(enable_plugins=False)
    md_text = md.convert(filepath)
    return md_text

def chunk_file_content(md_text: str):
    # split into sections -> store in datastructure, list
    headers = ["#", "##"]
    if headers[0] in md_text or headers[1] in md_text:
        section_idx = [
            idx
            for idx, char in enumerate(md_text)
            if char in headers
        ]
        sections = [md_text[i:i+1] for i in section_idx]
    else:
        md_lines = md_text.split("\n")
        print(md_lines)
        section_idx = [
            idx
            for idx, line in enumerate(md_lines)
            if line.strip() == ''
        ]
        chunks = []
        line_list = []
        for idx, line in enumerate(md_lines):
            if idx not in section_idx:
                line_list.append(line)                
            elif idx in section_idx:
                chunks.append(('\n').join(line_list))
                line_list = []
            else:
                chunks.append('\n').join(line_list)

        sections = chunks

    return sections


def create_file_type_dataclass(filepath: Path):
    
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem

    # Verify if file type supported
    supported_file_types = [".txt", ".pptx", ".docx", ".xlsx", ".pdf", ".md"]
    if file_extension not in supported_file_types:
        TypeError(f"Don't support file extension: {file_extension}")

    md_text = convert_to_markdown(filepath).text_content
    chunks = [md_text]
    if Path(md_text).stat().st_size > SMALL_FILE_SIZE_BYTES:
        chunks =  chunk_file_content(md_text)

    return ParsedFile(filename, file_extension, md_text, chunks)
      

def parse(filepath: Path) -> dict[str]:
    # Need to verify if its a directory or file
    # if directory, then loop through each file and make dict of each
    path = Path(filepath)
    if path.is_file():
        files = [filepath] # should be a file
    elif path.is_dir():
        files = [file for file in path.iterdir()]
    else:
        logging.error('File path cannot be read as file or dir')
        raise FileNotFoundError

    return [create_file_type_dataclass(file) for file in files]