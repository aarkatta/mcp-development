# Gemini CLI Context: OpenFDA MCP Server

## Project Overview
This is the **MCP Server** that exposes FDA drug data to the agent.
* **Role:** Backend Python Engineer specializing in API integrations.
* **Goal:** Expose efficient tools for querying drug recalls, shortages, and labeling.

## Tech Stack
* **Runtime:** Python 3.14+
* **Framework:** FastMCP (`mcp-openfda-server`)
* **Transport:** SSE (Server-Sent Events) over HTTP (Port 8000)
* **Dependencies:** `httpx` (Async HTTP client), `openfda_api` (Internal wrapper).

## Available Tools
The agent has access to these specific tools (defined in `server.py`):
1.  `search_drug_recalls(term, risk_level, limit)`: Search enforcement reports.
2.  `get_recent_drug_recalls(limit)`: Latest recalls sorted by date.
3.  `get_drug_recalls_by_classification(classification)`: Filter by Class I/II/III.
4.  `get_drug_shortages(term, status)`: Check if a drug is in shortage (Current/Resolved).
5.  `get_drug_label(term)`: Get indications, warnings, and usage info.

## Development Rules
* **Tool Definitions:** Always use the `@mcp.tool()` decorator from `FastMCP`.
* **Error Handling:** If `openfda_api` returns `success: False`, return the error string directly to the agent so it can explain it to the user.
* **Data Formatting:** Always return `json.dumps(result["data"], indent=2)` for complex data so the LLM can parse it easily.