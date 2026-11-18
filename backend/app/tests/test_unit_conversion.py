from decimal import Decimal
import pytest
from backend.app.services.unit_conversion_service import (
    convert_quantity,
    normalize_quantity,
    denormalize_quantity,
    validate_unit,
)


def test_weight_conversions():
    # 1000 g = 1 kg
    assert convert_quantity(1000, "g", "kg") == Decimal("1")
    # 2000 g = 2 kg
    assert convert_quantity("2000", "g", "kg") == Decimal("2")
    # 1.5 kg = 1500 g
    assert convert_quantity(Decimal("1.5"), "kg", "g") == Decimal("1500")


def test_volume_conversions():
    # 1000 ml = 1 litre
    assert convert_quantity(1000, "ml", "litre") == Decimal("1")
    # 0.5 litre = 500 ml
    assert convert_quantity("0.5", "litre", "ml") == Decimal("500")


def test_finished_goods_carton_conversions():
    # 200 packets with 20 packets_per_carton = 10 cartons
    assert convert_quantity(200, "packet", "carton", packets_per_carton=20) == Decimal("10")
    # 10 cartons with 20 packets_per_carton = 200 packets
    assert convert_quantity(10, "carton", "packet", packets_per_carton=20) == Decimal("200")


def test_missing_or_invalid_packets_per_carton():
    # Converting packet to carton without packets_per_carton must raise ValueError
    with pytest.raises(ValueError, match="requires valid positive packets_per_carton"):
        convert_quantity(100, "packet", "carton")

    with pytest.raises(ValueError, match="requires valid positive packets_per_carton"):
        convert_quantity(100, "carton", "packet", packets_per_carton=0)


def test_negative_quantity_rejected():
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        convert_quantity(-5, "kg", "g")


def test_unsupported_cross_category_conversions():
    # Cannot convert weight to volume or packaging
    with pytest.raises(ValueError, match="Unsupported unit conversion"):
        convert_quantity(10, "kg", "litre")

    with pytest.raises(ValueError, match="Unsupported unit conversion"):
        convert_quantity(10, "g", "packet")


def test_decimal_precision_preservation():
    # Test high precision without floating-point artifacts
    # 1.2345 kg -> g
    result = convert_quantity(Decimal("1.2345"), "kg", "g")
    assert result == Decimal("1234.5")
    # Normalize with 4 decimal places
    norm = normalize_quantity("1234.5", "g", "kg")
    assert norm == Decimal("1.2345")


def test_validate_unit():
    assert validate_unit("RAW_MATERIAL", "kg") is True
    assert validate_unit("RAW_MATERIAL", "litre") is True
    assert validate_unit("RAW_MATERIAL", "packet") is False

    assert validate_unit("PACKAGING", "piece") is True
    assert validate_unit("PACKAGING", "kg") is False

    assert validate_unit("FINISHED_GOODS", "packet") is True
    assert validate_unit("FINISHED_GOODS", "carton") is True


def test_unit_conversion_api_endpoints(client):
    # POST /units/convert
    res = client.post(
        "/units/convert",
        json={"quantity": "2000", "from_unit": "g", "to_unit": "kg"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["converted_quantity"] == "2"

    # POST /units/convert packet to carton
    res2 = client.post(
        "/units/convert",
        json={
            "quantity": "200",
            "from_unit": "packet",
            "to_unit": "carton",
            "packets_per_carton": 20,
        },
    )
    assert res2.status_code == 200
    assert res2.json()["converted_quantity"] == "10"

    # GET /units/supported
    res3 = client.get("/units/supported")
    assert res3.status_code == 200
    cat_data = res3.json()["categories"]
    assert "WEIGHT" in cat_data
    assert "VOLUME" in cat_data
