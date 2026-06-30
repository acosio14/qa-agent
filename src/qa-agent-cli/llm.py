from openrouter import OpenRouter
import os
from dotenv import load_dotenv
from models import Model, SystemPrompt, UserQuestion

load_dotenv() # does this need to cached?

class QAAssistant:
    def __init__(
        self,
        user_question: UserQuestion,
        system_prompt: SystemPrompt = SystemPrompt.text,
        model: Model = Model.GEMMA_4_31B
    ) -> None:
        
        self.system_prompt: SystemPrompt = system_prompt
        self.question_prompt: UserQuestion = user_question
        self.model: Model = model

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
