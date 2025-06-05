from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os

app = FastAPI()

API_KEY = os.getenv("GEMINI_API_KEY")
GENAI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + API_KEY

class Query(BaseModel):
    message: str

@app.post("/chat")
async def chat(query: Query):
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": query.message}
                ]
            }
        ]
    }
    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(GENAI_ENDPOINT, json=payload, headers=headers)
    data = response.json()

    try:
        text_reply = data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        text_reply = "Xin lỗi, đã có lỗi xảy ra."

    return {"reply": text_reply}
