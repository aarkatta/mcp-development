
import asyncio
import os
import uuid
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# Native Gemini SDK (Latest v1.0.0+)
from google import genai
from google.genai import types

# MCP Imports
from mcp import ClientSession
from mcp.client.sse import sse_client

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
REMOTE_SERVER_URL = "https://mcp-server-722021783439.us-central1.run.app/sse"
MODEL_NAME = "gemini-3-pro-preview"


# --- GLOBAL STATE ---
mcp_session: Optional[ClientSession] = None
gemini_client: Optional[genai.Client] = None

# Simple in-memory session store: { "session_id": [messages_list] }
user_sessions: Dict[str, List[types.Content]] = {}

SYSTEM_INSTRUCTION_ARCHIVE = (
    "You are an intelligent, proactive pharmaceutical assistant with access to official FDA data. "
    "Your goal is to provide accurate, safety-critical information using strictly defined tools.\n\n"

    "### AVAILABLE TOOLS\n"
    "1) `get_drug_label`: Authoritative source for safety, usage, and warnings.\n"
    "2) `search_drug_recalls`: Search for historical drug recall events for a specific drug.\n"
    "3) `get_recent_drug_recalls`: Get a list of the latest FDA drug recall alerts.\n"
    "4) `get_drug_recalls_by_classification`: Filter recalls by risk level (Class I, II, III).\n"
    "5) `get_drug_shortages`: Check current supply status and shortage details.\n\n"

    "### CORE AGENTIC WORKFLOW\n"
    "1. CLARIFY & PLAN: Before calling a tool, ensure you have the specific drug name. "
    "If the user's request is ambiguous (e.g., 'that heart medicine'), ask for the specific name first.\n"
    "2. EXECUTE: Use the most relevant tool for the primary intent. "
    "Do NOT guess—if a tool is needed, you must call it.\n"
    "3. ANSWER & VERIFY: Provide a clear answer based *strictly* on the tool's output. "
    "If the tool returns no data (e.g., 'No recalls found'), state that explicitly rather than hallucinating.\n"
    "4. PROACTIVE SAFETY CHECK (Required):\n"
    "   - After answering a safety/label question, ask: 'Would you like to check for recent recalls or shortages?'\n"
    "   - After answering a shortage question, ask: 'Would you like to review safety warnings?'\n"
    "   - After answering a recall question, ask: 'Would you like to see the risk classification?'\n"
    "   - **Constraint:** Never run these extra checks automatically. Always ask for permission."
)

SYSTEM_INSTRUCTION = """You are a pharmaceutical assistant with access to FDA drug databases. Your job is to provide clear, actionable safety information using real FDA data.

### AVAILABLE FDA DATA SOURCES
1. ADVERSE EVENTS: Side effects and patient safety reports.
2. PRODUCT LABELING: Official prescribing info, dosage, and warnings.
3. RECALL ENFORCEMENT: Recalls (Class I, II, or III) and reasons for removal.
4. DRUG SHORTAGES: Current supply availability and manufacturer status.

### CRITICAL OPERATING RULES

1. HANDLING GENERAL RECALL QUERIES:
- If a user asks "Are there any recalls?" or "What's new?", do NOT just ask for a drug name. 
- ACTION: Call `get_critical_recalls(limit=25)` immediately to provide a high-level summary of the most urgent safety risks (Class I). This provides immediate value.

2. HANDLING GENERAL SHORTAGE QUERIES:
- If a user asks "Are there any drug shortages?" or "What drugs are unavailable?", do NOT just ask for a drug name.
- ACTION: Call `get_current_drug_shortages(limit=25)` immediately to provide a summary of current supply disruptions. This provides immediate value.

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


async def connect_mcp(app: FastAPI, max_retries: int = 5, base_delay: float = 2.0):
    """Connect to MCP server with retries for Cloud Run cold-start race conditions."""
    global mcp_session

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Attempt {attempt}/{max_retries}] Connecting to MCP Server at {REMOTE_SERVER_URL}...")
            app.state.sse_streams = sse_client(REMOTE_SERVER_URL)
            streams = await app.state.sse_streams.__aenter__()

            app.state.client_session = ClientSession(streams[0], streams[1])
            mcp_session = await app.state.client_session.__aenter__()
            await mcp_session.initialize()

            mcp_tools = await mcp_session.list_tools()
            app.state.gemini_tools = convert_mcp_to_gemini_tools(mcp_tools)

            print(f"✓ Connected! Loaded {len(mcp_tools.tools)} tools:")
            for tool in mcp_tools.tools:
                print(f"  - {tool.name}")
            return
        except Exception as e:
            print(f"✗ Attempt {attempt} failed: {e}")
            # Clean up partial connections before retrying
            if mcp_session:
                try:
                    await app.state.client_session.__aexit__(None, None, None)
                except Exception:
                    pass
                mcp_session = None
            if hasattr(app.state, "sse_streams"):
                try:
                    await app.state.sse_streams.__aexit__(None, None, None)
                except Exception:
                    pass
            if attempt < max_retries:
                delay = base_delay * attempt
                print(f"  Retrying in {delay}s...")
                await asyncio.sleep(delay)

    raise RuntimeError(f"Failed to connect to MCP server after {max_retries} attempts")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles MCP connection and Gemini Client initialization."""
    global gemini_client

    try:
        # 1. Initialize Gemini Client (independent of MCP)
        gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 2. Connect to MCP server with retries
        await connect_mcp(app)

        yield

    except Exception as e:
        print(f"✗ Startup failed: {e}")
        raise
    finally:
        if mcp_session:
            await app.state.client_session.__aexit__(None, None, None)
        if hasattr(app.state, "sse_streams"):
            await app.state.sse_streams.__aexit__(None, None, None)
        print("✓ Cleanup complete.")


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
    
    Only calls tools when user explicitly requests information about a specific drug.
    """
    if not mcp_session or not gemini_client:
        raise HTTPException(status_code=503, detail="Services not initialized")

    session_id = request.session_id or str(uuid.uuid4())
    executed_tools = []

    try:
        # Create chat session
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

        # Tool execution loop
        max_turns = 10
        for turn in range(max_turns):
            if not response.function_calls:
                break

            tool_responses = []
            for fc in response.function_calls:
                print(f"[Turn {turn+1}] Calling: {fc.name}({fc.args})")
                try:
                    # Call MCP tool
                    result = await mcp_session.call_tool(name=fc.name, arguments=fc.args)
                    
                    # Extract text
                    tool_output = "\\n".join(
                        [c.text for c in result.content if c.type == "text"]
                    )
                    
                    # Log execution
                    executed_tools.append(ToolExecutionLog(
                        name=fc.name,
                        arguments=fc.args,
                        output=tool_output[:500]
                    ))

                    # Send result back
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"result": tool_output}
                        )
                    )
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    tool_responses.append(
                        types.Part.from_function_response(
                            name=fc.name,
                            response={"error": str(e)}
                        )
                    )

            # Continue conversation
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


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history."""
    user_sessions.pop(session_id, None)
    return {"status": "success"}


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "mcp": mcp_session is not None,
        "gemini": gemini_client is not None,
        "sessions": len(user_sessions)
    }



