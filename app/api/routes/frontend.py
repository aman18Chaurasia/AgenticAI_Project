from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def frontend():
    """Serve the main frontend page"""
    frontend_path = os.path.join(os.path.dirname(__file__), "../../../frontend/templates/index.html")
    with open(frontend_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page"""
    login_path = os.path.join(os.path.dirname(__file__), "../../../frontend/templates/login.html")
    with open(login_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/signup", response_class=HTMLResponse)
async def signup_page():
    """Serve the signup page"""
    signup_path = os.path.join(os.path.dirname(__file__), "../../../frontend/templates/signup.html")
    with open(signup_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page():
    """Serve the reset password page"""
    reset_path = os.path.join(os.path.dirname(__file__), "../../../frontend/templates/reset-password.html")
    with open(reset_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@router.get("/forgot", response_class=HTMLResponse)
async def forgot_page():
    """Serve the forgot password page"""
    path = os.path.join(os.path.dirname(__file__), "../../../frontend/templates/forgot.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@router.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files"""
    static_path = os.path.join(os.path.dirname(__file__), "../../../frontend/static", file_path)
    if os.path.exists(static_path):
        return FileResponse(static_path)
    return {"error": "File not found"}
