# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from file_types import ParsedFile, Chunk
from markitdown import MarkItDown

FILE_SIZE_2_KILOBYTES = 2000

def convert_to_markdown(filepath):
    md = MarkItDown(enable_plugins=False)
    md_text = md.convert(filepath)
    return md_text

def chunk_file_content(md_text: str):

    md_lines = md_text.split("\n")
    has_header = False
    for line in md_lines:
        if len(line) > 0 and line[0] == '#' and '# ' in line:
            has_header = True

    if has_header:
        section_idx = [
            idx
            for idx, line in enumerate(md_lines)
            if '# ' in line
        ]
        chunks = [
            Chunk(
                text=('\n').join(md_lines[section_idx[i]:section_idx[i+1]]),
                section=md_lines[section_idx[i]],
            )
            for i, _ in enumerate(section_idx[:len(section_idx)-1])
        ]
    else:
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
                chunks.append(
                    Chunk(('\n').join(line_list))
                )
                line_list = []
            else:
                chunks.append(
                    Chunk(('\n').join(line_list))
                )

    return chunks


def create_file_type_dataclass(filepath: Path):
    
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem

    # Verify if file type supported
    supported_file_types = [".txt", ".docx", ".pdf", ".md"]
    if file_extension not in supported_file_types:
        TypeError(f"Don't support file extension: {file_extension}")

    md_text = convert_to_markdown(filepath).text_content
    chunks = [Chunk(md_text)]
    if Path(filepath).stat().st_size > FILE_SIZE_2_KILOBYTES:
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