from pydantic.dataclasses import dataclass, field

@dataclass
class Chunk:
    text: str
    line_num: int | None = None
    page: int | None = None
    section: str | None = None


@dataclass
class Document:
    name: str
    extension: str
    raw_text: str = ""
    chunks: list[Chunk] = field(default_factory=list)