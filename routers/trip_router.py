from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Trip, Transporter, Truck

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
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])),
):
    trips = db.query(Trip).all()
    transporters = db.query(Transporter).all()
    trucks = db.query(Truck).all()

    return templates.TemplateResponse(
        "trips.html",
        {
            "request": request,
            "trips": trips,
            "transporters": transporters,
            "trucks": trucks,
            "user": user,
        },
    )


# ================================
# ADD TRIP (FREIGHT ENTRY)
# ================================
@router.post("/trips/add")
def add_trip(
    truck_id: int = Form(...),  # FIXED
    origin: str = Form(...),
    destination: str = Form(...),
    material: str = Form(...),
    qty_mt: float = Form(...),
    driver_name: str = Form(...),
    driver_number: str = Form(...),
    freight_amount: float = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])),
):

    truck = db.query(Truck).get(truck_id)

    if not truck:
        return {"error": "Truck not found"}

    transporter_id = truck.transporter_id  # derive properly

    # Create trip
    trip = Trip(
        truck_id=truck_id,  # FIXED
        origin=origin,
        destination=destination,
        material=material,
        qty_mt=qty_mt,
        driver_name=driver_name,
        driver_number=driver_number,
        freight_amount=freight_amount,
        remaining_balance=freight_amount,
        status="open",
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    # Ledger entry
    add_freight(
        db, transporter_id=transporter_id, trip_id=trip.id, amount=freight_amount
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
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])),
):

    trip = db.query(Trip).get(trip_id)

    if not trip:
        return {"error": "Trip not found"}

    transporter = trip.truck.transporter  # FIXED (no direct FK)

    return templates.TemplateResponse(
        "trip_detail.html",
        {"request": request, "trip": trip, "transporter": transporter, "user": user},
    )


# ================================
# DELETE TRIP (ADMIN ONLY)
# ================================
@router.get("/trips/delete/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["MASTER_ADMIN"], ROLES["FACTORY_EMP"]])),
):

    trip = db.query(Trip).get(trip_id)

    if not trip:
        return {"error": "Trip not found"}

    db.delete(trip)
    db.commit()

    return RedirectResponse("/trips", status_code=302)
