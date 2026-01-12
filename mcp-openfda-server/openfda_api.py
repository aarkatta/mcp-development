"""
OpenFDA Drug Recall API Client

Handles all interactions with the openFDA drug enforcement API.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.fda.gov/drug"
TIMEOUT = 10.0
API_KEY = os.getenv("OPENFDA_DRUG_API_KEY")


def _filter_recall_data(results: list) -> list:
    """
    Extract only LLM-relevant fields from raw API response.
    Reduces token usage by discarding administrative data.
    """
    simplified_data = []

    for item in results:
        entry = {
            "product": item.get("product_description"),
            "reason": item.get("reason_for_recall"),
            "risk_level": item.get("classification"),
            "company": item.get("recalling_firm"),
            "affected_lots": item.get("code_info"),
            "status": item.get("status"),
            "date": item.get("recall_initiation_date"),
            "scope": item.get("distribution_pattern"),
            "type": item.get("voluntary_mandated"),
        }
        simplified_data.append(entry)

    return simplified_data


# Helper function to clean the data and handle the logic we discussed
def _filter_shortage_data(results: list) -> list:
    """
    Simplifies raw FDA shortage data for LLM consumption.
    Prioritizes 'related_info' over 'shortage_reason' for better context.
    """
    clean_data = []
    
    for item in results:
        # LOGIC: Check 'related_info' first (often contains discontinuation info),
        # then fallback to 'shortage_reason'.
        reason = item.get("related_info", "").strip()
        if not reason:
            reason = item.get("shortage_reason", "").strip() or "Reason not specified"

        # Handle brand name safely (it is often nested in openfda object)
        brand_name = item.get("brand_name")
        if not brand_name and "openfda" in item:
            brands = item["openfda"].get("brand_name", [])
            if brands:
                brand_name = brands[0]
        
        entry = {
            "generic_name": item.get("generic_name"),
            "brand_name": brand_name or item.get("generic_name"), # Fallback if no brand
            "company_name": item.get("company_name"),
            "status": item.get("status"),
            "availability": item.get("availability", "Status Unknown"),
            "shortage_reason": reason, # The calculated reason
            "last_updated": item.get("update_date") or item.get("last_updated"),
            "presentation": item.get("presentation"), # Critical for dosage/vial size
            "contact_info": item.get("contact_info")
        }
        clean_data.append(entry)
        
    return clean_data


async def search_recalls(
    term: str = None, risk_level: str = None, limit: int = 5
) -> dict:
    """
    Search for drug recall enforcement reports.

    Args:
        term: Search term (e.g. "Tylenol", "Pfizer").
        risk_level: Filter by classification ("Class I", "Class II", "Class III").
        limit: Number of results to return (default 5, max 100).

    Returns:
        dict with 'success', 'data' or 'error' keys.
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/enforcement.json"

    # Build query dynamically
    query_parts = []
    if term:
        query_parts.append(f'"{term}"')
    if risk_level:
        query_parts.append(f'classification:"{risk_level}"')

    params = {"api_key": API_KEY, "limit": limit}
    if query_parts:
        params["search"] = "+AND+".join(query_parts)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                return {"success": True, "data": []}

            clean_results = _filter_recall_data(data["results"])
            return {"success": True, "data": clean_results}

        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}


async def get_recent_recalls(limit: int = 10) -> dict:
    """
    Get the most recent drug recalls sorted by report date.

    Args:
        limit: Number of results to return (default 10, max 100).

    Returns:
        dict with 'success', 'data' or 'error' keys.
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/enforcement.json"
    params = {
        "api_key": API_KEY,
        "sort": "report_date:desc",
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                return {"success": True, "data": []}

            clean_results = _filter_recall_data(data["results"])
            return {"success": True, "data": clean_results}

        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}


async def get_recalls_by_classification(classification: str, limit: int = 10) -> dict:
    """
    Get drug recalls filtered by classification level.

    Args:
        classification: Risk level - "Class I", "Class II", or "Class III".
        limit: Number of results to return (default 10, max 100).

    Returns:
        dict with 'success', 'data' or 'error' keys.
    """
    valid_classes = ["Class I", "Class II", "Class III"]
    if classification not in valid_classes:
        return {
            "success": False,
            "error": f"Invalid classification. Must be one of: {valid_classes}",
        }

    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/enforcement.json"
    params = {
        "api_key": API_KEY,
        "search": f'classification:"{classification}"',
        "limit": limit,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                return {"success": True, "data": []}

            clean_results = _filter_recall_data(data["results"])
            return {"success": True, "data": clean_results}

        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}


async def search_drug_shortages(
    term: str = None, status: str = None, limit: int = 5
) -> dict:
    """
    Search for drug shortages.

    Args:
        term: Drug name (e.g., "Clindamycin", "Pfizer").
        status: Filter by status (e.g., "Current", "Resolved").
        limit: Number of results (default 5).

    Returns:
        dict with 'success', 'data' or 'error' keys.
    """
    limit = min(max(1, limit), 100)
    # NOTE: Adjust this URL to match your specific API endpoint for shortages
    url = f"{BASE_URL}/shortages.json" 

    # Build query dynamically
    query_parts = []
    if term:
        # Search across generic name, brand name, or company
        query_parts.append(f'(generic_name:"{term}"+OR+brand_name:"{term}"+OR+company_name:"{term}")')
    
    if status:
        query_parts.append(f'status:"{status}"')

    params = {"limit": limit}
    # Add API_KEY if your specific endpoint requires it
    if API_KEY: 
        params["api_key"] = API_KEY
        
    if query_parts:
        params["search"] = "+AND+".join(query_parts)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()

            # Shortage APIs sometimes wrap results in "results" or return a list directly
            # Adjust based on your exact API response structure
            raw_results = data.get("results", []) if isinstance(data, dict) else data

            if not raw_results:
                return {"success": True, "data": []}

            clean_results = _filter_shortage_data(raw_results)
            return {"success": True, "data": clean_results}

        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}


async def get_drug_label(term: str) -> dict:
    """
    Search for official drug label information (indications, usage, warnings).

    Args:
        term: Drug name (brand or generic).

    Returns:
        dict with 'success', 'data' or 'error' keys.
    """
    if not term:
        return {"success": False, "error": "Drug name is required."}

    print(f"🤖 Drug label search term: {term}")

    url = f"{BASE_URL}/label.json"

    # Build params dict - search brand OR generic name
    search_query = f'(openfda.brand_name:"{term}")+OR+(openfda.generic_name:"{term}")'
    params = {
        "api_key": API_KEY,
        "limit": 1,
        "search": search_query,
    }

    print(f"🔍 Search query: {search_query}")
    print(f"🔗 Full URL: {url}?search={search_query}&limit=1")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)

            print(f"📡 Response status: {response.status_code}")

            if response.status_code == 404:
                return {"success": True, "data": []}

            response.raise_for_status()
            data = response.json()

            print(f"📦 Results found: {'results' in data and len(data.get('results', []))}")

            if "results" not in data or not data["results"]:
                return {"success": True, "data": []}

            # Extract the first result
            result = data["results"][0]

            # Safely get openfda object (could be None)
            openfda = result.get("openfda") or {}

            # --- EXTRACT RELEVANT FIELDS ---
            # We use .get(..., ["N/A"])[0] because most text fields are arrays of strings.
            clean_data = {
                "brand_name": openfda.get("brand_name", ["Unknown"])[0],
                "generic_name": openfda.get("generic_name", ["Unknown"])[0],
                "manufacturer": openfda.get("manufacturer_name", ["Unknown"])[0],
                "pharm_class": openfda.get("pharm_class_epc", ["Unknown"])[0],
            }

            # Truncate very long fields to prevent token overflow
            for key, value in clean_data.items():
                if isinstance(value, str) and len(value) > 1500:
                    clean_data[key] = value[:1500] + "... (truncated)"

            print(f"📋 clean_data: {clean_data}")

            # Return as LIST to match other functions
            return {"success": True, "data": [clean_data]}

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"success": True, "data": []}
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}