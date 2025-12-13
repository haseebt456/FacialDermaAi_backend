from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.treatment.schemas import (
    TreatmentSuggestionCreate,
    TreatmentSuggestionUpdate,
    TreatmentSuggestionResponse
)
from app.treatment.service import (
    get_treatment_suggestion_by_name,
    get_all_treatment_suggestions,
    create_treatment_suggestion,
    update_treatment_suggestion,
    delete_treatment_suggestion
)
from app.deps.auth import require_role
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/treatment", tags=["treatment"])


@router.get("/suggestions", response_model=List[TreatmentSuggestionResponse])
async def get_treatment_suggestions():
    """Get all treatment suggestions (public access for analysis)"""
    try:
        suggestions = await get_all_treatment_suggestions()
        return [TreatmentSuggestionResponse(**suggestion.dict()) for suggestion in suggestions]
    except Exception as e:
        logger.error(f"Error getting treatment suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve treatment suggestions"
        )


@router.get("/suggestions/{name}", response_model=TreatmentSuggestionResponse)
async def get_treatment_suggestion(name: str):
    """Get a specific treatment suggestion by name (public access)"""
    try:
        suggestion = await get_treatment_suggestion_by_name(name)
        if not suggestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Treatment suggestion for '{name}' not found"
            )
        return TreatmentSuggestionResponse(**suggestion.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting treatment suggestion '{name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve treatment suggestion"
        )


@router.post("/suggestions", response_model=TreatmentSuggestionResponse, dependencies=[Depends(require_role("admin"))])
async def create_suggestion(suggestion: TreatmentSuggestionCreate):
    """Create a new treatment suggestion (admin only)"""
    try:
        new_suggestion = await create_treatment_suggestion(suggestion)
        return TreatmentSuggestionResponse(**new_suggestion.dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating treatment suggestion: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create treatment suggestion"
        )


@router.put("/suggestions/{name}", response_model=TreatmentSuggestionResponse, dependencies=[Depends(require_role("admin"))])
async def update_suggestion(name: str, update_data: TreatmentSuggestionUpdate):
    """Update a treatment suggestion (admin only)"""
    try:
        updated_suggestion = await update_treatment_suggestion(name, update_data)
        if not updated_suggestion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Treatment suggestion for '{name}' not found"
            )
        return TreatmentSuggestionResponse(**updated_suggestion.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating treatment suggestion '{name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update treatment suggestion"
        )


@router.delete("/suggestions/{name}", dependencies=[Depends(require_role("admin"))])
async def delete_suggestion(name: str):
    """Delete a treatment suggestion (admin only)"""
    try:
        deleted = await delete_treatment_suggestion(name)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Treatment suggestion for '{name}' not found"
            )
        return {"message": f"Treatment suggestion for '{name}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting treatment suggestion '{name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete treatment suggestion"
        )
