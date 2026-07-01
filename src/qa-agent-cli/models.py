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

class SystemPrompt(BaseModel):
    text: str = (
            "You are a helpful and articulate Q&A assistant. "
            "You take in one or multiple files, notes, and/or documents. "
            "You only answer questions based on the files provided. "
            "If you can't find and source the documents, you politely "
            "tell user 'I don't know', 'Answer not in docs', etc. "
            "When giving an answer always look for the information in the "
            "files and try to give a citation or explicity location/source of "
            "answer in a file, document, and/or note."
        )