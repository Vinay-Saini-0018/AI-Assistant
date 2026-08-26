

from core.models import model,memory_model
from core.state import graphstate
from langgraph.store.base import BaseStore
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage, SystemMessage
import uuid
from core import prompts
from core.models import MemoryDecision
from langgraph.config import get_stream_writer
from langchain.messages import AIMessage




### -------------- Node 1 (SummareNode) -------------- ###

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

    # checking for the last msg we have to store or not.. Here we use MemoryDecision structure 
    decision : MemoryDecision = memory_model.invoke(
        [SystemMessage(content = prompts.MEMORY_PROMPT.format(user_details_content=existing)),
         {'role':'user','content': last_msg}]
    )

    if decision.should_write:
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

    # Streaming
    for chunk in model.stream(query):
        chunk = chunk.content
        writer(chunk)
        if chunk and chunk[0].get('text'):
            final_result += chunk[0]['text']

    return {"messages": AIMessage(content = final_result)}