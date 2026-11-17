from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def rupees_to_paise(rupees: Union[Decimal, float, str, int]) -> int:
    """Convert rupee value to exact integer paise using ROUND_HALF_UP."""
    dec = Decimal(str(rupees))
    paise = (dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(paise)


def paise_to_rupees(paise: int) -> Decimal:
    """Convert integer paise to exact rupee Decimal with 2 decimal places."""
    return (Decimal(paise) / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_inr(paise: int, include_symbol: bool = True) -> str:
    """Format paise into Indian numbering system currency string.
    
    Example:
        787500 paise -> '₹7,875.00'
        123456700 paise -> '₹12,34,567.00'
        -400000 paise -> '-₹4,000.00'
    """
    is_negative = paise < 0
    abs_paise = abs(paise)
    rupees_part = abs_paise // 100
    paise_part = abs_paise % 100
    
    s = str(rupees_part)
    if len(s) <= 3:
        formatted_rupees = s
    else:
        last_three = s[-3:]
        remaining = s[:-3]
        # Group remaining digits in pairs of two
        chunks = []
        while len(remaining) > 2:
            chunks.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            chunks.insert(0, remaining)
        formatted_rupees = ",".join(chunks) + "," + last_three

    formatted = f"{formatted_rupees}.{paise_part:02d}"
    if include_symbol:
        return f"-₹{formatted}" if is_negative else f"₹{formatted}"
    return f"-{formatted}" if is_negative else formatted
