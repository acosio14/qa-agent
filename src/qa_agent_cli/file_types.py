from pydantic.dataclasses import dataclass

@dataclass
class FileType:
    name: str
    extension: str
    content: str