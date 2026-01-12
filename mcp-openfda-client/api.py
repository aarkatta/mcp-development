import asyncio
import json
import os
import uuid  # Added for session IDs
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header  # Added Header for session tracking
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.types import CallToolRequest

load_dotenv()

# --- CONFIGURATION ---
REMOTE_SERVER_URL = "http://0.0.0.0:8000/sse"
# UPDATE: Use a valid model name. 'gemini-3' is not valid.
MODEL_NAME = "gemini-3-flash-preview"

client_llm = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Global MCP State (Connection is shared, but state is not)
mcp_session = None
llm_tools = []

# Session Store: { "session_id": [messages] }
# In production, use Redis or a database.
user_sessions = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MCP connection on startup."""
    global mcp_session, llm_tools

    print(f"🔌 Connecting to MCP Server at {REMOTE_SERVER_URL}...")

    # Keep connection alive
    app.state.sse_streams = sse_client(REMOTE_SERVER_URL)
    streams = await app.state.sse_streams.__aenter__()

    app.state.client_session = ClientSession(streams[0], streams[1])
    mcp_session = await app.state.client_session.__aenter__()
    await mcp_session.initialize()

    # Fetch tools once on startup
    mcp_tools = await mcp_session.list_tools()
    llm_tools = [{
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        }
    } for tool in mcp_tools.tools]

    print(f"✅ Loaded {len(mcp_tools.tools)} tools. API Ready!")

    yield

    # Cleanup
    await app.state.client_session.__aexit__(None, None, None)
    await app.state.sse_streams.__aexit__(None, None, None)

app = FastAPI(title="OpenFDA Chat API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None # Frontend can send an ID to resume chat

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_used: str | None = None
    tool_args: dict | None = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global user_sessions

    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP session not initialized")

    # 1. Handle Session
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in user_sessions:
        # Initialize new history for this user
        user_sessions[session_id] = [
            {"role": "system", "content": "You are a helpful assistant. Use available tools."}
        ]
    
    # Get this user's specific history
    history = user_sessions[session_id]
    history.append({"role": "user", "content": request.message})

    # 2. Ask LLM
    try:
        response = await client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            tools=llm_tools,
            tool_choice="auto"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    msg = response.choices[0].message
    history.append(msg) # Save thought process

    tool_used = None
    tool_args = None

    # 3. Handle Tool Calls
    if msg.tool_calls:
        tool_used = msg.tool_calls[0].function.name
        
        for tool_call in msg.tool_calls:
            # Safe JSON parsing
            try:
                args = json.loads(tool_call.function.arguments)
                tool_args = args
            except json.JSONDecodeError:
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "Error: Invalid JSON arguments generated."
                })
                continue

            print(f"🛠️ Executing {tool_call.function.name} for Session {session_id}...")

            # Execute Tool (Safe Call)
            try:
                result = await mcp_session.call_tool(
                    name=tool_call.function.name,
                    arguments=args
                )
                # Robust text extraction (handle multiple text blocks or empty content)
                tool_output = "\n".join(
                    [c.text for c in result.content if c.type == "text"]
                )
            except Exception as e:
                tool_output = f"Error executing tool: {str(e)}"

            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

        # 4. Get Final Answer
        final_response = await client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=history
        )
        bot_response = final_response.choices[0].message.content or ""
        history.append({"role": "assistant", "content": bot_response})
    else:
        bot_response = msg.content or ""
        history.append({"role": "assistant", "content": bot_response})

    return ChatResponse(
        response=bot_response,
        session_id=session_id,
        tool_used=tool_used,
        tool_args=tool_args
    )

@app.delete("/chat/{session_id}")
async def clear_session(session_id: str):
    """Clear history for a specific user."""
    if session_id in user_sessions:
        del user_sessions[session_id]
        return {"status": "cleared"}
    raise HTTPException(status_code=404, detail="Session not found")