from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Trip, Transporter

from services.balance_service import add_freight

from utils.security import require_roles
from config import ROLES

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ================================
# VIEW ALL TRIPS
# ================================

@router.get("/trips")
def trip_list(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]]))
):

    trips = db.query(Trip).all()
    transporters = db.query(Transporter).all()

    return templates.TemplateResponse(
        "trips.html",
        {
            "request": request,
            "trips": trips,
            "transporters": transporters,
            "user": user
        }
    )


# ================================
# ADD TRIP (FREIGHT ENTRY)
# ================================

@router.post("/trips/add")
def add_trip(
    transporter_id: int = Form(...),
    origin: str = Form(...),
    destination: str = Form(...),
    freight_amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"]]))
):

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        return {"error": "Transporter not found"}

    # Create trip
    trip = Trip(
        transporter_id=transporter_id,
        origin=origin,
        destination=destination,
        freight_amount=freight_amount,
        remaining_balance=freight_amount,
        status="open"
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Add freight to balance (ledger entry)
    add_freight(
        db,
        transporter_id=transporter_id,
        trip_id=trip.id,
        amount=freight_amount
    )

    return RedirectResponse("/trips", status_code=302)


# ================================
# VIEW SINGLE TRIP
# ================================

@router.get("/trips/{trip_id}")
def trip_detail(
    trip_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["FACTORY"], ROLES["ACCOUNTS"]]))
):

    trip = db.query(Trip).get(trip_id)

    if not trip:
        return {"error": "Trip not found"}

    transporter = db.query(Transporter).get(trip.transporter_id)

    return templates.TemplateResponse(
        "trip_detail.html",
        {
            "request": request,
            "trip": trip,
            "transporter": transporter,
            "user": user
        }
    )


# ================================
# DELETE TRIP (ADMIN ONLY)
# ================================

@router.get("/trips/delete/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"]]))
):

    trip = db.query(Trip).get(trip_id)

    if not trip:
        return {"error": "Trip not found"}

    db.delete(trip)
    db.commit()

    return RedirectResponse("/trips", status_code=302)