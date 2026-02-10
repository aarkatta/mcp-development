
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
from sse_starlette.sse import EventSourceResponse, ServerSentEvent
# Native Gemini SDK (Latest v1.0.0+)
from google import genai
from google.genai import types

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
REMOTE_SERVER_URL = os.getenv("REMOTE_SERVER_URL", "http://0.0.0.0:8000/sse")
MODEL_NAME = "gemini-3-pro-preview"


@asynccontextmanager
async def get_mcp_session():
    """Create a fresh MCP session via SSE for each request."""
    async with sse_client(REMOTE_SERVER_URL) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            yield session


async def load_gemini_tools():
    """Connect to MCP server once at startup to load tool definitions."""
    async with get_mcp_session() as session:
        mcp_tools = await session.list_tools()
        print(f"✓ Loaded {len(mcp_tools.tools)} tools from MCP server:")
        for tool in mcp_tools.tools:
            print(f"  - {tool.name}")
        return convert_mcp_to_gemini_tools(mcp_tools)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles Gemini Client initialization and MCP tool discovery."""
    global gemini_client

    try:
        # 1. Initialize Gemini Client
        gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 2. Load tool definitions from MCP server (one-time discovery)
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[Attempt {attempt}/{max_retries}] Loading tools from MCP Server at {REMOTE_SERVER_URL}...")
                app.state.gemini_tools = await load_gemini_tools()
                break
            except Exception as e:
                print(f"✗ Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    delay = 2.0 * attempt
                    print(f"  Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(f"Failed to load MCP tools after {max_retries} attempts")

        yield

    except Exception as e:
        print(f"✗ Startup failed: {e}")
        raise
    finally:
        print("✓ Cleanup complete.")


# --- GLOBAL STATE ---
gemini_client: Optional[genai.Client] = None

# Simple in-memory session store: { "session_id": [messages_list] }
user_sessions: Dict[str, List[types.Content]] = {}

SYSTEM_INSTRUCTION = """You are a pharmaceutical assistant with access to FDA drug databases. Your job is to provide clear, actionable safety information using real FDA data.

### AVAILABLE FDA DATA SOURCES
1. ADVERSE EVENTS: Side effects and patient safety reports.
2. PRODUCT LABELING: Official prescribing info, dosage, and warnings.
3. RECALL ENFORCEMENT: Recalls (Class I, II, or III) and reasons for removal.
4. DRUG SHORTAGES: Current supply availability and manufacturer status.

### CRITICAL OPERATING RULES

1. HANDLING GENERAL RECALL QUERIES:
- If a user asks "Are there any recalls?" or "What's new?", do NOT just ask for a drug name. 
- ACTION: Call `get_critical_recalls(limit=5)` immediately to provide a high-level summary of the most urgent safety risks (Class I). This provides immediate value.

2. HANDLING GENERAL SHORTAGE QUERIES:
- If a user asks "Are there any drug shortages?" or "What drugs are unavailable?", do NOT just ask for a drug name.
- ACTION: Call `get_current_drug_shortages(limit=5)` immediately to provide a summary of current supply disruptions. This provides immediate value.

3. SPECIFICITY IS SAFETY:
- When reporting a recall, always include:
    * The REASON (e.g., "rodent activity" or "microbial contamination").
    * The SCOPE: Is it a manufacturer recall or a distributor-level recall (e.g., Gold Star Distribution)?
    * IDENTIFIERS: Always list Lot Numbers and Expiration Dates if available in the data.
    * GEOGRAPHY: If the data mentions specific states (e.g., MN, IN, ND), tell the user.

4. RISK COMMUNICATION:
- Always define the Recall Class in plain language:
    * Class I: Serious or life-threatening risk. Action: "Stop using immediately."
    * Class II: Temporary or reversible health problems.
    * Class III: Unlikely to cause adverse health consequences (e.g., minor packaging issues).

5. TOOL PROTOCOL:
- Maximum 2 tool calls per message.
- Use `search_recalls` if a drug name is provided.
- If a search for a common drug (e.g., Tylenol) returns a distributor recall, clarify that it may not affect all brands/bottles.

### RESPONSE FORMAT
1. DIRECT ANSWER: State the most critical findings first.
2. LIST ALL RESULTS: When tool data returns multiple items (recalls, shortages, etc.), you MUST list EVERY item returned. Do NOT summarize or truncate. If the tool returns 10 recalls, show all 10. If it returns 25 shortages, show all 25.
3. FORMATTING IS CRITICAL: Each recall or shortage MUST be its own numbered block separated by a blank line. Never run multiple items together in one paragraph. Use this exact markdown structure for EVERY item:

**Item format for recalls:**

1. **Product Name** — Recalling Firm
   - Reason: [reason]
   - Classification: [Class I/II/III]
   - Distribution: [states/areas]
   - Status: [Ongoing/Terminated]

2. **Next Product Name** — Next Firm
   - Reason: [reason]
   - Classification: [Class I/II/III]
   - Distribution: [states/areas]
   - Status: [Ongoing/Terminated]

**Item format for shortages:**

1. **Drug Name** — Manufacturer
   - Status: [Currently in Shortage / Resolved]
   - Reason: [reason]
   - Dosage Form: [tablet/capsule/etc.]

4. SOURCE CITATION: "According to the FDA Recall Database..."
5. ACTIONABLE ADVICE: Tell the user exactly what to look for on their bottle (Lot #) or where they bought it.
6. PERMISSION-BASED FOLLOW-UP: Ask before diving into side effects or labels (e.g., "Would you like me to check the official dosage instructions for this medication?").

### EXAMPLE OF CORRECT FORMATTING
User: "Show me recent recalls"
Assistant: "According to the FDA Recall Database, here are the most recent Class I recalls:

1. **Acetaminophen Tablets 500mg** — PharmaCo Inc.
   - Reason: Failed dissolution specifications
   - Classification: Class I (Serious risk — stop using immediately)
   - Distribution: Nationwide
   - Status: Ongoing

2. **Metformin HCl Extended-Release** — Generic Labs LLC
   - Reason: NDMA impurity above acceptable limit
   - Classification: Class I (Serious risk — stop using immediately)
   - Distribution: CA, TX, NY, FL
   - Status: Ongoing

Would you like more details on any of these recalls?"
"""

def convert_mcp_to_gemini_tools(mcp_tools) -> List[types.Tool]:
    """Convert MCP tool schemas to Gemini FunctionDeclaration format."""
    function_declarations = []
    for tool in mcp_tools.tools:
        func_decl = types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
            parameters_json_schema=tool.inputSchema
        )
        function_declarations.append(func_decl)
    return [types.Tool(function_declarations=function_declarations)]




app = FastAPI(title="OpenFDA Pharmaceutical Assistant", lifespan=lifespan)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATA MODELS ---

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


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
    """
    Main chat endpoint for pharmaceutical queries.
    Opens a fresh MCP connection per request to avoid stale SSE connections.
    """
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    session_id = request.session_id or str(uuid.uuid4())
    executed_tools = []

    try:
        # Create Gemini chat session
        chat_session = gemini_client.aio.chats.create(
            model=MODEL_NAME,
            history=user_sessions.get(session_id, []),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=app.state.gemini_tools,
                max_output_tokens=8192,
            )
        )

        # Send user message
        response = await chat_session.send_message(request.message)

        # Tool execution loop — open a fresh MCP connection only if tools are needed
        max_turns = 10
        if response.function_calls:
            async with get_mcp_session() as mcp_session:
                for turn in range(max_turns):
                    if not response.function_calls:
                        break

                    tool_responses = []
                    for fc in response.function_calls:
                        print(f"[Turn {turn+1}] Calling: {fc.name}({fc.args})")
                        try:
                            result = await mcp_session.call_tool(name=fc.name, arguments=fc.args)

                            tool_output = "\n".join(
                                [c.text for c in result.content if c.type == "text"]
                            )

                            executed_tools.append(ToolExecutionLog(
                                name=fc.name,
                                arguments=fc.args,
                                output=tool_output[:500]
                            ))

                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"result": tool_output}
                                )
                            )

                        except Exception as e:
                            print(f"  Error calling {fc.name}: {e}")
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"error": str(e)}
                                )
                            )

                    # Continue conversation with tool results
                    response = await chat_session.send_message(tool_responses)

        # Save history
        user_sessions[session_id] = chat_session.get_history()

        return ChatResponse(
            response=response.text or "I couldn't provide an answer.",
            session_id=session_id,
            tools_used=executed_tools if executed_tools else None
        )

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint. Returns SSE events as the response is generated.

    Events:
    - text_delta: incremental text chunk from Gemini
    - tool_start: MCP tool execution beginning
    - tool_end: MCP tool execution complete
    - done: stream complete with session metadata
    - error: an error occurred
    """
    if not gemini_client:
        raise HTTPException(status_code=503, detail="Gemini client not initialized")

    session_id = request.session_id or str(uuid.uuid4())

    async def event_generator():
        executed_tools = []
        mcp_session_ctx = None
        mcp_session = None

        try:
            chat_session = gemini_client.aio.chats.create(
                model=MODEL_NAME,
                history=user_sessions.get(session_id, []),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=app.state.gemini_tools,
                    max_output_tokens=8192,
                )
            )

            message_input = request.message
            max_turns = 10

            for turn in range(max_turns):
                function_calls_this_turn = []
                has_text = False
                has_function_calls = False

                stream = await chat_session.send_message_stream(message_input)
                async for chunk in stream:
                    if chunk.text:
                        has_text = True
                        yield ServerSentEvent(
                            data=json.dumps({"text": chunk.text}),
                            event="text_delta"
                        )

                    if chunk.function_calls:
                        has_function_calls = True
                        function_calls_this_turn.extend(chunk.function_calls)

                # Pure text response — streaming is done
                if has_text and not has_function_calls:
                    break

                if has_function_calls:
                    # Open MCP session lazily (once per request)
                    if mcp_session is None:
                        mcp_session_ctx = get_mcp_session()
                        mcp_session = await mcp_session_ctx.__aenter__()

                    tool_responses = []
                    for fc in function_calls_this_turn:
                        print(f"[Stream Turn {turn+1}] Calling: {fc.name}({fc.args})")

                        yield ServerSentEvent(
                            data=json.dumps({"tool_name": fc.name, "tool_args": fc.args}),
                            event="tool_start"
                        )

                        try:
                            result = await mcp_session.call_tool(name=fc.name, arguments=fc.args)
                            tool_output = "\n".join(
                                [c.text for c in result.content if c.type == "text"]
                            )

                            executed_tools.append(ToolExecutionLog(
                                name=fc.name,
                                arguments=fc.args,
                                output=tool_output[:500]
                            ))

                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"result": tool_output}
                                )
                            )

                            yield ServerSentEvent(
                                data=json.dumps({"tool_name": fc.name, "success": True}),
                                event="tool_end"
                            )

                        except Exception as e:
                            print(f"  Error calling {fc.name}: {e}")
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"error": str(e)}
                                )
                            )
                            yield ServerSentEvent(
                                data=json.dumps({"tool_name": fc.name, "success": False, "error": str(e)}),
                                event="tool_end"
                            )

                    # Feed tool results back to Gemini for the next turn
                    message_input = tool_responses
                else:
                    # No text and no function calls — empty response
                    break

            # Save session history
            user_sessions[session_id] = chat_session.get_history()

            yield ServerSentEvent(
                data=json.dumps({
                    "session_id": session_id,
                    "tools_used": [t.model_dump() for t in executed_tools] if executed_tools else None
                }),
                event="done"
            )

        except Exception as e:
            print(f"Streaming error: {e}")
            yield ServerSentEvent(
                data=json.dumps({"message": str(e)}),
                event="error"
            )
        finally:
            if mcp_session_ctx is not None:
                try:
                    await mcp_session_ctx.__aexit__(None, None, None)
                except Exception:
                    pass

    return EventSourceResponse(
        event_generator(),
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
        },
        ping=15,
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history."""
    user_sessions.pop(session_id, None)
    return {"status": "success"}


@app.get("/health")
async def health():
    """Health check — verifies Gemini client and MCP server reachability."""
    mcp_ok = False
    try:
        async with get_mcp_session() as session:
            mcp_ok = True
    except Exception:
        pass
    return {
        "status": "healthy" if (mcp_ok and gemini_client) else "degraded",
        "mcp": mcp_ok,
        "gemini": gemini_client is not None,
        "sessions": len(user_sessions)
    }



