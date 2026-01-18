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
from google import genai
from google.genai import types

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

# --- CONFIGURATION ---
REMOTE_SERVER_URL = "http://0.0.0.0:8000/sse"
MODEL_NAME = "gemini-3-flash-preview"

client_llm = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- GLOBAL STATE ---
mcp_session: Optional[ClientSession] = None
gemini_tools: Optional[types.Tool] = None # Will store our native declarations
user_sessions: Dict[str, List[types.Content]] = {}

# --- HELPER: CONVERT MCP TO GEMINI NATIVE ---
def mcp_to_gemini_declaration(mcp_tool) -> types.FunctionDeclaration:
    """
    Converts an MCP tool into a Gemini native FunctionDeclaration.
    """
    # Gemini expects a specific 'Schema' object for parameters
    return types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description,
        parameters=types.Schema(
            type="OBJECT",
            properties={
                k: types.Schema(
                    type=v.get("type", "string").upper(),
                    description=v.get("description", "")
                )
                for k, v in mcp_tool.inputSchema.get("properties", {}).items()
            },
            required=mcp_tool.inputSchema.get("required", [])
        )
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mcp_session, gemini_tools
    print(f"🔌 Connecting to MCP Server...")
    try:
        app.state.sse_streams = sse_client(REMOTE_SERVER_URL)
        streams = await app.state.sse_streams.__aenter__()
        app.state.client_session = ClientSession(streams[0], streams[1])
        mcp_session = await app.state.client_session.__aenter__()
        await mcp_session.initialize()

        # 1. Fetch tools from MCP
        mcp_tools_resp = await mcp_session.list_tools()
        
        # 2. Convert to Gemini Native Function Declarations
        declarations = [mcp_to_gemini_declaration(t) for t in mcp_tools_resp.tools]
        
        # 3. Store as a Gemini Tool object
        gemini_tools = [types.Tool(function_declarations=declarations)]

        print(f"✅ Loaded {len(declarations)} tools natively into Gemini format.")
        yield
    finally:
        if mcp_session:
            await app.state.client_session.__aexit__(None, None, None)
        print("🔌 MCP Connection closed.")

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    global user_sessions

    if not mcp_session or not gemini_tools:
        raise HTTPException(status_code=503, detail="MCP Server not ready")

    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in user_sessions:
        user_sessions[session_id] = []

    history = user_sessions[session_id]
    
    # Define the core system instruction
    sys_inst = "You are a proactive FDA assistant. Use tools for all drug data. Always ask to check recalls/shortages after a label search."

    # 1. Add User Message to History
    user_msg = types.Content(role="user", parts=[types.Part(text=request.message)])
    history.append(user_msg)

    try:
        # 2. THE AGENTIC LOOP (Manual implementation of Tool Calling)
        # A robust two-step process:
        # 1. Call with tools to decide what actions to take.
        # 2. If actions are taken, call again WITHOUT tools to summarize.

        # --- Step 1: Call with tools ---
        response = client_llm.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=sys_inst,
                tools=gemini_tools,
            )
        )

        # Check if Gemini wants to call a tool
        tool_calls = [p.function_call for p in response.candidates[0].content.parts if p.function_call]

        if not tool_calls:
            # No tool calls? This is our final answer.
            final_text = response.text
            history.append(response.candidates[0].content)
        else:
            # --- Step 2: Execute tools and summarize ---
            # Add the assistant's decision to call tools to history
            history.append(response.candidates[0].content)
            
            tool_responses_parts = []
            for call in tool_calls:
                print(f"🔧 Calling tool: {call.name} with {call.args}")
                
                # Execute via MCP
                mcp_res = await mcp_session.call_tool(call.name, call.args)
                
                # Extract the text from MCP result
                output_text = "\n".join([c.text for c in mcp_res.content if c.type == "text"])
                
                # Create a FunctionResponse part
                try:
                    # The tool returns a JSON string, so we parse it
                    parsed_output = json.loads(output_text)
                    if isinstance(parsed_output, list):
                        parsed_output = {'results': parsed_output}
                except json.JSONDecodeError:
                    # If it's not valid JSON, use the raw text
                    parsed_output = {'result': output_text}
                
                tool_responses_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=call.name,
                            response=parsed_output
                        )
                    )
                )

            # Add the tool outputs back to history
            history.append(types.Content(role="tool", parts=tool_responses_parts))
            
            # --- Step 3: Call again WITHOUT tools to force summarization ---
            summary_response = client_llm.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config=types.GenerateContentConfig(
                    system_instruction=sys_inst,
                    # No tools provided in this call
                )
            )
            final_text = summary_response.text
            history.append(summary_response.candidates[0].content)

        user_sessions[session_id] = history
        return ChatResponse(response=final_text, session_id=session_id)

    except Exception as e:
        print(f"❌ Error in chat loop: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)