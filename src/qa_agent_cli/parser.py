# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import FileType
from charset_normalizer import detect
from docx import Document
import fitz

PARSER_REGISTRY = {}

def register_parser(file_type):
    def decorator(func):
        PARSER_REGISTRY[file_type] = func
        return func
    return decorator

@register_parser(".txt")
def txt_file_parser(filepath):
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    file_encoding = detect(file_bytes)["encoding"]
    file_content = file_bytes.decode(file_encoding)
    return file_content 

@register_parser(".md")
def markdown_parser(filepath):
    with open(filepath, "r") as f:
        file_content = f.read()
    return file_content 

@register_parser(".docx")
def docx_parser(docx_filepath):
    doc = Document(docx_filepath)
    file_content = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        style_name = p.style.name.lower()

        # Handle Headings
        if "heading 1" in style_name:
            file_content.append(f"# {text}")
        elif "heading 2" in style_name:
            file_content.append(f"## {text}")
        elif "heading 3" in style_name:
            file_content.append(f"### {text}")

        # Handle Bullet Points / Lists
        elif "list bullet" in style_name:
            file_content.append(f"* {text}")
        elif "list number" in style_name:
            file_content.append(f"1. {text}")

        # Handle Normal Paragraphs
        else:
            file_content.append(text)

    return "\n\n".join(file_content)

@register_parser(".pdf")
def pdf_parser(file):
    doc = fitz.open(file)
    for page in doc:
        text = page.get_text()

def create_file_type_dataclass(filepath: Path):
    # Verify if it a supported file type and parse it.
    # Supported types: .txt, .md, .csv, .docx, .pdf,
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem

    # Use specific file ext parser function in registry
    try:
        file_parser = PARSER_REGISTRY.get(file_extension)
        file_content = file_parser(filepath)
    except:
        TypeError(f"Don't support file extension: {file_extension}")
    
    return FileType(filename, file_extension, file_content)
        

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