from langgraph.graph import StateGraph,START,END
from langchain.messages import HumanMessage,AIMessage
from config import settings
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from core.state import graphstate

from core.nodes import ChatNode,Store_LTM,summarize_chat




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
