from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import os
from googleapiclient.discovery import build

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
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.getenv("GOOGLE_SEARCH_CX")

if not API_KEY:
    print("❌ Chưa cấu hình biến môi trường GEMINI_API_KEY")

# ✅ Cấu hình SDK Gemini
genai.configure(api_key=API_KEY)

# ✅ Khởi tạo model Gemini 2.5 Flash Preview
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# ✅ Hàm gọi Google Search
def search_sources(query):
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return []
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        res = service.cse().list(q=query, cx=GOOGLE_SEARCH_CX, num=3).execute()
        results = res.get("items", [])
        return [
            {
                "url": item.get("link"),
                "title": item.get("title"),
                "description": item.get("snippet")
            }
            for item in results
        ]
    except Exception as e:
        print("❌ Lỗi Google Search:", e)
        return []

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

        sources = search_sources(query.prompt)

        return {
            "answer": response.text,
            "sources": sources
        }

    except Exception as e:
        print("❌ Lỗi khi gọi Gemini API:", e)
        return {
            "answer": "Xin lỗi, đã có lỗi xảy ra.",
            "sources": []
        }