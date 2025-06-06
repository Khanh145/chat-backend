from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# ✅ Cấu hình CORS để cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Model dữ liệu nhận từ frontend
class Query(BaseModel):
    prompt: str

# ✅ Endpoint Gemini + API key
API_KEY = os.getenv("GEMINI_API_KEY")
GENAI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + API_KEY
)

# ✅ Endpoint xử lý chatbot
@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Prompt nhận được từ người dùng:", query.prompt)

    # Nếu chưa có key thì trả giả lập
    if not API_KEY:
        print("❌ Chưa cấu hình GEMINI_API_KEY trong biến môi trường.")
        return {
            "answer": "Không tìm thấy API key. Vui lòng cấu hình lại.",
            "sources": []
        }

    # Tạo payload gửi tới Gemini
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

    try:
        response = requests.post(GENAI_ENDPOINT, json=payload, headers=headers)
        print("📥 Phản hồi thô từ Gemini:", response.text)  # Log toàn bộ JSON trả về

        data = response.json()

        # Trích xuất câu trả lời
        text_reply = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "answer": text_reply,
            "sources": []  # Chưa có phân tích nguồn
        }

    except Exception as e:
        print("❌ Lỗi khi gọi Gemini API:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }