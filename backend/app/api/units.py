from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.unit import (
    UnitConvertRequest,
    UnitConvertResponse,
    SupportedUnitsResponse,
)
from backend.app.services.unit_conversion_service import (
    convert_quantity,
    SUPPORTED_UNITS_BY_CATEGORY,
    VALID_BASE_UNITS,
)

router = APIRouter(prefix="/units", tags=["Units"])


@router.post("/convert", response_model=UnitConvertResponse)
def convert_unit_endpoint(request: UnitConvertRequest):
    """Convert quantity between compatible measurement units with Decimal precision."""
    try:
        converted = convert_quantity(
            quantity=request.quantity,
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            packets_per_carton=request.packets_per_carton,
        )
        return UnitConvertResponse(
            original_quantity=str(request.quantity),
            converted_quantity=str(converted),
            from_unit=request.from_unit,
            to_unit=request.to_unit,
            packets_per_carton=request.packets_per_carton,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/supported", response_model=SupportedUnitsResponse)
def get_supported_units():
    """List all supported measurement units and standard base units."""
    categories = {cat: sorted(list(units)) for cat, units in SUPPORTED_UNITS_BY_CATEGORY.items()}
    return SupportedUnitsResponse(
        categories=categories,
        base_units=sorted(list(VALID_BASE_UNITS)),
    )
