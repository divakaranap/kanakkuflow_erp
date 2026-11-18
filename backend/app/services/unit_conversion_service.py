"""Unit Conversion Service for FACTORYFLOW ERP.

Handles high-precision quantity conversions across Weight, Volume, Packaging, and Cartons.
All conversions strictly use Python Decimal with ZERO floating-point drift.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, Dict, Set


# Precision definitions
DECIMAL_QUANTITY_PLACES = Decimal("0.0001")  # 4 decimal places for base inventory NUMERIC(14,4)

SUPPORTED_UNITS_BY_CATEGORY: Dict[str, Set[str]] = {
    "WEIGHT": {"kg", "g"},
    "VOLUME": {"litre", "l", "ml"},
    "PACKAGING": {"piece", "pc", "pieces"},
    "FINISHED_GOODS": {"packet", "carton"},
}

VALID_BASE_UNITS = {"kg", "litre", "piece", "packet"}


def to_decimal(val: Union[Decimal, float, int, str]) -> Decimal:
    """Safely convert any input value to Decimal."""
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def validate_unit(item_type: str, unit: str) -> bool:
    """Validate whether a unit is valid for the given item type.
    
    item_type can be: 'RAW_MATERIAL', 'PACKAGING', 'FINISHED_GOODS', 'PRODUCT', 'WEIGHT', 'VOLUME'
    """
    u = unit.lower().strip()
    item_type_upper = item_type.upper().strip()
    
    if item_type_upper in ["RAW_MATERIAL", "MATERIAL"]:
        return u in SUPPORTED_UNITS_BY_CATEGORY["WEIGHT"] or u in SUPPORTED_UNITS_BY_CATEGORY["VOLUME"]
    elif item_type_upper in ["PACKAGING", "PACKAGING_ITEM"]:
        return u in SUPPORTED_UNITS_BY_CATEGORY["PACKAGING"]
    elif item_type_upper in ["PRODUCT", "FINISHED_GOODS"]:
        return u in SUPPORTED_UNITS_BY_CATEGORY["FINISHED_GOODS"]
    elif item_type_upper in SUPPORTED_UNITS_BY_CATEGORY:
        return u in SUPPORTED_UNITS_BY_CATEGORY[item_type_upper]
    
    # Generic check across all supported units
    for units in SUPPORTED_UNITS_BY_CATEGORY.values():
        if u in units:
            return True
    return False


def normalize_unit_name(unit: str) -> str:
    """Normalize unit aliases to standard names."""
    u = unit.lower().strip()
    if u in ["kg", "kilogram", "kgs"]:
        return "kg"
    if u in ["g", "gram", "grams", "gm"]:
        return "g"
    if u in ["litre", "l", "liter", "litres", "liters"]:
        return "litre"
    if u in ["ml", "millilitre", "milliliter"]:
        return "ml"
    if u in ["piece", "pc", "pieces", "pcs"]:
        return "piece"
    if u in ["packet", "packets", "pkt", "pkts"]:
        return "packet"
    if u in ["carton", "cartons", "box", "boxes", "ctn"]:
        return "carton"
    return u


def convert_quantity(
    quantity: Union[Decimal, float, int, str],
    from_unit: str,
    to_unit: str,
    packets_per_carton: Optional[int] = None,
) -> Decimal:
    """Convert quantity from one unit to another using Decimal math.
    
    Raises:
        ValueError: If quantity < 0, units are incompatible, or carton conversion lacks packets_per_carton.
    """
    qty = to_decimal(quantity)
    if qty < 0:
        raise ValueError(f"Quantity cannot be negative: {qty}")
    
    f_unit = normalize_unit_name(from_unit)
    t_unit = normalize_unit_name(to_unit)
    
    if f_unit == t_unit:
        return qty

    # Weight conversions
    if f_unit == "g" and t_unit == "kg":
        return qty / Decimal("1000")
    if f_unit == "kg" and t_unit == "g":
        return qty * Decimal("1000")

    # Volume conversions
    if f_unit == "ml" and t_unit == "litre":
        return qty / Decimal("1000")
    if f_unit == "litre" and t_unit == "ml":
        return qty * Decimal("1000")

    # Packaging (piece to piece)
    if f_unit == "piece" and t_unit == "piece":
        return qty

    # Finished goods (packet to carton / carton to packet)
    if (f_unit == "packet" and t_unit == "carton") or (f_unit == "carton" and t_unit == "packet"):
        if not packets_per_carton or packets_per_carton <= 0:
            raise ValueError(
                f"Conversion between '{f_unit}' and '{t_unit}' requires valid positive packets_per_carton"
            )
        rate = Decimal(str(packets_per_carton))
        if f_unit == "packet" and t_unit == "carton":
            return qty / rate
        else:
            return qty * rate

    raise ValueError(f"Unsupported unit conversion from '{from_unit}' to '{to_unit}'")


def normalize_quantity(
    quantity: Union[Decimal, float, int, str],
    unit: str,
    base_unit: str,
    packets_per_carton: Optional[int] = None,
) -> Decimal:
    """Convert a transactional unit quantity to the item's standard base unit."""
    converted = convert_quantity(quantity, unit, base_unit, packets_per_carton)
    return converted.quantize(DECIMAL_QUANTITY_PLACES, rounding=ROUND_HALF_UP)


def denormalize_quantity(
    quantity: Union[Decimal, float, int, str],
    base_unit: str,
    target_unit: str,
    packets_per_carton: Optional[int] = None,
) -> Decimal:
    """Convert a base unit quantity to a target display/transactional unit."""
    return convert_quantity(quantity, base_unit, target_unit, packets_per_carton)
