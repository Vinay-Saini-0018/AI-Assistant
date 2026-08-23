from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langgraph.graph.message import add_messages
from langchain.messages import HumanMessage,AIMessage
from config import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import RemoveMessage, SystemMessage


model = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY
)

class graphstate(TypedDict):
    messages : Annotated[list,add_messages]
    summary : str


# ---------- Node 2 ----------
def ChatNode(state : graphstate):

    last_msgs = state['messages']
    summary = state.get('summary','')

    system_prompt = "You are helpful ai assistant"

    if summary:
        system_prompt += f" Conversation Summary : {summary}"

    # final query that is asked to model
    query = [SystemMessage(content = system_prompt )] + last_msgs

    writer = get_stream_writer()   # to send chunks outside the node

    final_result = ""

    # Streaming
    for chunk in model.stream(query):
        chunk = chunk.content
        writer(chunk)
        if chunk and chunk[0].get('text'):
            final_result += chunk[0]['text']

    return {"messages": AIMessage(content = final_result)}


# -------------- Node 1 --------------------
def summarize_chat(state = graphstate):
    messages = state['messages']

    if len(messages) < 10:
        return {}

    # old messages
    old_messages = messages[:-4]

    # latest 4 messages
    recent_messages = messages[-4:]

    summary = state.get('summary', "")
    if summary:
        prompt = f"""Current summary:{summary}
        Extend the summary using these new messages:{old_messages}
        """
    else:
        prompt = f"Summarize this conversation:{old_messages}"

    respone = model.invoke(prompt)

    # deleting old messages 
    delete_old = [RemoveMessage(id=message.id) for message in old_messages]

    return {
        'messages' : delete_old,
        'summary' : respone.content
    }

    




# ------- Constructing graph ---------

builder = StateGraph(graphstate)
builder.add_node('ChatNode',ChatNode)
builder.add_node('SummaryNode',summarize_chat)

builder.add_edge(START,'SummaryNode')
builder.add_edge('SummaryNode','ChatNode')
builder.add_edge('ChatNode',END)


with PostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer = checkpointer)

    config = {'configurable' : {'thread_id' : 'main'}}

    while True:
        query = input("\nquery : ")

        if query == "0":
            snapshot = graph.get_state(config)

            summary = snapshot.values.get("summary", "")
            messages = snapshot.values.get("messages", [])

            print("\n\nComplete Conversation:")
            print("Summary:", summary)

            for message in messages:
                print(message.type, ":", message.content)

            break

        # testing
        data = {"messages" : [HumanMessage(content = query)]}

        # this will run in all cases : if a chunk is empty because he not get data yet, at that time this will not throw the error
        for chunk in graph.stream(data, stream_mode="custom", config = config):
            if chunk and chunk[0].get('text'):
                print(chunk[0]['text'], end="", flush=True)
