from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User
from utils.security import verify_password, hash_password, require_roles
from config import ROLES

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ================================
# LOGIN PAGE
# ================================


@router.get("/login")
def login_page(request: Request):

    return templates.TemplateResponse("login.html", {"request": request})


# ================================
# LOGIN HANDLER
# ================================


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid username or password"}
        )

    from services.email_service import generate_otp, send_otp_email
    import datetime

    otp = generate_otp()
    user.current_otp = otp
    user.otp_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    db.commit()

    if user.email:
        send_otp_email(user.email, otp)
    else:
        print(f"\\n{'='*50}\\nWARNING: User '{user.username}' has no email configured! OTP: {otp}\\n{'='*50}\\n")

    # Store pending session instead of direct login granting
    request.session["pending_2fa_user_id"] = user.id

    return RedirectResponse("/login/verify", status_code=302)

# ================================
# 2FA VERIFICATION LOGIC
# ================================

@router.get("/login/verify")
def verify_2fa_page(request: Request):
    if "pending_2fa_user_id" not in request.session:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("verify_2fa.html", {"request": request})

@router.post("/login/verify")
def verify_2fa_submit(
    request: Request,
    otp: str = Form(...),
    db: Session = Depends(get_db)
):
    pending_id = request.session.get("pending_2fa_user_id")
    if not pending_id:
        return RedirectResponse("/login", status_code=302)
    
    user = db.query(User).get(pending_id)
    if not user:
        return RedirectResponse("/login", status_code=302)
        
    import datetime
    
    if user.current_otp != otp or user.otp_expires_at is None or user.otp_expires_at < datetime.datetime.utcnow():
        return templates.TemplateResponse("verify_2fa.html", {"request": request, "error": "Invalid or expired code."})
        
    # Valid context! Clear OTP constraints and grant permanent session
    user.current_otp = None
    user.otp_expires_at = None
    db.commit()
    
    request.session.pop("pending_2fa_user_id", None)
    
    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
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
        username="admin", password=hash_password("admin123"), role=ROLES["ADMIN"]
    )

    db.add(admin)
    db.commit()

    return {"message": "Admin created (username: admin, password: admin123)"}


# ================================
# USER MANAGEMENT (ADMIN)
# ================================


@router.post("/users/add")
def add_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])),
):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return RedirectResponse("/?tab=tab-users", status_code=302)

    new_user = User(username=username, email=email, password=hash_password(password), role=role)
    db.add(new_user)
    db.commit()

    return RedirectResponse("/?tab=tab-users", status_code=302)


@router.get("/users/delete/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["ADMIN"]])),
):
    target_user = db.query(User).get(user_id)
    if target_user and target_user.username != "admin":  # Prevent deleting super admin
        db.delete(target_user)
        db.commit()

    return RedirectResponse("/?tab=tab-users", status_code=302)

# ================================
# FORGOT PASSWORD FLOW
# ================================

@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password_request.html", {"request": request})

@router.post("/forgot-password")
def forgot_password_submit(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
        
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return templates.TemplateResponse("forgot_password_request.html", {"request": request, "error": "No account found with that username."})

    from services.email_service import generate_otp, send_otp_email
    import datetime
    
    otp = generate_otp()
    user.current_otp = otp
    user.otp_expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    db.commit()
    
    if user.email:
        send_otp_email(user.email, otp)
    else:
        print(f"\\n{'='*50}\\nWARNING: User '{user.username}' has no email configured! OTP: {otp}\\n{'='*50}\\n")
        
    request.session["reset_pending_user_id"] = user.id

    return RedirectResponse("/forgot-password/verify", status_code=302)


@router.get("/forgot-password/verify")
def forgot_password_verify_page(request: Request):
    if "reset_pending_user_id" not in request.session:
        return RedirectResponse("/forgot-password", status_code=302)
    return templates.TemplateResponse("forgot_password_verify.html", {"request": request})


@router.post("/forgot-password/verify")
def forgot_password_verify_submit(
    request: Request,
    otp: str = Form(...),
    db: Session = Depends(get_db)
):
    pending_id = request.session.get("reset_pending_user_id")
    if not pending_id:
        return RedirectResponse("/forgot-password", status_code=302)
        
    user = db.query(User).get(pending_id)
    if not user:
        return RedirectResponse("/forgot-password", status_code=302)
        
    import datetime
    
    if user.current_otp != otp or user.otp_expires_at is None or user.otp_expires_at < datetime.datetime.utcnow():
        return templates.TemplateResponse("forgot_password_verify.html", {"request": request, "error": "Invalid or expired code."})
        
    # Clear OTP logic securely
    user.current_otp = None
    user.otp_expires_at = None
    db.commit()
    
    # Escalate session securely
    request.session.pop("reset_pending_user_id", None)
    request.session["reset_verified_user_id"] = user.id
    
    return RedirectResponse("/forgot-password/new", status_code=302)


@router.get("/forgot-password/new")
def forgot_password_new_page(request: Request):
    if "reset_verified_user_id" not in request.session:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse("forgot_password_new.html", {"request": request})


@router.post("/forgot-password/new")
def forgot_password_new_submit(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    verified_id = request.session.get("reset_verified_user_id")
    if not verified_id:
        return RedirectResponse("/login", status_code=302)
        
    if new_password != confirm_password:
        return templates.TemplateResponse("forgot_password_new.html", {"request": request, "error": "Passwords do not match."})
        
    user = db.query(User).get(verified_id)
    if not user:
        return RedirectResponse("/login", status_code=302)
        
    user.password = hash_password(new_password)
    db.commit()
    
    # Terminate the reset authority
    request.session.pop("reset_verified_user_id", None)
    
    return templates.TemplateResponse("login.html", {"request": request, "success": "Password reset smoothly. Please login with your new credentials!"})
