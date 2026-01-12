from fastmcp import FastMCP
import json

import openfda_api

mcp = FastMCP("OpenFDA Remote Server")


@mcp.tool()
async def search_drug_recalls(term: str = None, risk_level: str = None, limit: int = 5) -> str:
    """
    Search for drug recall enforcement reports.

    Args:
        term: The drug name or company (e.g. "Tylenol", "Pfizer").
        risk_level: Filter by severity. INFER this from the user's tone:
            - "Class I": Use for "deadly", "serious", "dangerous", "life-threatening".
            - "Class II": Use for "temporary health problem", "reversible", "bad".
            - "Class III": Use for "minor", "unlikely to cause harm", "technical violation".
        limit: Number of results (default 5).
    """
    result = await openfda_api.search_recalls(term, risk_level, limit)

    if not result["success"]:
        return result["error"]

    if not result["data"]:
        return "No recalls found for this query."

    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_recent_drug_recalls(limit: int = 10) -> str:
    """
    Get the most recent drug recalls sorted by report date.

    Args:
        limit: Number of results to return (default 10).
    """
    result = await openfda_api.get_recent_recalls(limit)

    if not result["success"]:
        return result["error"]

    if not result["data"]:
        return "No recent recalls found."

    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_drug_recalls_by_classification(classification: str, limit: int = 10) -> str:
    """
    Get drug recalls filtered by risk classification level.

    Args:
        classification: Risk level - "Class I" (most serious, potential death),
            "Class II" (temporary health problems), or "Class III" (unlikely to cause harm).
        limit: Number of results to return (default 10).
    """
    result = await openfda_api.get_recalls_by_classification(classification, limit)

    if not result["success"]:
        return result["error"]

    if not result["data"]:
        return f"No {classification} recalls found."

    return json.dumps(result["data"], indent=2)

@mcp.tool()
async def get_drug_shortages(term: str = None, status: str = None, limit: int = 5) -> str:
    """
    Search for drug shortage reports.

    Args:
        term: Search term (e.g. "insulin", "Pfizer").
        status: Filter by status (e.g., "Current", "Resolved", "Discontinued").
        limit: Number of results to return (default 5).
    """
    # ensure arguments match the underlying 'search_drug_shortages' signature
    result = await openfda_api.search_drug_shortages(term=term, status=status, limit=limit)

    if not result["success"]:
        return f"Error searching shortages: {result['error']}"

    if not result["data"]:
        return f"No shortages found for query: {term} ({status or 'All Statuses'})"

    return json.dumps(result["data"], indent=2)

@mcp.tool()
async def get_drug_label(term: str) -> str:
    """
  Get official FDA drug label information including indications, warnings, 
  dosage, and safety information.

  Use this tool when the user asks about:
  - What a drug is used for (indications)
  - Drug side effects or adverse reactions
  - Drug interactions or contraindications
  - Dosage instructions
  - Pregnancy/pediatric/geriatric safety

  Args:
      term: The drug name (brand or generic, e.g., "Lipitor", "atorvastatin").
  """
    print(f"🤖 Drug label search term {term}")
    result = await openfda_api.get_drug_label(term)

    if not result["success"]:
        return f"Error retrieving drug label: {result['error']}"

    if not result["data"]:
        return f"No label information found for drug: {term}"

    return json.dumps(result["data"], indent=2)


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
