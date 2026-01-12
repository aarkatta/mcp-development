import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
REMOTE_SERVER_URL = "http://0.0.0.0:8000/sse"

# As requested: Using the specified preview model
MODEL_NAME = "gemini-3-flash-preview"

# Initialize OpenAI-compatible client for Gemini
client_llm = AsyncOpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# --- GLOBAL STATE ---
# We store the MCP session globally so we don't reconnect on every request.
# Note: In a high-traffic production app, you might use a pool of sessions.
mcp_session: Optional[ClientSession] = None
llm_tools: List[Dict] = []

# Simple in-memory session store: { "session_id": [messages_list] }
# In production, swap this for Redis or a database.
user_sessions: Dict[str, List[Dict]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle MCP connection startup and shutdown.
    """
    global mcp_session, llm_tools

    print(f"🔌 Connecting to MCP Server at {REMOTE_SERVER_URL}...")

    try:
        # 1. Establish SSE Connection
        # We store the stream manager in app.state to keep it alive
        app.state.sse_streams = sse_client(REMOTE_SERVER_URL)
        streams = await app.state.sse_streams.__aenter__()

        # 2. Initialize MCP Client Session
        app.state.client_session = ClientSession(streams[0], streams[1])
        mcp_session = await app.state.client_session.__aenter__()
        
        await mcp_session.initialize()

        # 3. Fetch Tools and Convert to OpenAI Format
        mcp_tools = await mcp_session.list_tools()
        
        llm_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in mcp_tools.tools]

        print(f"✅ Connected! Loaded {len(mcp_tools.tools)} tools.")
        print(f"   Model: {MODEL_NAME}")

        yield  # Application runs here

    except Exception as e:
        print(f"❌ Failed to connect to MCP Server: {e}")
        raise e
    finally:
        # Cleanup on shutdown
        if mcp_session:
            await app.state.client_session.__aexit__(None, None, None)
        if hasattr(app.state, "sse_streams"):
            await app.state.sse_streams.__aexit__(None, None, None)
        print("🔌 MCP Connection closed.")


app = FastAPI(title="OpenFDA Chat API", lifespan=lifespan)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production (e.g., ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATA MODELS ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  # Frontend sends this to resume context

class ToolExecutionLog(BaseModel):
    name: str
    arguments: Dict[str, Any]
    output: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: Optional[List[ToolExecutionLog]] = None


# --- ENDPOINTS ---

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global user_sessions

    if not mcp_session:
        raise HTTPException(status_code=503, detail="MCP Server not connected")

    # 1. Session Management
    # Generate a new ID if none provided, or verify existing one
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in user_sessions:
        # Initialize new conversation history
        user_sessions[session_id] = [
            {
                "role": "system", 
                "content": (
                    "You are an intelligent, proactive pharmaceutical assistant with access to official FDA data. "
                    "You have 5 specific tools to help users: "
                    "1) `get_drug_label` (for safety, usage, warnings), "
                    "2) `search_drug_recalls` (for specific recall history), "
                    "3) `get_recent_drug_recalls` (for the latest alerts), "
                    "4) `get_drug_recalls_by_classification` (by risk level), and "
                    "5) `get_drug_shortages` (for supply checks).\n\n"
                    
                    "CORE AGENTIC WORKFLOW:\n"
                    "1. ANALYZE & EXECUTE: When a user asks a question, identify the primary intent and immediately "
                    "use the most relevant tool (e.g., use `get_drug_label` for safety/usage questions, or `get_drug_shortages` if they ask about supply).\n"
                    "2. ANSWER: Provide a clear, helpful answer based *only* on the tool's output.\n"
                    "3. PROACTIVE SAFETY CHECK (The 'Agentic' Step): "
                    "   - If you answered a question about a specific drug's label/safety, YOU MUST END YOUR RESPONSE by asking: "
                    "     'Would you like me to check if this drug is currently in shortage or has any recent recalls?'\n"
                    "   - If you answered a question about shortages, ask if they want to check safety warnings or recalls.\n"
                    "   - If you answered a question about recalls, ask if they want to check risk level of the drug. \n"
                    "   - DO NOT run these extra tools automatically. Always ask the user for permission first."
                )
            }
        ]
    
    history = user_sessions[session_id]
    history.append({"role": "user", "content": request.message})

    # 2. Step A: Ask the LLM
    try:
        response_a = await client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            tools=llm_tools,
            tool_choice="auto"
        )
    except Exception as e:
        # Handle API errors (e.g., invalid model name, quota exceeded)
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    msg_a = response_a.choices[0].message
    history.append(msg_a)  # Add assistant's thought process to history

    executed_tools = []
    bot_final_response = ""

    # 3. Step B: Handle Tool Calls (if any)
    if msg_a.tool_calls:
        print(f"🤖 LLM requested {len(msg_a.tool_calls)} tool(s) for session {session_id}")
        print(f"🤖 (Thinking...) I need to use tool: {msg_a.tool_calls[0].function.name}")

        for tool_call in msg_a.tool_calls:
            tool_name = tool_call.function.name
            tool_args = {}
            tool_output = ""

            print(f"🔧 Executing tool: {tool_name}")
            print(f"   Raw arguments: {tool_call.function.arguments}")

            # Parse Arguments safely
            try:
                tool_args = json.loads(tool_call.function.arguments)
                print(f"   Parsed arguments: {tool_args}")
            except json.JSONDecodeError:
                tool_output = "Error: Invalid JSON arguments generated by LLM."
            
            # Execute Tool (if parsing succeeded)
            if not tool_output:
                try:
                    # Call the MCP Server
                    result = await mcp_session.call_tool(
                        name=tool_name,
                        arguments=tool_args
                    )
                    print(f"📥 Raw MCP result: {result}")
                    print(f"📥 Result content: {result.content}")
                    # Extract text content from result
                    tool_output = "\n".join(
                        [c.text for c in result.content if c.type == "text"]
                    )
                    print(f"📥 Extracted tool_output (length={len(tool_output)}): {tool_output[:200] if tool_output else 'EMPTY'}...")
                except Exception as e:
                    tool_output = f"Error executing tool '{tool_name}': {str(e)}"
                    print(f"❌ Tool execution error: {e}")

            # Log for the API response
            executed_tools.append({
                "name": tool_name,
                "arguments": tool_args,
                "output": tool_output[:200] + "..." if len(tool_output) > 200 else tool_output # Truncate for log only
            })

            # Append result to LLM history
            history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output
            })

        # 4. Step C: Get Final Answer (after tools)
        try:
            print(f"🧠 Asking LLM to summarize tool results...")
            # Add instruction to summarize (don't call more tools)
            summary_messages = history + [
                {"role": "user", "content": "Now summarize the tool results above in a helpful response. Do not call any more tools."}
            ]
            response_b = await client_llm.chat.completions.create(
                model=MODEL_NAME,
                messages=summary_messages
                # No tools parameter = LLM can't call tools
            )
            print(f"🧠 LLM response_b: {response_b}")
            bot_final_response = response_b.choices[0].message.content or ""
            print(f"🧠 Final response (length={len(bot_final_response)}): {bot_final_response[:200] if bot_final_response else 'EMPTY'}...")
            history.append({"role": "assistant", "content": bot_final_response})

        except Exception as e:
            print(f"❌ LLM Post-Tool Error: {e}")
            raise HTTPException(status_code=500, detail=f"LLM Post-Tool Error: {str(e)}")

    else:
        # No tools used, just simple chat
        bot_final_response = msg_a.content or ""
        # (Already appended msg_a to history above)

    return ChatResponse(
        response=bot_final_response,
        session_id=session_id,
        tools_used=executed_tools if executed_tools else None
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Endpoint to clear a specific user's history."""
    if session_id in user_sessions:
        del user_sessions[session_id]
        return {"status": "success", "message": "Session cleared"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "active",
        "mcp_connected": mcp_session is not None,
        "tools_loaded": len(llm_tools),
        "active_sessions": len(user_sessions)
    }

if __name__ == "__main__":
    import uvicorn
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=8080)