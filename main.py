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

# ✅ Lấy API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")
GENAI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + API_KEY
)

@app.post("/api/chat")
async def chat(query: Query):
    print("Prompt nhận được:", query.prompt)

    # ✅ Nếu không có API_KEY → phản hồi mô phỏng
    if not API_KEY:
        print("⚠️ Không tìm thấy GEMINI_API_KEY. Trả về dữ liệu mô phỏng.")
        return {
            "answer": f"Đây là câu trả lời mô phỏng cho: '{query.prompt}'",
            "sources": [
                {
                    "url": "https://example.com/source1",
                    "title": "Nguồn 1",
                    "description": "Nguồn học thuật minh họa"
                },
                {
                    "url": "https://example.com/source2",
                    "title": "Nguồn 2",
                    "description": "Báo cáo nghiên cứu giả lập"
                }
            ]
        }

    # ✅ Gọi Gemini nếu có key
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
        print("Phản hồi thô từ Gemini:", response.text)
        data = response.json()
        text_reply = data["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "answer": text_reply,
            "sources": []  # Sau có thể sinh tự động nếu cần
        }

    except Exception as e:
        print("Lỗi gọi Gemini:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }