from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import google.generativeai as genai
import os
import requests
from datetime import datetime

app = FastAPI()

# CORS cho frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://academic-chat-refine.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model dữ liệu đầu vào
class Query(BaseModel):
    prompt: str

# API Key từ môi trường
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

# Cấu hình Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# 👉 Hàm tối ưu prompt tìm kiếm
def refine_query(prompt: str) -> str:
    prompt = prompt.strip()
    today = datetime.now().strftime("%B %Y")  # ví dụ: "June 2025"
    if "?" not in prompt:
        prompt += "?"
    if "hiện tại" not in prompt.lower() and "mới nhất" not in prompt.lower():
        prompt += f" (thông tin mới nhất {today})"
    return prompt

# 👉 Hàm tìm kiếm Google
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
        print("❌ Google Search error:", e)
        return []

@app.post("/api/chat")
async def chat(query: Query):
    print("📨 Prompt người dùng:", query.prompt)

    if not GEMINI_API_KEY or not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return {"answer": "Thiếu cấu hình API key.", "sources": []}

    # ✅ Trả lời nhanh nếu chỉ hỏi ngày
    if any(x in query.prompt.lower() for x in ["hôm nay là ngày", "ngày bao nhiêu", "today"]):
        today = datetime.now().strftime("Hôm nay là %A, ngày %d tháng %m năm %Y.")
        return {"answer": today, "sources": []}

    try:
        # ✅ Cải thiện câu hỏi để tìm kiếm hiệu quả hơn
        search_query = refine_query(query.prompt)

        # 🔍 Tìm kiếm Google real-time
        snippets = google_search(search_query)
        if not snippets:
            return {
                "answer": "Hiện tại không tìm thấy thông tin mới nào liên quan đến câu hỏi của bạn.",
                "sources": []
            }

        # ✅ Tạo prompt chuẩn gửi đến Gemini
        today_str = datetime.now().strftime("%d/%m/%Y")
        context = "\n".join([f"- {s}" for s in snippets])
        full_prompt = f"""
Bạn là một trợ lý AI chính xác và đáng tin cậy.
Dưới đây là thông tin được tìm kiếm từ Google (cập nhật ngày {today_str}).

Chỉ sử dụng thông tin này để trả lời. Nếu không đủ dữ kiện, hãy trả lời rằng chưa có dữ liệu phù hợp.

Thông tin:
{context}

Câu hỏi người dùng: {query.prompt}

Trả lời:
"""

        # 🤖 Gửi tới Gemini
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
