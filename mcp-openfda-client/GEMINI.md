# Gemini CLI Context: OpenFDA Agent Client

## Project Overview
This is the **Agent Host** (FastAPI) that orchestrates the conversation.
* **Role:** AI Systems Architect building an Agentic Workflow.
* **Goal:** Manage user sessions, connect to the MCP Server, and execute the "Proactive Safety Check" workflow.

## Tech Stack
* **Framework:** FastAPI (Port 8080)
* **LLM Provider:** Gemini (via OpenAI-compatible endpoint).
* **Model:** `gemini-3-flash-preview`
* **Protocol:** MCP Client (SSE Transport).

## Agentic Workflow (The "Brain")
The system prompt (in `client.py`) enforces a specific behavior loop:
1.  **Analyze & Execute:** Use tools (`get_drug_label`, `search_drug_recalls`, etc.) immediately based on user intent.
2.  **Answer:** Provide the data found.
3.  **Proactive Safety Check:**
    * *If discussing safety/labels:* Ask to check for **shortages** or **recalls**.
    * *If discussing recalls:* Ask to check **risk levels**.
    * *Constraint:* Never run these extra tools automatically; always **ask permission** first.

## Debugging Checklist
* **Connection:** The client connects to the server at `http://0.0.0.0:8000/sse`.
* **Session Management:** Sessions are stored in memory (`user_sessions`). Ensure `session_id` is passed from the frontend to maintain context.
* **Tool Loop:** The client performs a 2-step LLM call:
    * Step A: Decide which tools to call.
    * Step B: Summarize tool outputs for the user.

## Deployment. N
## Note that the build commands were executed from their respective project directories, while deploy commands can be run from any configured project directory.
  
  gcloud builds submit --region=us-central1 --tag  us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --project=mcp-openfda-server
  gcloud run deploy  mcp-client --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --region=us-central1 --allow-unauthenticated
  --project=mcp-openfda-server
  