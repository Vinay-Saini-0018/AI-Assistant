from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from config import settings
from core.tools.GNews import get_news
from core.tools.web_search import web_search
from core.tools.wikipedia import wikipedia_search

# schemas for structured output
class MemoryItem(BaseModel):
    text : str = Field(description = "Atomic user memory.")
    is_new : bool = Field(description = "True if new, False if duplicate")

class MemoryDecision(BaseModel):
    should_write : bool
    memories : List[MemoryItem] = Field(default_factory=list)


tools = [get_news,web_search,wikipedia_search]

### ----------- Normal Chat Model ---------- ###

model = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY
)

### ---------- Tool Model (Use in ChatNode) ------------- ###

ToolModel = model.bind_tools(tools)


### ---------- Memory Model -------------- ###

model2 = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY,
)

memory_model = model2.with_structured_output(MemoryDecision)