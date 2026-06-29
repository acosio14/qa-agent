from openrouter import OpenRouter
import os
from dotenv import load_dotenv

load_dotenv() # does this need to cached?

class QAAssistant:
    def __init__(self,  user_question: str, model: str = "google/gemma-4-31b-it:free") -> None:
        self.system_prompt: str = (
            "You are a helpful and articulate Q&A assistant."
            "You take in one or multiple files, notes, and/or documents."
            "You only answer questions based on the files provided." \
            "If you can't find and source the documents, you politely" \
            "tell user 'I don't know', 'Answer not in docs', etc." \
            "When giving an answer always look for the information in the" \
            "files and try to give a citation or explicity location/source of" \
            "answer in a file, document, and/or note."
        )
        self.question_prompt: str = user_question
        self.model: str = model

    def GetAnswer(self) -> str:
        with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as open_router:
            response = open_router.chat.send(
                model=self.mo,
                messages=[
                    {"role": "system", "content": self.system_prompt}, 
                    {"role": "user", "content": self.question_prompt} #To-Do: Needs to include context of docs/files/notes
                ]
            )

            return response.choices[0].message.content
