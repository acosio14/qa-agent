from openrouter import OpenRouter
import openrouter.errors as errors
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
            try:
                response = open_router.chat.send(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.system_prompt}, 
                        {"role": "user", "content": self.user_prompt},
                    ]
                )

                return response.choices[0].message.content
            except errors.TooManyRequestsResponseError as e:
                print("status:", getattr(e, "status_code", None))
                print("body:", getattr(e, "body", None))
                print("message:", getattr(e, "message", None))
                print("raw:", getattr(e, "raw_response", None))
                print("dir:", [a for a in dir(e) if not a.startswith("_")])