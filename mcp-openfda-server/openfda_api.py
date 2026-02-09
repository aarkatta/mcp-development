"""
OpenFDA Drug API Client - Corrected Endpoints

Uses correct API field names based on actual openFDA endpoints:
- Recall Enforcement: report_date, classification, voluntary_mandated
- Adverse Events: receivedate, patient.drug.openfda.pharm_class_epc, patient.reaction.reactionmeddrapt
- Drug Labeling: effective_time, boxed_warning, openfda.product_type
- Drug Shortages: dosage_form, update_type (simpler endpoint)
"""

import os
import httpx
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

load_dotenv()

BASE_URL = "https://api.fda.gov"
TIMEOUT = 10.0
API_KEY = os.getenv("OPENFDA_DRUG_API_KEY")


# ============================================================================
# FILTER FUNCTIONS - ENDPOINT-SPECIFIC OPTIMIZATION
# ============================================================================

def filter_adverse_events_data(results: list) -> list:
    """
    Extract LLM-relevant fields from adverse events API response.
    """
    clean_data = []
    
    for item in results:
        patient = item.get("patient", {})
        
        # Extract reactions with outcomes (limit to 3)
        reactions = []
        for reaction in patient.get("reaction", [])[:3]:
            reactions.append({
                "meddra_term": reaction.get("reactionmeddrapt", "Unknown"),
                "outcome": reaction.get("reactionoutcome", "Unknown")
            })
        
        # Extract drugs with key details (limit to 2)
        drugs = []
        for drug in patient.get("drug", [])[:2]:
            active_substance = drug.get("activesubstance", {})
            substance_name = (
                active_substance.get("activesubstancename", "Unknown") 
                if isinstance(active_substance, dict) else "Unknown"
            )
            
            # Get openfda data if available
            openfda = drug.get("openfda", {})
            
            drugs.append({
                "product_name": drug.get("drugname", "Unknown"),
                "active_substance": substance_name,
                "route": drug.get("drugadministrationroute", "Unknown"),
                "indication": drug.get("drugindication", "Unknown"),
                "pharm_class": openfda.get("pharm_class_epc", ["Unknown"])[0] if openfda.get("pharm_class_epc") else "Unknown"
            })
        
        # Extract seriousness indicators
        seriousness_types = []
        if item.get("seriousnessdeathcoding") == "1":
            seriousness_types.append("Death")
        if item.get("seriousnesslifethreatening") == "1":
            seriousness_types.append("Life Threatening")
        if item.get("seriousnesshospitalization") == "1":
            seriousness_types.append("Hospitalization")
        if item.get("seriousnessdisabling") == "1":
            seriousness_types.append("Disabling")
        
        entry = {
            "report_id": item.get("safetyreportid"),
            "received_date": item.get("receivedate"),  # CORRECTED field name
            "is_serious": item.get("serious") == "1",
            "seriousness_types": seriousness_types,
            "reactions": reactions,
            "drugs": drugs,
            "patient_info": {
                "age_group": patient.get("patientagegroup"),
                "gender": patient.get("patientsex"),
            }
        }
        clean_data.append(entry)
    
    return clean_data


def filter_product_labeling_data(results: list) -> list:
    """
    Extract LLM-relevant fields from drug labeling API response.
    """
    clean_data = []
    
    for item in results:
        openfda = item.get("openfda", {})
        
        def get_first(field_value, default="Not specified"):
            if isinstance(field_value, list) and field_value:
                val = field_value[0]
                return val[:500] if isinstance(val, str) and len(val) > 500 else val
            elif isinstance(field_value, str):
                return field_value[:500]
            return default
        
        warnings = get_first(item.get("warnings", []), "No specific warnings")
        boxed_warning = get_first(item.get("boxed_warning", []), None)
        adverse_reactions = get_first(item.get("adverse_reactions", []), "No specific reactions listed")
        indications = get_first(item.get("indications_and_usage", []), "Indication not specified")
        contraindications = get_first(item.get("contraindications", []), "No specific contraindications")
        
        # Extract active ingredients
        active_ingredients = []
        for ingredient in item.get("active_ingredient", [])[:3]:
            if isinstance(ingredient, dict):
                active_ingredients.append({
                    "name": ingredient.get("active_ingredient_base", "Unknown"),
                    "strength": ingredient.get("strength", "Unknown")
                })
        
        entry = {
            "effective_date": item.get("effective_time"),  # CORRECTED field name
            "brand_name": openfda.get("brand_name", ["Unknown"])[0],
            "generic_name": openfda.get("generic_name", ["Unknown"])[0],
            "manufacturer": openfda.get("manufacturer_name", ["Unknown"])[0],
            "route": openfda.get("route", ["Unknown"])[0],
            "product_type": openfda.get("product_type", ["Unknown"])[0],
            "indication": indications,
            "warnings_summary": warnings,
            "boxed_warning": boxed_warning,
            "contraindications": contraindications,
            "adverse_reactions_summary": adverse_reactions,
            "active_ingredients": active_ingredients,
            "dosage": get_first(item.get("dosage_and_administration", []), "Not specified")
        }
        clean_data.append(entry)
    
    return clean_data


def filter_recall_enforcement_data(results: list) -> list:
    """
    Extract LLM-relevant fields from recall enforcement API response.
    Uses correct field names: report_date, classification, voluntary_mandated
    """
    clean_data = []    

    for item in results:
        entry = {
            "recall_number": item.get("recall_number"),
            "event_id": item.get("event_id"),
            "report_date": item.get("report_date"),  # CORRECTED field name
            "classification_date": item.get("center_classification_date"),
            "classification": item.get("classification"),  # Class I, II, or III
            "status": item.get("status"),
            "termination_date": item.get("termination_date"),
            "product": {
                "description": item.get("product_description"),
                "type": item.get("product_type"),
                "quantity": item.get("product_quantity"),
                "codes": item.get("code_info")
            },
            "recall_reason": item.get("reason_for_recall", "")[:200],
            "distribution": item.get("distribution_pattern"),
            "voluntary_mandated": item.get("voluntary_mandated"),  # CORRECTED field name
            "recalling_firm": item.get("recalling_firm"),
            "location": {
                "city": item.get("city"),
                "state": item.get("state"),
                "country": item.get("country"),
                "address": item.get("address_1"),
            },
            "recall_initiation_date": item.get("recall_initiation_date")
        }
        clean_data.append(entry)
    
    return clean_data


def filter_drug_shortages_data(results: list) -> list:
    """
    Extract LLM-relevant fields from drug shortages API response.
    """
    clean_data = []
    
    for item in results:
        brand_name = item.get("brand_name")
        if not brand_name and "openfda" in item:
            brands = item["openfda"].get("brand_name", [])
            brand_name = brands[0] if brands else None
        
        reason = item.get("related_info", "").strip()
        if not reason:
            reason = item.get("shortage_reason", "").strip() or "No reason specified"
        
        entry = {
            "generic_name": item.get("generic_name"),
            "brand_name": brand_name or item.get("generic_name"),
            "update_type": item.get("update_type"),  # Corrected: using actual field
            "initial_posting_date": item.get("initial_posting_date"),
            "availability_status": item.get("availability", "Unknown"),
            "shortage_reason": reason[:250],
            "manufacturer": item.get("company_name") or item.get("manufacturer_name"),
            "contact_info": item.get("contact_info"),
            "product_details": {
                "dosage_form": item.get("dosage_form"),  # Corrected field
                "route": item.get("route"),
                "strength": item.get("strength"),
            },
            "last_updated": item.get("update_date") or item.get("last_updated"),
        }
        clean_data.append(entry)
    
    return clean_data


# ============================================================================
# API REQUEST FUNCTIONS
# ============================================================================

async def make_fda_request(url: str, params: dict) -> dict:
    """
    Makes a request to the openFDA API and handles common errors.
    """
    if API_KEY:
        params["api_key"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=TIMEOUT)
            print(f"FDA API request: {response.url}")
            
            if response.status_code == 404:
                return {"success": True, "data": {"results": []}}
            
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"API Error: {e.response.status_code}"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            return {"success": False, "error": f"Server Error: {str(e)}"}


# ============================================================================
# ADVERSE EVENTS ENDPOINT
# ============================================================================

async def search_adverse_events(
    drug_name: str = None,
    pharm_class: str = None,
    serious: bool = False,
    limit: int = 15
) -> dict:
    """
    Search for adverse drug event reports.
    
    Uses correct fields:
    - receivedate for date range
    - patient.drug.openfda.pharm_class_epc for pharmaceutical class
    - patient.reaction.reactionmeddrapt for reaction search
    
    Args:
        drug_name: Drug name (brand or generic)
        pharm_class: Pharmaceutical class (e.g., "nonsteroidal anti-inflammatory drug")
        serious: Filter for serious events only
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/event.json"
    
    query_parts = []
    if drug_name:
        query_parts.append(f'openfda.generic_name:"{drug_name}" OR openfda.brand_name:"{drug_name}"')
    if pharm_class:
        query_parts.append(f'patient.drug.openfda.pharm_class_epc:"{pharm_class}"')
    if serious:
        query_parts.append('serious:1')
    
    params = {"limit": limit}
    if query_parts:
        params["search"] = " AND ".join(query_parts)

    result = await make_fda_request(url, params)

    if not result["success"]:
        return result

    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}

    clean_results = filter_adverse_events_data(data["results"])
    return {"success": True, "data": clean_results}


async def get_serious_adverse_events(limit: int = 50) -> dict:
    """
    Get recent serious adverse events from the last 100 days.
    
    Uses receivedate for date range search.
    Date range: System date - 100 days to System date (TODAY)
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/event.json"
    
    # Calculate date range: Last 100 days from today
    end_date = datetime.now()  # TODAY (current system date)
    start_date = end_date - timedelta(days=100)  # 100 days ago
    
    # Format as YYYYMMDD
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    # Example: If today is 2026-02-01, fetch data from 2025-10-24 to 2026-02-01
    print(f"Fetching serious adverse events from {start_date_str} to {end_date_str}")
    
    params = {
        "search": f"receivedate:[{start_date_str} TO {end_date_str}] AND serious:1",
        "limit": limit
    }
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}
    
    clean_results = filter_adverse_events_data(data["results"])
    return {"success": True, "data": clean_results}

async def get_adverse_events_by_pharm_class(pharm_class: str, limit: int = 15) -> dict:
    """
    Get adverse events for a specific pharmaceutical class.
    
    Uses: patient.drug.openfda.pharm_class_epc field
    Example pharm_class: "nonsteroidal anti-inflammatory drug"
    
    Args:
        pharm_class: Pharmaceutical class name
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    return await search_adverse_events(pharm_class=pharm_class, limit=limit)


# ============================================================================
# PRODUCT LABELING ENDPOINT
# ============================================================================

async def get_drug_label(drug_name: str, limit: int = 1) -> dict:
    """
    Search for official drug label information.
    
    Args:
        drug_name: The drug name (brand or generic)
        limit: Number of results (default 1, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    if not drug_name:
        return {"success": False, "error": "Drug name is required."}
    
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/label.json"
    
    search_query = f'(openfda.brand_name:"{drug_name}") OR (openfda.generic_name:"{drug_name}")'
    params = {
        "limit": limit,
        "search": search_query,
    }
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data or not data["results"]:
        return {"success": True, "data": []}
    
    clean_results = filter_product_labeling_data(data["results"])
    return {"success": True, "data": clean_results}


async def search_drug_labels(
    search_term: str = None,
    manufacturer: str = None,
    effective_time_start: str = None,
    effective_time_end: str = None,
    limit: int = 15
) -> dict:
    """
    Search drug labels by content, manufacturer, or effective date.
    
    Uses correct field: effective_time for date range
    
    Args:
        search_term: Text to search in label content
        manufacturer: Filter by manufacturer name
        effective_time_start: Start date (YYYYMMDD format)
        effective_time_end: End date (YYYYMMDD format)
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/label.json"
    
    query_parts = []
    if search_term:
        query_parts.append(f'(indications_and_usage:"{search_term}" OR warnings:"{search_term}")')
    if manufacturer:
        query_parts.append(f'openfda.manufacturer_name:"{manufacturer}"')
    if effective_time_start and effective_time_end:
        query_parts.append(f'effective_time:[{effective_time_start} TO {effective_time_end}]')
    
    params = {"limit": limit}
    if query_parts:
        params["search"] = " AND ".join(query_parts)

    result = await make_fda_request(url, params)

    if not result["success"]:
        return result

    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}

    clean_results = filter_product_labeling_data(data["results"])
    return {"success": True, "data": clean_results}


async def get_labels_with_boxed_warning(limit: int = 15) -> dict:
    """
    Get drug labels that contain a black box warning.
    
    Uses: _exists_:boxed_warning search
    
    Args:
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/label.json"
    
    params = {
        "search": "_exists_:boxed_warning",
        "limit": limit
    }
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}
    
    clean_results = filter_product_labeling_data(data["results"])
    return {"success": True, "data": clean_results}


# ============================================================================
# RECALL ENFORCEMENT ENDPOINT
# ============================================================================

async def search_recalls(
    term: str = None,
    risk_level: str = None,
    limit: int = 15
) -> dict:
    """
    Search for drug recall enforcement reports.
    
    Uses correct fields: report_date, classification, voluntary_mandated
    
    Args:
        term: Search term (product, company, etc.)
        risk_level: "Class I", "Class II", or "Class III"
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/enforcement.json"
    
    # Calculate date range: Last 100 days from today
    end_date = datetime.now()  # TODAY (current system date)
    start_date = end_date - timedelta(days=100)  # 100 days ago
    
    # Format as YYYYMMDD
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    print(f"Fetching recent recalls from {start_date_str} to {end_date_str}")
    
    # Build query with date range as base
    query_parts = [f"report_date:[{start_date_str} TO {end_date_str}]"]
    
    # Add additional filters if provided
    if term:
        query_parts.append(f'"{term}"')
    if risk_level:
        query_parts.append(f'classification:"{risk_level}"')
    
    # Build final search parameter
    params = {
        "search": " AND ".join(query_parts),
        "limit": limit
    }

    result = await make_fda_request(url, params)

    if not result["success"]:
        return result

    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}

    clean_results = filter_recall_enforcement_data(data["results"])
    print(f"Found {len(clean_results)} recalls search_recalls")
    print(f" {clean_results}")
        
    return {"success": True, "data": clean_results}

async def get_recent_drug_recalls(limit: int = 50) -> dict:
    """
    Get the most recent drug recalls from the last 100 days.
    
    Uses: report_date for date range
    Date range: System date - 100 days to System date (TODAY)
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
        
    # Calculate date range: Last 100 days from today
    end_date = datetime.now()  # TODAY (current system date)
    start_date = end_date - timedelta(days=100)  # 100 days ago
    
    # Format as YYYYMMDD
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
        
    # Example: If today is 2026-02-01, fetch data from 2025-10-24 to 2026-02-01
    print(f"Fetching recent recalls from {start_date_str} to {end_date_str}")
    
    url = f"{BASE_URL}/drug/enforcement.json"

    params = {
        "limit": limit,
        "search": f"report_date:[{start_date_str} TO {end_date_str}]"
    }
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}
    
    clean_results = filter_recall_enforcement_data(data["results"])
    print(f"Found {len(clean_results)} recent recalls")    
   
    return {"success": True, "data": clean_results}

async def get_recalls_by_classification(
    classification: str,
    limit: int = 15
) -> dict:
    """
    Get drug recalls filtered by classification level.
    
    Uses: classification field (Class I/II/III)
    
    Args:
        classification: "Class I", "Class II", or "Class III"
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    valid_classes = ["Class I", "Class II", "Class III"]
    if classification not in valid_classes:
        return {
            "success": False,
            "error": f"Invalid classification. Must be one of: {valid_classes}",
        }
    
    limit = min(max(1, limit), 100)
   
    # Calculate date range: Last 100 days from today
    end_date = datetime.now()  # TODAY (current system date)
    start_date = end_date - timedelta(days=100)  # 100 days ago
    
    # Format as YYYYMMDD
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    
    print(f"Fetching recent recalls from {start_date_str} to {end_date_str}")

    url = f"{BASE_URL}/drug/enforcement.json"

    params = {
        "limit": limit,
        "search": f'classification:"{classification}" AND report_date:[{start_date_str} TO {end_date_str}]'
    }

    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}
    
    clean_results = filter_recall_enforcement_data(data["results"])
    print(f"Found {len(clean_results)} recalls with classification {classification}")        
    return {"success": True, "data": clean_results}


async def get_critical_recalls(limit: int = 50) -> dict:
    """
    Get critical Class I recalls.
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    return await get_recalls_by_classification("Class I", limit)


async def get_voluntary_recalls(limit: int = 50) -> dict:
    """
    Get voluntary recalls (firm-initiated).
    
    Uses: voluntary_mandated field
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/enforcement.json"
    
    params = {
        "search": 'voluntary_mandated:"Voluntary: Firm initiated"',
        "limit": limit
    }
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    if "results" not in data:
        return {"success": True, "data": []}
    
    clean_results = filter_recall_enforcement_data(data["results"])
    print(f"Found {len(clean_results)} recalls that are voluntary")
    return {"success": True, "data": clean_results}


# ============================================================================
# DRUG SHORTAGES ENDPOINT
# ============================================================================

async def search_drug_shortages(
    term: str = None,
    dosage_form: str = None,
    limit: int = 15
) -> dict:
    """
    Search for drug shortages.
    
    Uses correct fields: dosage_form for product form search
    
    Args:
        term: Drug name (generic, brand, or company)
        dosage_form: Product form (e.g., "Capsule", "Tablet", "Injectable")
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/shortages.json"
    
    query_parts = []
    if term:
        query_parts.append(
            f'(generic_name:"{term}" OR brand_name:"{term}" OR company_name:"{term}")'
        )
    if dosage_form:
        query_parts.append(f'dosage_form:"{dosage_form}"')
    
    params = {"limit": limit}
    if query_parts:
        params["search"] = " AND ".join(query_parts)

    result = await make_fda_request(url, params)

    if not result["success"]:
        return result

    data = result["data"]
    raw_results = data.get("results", []) if isinstance(data, dict) else data

    if not raw_results:
        return {"success": True, "data": []}

    clean_results = filter_drug_shortages_data(raw_results)
    return {"success": True, "data": clean_results}


async def get_current_drug_shortages(limit: int = 100) -> dict:
    """
    Get drug shortages updated in the last 100 days.
    
    NOTE: The openFDA shortages API does NOT support update_date in search parameters.
    This function fetches all shortages and MANUALLY FILTERS by update_date in Python.
    
    Date range: System date - 100 days to System date (TODAY)
    update_date format from API: MM/DD/YYYY (e.g., "01/06/2026")
    
    Args:
        limit: Maximum results to fetch from API (we'll filter after)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/shortages.json"
    
    # Fetch all shortages (API doesn't support date filtering)
    params = {"limit": limit}
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    raw_results = data.get("results", []) if isinstance(data, dict) else data
    
    if not raw_results:
        return {"success": True, "data": []}
    
    # MANUAL DATE FILTERING IN PYTHON
    # Calculate date range: Last 100 days from today
    end_date = datetime.now()  # TODAY (current system date)
    start_date = end_date - timedelta(days=100)  # 100 days ago
    
    print(f"Filtering drug shortages updated between {start_date.strftime('%m/%d/%Y')} and {end_date.strftime('%m/%d/%Y')}")
    
    # Filter results by update_date
    filtered_results = []
    for item in raw_results:
        update_date_str = item.get("update_date")  # Format: MM/DD/YYYY
        
        if not update_date_str:
            # Skip items without update_date
            continue
        
        try:
            # Parse MM/DD/YYYY format from API response
            update_date = datetime.strptime(update_date_str, "%m/%d/%Y")
            
            # Check if update_date falls within last 100 days
            if start_date <= update_date <= end_date:
                filtered_results.append(item)
        
        except ValueError:
            # Skip items with invalid date format
            print(f"Warning: Could not parse update_date '{update_date_str}'")
            continue
    
    if not filtered_results:
        return {"success": True, "data": []}
    
    print(f"Found {len(filtered_results)} shortages updated in last 100 days")
    
    
    clean_results = filter_drug_shortages_data(filtered_results)
    return {"success": True, "data": clean_results}

async def search_shortage_by_manufacturer(
    manufacturer: str,
    limit: int = 15
) -> dict:
    """
    Search drug shortages by manufacturer.
    
    Args:
        manufacturer: Manufacturer name
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    limit = min(max(1, limit), 100)
    url = f"{BASE_URL}/drug/shortages.json"
    
    params = {
        "search": f'company_name:"{manufacturer}"',
        "limit": limit
    }
    
    result = await make_fda_request(url, params)
    
    if not result["success"]:
        return result
    
    data = result["data"]
    raw_results = data.get("results", []) if isinstance(data, dict) else data
    
    if not raw_results:
        return {"success": True, "data": []}
    
    clean_results = filter_drug_shortages_data(raw_results)
    return {"success": True, "data": clean_results}


async def search_shortages_by_dosage_form(
    dosage_form: str,
    limit: int = 15
) -> dict:
    """
    Search drug shortages by dosage form.
    
    Uses: dosage_form field
    Example: "Capsule", "Tablet", "Injectable"
    
    Args:
        dosage_form: Product form type
        limit: Number of results (default 15, max 100)
    
    Returns:
        dict with 'success', 'data' or 'error' keys
    """
    return await search_drug_shortages(dosage_form=dosage_form, limit=limit)