from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session, joinedload

from database.db import get_db
from database.models import Transporter, Truck, Trip
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
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    transporters = db.query(Transporter).all()

    return templates.TemplateResponse(
        "transporters.html",
        {"request": request, "transporters": transporters, "user": user},
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
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    transporter = Transporter(name=name, phone=phone, balance=0)

    db.add(transporter)
    db.commit()
    db.refresh(transporter)

    # Optional truck creation
    if vehicle_number:
        truck = Truck(vehicle_number=vehicle_number, transporter_id=transporter.id)
        db.add(truck)
        db.commit()

    return RedirectResponse("/transporters", status_code=303)


# ================================
# TRANSPORTER → TRUCKS
# ================================
@router.get("/transporters/{transporter_id}/trucks")
def transporter_trucks(
    transporter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    transporter = db.get(Transporter, transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    trucks = db.query(Truck).filter(Truck.transporter_id == transporter_id).all()

    return templates.TemplateResponse(
        "transporter_trucks.html",
        {
            "request": request,
            "transporter": transporter,
            "trucks": trucks,
            "user": user,
        },
    )


# ================================
# TRUCK → TRIPS
# ================================
@router.get("/trucks/{truck_id}/trips")
def truck_trips(
    truck_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    truck = db.get(Truck, truck_id)

    if not truck:
        return {"error": "Truck not found"}

    trips = db.query(Trip).filter(Trip.truck_id == truck_id).all()

    return templates.TemplateResponse(
        "truck_trips.html",
        {"request": request, "truck": truck, "trips": trips, "user": user},
    )


# ================================
# TRANSPORTER DETAIL (FIXED)
# ================================
@router.get("/transporters/{transporter_id}")
def transporter_detail(
    transporter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    transporter = db.get(Transporter, transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    # FIX: Fetch trips via Truck relationship
    trips = (
        db.query(Trip)
        .join(Trip.truck)
        .options(joinedload(Trip.truck))
        .filter(Truck.transporter_id == transporter_id)
        .order_by(Trip.id.desc())
        .all()
    )

    # Ledger
    ledger = get_ledger(db, transporter_id)

    return templates.TemplateResponse(
        "transporter_detail.html",
        {
            "request": request,
            "transporter": transporter,
            "trips": trips,  # IMPORTANT (was missing earlier)
            "ledger": ledger,
            "user": user,
        },
    )


# ================================
# DELETE TRANSPORTER (ADMIN ONLY)
# ================================
@router.post("/transporters/delete/{transporter_id}")
def delete_transporter(
    transporter_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_OPS"]])),
):
    transporter = db.get(Transporter, transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    db.delete(transporter)
    db.commit()

    return RedirectResponse("/transporters", status_code=302)
