# app/support/service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.db.mongo import get_database
from app.email.mailer import send_support_ticket_confirmation_email, send_support_ticket_response_email


def get_support_tickets_collection():
    """Get support tickets collection"""
    db = get_database()
    return db["support_tickets"]


async def create_support_ticket_service(data: dict):
    """Create a new support ticket"""
    tickets = get_support_tickets_collection()
    
    ticket_doc = {
        "name": data.get("name"),
        "email": data.get("email"),
        "subject": data.get("subject"),
        "category": data.get("category"),
        "message": data.get("message"),
        "userId": data.get("userId"),
        "status": "open",
        "createdAt": datetime.utcnow(),
        "updatedAt": None,
        "adminResponse": None,
        "respondedBy": None,
        "respondedAt": None,
    }
    
    result = await tickets.insert_one(ticket_doc)
    
    # Send confirmation email to user
    await send_support_ticket_confirmation_email(
        data.get("email"),
        data.get("name"),
        data.get("subject"),
        str(result.inserted_id)
    )
    
    return {"message": "Support ticket submitted successfully", "ticketId": str(result.inserted_id)}


async def get_all_support_tickets_service(skip: int = 0, limit: int = 50, status: str = None):
    """Get all support tickets with pagination"""
    tickets = get_support_tickets_collection()
    
    query = {}
    if status:
        query["status"] = status
    
    results = await tickets.find(query).sort("createdAt", -1).skip(skip).limit(limit).to_list(None)
    
    cleaned = []
    for ticket in results:
        ticket["id"] = str(ticket["_id"])
        del ticket["_id"]
        cleaned.append(ticket)
    
    total = await tickets.count_documents(query)
    
    return {"tickets": cleaned, "total": total}


async def get_user_support_tickets_service(user_id: str):
    """Get all support tickets for a specific user"""
    tickets = get_support_tickets_collection()
    
    results = await tickets.find({"userId": user_id}).sort("createdAt", -1).to_list(None)
    
    cleaned = []
    for ticket in results:
        ticket["id"] = str(ticket["_id"])
        del ticket["_id"]
        cleaned.append(ticket)
    
    return {"tickets": cleaned}


async def update_support_ticket_service(ticket_id: str, data: dict, current_admin: dict):
    """Update support ticket status and add admin response"""
    tickets = get_support_tickets_collection()
    
    update_data = {
        "updatedAt": datetime.utcnow(),
    }
    
    if data.get("status"):
        update_data["status"] = data.get("status")
    
    if data.get("adminResponse"):
        update_data["adminResponse"] = data.get("adminResponse")
        update_data["respondedBy"] = str(current_admin.get("_id", current_admin.get("id", "")))
        update_data["respondedAt"] = datetime.utcnow()
    
    result = await tickets.update_one(
        {"_id": ObjectId(ticket_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    
    # Get ticket details for email notification
    ticket = await tickets.find_one({"_id": ObjectId(ticket_id)})
    
    # Send response email to user if admin responded
    if data.get("adminResponse") and ticket:
        await send_support_ticket_response_email(
            ticket.get("email"),
            ticket.get("name"),
            ticket.get("subject"),
            data.get("adminResponse"),
            ticket_id
        )
    
    return {"message": "Support ticket updated successfully"}


async def delete_support_ticket_service(ticket_id: str):
    """Delete a support ticket"""
    tickets = get_support_tickets_collection()
    
    result = await tickets.delete_one({"_id": ObjectId(ticket_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Support ticket not found")
    
    return {"message": "Support ticket deleted successfully"}
