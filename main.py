from core.agent import chat,load_thread_history
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["null"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ==============================
# Request model
# ==============================

class ChatRequest(BaseModel):

    query: str
    thread_id: str


# ==============================
# Chat API
# ==============================

@app.post("/chat")
def chat_api(data: ChatRequest):

    try:
        result = chat(data.query, data.thread_id)

        return StreamingResponse(
            result,
            media_type="text/plain"
        )

    except Exception as e:
        print("CHAT ERROR:", repr(e))
        raise


# ==============================
# Load previous chat
# ==============================

@app.get("/chat/{thread_id}")
def load_chat_api(thread_id: str):

    return load_thread_history(thread_id)


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "frontend", html=True),
    name="frontend",
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)