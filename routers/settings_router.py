import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from utils.security import require_roles
from config import ROLES

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def update_env_file(key: str, value: str):
    """Safely extracts, manipulates, and overwrites target keys locally in the rigid .env matrix."""
    env_path = ".env"
    lines = []
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}=\"{value}\"\n"
            updated = True
            break
            
    if not updated:
        lines.append(f"{key}=\"{value}\"\n")
        
    with open(env_path, "w") as f:
        f.writelines(lines)
        
    os.environ[key] = value

@router.get("/settings")
def get_settings(
    request: Request,
    user=Depends(require_roles([ROLES["MASTER_ADMIN"]]))
):
    current_username = os.getenv("SMTP_USERNAME", "")
    current_password = os.getenv("SMTP_PASSWORD", "")
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user,
        "smtp_username": current_username,
        "smtp_password": current_password
    })

@router.post("/settings/smtp")
def update_smtp_settings(
    request: Request,
    smtp_username: str = Form(...),
    smtp_password: str = Form(...),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"]]))
):
    update_env_file("SMTP_USERNAME", smtp_username.strip())
    update_env_file("SMTP_PASSWORD", smtp_password.strip())
    
    # Cascade hot-reload explicitly
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    return RedirectResponse("/settings?success=true", status_code=302)
