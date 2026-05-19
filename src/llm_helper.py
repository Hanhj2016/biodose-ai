import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please create a .env file in the project root."
        )
    return OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str, model: str | None = None) -> str:
    client = get_openai_client()
    selected_model = model or DEFAULT_MODEL

    response = client.responses.create(
        model=selected_model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.output_text
