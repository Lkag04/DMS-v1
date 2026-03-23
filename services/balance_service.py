from sqlalchemy.orm import Session
from datetime import datetime

from database.models import Transaction, Transporter, Trip

# ================================
# CREATE TRANSACTION ENTRY
# ================================


def create_transaction(
    db: Session,
    transporter_id: int,
    trip_id: int,
    txn_type: str,
    amount: float,
    description: str = "",
):
    """
    Creates a ledger entry (like Tally)
    """

    txn = Transaction(
        transporter_id=transporter_id,
        trip_id=trip_id,
        type=txn_type,
        amount=amount,
        description=description,
        created_at=datetime.utcnow(),
    )

    db.add(txn)
    db.commit()

    return txn


# ================================
# ADD FREIGHT (TRIP CREATION)
# ================================


def add_freight(db: Session, transporter_id: int, trip_id: int, amount: float):
    """
    Adds freight to transporter balance
    """

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        raise Exception("Transporter not found")

    transporter.balance += amount

    db.commit()

    create_transaction(
        db, transporter_id, trip_id, "freight_added", amount, "Freight added for trip"
    )


# ================================
# DEDUCT DIESEL (TOKEN ISSUE)
# ================================


def deduct_diesel(db: Session, transporter_id: int, trip_id: int, amount: float):
    """
    Deduct diesel value from transporter balance
    """

    transporter = db.query(Transporter).get(transporter_id)
    trip = db.query(Trip).get(trip_id)

    if not transporter or not trip:
        raise Exception("Invalid transporter or trip")

    # Prevent negative balance
    if transporter.balance < amount:
        raise Exception("Insufficient transporter balance")

    if trip.remaining_balance < amount:
        raise Exception("Insufficient trip balance")

    transporter.balance -= amount
    trip.remaining_balance -= amount

    # If trip settled
    if trip.remaining_balance == 0:
        trip.status = "settled"

    db.commit()

    create_transaction(
        db,
        transporter_id,
        trip_id,
        "diesel_redeemed",
        -amount,
        "Diesel issued against token",
    )


# ================================
# MANUAL ADJUSTMENT (ADMIN USE)
# ================================


def adjust_balance(db: Session, transporter_id: int, amount: float, description: str):
    """
    Admin can adjust balance (+ or -)
    """

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        raise Exception("Transporter not found")

    transporter.balance += amount

    db.commit()

    create_transaction(db, transporter_id, None, "adjustment", amount, description)


# ================================
# GET TRANSPORTER BALANCE
# ================================


def get_transporter_balance(db: Session, transporter_id: int):

    transporter = db.query(Transporter).get(transporter_id)

    if not transporter:
        return 0

    return transporter.balance


# ================================
# GET TRIP BALANCE
# ================================


def get_trip_balance(db: Session, trip_id: int):

    trip = db.query(Trip).get(trip_id)

    if not trip:
        return 0

    return trip.remaining_balance


# ================================
# LEDGER GENERATION (RUNNING BALANCE)
# ================================


def get_ledger(db: Session, transporter_id: int):
    """
    Returns running ledger like Tally
    """

    txns = (
        db.query(Transaction)
        .filter(Transaction.transporter_id == transporter_id)
        .order_by(Transaction.created_at)
        .all()
    )

    balance = 0
    ledger = []

    for txn in txns:
        balance += txn.amount

        ledger.append(
            {
                "date": txn.created_at,
                "type": txn.type,
                "amount": txn.amount,
                "balance": balance,
                "description": txn.description,
            }
        )

    return ledger
