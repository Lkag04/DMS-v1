from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User
from utils.security import verify_password
from config import ROLES

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ================================
# LOGIN PAGE
# ================================

@router.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


# ================================
# LOGIN HANDLER
# ================================

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password"
            }
        )

    # Store session
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

    return RedirectResponse("/", status_code=302)


# ================================
# LOGOUT
# ================================

@router.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse("/login", status_code=302)


# ================================
# CREATE DEFAULT ADMIN (ONE-TIME)
# ================================

@router.get("/create-admin")
def create_admin(db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.username == "admin").first()

    if existing:
        return {"message": "Admin already exists"}

    from utils.security import hash_password

    admin = User(
        username="admin",
        password=hash_password("admin123"),
        role=ROLES["ADMIN"]
    )

    db.add(admin)
    db.commit()

    return {"message": "Admin created (username: admin, password: admin123)"}