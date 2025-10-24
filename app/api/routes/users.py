from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ...core.db import engine
from ...core.security import get_password_hash, verify_password, create_access_token
from ...models.user import User
from ...schemas.users import UserCreate, UserOut, Login, Token
from ...core.deps import get_current_user

router = APIRouter()


@router.post("/signup", response_model=UserOut)
def signup(payload: UserCreate):
    with Session(engine) as session:
        # Promote first user to admin to bootstrap
        is_first = session.exec(select(User)).first() is None
        existing = session.exec(select(User).where(User.email == payload.email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user = User(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=get_password_hash(payload.password),
            role=("admin" if is_first else "user"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


@router.post("/login", response_model=Token)
def login(payload: Login):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == payload.email)).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(subject=str(user.id))
        return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return UserOut(id=current.id, email=current.email, full_name=current.full_name, role=current.role)

