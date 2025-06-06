from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# ✅ Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Mô hình dữ liệu gửi từ frontend
class Query(BaseModel):
    prompt: str

# ✅ Endpoint Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
GENAI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + API_KEY
)

# ✅ Endpoint đúng frontend gọi
@app.post("/api/chat")
async def chat(query: Query):
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": query.prompt}
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
    except Exception as e:
        print("Lỗi gọi Gemini:", e)
        text_reply = "Xin lỗi, đã có lỗi xảy ra."

    return {
        "answer": text_reply,
        "sources": []  # Nếu cần, có thể sinh sources thật ở đây
    }