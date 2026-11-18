import re
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional
from backend.app.config import settings

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

# Indian state codes dictionary
STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "27": "Maharashtra",
    "29": "Karnataka",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "36": "Telangana",
    "37": "Andhra Pradesh",
}

DEFAULT_SELLER_STATE_CODE = "33"  # Tamil Nadu


def validate_gstin(gstin: Optional[str]) -> bool:
    """Validate 15-character Indian Goods and Services Tax Identification Number."""
    if not gstin:
        return False
    clean = gstin.strip().upper()
    if len(clean) != 15:
        return False
    return bool(GSTIN_REGEX.match(clean))


def get_place_of_supply(state_code_or_gstin: str) -> str:
    """Extract or return 2-digit place of supply state code."""
    if not state_code_or_gstin:
        return DEFAULT_SELLER_STATE_CODE
    clean = state_code_or_gstin.strip().upper()
    if len(clean) == 15 and clean[:2].isdigit():
        return clean[:2]
    if len(clean) == 2 and clean.isdigit():
        return clean
    # Fallback to pad single digit
    if len(clean) == 1 and clean.isdigit():
        return f"0{clean}"
    return DEFAULT_SELLER_STATE_CODE


def determine_tax_type(
    seller_state_code: str,
    place_of_supply_state_code: str,
) -> str:
    """
    Determine if sale is INTRA_STATE (CGST + SGST) or INTER_STATE (IGST).
    Intra-state: place_of_supply == seller_state_code.
    Inter-state: place_of_supply != seller_state_code.
    """
    seller = seller_state_code.strip()
    pos = place_of_supply_state_code.strip()
    return "INTRA_STATE" if seller == pos else "INTER_STATE"


def calculate_cgst_sgst(
    taxable_amount_paise: int,
    gst_rate: Decimal,
) -> Tuple[int, int]:
    """
    Calculate equal CGST and SGST for intra-state sale.
    gst_rate is percentage (e.g. Decimal('5.00') for 5%).
    Half rate applies to CGST and half to SGST.
    """
    if taxable_amount_paise <= 0 or gst_rate <= 0:
        return 0, 0
    half_rate = gst_rate / Decimal("2")
    # round half up to nearest integer paise
    tax_paise = int(round(Decimal(taxable_amount_paise) * half_rate / Decimal("100")))
    return tax_paise, tax_paise


def calculate_igst(
    taxable_amount_paise: int,
    gst_rate: Decimal,
) -> int:
    """
    Calculate IGST for inter-state sale.
    gst_rate is percentage (e.g. Decimal('5.00') for 5%).
    """
    if taxable_amount_paise <= 0 or gst_rate <= 0:
        return 0
    return int(round(Decimal(taxable_amount_paise) * gst_rate / Decimal("100")))


def calculate_gst(
    taxable_amount_paise: int,
    gst_rate: Decimal,
    place_of_supply_state_code: str,
    seller_state_code: str = DEFAULT_SELLER_STATE_CODE,
) -> Dict[str, Any]:
    """
    Comprehensive GST calculation engine conforming to Indian GST rules.
    - Intra-state (e.g. Tamil Nadu -> Tamil Nadu): CGST + SGST, IGST = 0
    - Inter-state (e.g. Tamil Nadu -> Karnataka): IGST, CGST = 0, SGST = 0
    All monetary amounts returned in integer paise.
    """
    tax_type = determine_tax_type(seller_state_code, place_of_supply_state_code)

    if tax_type == "INTRA_STATE":
        cgst_paise, sgst_paise = calculate_cgst_sgst(taxable_amount_paise, gst_rate)
        igst_paise = 0
    else:
        cgst_paise = 0
        sgst_paise = 0
        igst_paise = calculate_igst(taxable_amount_paise, gst_rate)

    total_tax_paise = cgst_paise + sgst_paise + igst_paise
    grand_total_paise = taxable_amount_paise + total_tax_paise

    return {
        "tax_type": tax_type,
        "seller_state_code": seller_state_code,
        "place_of_supply_state_code": place_of_supply_state_code,
        "gst_rate": gst_rate,
        "taxable_amount_paise": taxable_amount_paise,
        "cgst_paise": cgst_paise,
        "sgst_paise": sgst_paise,
        "igst_paise": igst_paise,
        "total_tax_paise": total_tax_paise,
        "grand_total_paise": grand_total_paise,
    }
