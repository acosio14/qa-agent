from openrouter import OpenRouter
import os
from dotenv import load_dotenv

load_dotenv() # does this need to cached?

class QAAssistant:
    def __init__(
        self,
        files: str,
        question: str,
        model: str,
    ) -> None:
        
        self.system_prompt: str = (
            "You are a helpful and articulate Q&A assistant. "
            "You take in one or multiple files. "
            "You only answer questions based on the files provided. "
            "If you can't find and source the documents, you politely "
            "tell user 'I don't know', 'Answer not in docs', etc. "
            "When giving an answer, always look for the information in the "
            "files and attempt to give a citation or explicit location/source of "
            "answer in a given file."
        )
        self.files: str = files
        self.question: str = question
        self.model: str = model

    def GetAnswer(self) -> str:
        question_prompt = (
            f"You are using the llm in parentheses ({self.model}). "
            f"You are given the files inside the brackets [{self.files}]. "
            f"Concisely answer the question inside the triple ticks ```{self.question}```. "
            f"The response should be less than or equal to 2 to 3 sentences. "
            f"The response should be formatted in the following way: "
            f"Answer: <RESPONSE HERE>.\n"
            f"Model: <MODEL HERE>\n"
        )
        with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as open_router:
            response = open_router.chat.send(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt}, 
                    {"role": "user", "content": question_prompt},
                ]
            )

            return response.choices[0].message.content
