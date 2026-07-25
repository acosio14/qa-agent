# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import ParsedFile
from docx import Document
from markitdown import MarkItDown


def convert_to_markdown(filepath):
    md = MarkItDown(enable_plugins=False)
    md_text = md.convert(filepath)
    return md_text

def chunk_file_content(markdown_text: str):
    ...

def create_file_type_dataclass(filepath: Path):
    
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem

    # Verify if file type supported
    supported_file_types = [".txt", ".pptx", ".docx", ".xlsx", ".pdf", ".md"]
    if file_extension not in supported_file_types:
        TypeError(f"Don't support file extension: {file_extension}")

    md_text = convert_to_markdown(filepath)
    # if len(md_text) > some_size:
    chunks =  chunk_file_content(md_text)
    # else { no chunks }

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