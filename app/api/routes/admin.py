from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from ...core.db import get_session
from ...core.security import get_password_hash
from ...models.user import User
from ...models.auth import SubscriptionRequest
from ...schemas.auth import SubscriptionRequestOut
from ...api.routes.auth import require_admin
from typing import List

router = APIRouter()

@router.get("/subscription-requests", response_model=List[SubscriptionRequestOut])
def get_subscription_requests(admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    requests = session.exec(select(SubscriptionRequest).where(SubscriptionRequest.status == "pending")).all()
    return requests

@router.post("/approve-subscription/{request_id}")
def approve_subscription(request_id: int, admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    sub_request = session.get(SubscriptionRequest, request_id)
    if not sub_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if sub_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Create user account
    user = User(
        email=sub_request.email,
        full_name=sub_request.full_name,
        hashed_password=get_password_hash("temp123"),  # Temporary password
        role="user",
        daily_capsule_subscribed=True
    )
    session.add(user)
    
    # Update request
    sub_request.status = "approved"
    sub_request.reviewed_by = admin.id
    sub_request.reviewed_at = datetime.now().isoformat()
    session.add(sub_request)
    
    session.commit()
    
    return {"message": f"Subscription approved for {sub_request.email}. Temporary password: temp123"}

@router.post("/reject-subscription/{request_id}")
def reject_subscription(request_id: int, admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    sub_request = session.get(SubscriptionRequest, request_id)
    if not sub_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    sub_request.status = "rejected"
    sub_request.reviewed_by = admin.id
    sub_request.reviewed_at = datetime.now().isoformat()
    session.add(sub_request)
    session.commit()
    
    return {"message": f"Subscription rejected for {sub_request.email}"}

@router.get("/users")
def get_all_users(admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    users = session.exec(select(User)).all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role, 
             "is_active": u.is_active, "subscribed": u.daily_capsule_subscribed} for u in users]

@router.post("/toggle-subscription/{user_id}")
def toggle_user_subscription(user_id: int, admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.daily_capsule_subscribed = not user.daily_capsule_subscribed
    session.add(user)
    session.commit()
    
    status = "subscribed" if user.daily_capsule_subscribed else "unsubscribed"
    return {"message": f"User {user.email} {status}"}

@router.post("/deactivate-user/{user_id}")
def deactivate_user(user_id: int, admin: User = Depends(require_admin), session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role in ["admin", "manager"]:
        raise HTTPException(status_code=400, detail="Cannot deactivate admin/manager")
    
    user.is_active = False
    user.daily_capsule_subscribed = False
    session.add(user)
    session.commit()
    
    return {"message": f"User {user.email} deactivated"}