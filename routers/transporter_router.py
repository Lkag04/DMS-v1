from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Transporter
from services.balance_service import get_ledger

from utils.security import require_roles
from config import ROLES

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ================================
# VIEW ALL TRANSPORTERS
# ================================

@router.get("/transporters")
def transporter_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]]))
):

    transporters = db.query(Transporter).all()

    return templates.TemplateResponse(
        "transporters.html",
        {
            "request": request,
            "transporters": transporters,
            "user": user
        }
    )


# ================================
# ADD TRANSPORTER
# ================================

@router.post("/transporters/add")
def add_transporter(
    name: str = Form(...),
    phone: str = Form(""),
    vehicle_number: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"]]))
):

    transporter = Transporter(
        name=name,
        phone=phone,
        vehicle_number=vehicle_number,
        balance=0
    )

    db.add(transporter)
    db.commit()

    return RedirectResponse("/transporters", status_code=302)


# ================================
# TRANSPORTER DETAIL + LEDGER
# ================================

@router.get("/transporters/{transporter_id}")
def transporter_detail(
    transporter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"], ROLES["FACTORY"]]))
):

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    ledger = get_ledger(db, transporter_id)

    return templates.TemplateResponse(
        "transporter_detail.html",
        {
            "request": request,
            "transporter": transporter,
            "ledger": ledger,
            "user": user
        }
    )


# ================================
# DELETE TRANSPORTER (ADMIN ONLY)
# ================================

@router.get("/transporters/delete/{transporter_id}")
def delete_transporter(
    transporter_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"]]))
):

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    db.delete(transporter)
    db.commit()

    return RedirectResponse("/transporters", status_code=302)