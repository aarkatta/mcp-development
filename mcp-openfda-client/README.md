1. Install dependencies:
uv add google-genai

  uv sync

  2. Start the MCP server first (in one terminal):
  # In mcp-openfda-server directory
  uv run python server.py

  3. Start the API (in another terminal):
  uv run uvicorn client:app --host 0.0.0.0 --port 8080 --reload

API Endpoints:
  ┌──────────┬────────┬────────────────────────────┐
  │ Endpoint │ Method │        Description         │
  ├──────────┼────────┼────────────────────────────┤
  │ /chat    │ POST   │ Send message, get response │
  ├──────────┼────────┼────────────────────────────┤
  │ /reset   │ POST   │ Reset conversation history │
  ├──────────┼────────┼────────────────────────────┤
  │ /health  │ GET    │ Check API status           │
  └──────────┴────────┴────────────────────────────┘


  Other UV command
  rm -rf .venv
  uv venv