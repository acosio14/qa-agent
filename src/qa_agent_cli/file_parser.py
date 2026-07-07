# Parses the terminal inputs (takes and structures it to correct format)
from pathlib import Path
import logging

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