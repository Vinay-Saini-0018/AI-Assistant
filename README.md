# AI Chatbot

A personal AI chatbot built with **LangGraph** that can remember conversations, store long-term user information, use external tools, summarize older conversations, and support voice interaction.

## Features

* **Short-term memory** using PostgreSQL and `PostgresSaver`
* **Long-term memory** using `PostgresStore`
* **Conversation summarization** for long chats
* **Tool calling** with:

  * Web Search — Tavily
  * News — GNews
  * Wikipedia
* **Streaming responses**
* **Speech-to-text** using Groq Whisper
* **Text-to-speech** using Edge TTS
* Modular architecture that can be connected to a frontend or API

## Architecture

```text
User
 │
 ▼
Summarization
 │
 ▼
Long-Term Memory
 │
 ▼
LLM
 │
 ├── Tool required ──► Tool ──► LLM
 │
 └── No tool ────────────────► Response
```

### Memory

The project uses two types of memory:

| Memory     | Purpose              | Storage         |
| ---------- | -------------------- | --------------- |
| Short-term | Current conversation | `PostgresSaver` |
| Long-term  | User information     | `PostgresStore` |

`thread_id` is used for individual conversations, while `user_id` connects long-term memory across conversations.

## Project Structure

```text
AI-Chatbot/
│
├── config/
│   └── settings.py
│
├── core/
│   ├── agent.py
│   ├── nodes.py
│   ├── models.py
│   ├── state.py
│   ├── prompts.py
│   └── tools/
│       ├── web_search.py
│       ├── gnews.py
│       └── wikipedia.py
│
├── VoiceText/
│   └── TTS.py
│
├── main.py
├── requirements.txt
└── README.md
```

## How I Built It

I developed the project step by step:

1. Created the basic **LangGraph** workflow.
2. Added **streaming responses**.
3. Added **short-term conversation memory**.
4. Added **long-term user memory**.
5. Connected long-term memory with the chat node.
6. Added **conversation summarization**.
7. Added external tools for web, news, and Wikipedia search.
8. Added speech-to-text and text-to-speech functionality.

## Setup

#### 1. Install dependencies

```bash
pip install -r requirements.txt
```

#### 2. Create `.env`

```env
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
DATABASE_URL=your_postgresql_url
GNEWS_API_KEY=your_key
TAVILY_API_KEY=your_key
```

#### 3. Run

```bash
python -m core.agent
```


## Tech Stack

**Python · LangGraph · LangChain · Gemini · PostgreSQL · Groq Whisper · Edge TTS · Tavily · GNews · Wikipedia**


## Current Status

The core chatbot is implemented with LangGraph, short-term and long-term memory, PostgreSQL persistence, tool calling, conversation summarization, and voice processing.

## Future Development

The existing core logic is designed to be extended without rewriting the main agent. Most of the future changes will be made in `main.py` and `core/agent.py` files.
The following features can be added:
#### 1. FastAPI Backend

Create API endpoints around the existing LangGraph agent.

**Where to work:**
- `main.py` — Create the FastAPI application and API endpoints.
- `core/agent.py` — Convert the existing testing/terminal code that builds and runs the graph into a reusable function. S0 that, the function can be called from the FastAPI endpoints

**What to add:**
- `POST /chat` endpoint for sending messages.
- Stream responses from the LangGraph agent.
- Pass `user_id` and `thread_id` with each request.

---

#### 2. Web Frontend

Build a web interface that communicates with the FastAPI backend.

**Where to work:**
- Create a new `frontend/` directory.
- Connect the frontend to the `/chat` API created in `main.py`.

**What to add:**
- Chat interface
- New conversation
- Conversation history
- Streaming responses
- Voice controls

---

#### 3. Voice Integration

The voice functionality already exists but is separate from the main chatbot.

**Where to work:**
- `VoiceText/TTS.py`
- `core/agent.py` or the API layer

**What to add:**
- Send microphone input to speech-to-text.
- Pass the converted text to the LangGraph agent.
- Send the AI response to text-to-speech.
- Play the generated audio to the user.

---

#### 4. Authentication

Add authentication so each user can securely access their own conversations and memories.

**Where to work:**
- `main.py` — Add authentication endpoints and middleware.
- `core/agent.py` — Pass the authenticated `user_id` to the graph.
- Database layer — Store user/account information if required.

**What to add:**
- User registration and login
- Authentication tokens/sessions
- User-specific conversations
- User-specific long-term memory

---

#### 5. Chat Management

Add functionality for managing multiple conversations.

**Where to work:**
- `main.py` — Add chat management API endpoints.
- `core/agent.py` — Use `thread_id` to manage individual conversations.
- Frontend — Add the chat management interface.

**What to add:**
- Create new chat
- Switch between chats
- Rename chats
- Delete chats
- Load previous conversations

---

#### 6. Deployment

Deploy the application so it can be accessed online.

**Components to deploy:**
- FastAPI backend
- Frontend
- PostgreSQL database

**Recommended flow:**

```text
Frontend
   │
   ▼
FastAPI Backend
   │
   ▼
LangGraph Agent
   │
   ├── LLM
   ├── Tools
   └── PostgreSQL
