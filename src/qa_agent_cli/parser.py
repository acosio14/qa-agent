# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import FileType

def create_file_type_dataclass(filepath: Path):
    # Used to verify if its a file type the app supports
    # Supported types: .txt, .md, .csv, .docx, .pdf,
    # Not supported: .json, .xlsx, .yaml
    file_extension = filepath.suffix
    filename = filepath.stem

    # Match should be to decide what content is extracted
    # based off of the extension.
    match file_extension:
        case '.txt':
            with open(filepath) as f:
                file_content = f.read()
        case '.md':
            ...
        case '.csv':
            ...
        case '.docx':
            ...
        case '.pdf':
            ...
        case _:
            raise TypeError(f"Don't support file extension: {file_extension}")
        
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