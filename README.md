How i work on this project
 
s1 : created  requirements.txt,settings.py, .env, files  then TTS.py file for text and speech

s2 : * created chat.py file in this 1st create simple graph then add streaming in that.
     *  converted state in messages state and added Message type 
     * addition of short term memory and persistance functionalities complete on 23-08-2026
     * Adding Long term memeory  -> creating a node which will store the memory for this. And  we need two classes for the structured output (memoryitem and memory decision)  memory decision checks we have to extract memory from this query or not .   memoryitem checks this is already in memory or not.

     Also make that model with structuerd output (Memorydecisi)


s3 : Changing in ChatNode so that it can get LTM and after that tell the answer
      * In chatnode we get the LTM and convert this into System messages ( LTM + conversation summary)
      * looks like this : system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_details_content=user_details)    ---> user_details = LTM and SystemPrompt_template contains who are you and how to use LTM memory


s4 : What to do while starting the graph
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

s5 : connect the node and edges in the graph

s6 : If your database service shut down then then start that to go to the website 


How to run:
1. Run the backend where so that we can acces that apis
uvicorn main:app --reload --port 8001

Then you should have:
Frontend → http://localhost:8000
Backend  → http://127.0.0.1:8001