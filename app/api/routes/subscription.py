from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import date, datetime, timedelta
from ...core.db import get_session
from ...models.user import User
from ...models.content import Capsule
from ...services.notifier import send_daily_capsule_email
from ...schemas.users import UserOut
import json

router = APIRouter()

@router.post("/subscribe/{email}")
def subscribe_to_daily_capsule(email: str, session: Session = Depends(get_session)):
    """Subscribe an email to daily capsule and send missed capsules"""
    user = session.exec(select(User).where(User.email == email)).first()
    
    # Create user if doesn't exist
    if not user:
        user = User(
            email=email,
            full_name=email.split('@')[0].title(),
            role="student",
            hashed_password="default123",
            daily_capsule_subscribed=False
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # Check if already subscribed
    was_subscribed = user.daily_capsule_subscribed
    
    if not was_subscribed:
        # New subscription - send missed capsules from last 7 days
        sent_count = send_missed_capsules(session, email, 7)
        user.daily_capsule_subscribed = True
        session.add(user)
        session.commit()
        return {"message": f"Successfully subscribed {email} to daily capsule. Sent {sent_count} missed capsules."}
    else:
        return {"message": f"{email} is already subscribed to daily capsule"}

@router.post("/unsubscribe/{email}")
def unsubscribe_from_daily_capsule(email: str, session: Session = Depends(get_session)):
    """Unsubscribe an email from daily capsule"""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.daily_capsule_subscribed = False
    session.add(user)
    session.commit()
    return {"message": f"Successfully unsubscribed {email} from daily capsule"}

def send_missed_capsules(session: Session, email: str, days_back: int = 7):
    """Send missed capsules to new subscriber"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)
    
    # Get capsules from the last N days
    capsules = session.exec(
        select(Capsule).where(
            Capsule.date >= str(start_date),
            Capsule.date < str(end_date)
        ).order_by(Capsule.date.desc())
    ).all()
    
    sent_count = 0
    for capsule in capsules:
        capsule_data = {
            "date": capsule.date,
            "items": json.loads(capsule.items_json)
        }
        if send_daily_capsule_email(email, capsule_data):
            sent_count += 1
    
    return sent_count


@router.get("/subscribers")
def get_subscribers(session: Session = Depends(get_session)):
    """Get list of all subscribers"""
    subscribers = session.exec(
        select(User.email, User.full_name).where(User.daily_capsule_subscribed == True)
    ).all()
    return {"subscribers": [{"email": s[0], "name": s[1]} for s in subscribers]}


@router.post("/send-missed/{email}")
def send_missed_capsules_manual(email: str, days: int = 7, session: Session = Depends(get_session)):
    """Manually send missed capsules to a subscriber"""
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    sent_count = send_missed_capsules(session, email, days)
    return {"message": f"Sent {sent_count} missed capsules to {email}"}


@router.get("/missed-capsules/{days}")
def get_missed_capsules(days: int = 7, session: Session = Depends(get_session)):
    """Get missed capsules for viewing"""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    capsules = session.exec(
        select(Capsule).where(
            Capsule.date >= str(start_date),
            Capsule.date < str(end_date)
        ).order_by(Capsule.date.desc())
    ).all()
    
    result = []
    for capsule in capsules:
        result.append({
            "date": capsule.date,
            "items": json.loads(capsule.items_json)
        })
    
    return {"capsules": result}