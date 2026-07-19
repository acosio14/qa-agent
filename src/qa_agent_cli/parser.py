# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import FileType

PARSER_REGISTRY = {}

def register_parser(file_type):
    def decorator(func):
        PARSER_REGISTRY[file_type] = func
        return func
    return decorator

@register_parser(".txt")
def txt_file_parser(file):
    with open(file) as f:
        file_content = f.read()
        return file_content

@register_parser(".md")
def markdown_parser(file):
    print("md file")

@register_parser(".csv")
def csv_parser(file):
    print("csv file")

@register_parser(".docx")
def docx_parser(file):
    print("docx file")

@register_parser(".pdf")
def pdf_parser(file):
    print("pdf file")

def create_file_type_dataclass(filepath: Path):
    # Verify if it a supported file type and parse it.
    # Supported types: .txt, .md, .csv, .docx, .pdf,
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem

    # Use specific file ext parser function in registry
    try:
        file_parser_fcn = PARSER_REGISTRY.get(file_extension)
        file_content = file_parser_fcn(filepath)
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
        logging.error('File path cant be read as file or dir')
        raise FileNotFoundError

    return [create_file_type_dataclass(file) for file in files]