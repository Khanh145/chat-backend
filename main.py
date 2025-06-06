from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

# ✅ CORS cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Mô hình dữ liệu từ frontend
class Query(BaseModel):
    prompt: str

# ✅ Lấy API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ Chưa cấu hình biến môi trường GEMINI_API_KEY")

# ✅ Cấu hình SDK Gemini
genai.configure(api_key=API_KEY)

# ✅ Khởi tạo model Gemini 2.5 Flash Preview
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Prompt nhận được từ người dùng:", query.prompt)

    if not API_KEY:
        return {
            "answer": "Không tìm thấy API key. Vui lòng cấu hình lại.",
            "sources": []
        }

    try:
        response = model.generate_content(query.prompt)
        print("📥 Phản hồi từ Gemini:", response.text)

        return {
            "answer": response.text,
            "sources": []  # Có thể cập nhật sau
        }

    except Exception as e:
        print("❌ Lỗi khi gọi Gemini API:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }