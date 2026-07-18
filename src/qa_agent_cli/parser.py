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

@register_parser("txt")
def txt_file_parser():
    ...

@register_parser("md")
def markdown_parser():
    ...

@register_parser("csv")
def csv_parser():
    ...

@register_parser("docx")
def docx_parser():
    ...

@register_parser("pdf")
def pdf_parser():
    ...

def create_file_type_dataclass(filepath: Path):
    # Used to verify if supported file type and parse it.
    # Supported types: .txt, .md, .csv, .docx, .pdf,
    # Not supported: .json, .xlsx, .yaml
    file_extension = filepath.suffix
    filename = filepath.stem

    # Match should be to decide what content is extracted
    # based off of the extension.
    try:
        file_content = PARSER_REGISTRY.get(file_extension)
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