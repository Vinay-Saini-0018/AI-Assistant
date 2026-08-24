from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langgraph.graph.message import add_messages
from langchain.messages import HumanMessage,AIMessage
from config import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage, SystemMessage

from pydantic import BaseModel, Field
from typing import List
import uuid



# classes for structured output
class MemoryItem(BaseModel):
    text : str = Field(description = "Atomic user memory.")
    is_new : bool = Field(description = "True if new, False if duplicate")

class MemoryDecision(BaseModel):
    should_write : bool
    memories : List[MemoryItem] = Field(default_factory=list)



# Langgraph state
class graphstate(TypedDict):
    messages : Annotated[list,add_messages]
    summary : str

# ----------------------------------------

model = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY
)

model2 = ChatGoogleGenerativeAI(
    model=settings.ChatModel,
    api_key=settings.GEMINI_API_KEY,
    temperature = 0
)

memory_model = model2.with_structured_output(MemoryDecision)


# --------------------------------------------------


SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant with memory capabilities.
If user-specific memory is available, use it to personalize 
your responses based on what you know about the user.

Your goal is to provide relevant, friendly, and tailored 
assistance that reflects the user’s preferences, context, and past interactions.

If the user’s name or relevant personal context is available, always personalize your responses by:
    – Always Address the user by name (e.g., "Sure, Nitish...") when appropriate
    – Referencing known projects, tools, or preferences (e.g., "your MCP server python based project")
    – Adjusting the tone to feel friendly, natural, and directly aimed at the user

Avoid generic phrasing when personalization is possible.

Use personalization especially in:
    – Greetings and transitions
    – Help or guidance tailored to tools and frameworks the user uses
    – Follow-up messages that continue from past context

Always ensure that personalization is based only on known user details and not assumed.

In the end suggest 3 relevant further questions based on the current response and user profile

The user’s memory (which may be empty) is provided as: {user_details_content}
"""



# ---------- Node 2 ----------
def ChatNode(state : graphstate, config : RunnableConfig, store : BaseStore):

    user_id = config['configurable']['user_id']
    ns = ('user',user_id,'details')

    items = store.search(ns)
    if items:
        user_details = "\n".join(item.value.get('data','') for item in items)
    else:
        user_details = ' '

    last_msgs = state['messages']
    summary = state.get('summary','')

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_details_content=user_details)

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


MEMORY_PROMPT = """You are responsible for updating and maintaining accurate user memory.

CURRENT USER DETAILS (existing memories):
{user_details_content}

TASK:
- Review the user's latest message.
- Extract user-specific info worth storing long-term (identity, stable preferences, ongoing projects/goals).
- For each extracted item, set is_new=true ONLY if it adds NEW information compared to CURRENT USER DETAILS.
- If it is basically the same meaning as something already present, set is_new=false.
- Keep each memory as a short atomic sentence.
- No speculation; only facts stated by the user.
- If there is nothing memory-worthy, return should_write=false and an empty list.
"""
    
# ------------ Node 3 -------------
def Store_LTM(state : graphstate, config = RunnableConfig, store = BaseStore):
    user_id = config['configurable']['user_id']
    ns = ('user',user_id, 'details')

    # getting the Long term memory
    items = store.search(ns)
    if items:
        existing = "\n".join(item.value.get('data','') for item in items)
    else:
        existing = " "

    last_msg = state['messages'][-1].content

    # checking for the last msg we have to store or not.. Here we use MemoryDecision structure 
    decision : MemoryDecision = memory_model.invoke(
        [SystemMessage(content=MEMORY_PROMPT.format(user_details_content=existing)),
         {'role':'user','content': last_msg}]
    )

    if decision.should_write:
        for mem in decision.memories:
            if mem.is_new and mem.text.strip():
                store.put(ns, str(uuid.uuid4()),{'data':mem.text.strip()})

    return {}





# ------- Constructing graph ---------

builder = StateGraph(graphstate)
builder.add_node('ChatNode',ChatNode)
builder.add_node('LTM',Store_LTM)
builder.add_node('SummaryNode',summarize_chat)

builder.add_edge(START,'SummaryNode')
builder.add_edge('SummaryNode','LTM')
builder.add_edge('LTM','ChatNode')
builder.add_edge('ChatNode',END)


with PostgresSaver.from_conn_string(settings.DATABASE_URL) as checkpointer:
    checkpointer.setup()

    with PostgresStore.from_conn_string(settings.DATABASE_URL) as store:
        store.setup()



        graph = builder.compile(checkpointer = checkpointer,store = store)

        config = {'configurable' : {'thread_id' : 'main','user_id' : 'u1'}}

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


                # Getting Long term Memory
                namespace = ("user",config["configurable"]["user_id"],"details")   # path of stored memory 

                memories = store.search(namespace)   # searching in that stored path

                print("\n\nLong-Term Memories:")

                for memory in memories:
                    print("-", memory.value.get("data", ""))


                break

            # testing
            data = {"messages" : [HumanMessage(content = query)]}

            # this will run in all cases : if a chunk is empty because he not get data yet, at that time this will not throw the error
            for chunk in graph.stream(data, stream_mode="custom", config = config):
                if chunk and chunk[0].get('text'):
                    print(chunk[0]['text'], end="", flush=True)
