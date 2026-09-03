

from core.models import ToolModel,memory_model,model
from core.state import graphstate
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, RemoveMessage, SystemMessage,HumanMessage,ToolMessage
import uuid
from core import prompts
from core.models import MemoryDecision
from langgraph.config import get_stream_writer
from langgraph.prebuilt import ToolNode
from core.models import tools



### -------------- Node 1 (SummareNode) -------------- ###

def summarize_chat(state = graphstate):
    messages = state['messages']

    if len(messages) < 10:
        return {}

    # Find the latest user message
    latest_user_index = max(
        index
        for index, message in enumerate(messages)
        if isinstance(message, HumanMessage)
    )

    # Only summarize messages before the latest user message
    old_messages = messages[:latest_user_index]

    if not old_messages:
        return {}


    summary = state.get('summary', "")
    if summary:
        prompt = f"""Current summary:{summary}
        Extend the summary using these new messages:{old_messages}
        """
    else:
        prompt = f"Summarize this conversation:{old_messages}"

    respone = model.invoke(prompt)

    # deleting old messages 
    delete_old = [RemoveMessage(id=message.id) for message in old_messages if getattr(message, 'id', None)]

    return {
        'messages' : delete_old,
        'summary' : respone.content
    } 



### ------------ Node 2 (LTM Node) ------------- ###

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
    if isinstance(last_msg, list):
        last_msg = " ".join(part.get("text", "") for part in last_msg if isinstance(part, dict))

    # checking for the last msg we have to store or not.. Here we use MemoryDecision structure 
    decision : MemoryDecision = memory_model.invoke(
        [SystemMessage(content = prompts.MEMORY_PROMPT.format(user_details_content=existing)),
         HumanMessage(content = str(last_msg))]
    )

    if decision and decision.should_write:
        for mem in decision.memories:
            if mem.is_new and mem.text.strip():
                store.put(ns, str(uuid.uuid4()),{'data':mem.text.strip()})

    return {}




###  ---------- Node 3 (ChatNode) ----------- ###

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

    system_prompt = prompts.SYSTEM_PROMPT_TEMPLATE.format(user_details_content=user_details)

    if summary:
        system_prompt += f" Conversation Summary : {summary}"

    # final query that is asked to model
    query = [SystemMessage(content = system_prompt )] + last_msgs

    writer = get_stream_writer()   # to send chunks outside the node

    final_result = ""

    full_response = None


    # Streaming
    for chunk in ToolModel.stream(query):
        full_response = chunk if full_response is None else full_response + chunk

        chunk = chunk.content
        if isinstance(chunk, list):
            text = "".join(
                    part.get("text", "")
                    for part in chunk
                    if isinstance(part, dict)
                )
        elif isinstance(chunk, str):
            text = chunk
        else:
            text = ""

        if text:
            writer(text)
            final_result += text

        

    if full_response is None:
        return {"messages": [AIMessage(content=final_result)]}

    return {
        "messages": [full_response]
    }


### ----------- Node 4 (Tool Node) ---------- ###
tool_node = ToolNode(tools)


### --------- Node 5 (ToolDecision) ---------- ###
def should_use_tool(state: graphstate) -> str:
    last_message = state["messages"][-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "use_tool"   # → go to tool_node
    
    return "end"  