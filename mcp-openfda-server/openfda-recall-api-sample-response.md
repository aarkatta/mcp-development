# OpenFDA Drug Recall Enforcement API - Sample Response

## Endpoint

```
GET https://api.fda.gov/drug/enforcement.json
```

## Sample Raw API Response

```json
{
  "meta": {
    "disclaimer": "Do not rely on openFDA to make decisions regarding medical care. While we make every effort to ensure that data is accurate, you should assume all results are unvalidated. We may limit or otherwise restrict your access to the API in line with our Terms of Service.",
    "terms": "https://open.fda.gov/terms/",
    "license": "https://open.fda.gov/license/",
    "last_updated": "2026-01-28",
    "results": {
      "skip": 0,
      "limit": 10,
      "total": 209
    }
  },
  "results": [
    {
      "status": "Ongoing",
      "city": "Exton",
      "state": "PA",
      "country": "United States",
      "classification": "Class II",
      "openfda": {},
      "product_type": "Drugs",
      "event_id": "97808",
      "recalling_firm": "ProRx LLC",
      "address_1": "619 Jeffers Cir",
      "address_2": "N/A",
      "postal_code": "19341-2540",
      "voluntary_mandated": "Voluntary: Firm initiated",
      "initial_firm_notification": "Letter",
      "distribution_pattern": "TX and UT",
      "recall_number": "D-0115-2026",
      "product_description": "Semaglutide Injection, 10 mg/4 mL (2.5 mg/mL), 4mL Multidose Vial, For Subcutaneous Use, Rx Only, Mfd by: ProRx, 619 Jeffers Cir, Exton, PA 19341. NDC: 84139-225-04",
      "product_quantity": "8,400 vials",
      "reason_for_recall": "Lack of Assurance of Sterility",
      "recall_initiation_date": "20251015",
      "center_classification_date": "20251027",
      "report_date": "20251105",
      "code_info": "Lot, Best Use Date (BUD): Lot PRORX050925-1, BUD November 4, 2025; Lot ProRx051425-5, BUD November 10, 2025; Lot ProRx051425-6, BUD November 10, 2025"
    },
    {
      "status": "Ongoing",
      "city": "Albuquerque",
      "state": "NM",
      "country": "United States",
      "classification": "Class I",
      "openfda": {
        "brand_name": ["CLEARLIFE EXTRA STRENGTH"],
        "generic_name": ["ONION, GALPHIMIA GLAUCA FLOWERING TOP, HISTAMINE DIHYDROCHLORIDE, LUFFA OPERCULATA FRUIT, SULFUR, AMBROSIA ARTEMISIIFOLIA WHOLE, EUPHRASIA STRICTA AND SCHOENOCAULON OFFICINALE SEED"],
        "manufacturer_name": ["MediNatura Inc."],
        "product_ndc": ["62795-4006"],
        "product_type": ["HUMAN OTC DRUG"],
        "route": ["NASAL"],
        "substance_name": ["AMBROSIA ARTEMISIIFOLIA WHOLE", "EUPHRASIA STRICTA", "GALPHIMIA GLAUCA FLOWERING TOP", "HISTAMINE DIHYDROCHLORIDE", "LUFFA OPERCULATA FRUIT", "ONION", "SCHOENOCAULON OFFICINALE SEED", "SULFUR"],
        "spl_id": ["c5d30dbc-f317-4ff1-86b6-8d57bfb0da75"],
        "spl_set_id": ["09fbebf9-3d8b-479c-80f3-37f07cb699d6"],
        "package_ndc": ["62795-4006-9", "7876471018"],
        "is_original_packager": [true],
        "upc": ["0818204025725", "818204025725"],
        "unii": ["9W34L2CQ9A", "C9642I91WL"]
      },
      "product_type": "Drugs",
      "event_id": "98095",
      "recalling_firm": "Medinatura New Mexico, inc.",
      "address_1": "10421 Research Rd Se",
      "address_2": "",
      "postal_code": "87123-3423",
      "voluntary_mandated": "Voluntary: Firm initiated",
      "initial_firm_notification": "Two or more of the following: Email, Fax, Letter, Press Release, Telephone, Visit",
      "distribution_pattern": "Nationwide in the US",
      "recall_number": "D-0289-2026",
      "product_description": "ClearLife Allergy Nasal Spray, Extra Strength, 0.68 fl. oz. (20 mL) bottles, Distributed by: MediNatura, 10421 Research Rd., SE, Albuquerque, NM 87123, NDC 62795-4006-9, UPC 787647101887",
      "product_quantity": "",
      "reason_for_recall": "Microbial Contamination of Non-Sterile Products: The products have been found to contain yeast/mold and microbial contamination identified as Achromobacter.",
      "recall_initiation_date": "20251212",
      "center_classification_date": "20260115",
      "report_date": "20260114",
      "code_info": "All lots within expiry.",
      "more_code_info": ""
    },
    {
      "status": "Ongoing",
      "city": "Pennington",
      "state": "NJ",
      "country": "United States",
      "classification": "Class III",
      "openfda": {
        "application_number": ["ANDA205253"],
        "brand_name": ["TRAZODONE HYDROCHLORIDE"],
        "generic_name": ["TRAZODONE HYDROCHLORIDE"],
        "manufacturer_name": ["Zydus Pharmaceuticals USA Inc."],
        "product_ndc": ["68382-609", "68382-805", "68382-806", "68382-807", "68382-808", "68382-610"],
        "product_type": ["HUMAN PRESCRIPTION DRUG"],
        "route": ["ORAL"],
        "substance_name": ["TRAZODONE HYDROCHLORIDE"],
        "rxcui": ["856364", "856369", "856373", "856377"],
        "spl_id": ["24cb2e4c-a9ba-4283-8396-343f6aa03121"],
        "spl_set_id": ["704aebf9-2fff-4ef3-8323-9ff0d7f0ffd9"],
        "package_ndc": ["68382-805-01", "68382-805-30", "68382-805-77"],
        "is_original_packager": [true],
        "unii": ["6E8ZO8LRNM"]
      },
      "product_type": "Drugs",
      "event_id": "98184",
      "recalling_firm": "Zydus Pharmaceuticals (USA) Inc",
      "address_1": "73 Route 31 N",
      "address_2": "N/A",
      "postal_code": "08534-3601",
      "voluntary_mandated": "Voluntary: Firm initiated",
      "initial_firm_notification": "Letter",
      "distribution_pattern": "Nationwide in the USA",
      "recall_number": "D-0247-2026",
      "product_description": "traZODONE Hydrochloride Tablets, USP, 100mg, 1,000 Tablets, Rx only",
      "product_quantity": "2,136 1000-count bottles",
      "reason_for_recall": "Failed Tablet/Capsule Specifications: Product complaint received that some tablets had a dent on the plain side of the tablet surface.",
      "recall_initiation_date": "20251219",
      "center_classification_date": "20251231",
      "report_date": "20260107",
      "code_info": "Lot # EA00237A, Exp Date: 04/30/2027"
    }
  ]
}
```

## Cleaned/Normalized Response Structure

After processing, each recall record is normalized to this shape:

```json
{
  "recall_number": "D-0289-2026",
  "event_id": "98095",
  "report_date": "20260114",
  "classification_date": "20260115",
  "classification": "Class I",
  "status": "Ongoing",
  "termination_date": null,
  "product": {
    "description": "ClearLife Allergy Nasal Spray, Extra Strength, 0.68 fl. oz. (20 mL) bottles",
    "type": "Drugs",
    "quantity": "",
    "codes": "All lots within expiry."
  },
  "recall_reason": "Microbial Contamination of Non-Sterile Products: The products have been found to contain yeast/mold and microbial contamination identified as Achromobacter.",
  "distribution": "Nationwide in the US",
  "voluntary_mandated": "Voluntary: Firm initiated",
  "recalling_firm": "Medinatura New Mexico, inc.",
  "location": {
    "city": "Albuquerque",
    "state": "NM",
    "country": "United States",
    "address": "10421 Research Rd Se"
  },
  "recall_initiation_date": "20251212"
}
```

## Key Fields Reference

| Field | Type | Description |
|---|---|---|
| `recall_number` | string | Unique recall identifier (e.g., `D-0289-2026`) |
| `event_id` | string | FDA event ID grouping related recalls |
| `classification` | string | Severity: `Class I` (most serious), `Class II`, `Class III` (least serious) |
| `status` | string | `Ongoing`, `Completed`, or `Terminated` |
| `product_type` | string | Always `"Drugs"` for this endpoint |
| `reason_for_recall` | string | Free-text description of the recall reason |
| `recall_initiation_date` | string | Date format: `YYYYMMDD` |
| `report_date` | string | Date format: `YYYYMMDD` |
| `center_classification_date` | string | Date format: `YYYYMMDD` |
| `distribution_pattern` | string | Geographic distribution (e.g., `"Nationwide in the US"`, `"TX and UT"`) |
| `voluntary_mandated` | string | Whether recall was voluntary or FDA-mandated |
| `openfda` | object | Enriched drug data (may be empty `{}` for compounded drugs) |

## Classification Definitions

- **Class I** — Dangerous or defective products that could cause serious health problems or death.
- **Class II** — Products that might cause a temporary health problem or pose a slight threat of a serious nature.
- **Class III** — Products that are unlikely to cause any adverse health reaction but violate FDA regulations.

## Common `reason_for_recall` Categories

- `Lack of Assurance of Sterility`
- `CGMP Deviations` (including insanitary conditions)
- `Microbial Contamination of Non-Sterile Products`
- `Failed Tablet/Capsule Specifications`
- `Cross Contamination with Other Products`
- `cGMP deviations`

## Notes

- The `openfda` object is **empty** for compounded pharmacy products (e.g., compounded semaglutide from ProRx LLC) but populated for commercially manufactured drugs.
- Date fields use `YYYYMMDD` string format — parse accordingly.
- `product_quantity` may be an empty string when quantity is not reported.
- `more_code_info` is an optional field, not always present in every record.
- Pagination is controlled via `meta.results.skip` and `meta.results.limit` (max 1000 per request). Use `skip` parameter to paginate through results.
