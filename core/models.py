from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from config import settings


# schemas for structured output
class MemoryItem(BaseModel):
    text : str = Field(description = "Atomic user memory.")
    is_new : bool = Field(description = "True if new, False if duplicate")

class MemoryDecision(BaseModel):
    should_write : bool
    memories : List[MemoryItem] = Field(default_factory=list)



### ----------- Normal Chat Model ---------- ###

model = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY
)


### ---------- Memory Model -------------- ###

model2 = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY,
    temperature = 0
)

memory_model = model2.with_structured_output(MemoryDecision)