import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_model = None


def get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel("gemini-flash-latest")
    return _model


def generate_text(prompt: str) -> str:
    return get_model().generate_content(prompt).text


generate_email = generate_text
