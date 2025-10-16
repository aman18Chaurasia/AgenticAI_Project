import json
import os
from sqlmodel import Session, select
from ..core.db import engine
from ..models.content import SyllabusTopic, PyqQuestion
from ..models.user import User


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_basics() -> None:
    base = os.path.join("data", "seed")
    os.makedirs(base, exist_ok=True)
    syllabus_path = os.path.join(base, "syllabus.json")
    pyq_path = os.path.join(base, "pyq.json")
    users_path = os.path.join(base, "users.json")

    with Session(engine) as session:
        if os.path.exists(syllabus_path):
            existing = session.exec(select(SyllabusTopic)).first()
            if not existing:
                for item in _load_json(syllabus_path):
                    session.add(SyllabusTopic(**item))
        if os.path.exists(pyq_path):
            existing = session.exec(select(PyqQuestion)).first()
            if not existing:
                for q in _load_json(pyq_path):
                    session.add(PyqQuestion(**q))
        if os.path.exists(users_path):
            existing = session.exec(select(User)).first()
            if not existing:
                for u in _load_json(users_path):
                    password = u.pop("password", "default123")
                    from ..core.security import get_password_hash
                    hashed_password = get_password_hash(password)
                    session.add(User(**u, hashed_password=hashed_password))
        session.commit()
