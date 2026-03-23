import uuid
from sqlalchemy.orm import Session

from database.models import DieselToken, Trip
from config import MIN_TOKEN_VALUE, MAX_TOKEN_VALUE

# ================================
# GENERATE UNIQUE TOKEN
# ================================


def generate_token_uuid():
    """
    Generates a short unique token ID
    """
    return str(uuid.uuid4())[:8]


# ================================
# VALIDATE TOKEN VALUE
# ================================


def validate_token_value(value: float):
    """
    Ensures token value is within allowed limits
    """

    if value < MIN_TOKEN_VALUE:
        raise Exception(f"Minimum token value is {MIN_TOKEN_VALUE}")

    if value > MAX_TOKEN_VALUE:
        raise Exception(f"Maximum token value is {MAX_TOKEN_VALUE}")


# ================================
# CREATE DIESEL TOKEN
# ================================


def create_token(db: Session, trip_id: int, value: float):
    """
    Creates a diesel token (does NOT deduct balance here)
    Balance deduction is handled separately in balance_service
    """

    # Validate token value
    validate_token_value(value)

    # Fetch trip
    trip = db.query(Trip).get(trip_id)

    if not trip:
        raise Exception("Trip not found")

    if trip.remaining_balance < value:
        raise Exception("Insufficient trip balance")

    # Generate unique token
    token_uuid = generate_token_uuid()

    # Ensure uniqueness (rare but safe)
    existing = (
        db.query(DieselToken).filter(DieselToken.token_uuid == token_uuid).first()
    )

    if existing:
        return create_token(db, trip_id, value)  # retry

    # Create token
    token = DieselToken(
        token_uuid=token_uuid,
        trip_id=trip_id,
        transporter_id=trip.truck.transporter_id,
        value=value,
        status="issued",
    )

    db.add(token)
    db.commit()
    db.refresh(token)

    return token


# ================================
# GET TOKEN BY UUID
# ================================


def get_token(db: Session, token_uuid: str):

    return db.query(DieselToken).filter(DieselToken.token_uuid == token_uuid).first()


# ================================
# VALIDATE TOKEN FOR REDEMPTION
# ================================


def validate_token_for_redeem(token: DieselToken):
    """
    Ensures token is valid for redemption
    """

    if not token:
        raise Exception("Invalid token")

    if token.status == "redeemed":
        raise Exception("Token already redeemed")

    if token.status == "cancelled":
        raise Exception("Token cancelled")


# ================================
# PROCESS REDEMPTION
# ================================


def process_redemption(db: Session, token: DieselToken, amount: float):
    from datetime import datetime

    if token.status == "redeemed":
        raise Exception("Token already fully redeemed")

    if token.status == "pending_overdraft":
        raise Exception("Token is locked pending overdraft approval")

    token.redeemed_at = datetime.utcnow()

    if amount <= token.remaining_value:
        # Partial or Exact Redemption
        token.remaining_value -= amount
        if token.remaining_value <= 0:
            token.status = "redeemed"
        db.commit()
        db.refresh(token)
        return {
            "status": "success",
            "message": f"Successfully redeemed ₹{amount}. Remaining token balance: ₹{token.remaining_value}",
        }

    else:
        # Overdraft Request
        overdraft = amount - token.remaining_value
        token.overdraft_amount = overdraft
        token.overdraft_status = "pending"
        token.status = "pending_overdraft"
        token.remaining_value = 0
        db.commit()
        db.refresh(token)
        return {
            "status": "pending_overdraft",
            "message": f"Overdraft of ₹{overdraft} requested. Awaiting Pump Operations approval.",
        }


def approve_overdraft(db: Session, token: DieselToken):
    if token.status != "pending_overdraft":
        raise Exception("Token is not pending overdraft approval")

    from services.balance_service import deduct_diesel

    # Deduct the overdraft amount from the transporter ledger
    deduct_diesel(db, token.transporter_id, token.trip_id, token.overdraft_amount)

    token.status = "redeemed"
    token.overdraft_status = "approved"
    db.commit()
    db.refresh(token)
    return token


def reject_overdraft(db: Session, token: DieselToken):
    if token.status != "pending_overdraft":
        raise Exception("Token is not pending overdraft approval")

    token.status = "redeemed"
    token.overdraft_status = "rejected"
    db.commit()
    db.refresh(token)
    return token


# ================================
# CANCEL TOKEN (ADMIN)
# ================================


def cancel_token(db: Session, token: DieselToken):

    if token.status == "redeemed":
        raise Exception("Cannot cancel redeemed token")

    token.status = "cancelled"

    db.commit()

    return token
