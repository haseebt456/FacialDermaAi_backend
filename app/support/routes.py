# app/support/routes.py
from fastapi import APIRouter, Depends
from typing import Optional, List
from .schemas import SupportTicketCreate, SupportTicketResponse, SupportTicketUpdate
from .service import (
    create_support_ticket_service,
    get_all_support_tickets_service,
    get_user_support_tickets_service,
    update_support_ticket_service,
    delete_support_ticket_service
)
from app.deps.auth import get_current_user, get_optional_current_user
from app.admin.deps import get_current_admin_user

router = APIRouter(prefix="/api/support", tags=["Support"])


@router.post("/tickets")
async def create_support_ticket(
    ticket: SupportTicketCreate,
    current_user: dict = Depends(get_optional_current_user)
):
    """Create a new support ticket (public endpoint, authentication optional)"""
    ticket_data = ticket.dict()
    
    # If user is authenticated, attach their user ID
    if current_user:
        ticket_data["userId"] = str(current_user.get("_id", current_user.get("id", "")))
    
    return await create_support_ticket_service(ticket_data)


@router.get("/tickets/my", response_model=dict)
async def get_my_support_tickets(current_user: dict = Depends(get_current_user)):
    """Get all support tickets for the current user"""
    user_id = str(current_user.get("_id", current_user.get("id", "")))
    return await get_user_support_tickets_service(user_id)


@router.get("/tickets", response_model=dict)
async def get_all_support_tickets(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Get all support tickets (admin only)"""
    return await get_all_support_tickets_service(skip, limit, status)


@router.put("/tickets/{ticket_id}")
async def update_support_ticket(
    ticket_id: str,
    update_data: SupportTicketUpdate,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Update support ticket status and add admin response (admin only)"""
    return await update_support_ticket_service(ticket_id, update_data.dict(exclude_none=True), current_admin)


@router.delete("/tickets/{ticket_id}")
async def delete_support_ticket(
    ticket_id: str,
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete a support ticket (admin only)"""
    return await delete_support_ticket_service(ticket_id)
