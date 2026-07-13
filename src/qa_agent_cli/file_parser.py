# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging

def file_type():
    # Used to verify if its a file type the app supports
    # Supported types: .txt, .md, .csv, .docx, .pdf,
    # Not supported: .json, .xlsx, .yaml
    ...

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

    file_dict = {}
    for file in files:
        with open(file) as f:
            content = f.read()
            filename = str(file).split("/")[-1].replace(".","_")
            file_dict[filename] = content

    return file_dict