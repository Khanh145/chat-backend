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

# Dữ liệu frontend gửi lên
class Query(BaseModel):
    prompt: str

# API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# Tìm kiếm Google
def google_search(query: str, num_results: int = 5) -> List[str]:
    try:
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_CX,
            "q": query,
            "num": num_results
        }
        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        items = response.json().get("items", [])[:num_results]
        return [f"{item['title']}: {item['snippet']}" for item in items]
    except Exception as e:
        print("❌ Google Search Error:", e)
        return []

# Xử lý API chat
@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Câu hỏi:", query.prompt)

    if not GEMINI_API_KEY or not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return {"answer": "Chưa cấu hình API key.", "sources": []}

    try:
        # Bước 1: Hỏi Gemini có cần Google Search không
        check_prompt = f"""
Người dùng hỏi: "{query.prompt}"

Bạn hãy trả lời ngắn gọn "YES" nếu cần thêm thông tin Google để trả lời chính xác hơn.
Nếu có thể tự trả lời, hãy viết "NO".
Chỉ trả về YES hoặc NO.
"""
        need_search = model.generate_content(check_prompt).text.strip().upper()
        print("🤖 Có cần tìm kiếm không?", need_search)

        snippets = []
        final_prompt = ""

        # Bước 2: Nếu cần Google → tìm kiếm và gửi lại prompt kèm context
        if "YES" in need_search:
            snippets = google_search(query.prompt)
            context = "\n".join([f"- {s}" for s in snippets])
            today = datetime.now().strftime("%d/%m/%Y")
            final_prompt = f"""
Bạn là một trợ lý AI đáng tin cậy. Dưới đây là thông tin tìm kiếm mới nhất từ Google (cập nhật ngày {today}).

Chỉ dựa vào dữ kiện sau để trả lời:
{context}

Câu hỏi: {query.prompt}

Trả lời:
"""
        else:
            final_prompt = query.prompt

        # Bước 3: Gửi prompt chính thức đến Gemini
        answer = model.generate_content(final_prompt).text.strip()

        return {
            "answer": answer,
            "sources": snippets
        }

    except Exception as e:
        print("❌ Lỗi xử lý:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }
