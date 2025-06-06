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

class Query(BaseModel):
    prompt: str

# Load keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

def google_search(query: str, num_results: int = 5) -> List[str]:
    """Tìm kiếm Google và trả về các snippet có liên quan"""
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

    # ✅ Nếu là câu hỏi về ngày hiện tại
    if any(x in query.prompt.lower() for x in ["hôm nay là ngày", "ngày bao nhiêu", "today"]):
        today = datetime.now().strftime("Hôm nay là %A, ngày %d tháng %m năm %Y.")
        return {"answer": today, "sources": []}

    try:
        # Tìm kiếm real-time
        snippets = google_search(query.prompt)
        context = "\n".join([f"- {s}" for s in snippets])

        # Prompt định hướng dùng dữ kiện mới
        full_prompt = f"""
Bạn là một trợ lý AI đáng tin cậy. Dưới đây là những dữ liệu tìm kiếm mới nhất từ Google.
Hãy trả lời người dùng chỉ dựa vào thông tin này, không phỏng đoán nếu không có dữ kiện rõ ràng.

Thông tin mới nhất:
{context}

Câu hỏi người dùng: {query.prompt}
Trả lời:
"""

        response = model.generate_content(full_prompt)
        print("📥 Gemini trả về:", response.text)

        return {
            "answer": response.text,
            "sources": snippets
        }

    except Exception as e:
        print("❌ Lỗi xử lý:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }