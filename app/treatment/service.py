from app.db.mongo import get_treatment_suggestions_collection
from app.treatment.schemas import (
    TreatmentSuggestionCreate,
    TreatmentSuggestionUpdate,
    TreatmentSuggestionInDB,
    TreatmentSuggestionResponse
)
from bson import ObjectId
from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


async def get_treatment_suggestion_by_name(name: str) -> Optional[TreatmentSuggestionInDB]:
    """Get a treatment suggestion by name"""
    collection = get_treatment_suggestions_collection()
    doc = await collection.find_one({"name": name})
    if doc:
        # Convert ObjectId to string for Pydantic
        doc["id"] = str(doc.pop("_id"))
        return TreatmentSuggestionInDB(**doc)
    return None


async def get_all_treatment_suggestions() -> List[TreatmentSuggestionInDB]:
    """Get all treatment suggestions"""
    collection = get_treatment_suggestions_collection()
    cursor = collection.find({})
    suggestions = []
    async for doc in cursor:
        # Convert ObjectId to string for Pydantic
        doc["id"] = str(doc.pop("_id"))
        suggestions.append(TreatmentSuggestionInDB(**doc))
    return suggestions


async def create_treatment_suggestion(suggestion: TreatmentSuggestionCreate) -> TreatmentSuggestionInDB:
    """Create a new treatment suggestion"""
    collection = get_treatment_suggestions_collection()
    
    # Check if name already exists
    existing = await get_treatment_suggestion_by_name(suggestion.name)
    if existing:
        raise ValueError(f"Treatment suggestion with name '{suggestion.name}' already exists")
    
    doc = suggestion.dict()
    doc["_id"] = ObjectId()
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    
    result = await collection.insert_one(doc)
    logger.info(f"Created treatment suggestion: {suggestion.name}")
    
    # Convert ObjectId to string for Pydantic
    doc["id"] = str(doc.pop("_id"))
    return TreatmentSuggestionInDB(**doc)


async def update_treatment_suggestion(name: str, update_data: TreatmentSuggestionUpdate) -> Optional[TreatmentSuggestionInDB]:
    """Update a treatment suggestion by name"""
    collection = get_treatment_suggestions_collection()
    
    update_dict = update_data.dict(exclude_unset=True)
    if not update_dict:
        return None
    
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await collection.update_one(
        {"name": name},
        {"$set": update_dict}
    )
    
    if result.modified_count == 0:
        return None
    
    # Return updated document
    updated_doc = await collection.find_one({"name": name})
    if updated_doc:
        logger.info(f"Updated treatment suggestion: {name}")
        # Convert ObjectId to string for Pydantic
        updated_doc["id"] = str(updated_doc.pop("_id"))
        return TreatmentSuggestionInDB(**updated_doc)
    return None


async def delete_treatment_suggestion(name: str) -> bool:
    """Delete a treatment suggestion by name"""
    collection = get_treatment_suggestions_collection()
    
    result = await collection.delete_one({"name": name})
    if result.deleted_count > 0:
        logger.info(f"Deleted treatment suggestion: {name}")
        return True
    return False
