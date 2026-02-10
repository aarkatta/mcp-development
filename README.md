# DrugBot - FDA Pharmaceutical Assistant

> **GEMIN Hackathon Project**

**Live App**: [https://www.thedrugbot.com](https://www.thedrugbot.com)

An AI-powered pharmaceutical assistant that provides real-time FDA drug safety information through a conversational interface. DrugBot connects to the [openFDA API](https://open.fda.gov/) via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and uses Google Gemini as the reasoning engine to answer drug-related queries.

## Architecture

```
┌─────────────┐       ┌──────────────────┐       ┌──────────────────┐       ┌───────────┐
│  DrugBot UI │──────>│  MCP Client /    │──────>│  MCP Server      │──────>│  openFDA  │
│  (Next.js)  │ REST  │  FastAPI Backend  │  SSE  │  (FastMCP)       │ HTTP  │  API      │
│  Port 3000  │<──────│  Port 9080        │<──────│  Port 8080       │<──────│           │
└─────────────┘       └──────────────────┘       └──────────────────┘       └───────────┘
                             │
                             │ Gemini API
                             v
                      ┌──────────────┐
                      │  Google      │
                      │  Gemini Pro  │
                      └──────────────┘
```

The system is composed of three services:

| Service | Directory | Tech Stack | Description |
|---------|-----------|------------|-------------|
| **MCP Server** | `mcp-openfda-server/` | Python, FastMCP | Exposes FDA drug data as MCP tools over SSE transport |
| **MCP Client / API** | `mcp-openfda-client/` | Python, FastAPI, Google Gemini SDK | Orchestrates LLM reasoning with MCP tool calls; serves REST API |
| **Frontend UI** | `drugbot-ui/` | Next.js, React, Tailwind CSS | Conversational chat interface for end users |

## FDA Data Sources

DrugBot provides access to four FDA datasets through 12 MCP tools:

| Dataset | Tools | What You Can Ask |
|---------|-------|------------------|
| **Adverse Events** | `search_adverse_events`, `get_serious_adverse_events` | Side effects, safety reports, serious reactions |
| **Product Labeling** | `get_drug_label`, `search_drug_labels` | Dosage, warnings, contraindications, ingredients |
| **Recall Enforcement** | `search_recalls`, `get_recent_drug_recalls`, `get_recalls_by_classification`, `get_critical_recalls` | Drug recalls by severity (Class I/II/III), company, product |
| **Drug Shortages** | `search_drug_shortages`, `get_current_drug_shortages`, `search_shortages_by_manufacturer` | Supply availability, shortage reasons, manufacturer status |

## Prerequisites

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) package manager
- **Node.js 18+** with npm
- **Google Gemini API key** (set as `GEMINI_API_KEY`)
- **openFDA API key** (optional, set as `OPENFDA_DRUG_API_KEY` for higher rate limits)

## Getting Started

### 1. MCP Server

```bash
cd mcp-openfda-server
uv sync
uv run python server.py
```

The server starts on port **8080** and exposes FDA data tools via SSE.

### 2. MCP Client / API Backend

```bash
cd mcp-openfda-client
uv add google-genai   # first time only
uv sync
uv run uvicorn client:app --host 0.0.0.0 --port 9080 --reload
```

### 3. Frontend UI

```bash
cd drugbot-ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## API Endpoints

The MCP Client exposes a REST API consumed by the frontend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send a message and get an AI-powered response with FDA data |
| `/session/{session_id}` | DELETE | Clear conversation history for a session |
| `/health` | GET | Check API status (MCP connection, Gemini client, active sessions) |

## Deployment (Google Cloud Run)

All three services are containerized with Docker and deployed to Google Cloud Run.

### Initial Setup

```bash
gcloud init

# Create artifact repository (one-time)
gcloud artifacts repositories create remote-mcp-servers \
  --repository-format=docker \
  --location=us-central1 \
  --description="Repository for remote MCP servers" \
  --project=mcp-openfda-server
```

### Deploy MCP Server

```bash
cd mcp-openfda-server

gcloud builds submit \
  --region=us-central1 \
  --tag us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-server:latest

gcloud run deploy mcp-server \
  --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-server:latest \
  --region=us-central1 \
  --allow-unauthenticated
```

### Deploy MCP Client / API

```bash
cd mcp-openfda-client

gcloud builds submit \
  --region=us-central1 \
  --tag us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest \
  --project=mcp-openfda-server

gcloud run deploy mcp-client \
  --image us-central1-docker.pkg.dev/mcp-openfda-server/remote-mcp-servers/mcp-client:latest \
  --region=us-central1 \
  --allow-unauthenticated \
  --project=mcp-openfda-server \
  --set-env-vars="GEMINI_API_KEY=<your-api-key>"
```

## Project Structure

```
mcp-development/
├── mcp-openfda-server/       # MCP Server (FastMCP + openFDA)
│   ├── server.py             #   MCP tool definitions (12 tools)
│   ├── openfda_api.py        #   openFDA API client with response optimization
│   ├── main.py               #   Entry point
│   ├── Dockerfile            #   Container config
│   └── pyproject.toml        #   Python dependencies
├── mcp-openfda-client/       # MCP Client + FastAPI Backend
│   ├── client.py             #   Gemini integration, MCP client, REST API
│   ├── api.py                #   Additional API routes
│   ├── main.py               #   Entry point
│   ├── Dockerfile            #   Container config
│   └── pyproject.toml        #   Python dependencies
├── drugbot-ui/               # Frontend (Next.js + React)
│   ├── src/
│   │   ├── app/              #   Next.js app router pages
│   │   ├── components/       #   React UI components
│   │   ├── hooks/            #   Custom React hooks (chat logic)
│   │   └── lib/              #   Utility functions
│   ├── package.json          #   Node.js dependencies
│   └── next.config.ts        #   Next.js configuration
└── docs/                     # Documentation & requirements
    ├── architecture-slider.html  #   Interactive architecture diagram
    └── DrugBot_Requirements.pdf  #   Project requirements document
```

## Documentation

- [Architecture Diagram](docs/architecture-slider.html) - Interactive slider showing the system architecture
- [Project Requirements](docs/DrugBot_Requirements.pdf) - DrugBot requirements specification

## Tech Stack

- **LLM**: gemini-3-pro-preview
- **Protocol**: Model Context Protocol (MCP) over SSE transport
- **Backend**: Python, FastAPI, FastMCP, httpx
- **Frontend**: Next.js 16, React 19, Tailwind CSS 4, Radix UI, Framer Motion
- **Data Source**: [openFDA Drug APIs](https://open.fda.gov/apis/)
- **Deployment**: Docker, Google Cloud Run, Google Artifact Registry
