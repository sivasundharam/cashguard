import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def generate_text(prompt: str) -> str:
    response = get_client().models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    return response.text


generate_email = generate_text
