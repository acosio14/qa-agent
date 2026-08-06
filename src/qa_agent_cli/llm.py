from openrouter import OpenRouter
import os
from dotenv import load_dotenv

load_dotenv() # does this need to cached?

class QAAssistant:
    def __init__(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
    ) -> None:
        
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.model: str = model

    def GetAnswer(self) -> str:

        with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as open_router:
            response = open_router.chat.send(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt}, 
                    {"role": "user", "content": self.user_prompt},
                ]
            )

            return response.choices[0].message.content
