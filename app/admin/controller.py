# app/admin/controller.py
from fastapi import Depends, Body
from typing import Optional
from .deps import get_current_admin_user
from .schemas import DermatologistVerificationRequest
from .service import (
    get_admin_stats,
    get_pending_verifications_service,
    get_rejected_verifications_service,
    verify_dermatologist_service,
    get_all_users_service,
    suspend_user_service,
    unsuspend_user_service,
    delete_user_service,
    update_admin_profile_service,
    change_password_service
)

async def dashboard_stats_controller(current_admin=Depends(get_current_admin_user)):
    return await get_admin_stats()

async def pending_verifications_controller(current_admin=Depends(get_current_admin_user)):
    return await get_pending_verifications_service()

async def rejected_verifications_controller(current_admin=Depends(get_current_admin_user)):
    return await get_rejected_verifications_service()

async def verify_dermatologist_controller(
    dermatologist_id: str,
    data: DermatologistVerificationRequest,
    current_admin=Depends(get_current_admin_user)
):
    return await verify_dermatologist_service(dermatologist_id, data.dict(), current_admin)

async def get_users_controller(
    skip: int,
    limit: int,
    role: Optional[str],
    current_admin=Depends(get_current_admin_user)
):
    return await get_all_users_service(skip, limit, role)

async def suspend_user_controller(
    user_id: str,
    current_admin=Depends(get_current_admin_user)
):
    return await suspend_user_service(user_id)

async def unsuspend_user_controller(
    user_id: str,
    current_admin=Depends(get_current_admin_user)
):
    return await unsuspend_user_service(user_id)

async def delete_user_controller(
    user_id: str,
    current_admin=Depends(get_current_admin_user)
):
    return await delete_user_service(user_id)

async def update_profile_controller(
    data: dict,
    current_admin=Depends(get_current_admin_user)
):
    return await update_admin_profile_service(current_admin, data)

async def change_password_controller(
    data: dict,
    current_admin=Depends(get_current_admin_user)
):
    return await change_password_service(current_admin, data)
