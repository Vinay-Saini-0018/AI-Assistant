How i work on this project
 
s1 : created  requirements.txt,settings.py, .env, files  then TTS.py file for text and speech

s2 : * created chat.py file in this 1st create simple graph then add streaming in that.
     *  converted state in messages state and added Message type 
     * addition of short term memory and persistance functionalities complete on 23-08-2026
     * Adding Long term memeory  -> creating a node which will store the memory for this. And  we need two classes for the structured output (memoryitem and memory decision)  memory decision checks we have to extract memory from this query or not .   memoryitem checks this is already in memory or not.

     Also make that model with structuerd output (Memorydecision)





          node and memory 



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
        existing = "\n".join(item.get.value('data','') for item in items)
    else:
        existing = " "

    last_msg = state[messages][-1].content

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


s3 : Changing in ChatNode so that it can get LTM and after that tell the answer
      * In chatnode we get the LTM and convert this into System messages ( LTM + conversation summary)
      * looks like this : system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_details_content=user_details)    ---> user_details = LTM and SystemPrompt_template contains who are you and how to use LTM memory


s4 : What to do while starting the graph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore


# Same PostgreSQL database
DATABASE_URL = settings.DATABASE_URL


with PostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:

    # STM tables
    checkpointer.setup()

    # LTM store — same PostgreSQL database
    with PostgresStore.from_conn_string(DATABASE_URL) as store:

        # LTM tables
        store.setup()

        # Graph uses both
        graph = builder.compile(
            checkpointer=checkpointer,   # Short-Term Memory
            store=store                   # Long-Term Memory
        )

        config = {
            "configurable": {
                "thread_id": "main",     # STM conversation
                "user_id": "u1"           # LTM user
            }
        }

        while True:

            query = input("\nquery : ")

            if query == "0":

                snapshot = graph.get_state(config)

                summary = snapshot.values.get("summary", "")
                messages = snapshot.values.get("messages", [])

                print("\n\nComplete Conversation:")
                print("Summary:", summary)

                for message in messages:
                    print(
                        message.type,
                        ":",
                        message.content
                    )

               # Getting Long term Memory
                namespace = ("user",config["configurable"]["user_id"],"details")   # path of stored memory 

                memories = store.search(namespace)   # searching in that stored path

                print("\n\nLong-Term Memories:")

                for memory in memories:
                    print("-", memory.value.get("data", ""))

                break

            data = {
                "messages": [
                    HumanMessage(content=query)
                ]
            }

            for chunk in graph.stream(
                data,
                stream_mode="custom",
                config=config
            ):

                if chunk and chunk[0].get("text"):
                    print(
                        chunk[0]["text"],
                        end="",
                        flush=True
                    )

s5 : connect the node and edges in the graph