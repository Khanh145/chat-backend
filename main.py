from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
import os
import requests
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dữ liệu từ frontend
class Query(BaseModel):
    prompt: str

# Load biến môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# Hàm tìm kiếm real-time
def google_search(query: str, num_results: int = 5) -> List[str]:
    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": GOOGLE_SEARCH_CX,
        "q": query,
        "num": num_results
    }

    try:
        response = requests.get(search_url, params=params)
        items = response.json().get("items", [])[:num_results]
        snippets = [f"{item.get('title')}: {item.get('snippet')}" for item in items]
        return snippets
    except Exception as e:
        print("❌ Lỗi Google Search:", e)
        return []

@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Prompt người dùng:", query.prompt)

    if not GEMINI_API_KEY or not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return {"answer": "Thiếu cấu hình API key.", "sources": []}

    # ✅ Trả lời nhanh nếu người dùng hỏi ngày hôm nay
    if any(x in query.prompt.lower() for x in ["hôm nay là ngày", "ngày bao nhiêu", "today"]):
        today = datetime.now().strftime("Hôm nay là %A, ngày %d tháng %m năm %Y.")
        return {"answer": today, "sources": []}

    try:
        # 🔍 Google Search real-time
        snippets = google_search(query.prompt)
        if not snippets:
            return {
                "answer": "Hiện tại không tìm thấy thông tin mới nào liên quan đến câu hỏi của bạn.",
                "sources": []
            }

        context = "\n".join([f"- {s}" for s in snippets])
        today = datetime.now().strftime("%d/%m/%Y")

        # ✅ Prompt cập nhật rõ ràng + thời gian
        full_prompt = f"""
Bạn là một trợ lý AI chính xác và đáng tin cậy. Dưới đây là những thông tin mới nhất từ Google Search (cập nhật ngày {today}).
Chỉ sử dụng thông tin bên dưới để trả lời. Nếu không có đủ dữ kiện, hãy trả lời "Tôi không tìm thấy thông tin liên quan."

Thông tin mới nhất:
{context}

Câu hỏi: {query.prompt}

Trả lời ngắn gọn và đúng sự thật:
"""

        # 🤖 Gửi đến Gemini
        response = model.generate_content(full_prompt)
        print("📥 Gemini trả về:", response.text)

        return {
            "answer": response.text.strip(),
            "sources": snippets
        }

    except Exception as e:
        print("❌ Lỗi xử lý:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }