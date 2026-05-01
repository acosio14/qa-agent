# Document/Notes dataclass, shared types
from pydantic.dataclasses import dataclass
from pathlib import Path

@dataclass
class Section:
    source_path: Path
    heading: str
    heading_path: list[str]
    content: str
