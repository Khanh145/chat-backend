from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
import os
import requests

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class Query(BaseModel):
    prompt: str

# Load environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Configure Gemini SDK
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

def google_search(query: str, num_results: int = 3) -> List[str]:
    """Thực hiện Google Search và trả về danh sách snippet"""
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query
    }

    try:
        response = requests.get(search_url, params=params)
        results = response.json().get("items", [])[:num_results]
        snippets = [f"{item.get('title')}: {item.get('snippet')}" for item in results]
        return snippets

    except Exception as e:
        print("❌ Lỗi khi tìm kiếm Google:", e)
        return []

@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Prompt từ frontend:", query.prompt)

    if not GEMINI_API_KEY or not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return {"answer": "Thiếu cấu hình API key.", "sources": []}

    try:
        # 1. Google Search
        snippets = google_search(query.prompt)
        context = "\n".join([f"- {s}" for s in snippets])

        # 2. Tạo prompt hoàn chỉnh
        full_prompt = f"""Dưới đây là một số thông tin tìm kiếm liên quan, bạn hãy dùng chúng để trả lời thật chính xác, cập nhật:

Thông tin:
{context}

Câu hỏi: {query.prompt}
Trả lời:"""

        # 3. Gửi tới Gemini
        response = model.generate_content(full_prompt)
        print("📥 Phản hồi Gemini:", response.text)

        return {
            "answer": response.text,
            "sources": snippets  # Trả về luôn danh sách snippet
        }

    except Exception as e:
        print("❌ Lỗi hệ thống:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }