"""
OpenFDA FastMCP Server

Exposes four FDA drug data endpoints through MCP tools:
1. Adverse Events - Patient safety reports
2. Product Labeling - Prescribing information
3. Recall Enforcement - Drug recalls and enforcement actions
4. Drug Shortages - Supply availability

All tools return optimized JSON responses (60-80% token reduction vs raw API).
"""

from fastmcp import FastMCP
import json
import openfda_api

mcp = FastMCP("OpenFDA Remote Server")


# ============================================================================
# ADVERSE EVENTS ENDPOINT
# ============================================================================

@mcp.tool()
async def search_adverse_events(
    drug_name: str = None,
    reaction: str = None,
    serious: bool = False,
    limit: int = 15
) -> str:
    """
    Search FDA adverse event reports for patient safety data.
    
    Returns: Patient reactions (MedDRA terms), severity, drug administration details
    
    Use this when user asks about:
    - Side effects or adverse reactions to a drug
    - Safety concerns or patient experiences
    - Serious adverse events (deaths, hospitalizations)
    - Specific reaction types (e.g., "Does Aspirin cause bleeding?")
    
    Args:
        drug_name: The drug name (brand or generic, e.g., "Lisinopril", "Zocor")
        reaction: MedDRA reaction term (e.g., "Hypotension", "Cough"). Optional.
        serious: Filter for serious events only (deaths, life-threatening). Default False.
        limit: Number of results (default 15, max 100)
    
    Returns JSON with:
    - report_id, is_serious, seriousness_types
    - reactions: [meddra_term, outcome]
    - drugs: [product_name, route, indication]
    - patient_info: [age_group, gender]
    """
    result = await openfda_api.search_adverse_events(drug_name, reaction, serious, limit)
    
    if not result["success"]:
        return f"Error searching adverse events: {result['error']}"
    
    if not result["data"]:
        return f"No adverse event reports found for {drug_name or 'that query'}."
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_serious_adverse_events(limit: int = 50) -> str:
    """
    Get recent serious adverse events (deaths, life-threatening, hospitalizations).
    
    Returns only events marked as serious in the FDA database.
    
    Use this when user asks about:
    - Recent serious side effects or adverse events
    - Deaths or hospitalizations associated with drugs
    - Life-threatening complications
    - High-severity patient safety issues
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns JSON with serious adverse events sorted by date received.
    """
    result = await openfda_api.get_serious_adverse_events(limit)
    
    if not result["success"]:
        return f"Error retrieving serious adverse events: {result['error']}"
    
    if not result["data"]:
        return "No recent serious adverse events found."
    
    return json.dumps(result["data"], indent=2)


# ============================================================================
# PRODUCT LABELING ENDPOINT
# ============================================================================

@mcp.tool()
async def get_drug_label(drug_name: str, limit: int = 1) -> str:
    """
    Get official FDA drug label information.
    
    Returns: Brand/generic name, manufacturer, indications, warnings, contraindications, dosage, active ingredients
    
    Use this when user asks about:
    - What a drug is used for (indications/purpose)
    - How to take the drug (dosage instructions)
    - Drug warnings, side effects, or contraindications
    - Ingredients or drug interactions
    - Pregnancy/pediatric/geriatric safety
    - Black box warnings or precautions
    
    Args:
        drug_name: The drug name (brand or generic, e.g., "Lipitor", "atorvastatin")
        limit: Number of label versions to return (default 1, max 100)
    
    Returns JSON with:
    - brand_name, generic_name, manufacturer
    - indication, warnings_summary, contraindications
    - adverse_reactions_summary, active_ingredients, dosage
    - rxcui, application_number
    """
    result = await openfda_api.get_drug_label(drug_name, limit)
    
    if not result["success"]:
        return f"Error retrieving drug label: {result['error']}"
    
    if not result["data"]:
        return f"No label information found for: {drug_name}"
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def search_drug_labels(
    search_term: str = None,
    manufacturer: str = None,
    limit: int = 15
) -> str:
    """
    Search drug labels by content or manufacturer.
    
    Use this when user asks about:
    - Drugs with specific side effects or reactions
    - Drugs from a specific manufacturer
    - Drugs for a particular indication (e.g., "blood pressure medications")
    - Drugs with certain warnings or contraindications
    
    Args:
        search_term: Text to search in label content (e.g., "cough", "hypertension")
        manufacturer: Filter by manufacturer name (e.g., "Pfizer", "Merck")
        limit: Number of results (default 15, max 100)
    
    Returns JSON with matching drug labels and their details.
    """
    result = await openfda_api.search_drug_labels(search_term, manufacturer, limit)
    
    if not result["success"]:
        return f"Error searching drug labels: {result['error']}"
    
    if not result["data"]:
        return f"No drug labels found matching: {search_term or manufacturer}"
    
    return json.dumps(result["data"], indent=2)


# ============================================================================
# RECALL ENFORCEMENT ENDPOINT
# ============================================================================

@mcp.tool()
async def search_recalls(
    term: str = None,
    risk_level: str = None,
    limit: int = 15
) -> str:
    """
    Search for drug recall enforcement reports.
    
    Returns: Recall number, classification, status, affected products, reason, company
    
    Use this when user asks about:
    - Drug recalls or enforcement actions
    - Product quality issues or safety concerns
    - Recalled batches or lot numbers
    - Specific company recalls
    
    Args:
        term: Drug name, company, or product (e.g., "Tylenol", "Pfizer", "Aspirin")
        risk_level: Filter by severity:
            - "Class I": Most serious, risk of serious health consequences or death
            - "Class II": Temporary health problems or reversible adverse reaction
            - "Class III": Minor violations, unlikely to cause harm
        limit: Number of results (default 15, max 100)
    
    Returns JSON with:
    - recall_number, classification (Class I/II/III), status
    - product: [description, quantity, codes/lot numbers]
    - recall_reason, distribution_pattern, recalling_firm
    - location: [city, state, country]
    - recall_initiation_date
    """
    result = await openfda_api.search_recalls(term, risk_level, limit)
    
    if not result["success"]:
        return f"Error searching recalls: {result['error']}"
    
    if not result["data"]:
        return f"No recalls found for: {term or 'that query'}"
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_recent_drug_recalls(limit: int = 50) -> str:
    """
    Get the most recent drug recalls (last 100 days) sorted by report date.
    
    Use this when user asks about:
    - Recent drug recalls or enforcement actions
    - Latest safety concerns or product issues
    - Current recall status
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns JSON with recent recalls sorted by date, newest first.
    """
    result = await openfda_api.get_recent_drug_recalls(limit)
    
    if not result["success"]:
        return f"Error retrieving recent recalls: {result['error']}"
    
    if not result["data"]:
        return "No recent recalls found."
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_recalls_by_classification(classification: str, limit: int = 15) -> str:
    """
    Get drug recalls filtered by risk classification level.
    
    Use this when user asks about:
    - Critical/Class I recalls (deaths, serious harm)
    - Class II recalls (temporary problems)
    - Class III recalls (minor violations)
    - All recalls of a specific severity level
    
    Args:
        classification: Risk level - must be one of:
            - "Class I": Serious health consequences or death
            - "Class II": Temporary or reversible health problems
            - "Class III": Minor violations, unlikely to cause harm
        limit: Number of results (default 15, max 100)
    
    Returns JSON with recalls of the specified classification.
    """
    result = await openfda_api.get_recalls_by_classification(classification, limit)
    
    if not result["success"]:
        return f"Error retrieving recalls: {result['error']}"
    
    if not result["data"]:
        return f"No {classification} recalls found."
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_critical_recalls(limit: int = 50) -> str:
    """
    Get critical Class I recalls (highest risk).
    
    Class I recalls involve risk of serious health consequences or death.
    
    Use this when user asks about:
    - Most serious drug recalls
    - Recalls with risk of death
    - Life-threatening product issues
    - Critical safety enforcement actions
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns JSON with Class I (critical) recalls only.
    """
    result = await openfda_api.get_critical_recalls(limit)
    
    if not result["success"]:
        return f"Error retrieving critical recalls: {result['error']}"
    
    if not result["data"]:
        return "No Class I (critical) recalls found."
    
    return json.dumps(result["data"], indent=2)


# ============================================================================
# DRUG SHORTAGES ENDPOINT
# ============================================================================

@mcp.tool()
async def search_drug_shortages(
    term: str = None,
    availability: str = None,
    limit: int = 15
) -> str:
    """
    Search for drug shortages and supply availability.
    
    Returns: Drug name, manufacturer, availability status, shortage reason, contact info, NDC codes
    
    Use this when user asks about:
    - Drug availability or shortages
    - Supply status of a medication
    - Which drugs are in short supply
    - Where to obtain a medication
    - Alternative sources or contact information
    
    Args:
        term: Drug name (generic or brand, e.g., "insulin", "Pfizer"), or manufacturer
        availability: Filter by status (e.g., "Available", "Shortage", "Resolved", "Discontinued")
        limit: Number of results (default 15, max 100)
    
    Returns JSON with:
    - generic_name, brand_name, update_type
    - availability_status, shortage_reason
    - manufacturer, contact_info
    - product_details: [ndc, route, strength, presentation]
    - last_updated
    """
    result = await openfda_api.search_drug_shortages(term, availability, limit)
    
    if not result["success"]:
        return f"Error searching shortages: {result['error']}"
    
    if not result["data"]:
        return f"No shortages found for: {term or 'that query'}"
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def get_current_drug_shortages(limit: int = 50) -> str:
    """
    Get all currently active drug shortages.
    
    Returns current supply availability status for drugs.
    
    Use this when user asks about:
    - Current drug shortages
    - What drugs are unavailable right now
    - Real-time supply status
    - Recent supply disruptions
    
    Args:
        limit: Number of results (default 50, max 100)
    
    Returns JSON with all active shortage records.
    """
    result = await openfda_api.get_current_drug_shortages(limit)
    
    if not result["success"]:
        return f"Error retrieving shortages: {result['error']}"
    
    if not result["data"]:
        return "No current drug shortages found."
    
    return json.dumps(result["data"], indent=2)


@mcp.tool()
async def search_shortages_by_manufacturer(manufacturer: str, limit: int = 15) -> str:
    """
    Search drug shortages by manufacturer.
    
    Use this when user asks about:
    - Shortages from a specific company (e.g., "Does Pfizer have any shortages?")
    - All affected drugs from a manufacturer
    - Supply status of a company's products
    
    Args:
        manufacturer: Manufacturer name (e.g., "Pfizer", "Johnson & Johnson", "Merck")
        limit: Number of results (default 15, max 100)
    
    Returns JSON with shortage records for the specified manufacturer.
    """
    result = await openfda_api.search_shortage_by_manufacturer(manufacturer, limit)
    
    if not result["success"]:
        return f"Error searching shortages: {result['error']}"
    
    if not result["data"]:
        return f"No shortages found for manufacturer: {manufacturer}"
    
    return json.dumps(result["data"], indent=2)


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)