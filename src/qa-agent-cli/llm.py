from openrouter import OpenRouter
import os
from dotenv import load_dotenv

load_dotenv() # does this need to cached?

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as open_router:
    response = open_router.chat.send(
        model="google/gemma-4-31b-it:free",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )

    print(response.choices[0].message.content)
