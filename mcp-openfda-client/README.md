1. Install dependencies:
uv add google-genai

  uv sync

  2. Start the MCP server first (in one terminal):
  # In mcp-openfda-server directory
  uv run python server.py

  3. Start the API (in another terminal):
  uv run uvicorn client:app --host 0.0.0.0 --port 9080 --reload

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


  ## Deployment
  ## Note that the build commands were executed from their respective project directories, while deploy commands can be run from any configured project directory.
  
  gcloud builds submit --region=us-central1 --tag  us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --project=mcp-openfda-server
  
  gcloud run deploy  mcp-client --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest --region=us-central1 --allow-unauthenticated
  --project=mcp-openfda-server

  gcloud run deploy mcp-client \
    --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest \
    --region=us-central1 \
    --allow-unauthenticated \
    --project=mcp-openfda-server \
    --set-env-vars="GEMINI_API_KEY=api_key