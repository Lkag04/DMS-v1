from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Trip

from services.token_service import (
    create_token,
    get_token,
    validate_token_for_redeem,
    mark_token_redeemed
)

from services.balance_service import deduct_diesel
from services.qr_service import generate_qr, get_qr_path

from utils.security import require_roles
from config import ROLES

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ================================
# ISSUE TOKEN PAGE
# ================================

@router.get("/tokens/issue/{trip_id}")
def issue_token_page(
    trip_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"]]))
):
    trip = db.query(Trip).get(trip_id)

    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return templates.TemplateResponse(
        "issue_token.html",
        {
            "request": request,
            "trip": trip,
            "user": user
        }
    )


# ================================
# ISSUE TOKEN (CREATE + DEDUCT)
# ================================

@router.post("/tokens/issue")
def issue_token(
    request: Request,   # ✅ FIXED
    trip_id: int = Form(...),
    value: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"]]))
):
    # Validate trip
    trip = db.query(Trip).get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Step 1: Create token
    token = create_token(db, trip_id, value)

    # Step 2: Deduct balance
    deduct_diesel(
        db,
        transporter_id=token.transporter_id,
        trip_id=trip_id,
        amount=value
    )

    # Step 3: Generate QR
    generate_qr(token.token_uuid)

    # ✅ PRG Pattern (Redirect after POST)
    return RedirectResponse(
        url=f"/tokens/{token.token_uuid}",
        status_code=303
    )


# ================================
# REDEEM PAGE (QR SCANNER)
# ================================

@router.get("/tokens/redeem")
def redeem_page(
    request: Request,
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["PUMP"]]))
):
    return templates.TemplateResponse(
        "redeem_token.html",
        {
            "request": request,
            "user": user
        }
    )


# ================================
# REDEEM TOKEN
# ================================

@router.post("/tokens/redeem")
def redeem_token(
    request: Request,
    token_uuid: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["PUMP"]]))
):
    token = get_token(db, token_uuid)

    try:
        validate_token_for_redeem(token)
    except Exception as e:
        return templates.TemplateResponse(
            "redeem_token.html",
            {
                "request": request,
                "error": str(e),
                "user": user
            }
        )

    # Mark redeemed
    mark_token_redeemed(db, token)

    return templates.TemplateResponse(
        "redeem_token.html",
        {
            "request": request,
            "message": f"Diesel issued: ₹{token.value}",
            "user": user
        }
    )


# ================================
# VIEW TOKEN DETAILS
# ================================

@router.get("/tokens/{token_uuid}")
def view_token(
    token_uuid: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]]))
):
    token = get_token(db, token_uuid)

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    qr_path = get_qr_path(token.token_uuid)

    return templates.TemplateResponse(
        "token_detail.html",
        {
            "request": request,
            "token": token,
            "qr_path": qr_path,
            "user": user
        }
    )