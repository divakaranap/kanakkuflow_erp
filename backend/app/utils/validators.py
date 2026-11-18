import re
from typing import Optional

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
PHONE_REGEX = re.compile(r"^(\+91[\-\s]?)?[0]?[6789]\d{9}$")

INDIAN_STATE_CODES = {
    "Jammu and Kashmir": "01",
    "Himachal Pradesh": "02",
    "Punjab": "03",
    "Chandigarh": "04",
    "Uttarakhand": "05",
    "Haryana": "06",
    "Delhi": "07",
    "Rajasthan": "08",
    "Uttar Pradesh": "09",
    "Bihar": "10",
    "Sikkim": "11",
    "Arunachal Pradesh": "12",
    "Nagaland": "13",
    "Manipur": "14",
    "Mizoram": "15",
    "Tripura": "16",
    "Meghalaya": "17",
    "Assam": "18",
    "West Bengal": "19",
    "Jharkhand": "20",
    "Odisha": "21",
    "Chhattisgarh": "22",
    "Madhya Pradesh": "23",
    "Gujarat": "24",
    "Maharashtra": "27",
    "Andhra Pradesh": "37",
    "Karnataka": "29",
    "Goa": "30",
    "Kerala": "32",
    "Tamil Nadu": "33",
    "Puducherry": "34",
    "Telangana": "36",
}


def validate_gstin(gstin: Optional[str]) -> bool:
    """Validate Indian 15-character GSTIN format."""
    if not gstin:
        return False
    return bool(GSTIN_REGEX.match(gstin.strip().upper()))


def validate_phone(phone: Optional[str]) -> bool:
    """Validate Indian mobile / telephone numbers."""
    if not phone:
        return False
    clean = re.sub(r"[\s\-\(\)]", "", phone.strip())
    return bool(PHONE_REGEX.match(clean))


def get_state_code(state_name: str) -> Optional[str]:
    """Retrieve 2-digit GST state code for an Indian state."""
    return INDIAN_STATE_CODES.get(state_name.strip())
