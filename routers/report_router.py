from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

import io
import csv

from database.db import get_db
from database.models import Transporter, Transaction, Trip, DieselToken

from utils.security import require_roles
from config import ROLES

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ================================
# REPORT DASHBOARD
# ================================

@router.get("/reports")
def reports_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"]]))
):

    transporters = db.query(Transporter).all()
    trips = db.query(Trip).all()
    tokens = db.query(DieselToken).all()
    transactions = db.query(Transaction).all()

    total_balance = sum([t.balance for t in transporters])
    total_freight = sum([t.freight_amount for t in trips])
    total_diesel = sum([t.value for t in tokens])

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "transporters": transporters,
            "transactions": transactions,
            "total_balance": total_balance,
            "total_freight": total_freight,
            "total_diesel": total_diesel,
            "user": user
        }
    )


# ================================
# TRANSPORTER SUMMARY REPORT
# ================================

@router.get("/reports/transporters")
def transporter_report(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"]]))
):

    transporters = db.query(Transporter).all()

    data = []

    for t in transporters:
        data.append({
            "name": t.name,
            "balance": t.balance
        })

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "transporter_summary": data,
            "user": user
        }
    )


# ================================
# TRANSACTION REPORT
# ================================

@router.get("/reports/transactions")
def transaction_report(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"]]))
):

    transactions = db.query(Transaction).all()

    return templates.TemplateResponse(
        "reports.html",
        {
            "request": request,
            "transactions": transactions,
            "user": user
        }
    )


# ================================
# EXPORT CSV (TALLY INTEGRATION)
# ================================

@router.get("/reports/export")
def export_csv(
    db: Session = Depends(get_db),
    user=Depends(require_roles([ROLES["ADMIN"], ROLES["ACCOUNTS"]]))
):

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Date",
        "Transporter ID",
        "Trip ID",
        "Type",
        "Amount",
        "Description"
    ])

    transactions = db.query(Transaction).all()

    for txn in transactions:
        writer.writerow([
            txn.created_at,
            txn.transporter_id,
            txn.trip_id,
            txn.type,
            txn.amount,
            txn.description
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=erp_report.csv"
        }
    )