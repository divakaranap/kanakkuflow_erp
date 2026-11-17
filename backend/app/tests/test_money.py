from decimal import Decimal
from backend.app.utils.money import format_inr, rupees_to_paise, paise_to_rupees


def test_rupees_to_paise_and_back():
    # Benchmark requirement: ₹7,875 = 787500 paise
    paise = rupees_to_paise("7875.00")
    assert paise == 787500
    assert paise_to_rupees(paise) == Decimal("7875.00")

    # Rounding check
    assert rupees_to_paise(Decimal("187.50")) == 18750
    assert rupees_to_paise(Decimal("31.1436")) == 3114


def test_format_inr():
    assert format_inr(787500) == "₹7,875.00"
    assert format_inr(18750) == "₹187.50"
    assert format_inr(5000) == "₹50.00"
    assert format_inr(123456700) == "₹12,34,567.00"
    assert format_inr(0) == "₹0.00"
    assert format_inr(-400000) == "-₹4,000.00"
