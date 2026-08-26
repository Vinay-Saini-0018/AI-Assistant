from typing import TypedDict,Annotated
from langgraph.graph.message import add_messages

# Langgraph state
class graphstate(TypedDict):
    messages : Annotated[list,add_messages]
    summary : str