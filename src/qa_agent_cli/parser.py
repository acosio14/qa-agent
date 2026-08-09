# Parses the terminal inputs
# Extractor - get the meaningful content out of the file.
# Read bytes, detect type, decode or convert.
# Hand back clean structured content

from pathlib import Path
import logging
from .file_types import ParsedFile, Chunk
from markitdown import MarkItDown

CHUNK_SIZE_THRESHOLD_BYTES = 2048
SUPPORTED_FILE_TYPES = {".txt", ".docx", ".pdf", ".md"}

def convert_to_markdown(filepath):
    md = MarkItDown(enable_plugins=False)
    md_text = md.convert(filepath)
    return md_text

def chunk_file_content(filename: str, md_text: str):

    md_lines = md_text.split("\n")
    has_header = any(line.strip().startswith('#') for line in md_lines)

    if has_header:
        section_idx = [
            idx
            for idx, line in enumerate(md_lines)
            if line.strip().startswith('#')
        ]
        section_idx.append(len(md_lines))

        chunks = []
        # Content before the first header would otherwise be dropped.
        if section_idx[0] > 0:
            chunks.append(
                Chunk(filename=filename, text=('\n').join(md_lines[:section_idx[0]]))
            )

        for start, end in zip(section_idx, section_idx[1:]):
            chunks.append(
                Chunk(
                    filename=filename,
                    text=('\n').join(md_lines[start:end]),
                    section=md_lines[start].strip(),
                )
            )
    else:
        blank_idx = {
            idx
            for idx, line in enumerate(md_lines)
            if line.strip() == ''
        }

        chunks = []
        line_list = []
        for idx, line in enumerate(md_lines):
            if idx not in blank_idx:
                line_list.append(line)
            elif line_list:
                chunks.append(Chunk(
                    filename=filename,
                    text=('\n').join(line_list)),
                )
                line_list = []
        if line_list:
            chunks.append(Chunk(
                filename=filename,
                text=('\n').join(line_list)),
            )

    return chunks


def create_file_type_dataclass(filepath: str | Path) -> ParsedFile:
    filepath = Path(filepath)
    file_extension = filepath.suffix
    filename = filepath.stem
    try:
        # Verify if file type supported (Wrong type guardrail)
        if file_extension.lower() not in SUPPORTED_FILE_TYPES:
            raise TypeError(f"Don't support file extension: {file_extension}")
        if filepath.stat().st_size <= 0:
            raise ValueError(f"File is empty.")

        md_text = convert_to_markdown(filepath).text_content
        chunks = [Chunk(filename=filename, text=md_text)]
        if filepath.stat().st_size > CHUNK_SIZE_THRESHOLD_BYTES:
            chunks = chunk_file_content(filename, md_text)

        return ParsedFile(filename, file_extension, md_text, chunks)
    except Exception as e:
        # Record the failure on the file instead of raising: one bad file
        # must not abort a whole batch, and it must not vanish silently.
        logging.exception(f"The file {filepath} failed with exception {e}")
        return ParsedFile(
            name=filename,
            extension=file_extension,
            ok=False,
            error=str(e),
        )

def parse(filepath: str | Path) -> list[ParsedFile]:
    # Need to verify if its a directory or file
    # if directory, then loop through each file and make dict of each
    # (Not file or directory guardrail)
    path = Path(filepath)
    if path.is_file():
        files = [path] # should be a file
    elif path.is_dir():
        # Skip incidental noise (hidden/system files, subdirectories) so it is
        # not mistaken for a parse failure and does not clutter the results.
        files = [
            file
            for file in path.iterdir()
            if file.is_file()
            and file.suffix.lower() in SUPPORTED_FILE_TYPES
            and not file.name.startswith(".")
        ]
    else:
        logging.error('File path cannot be read as file or dir')
        raise FileNotFoundError

    return [create_file_type_dataclass(file) for file in files]