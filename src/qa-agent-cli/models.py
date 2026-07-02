from pathlib import Path
from pydantic import BaseModel
from enum import Enum

class Document(BaseModel):
    path: Path

class UserQuestion(BaseModel):
    text: str

class AgentResponse(BaseModel):
    text: str

class Model(str, Enum):
    GEMMA_4_31B = "google/gemma-4-31b-it:free"
    MINSTRAL_7B = "minstralai/mistral-7b-instruct:free"
    #add other free models