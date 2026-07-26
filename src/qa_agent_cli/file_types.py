from pydantic.dataclasses import dataclass, Field

@dataclass
class Chunk:
    text: str
    line_num: int | None = None
    page: int | None = None
    section: str | None = None


@dataclass
class ParsedFile:
    name: str
    extension: str
    raw_text: str = ""
    chunks: list[Chunk] = Field(default_factory=list)