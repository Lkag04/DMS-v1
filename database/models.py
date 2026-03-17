from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


# ================================
# USER MODEL (AUTH + ROLES)
# ================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)

    created_at = Column(DateTime, server_default=func.now())


# ================================
# TRANSPORTER MODEL
# ================================

class Transporter(Base):
    __tablename__ = "transporters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    vehicle_number = Column(String, nullable=True)

    balance = Column(Float, default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    trips = relationship("Trip", back_populates="transporter")
    tokens = relationship("DieselToken", back_populates="transporter")


# ================================
# TRIP MODEL
# ================================

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    transporter_id = Column(Integer, ForeignKey("transporters.id"), nullable=False)

    origin = Column(String)
    destination = Column(String)

    freight_amount = Column(Float, nullable=False)
    remaining_balance = Column(Float, nullable=False)

    status = Column(String, default="open")  # open / settled

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transporter = relationship("Transporter", back_populates="trips")
    tokens = relationship("DieselToken", back_populates="trip")


# ================================
# DIESEL TOKEN MODEL
# ================================

class DieselToken(Base):
    __tablename__ = "diesel_tokens"

    id = Column(Integer, primary_key=True, index=True)

    token_uuid = Column(String, unique=True, nullable=False, index=True)

    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False)
    transporter_id = Column(Integer, ForeignKey("transporters.id"), nullable=False)

    value = Column(Float, nullable=False)

    status = Column(String, default="issued")  # issued / redeemed / cancelled

    created_at = Column(DateTime, server_default=func.now())
    redeemed_at = Column(DateTime, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="tokens")
    transporter = relationship("Transporter", back_populates="tokens")

    __table_args__ = (
        UniqueConstraint("token_uuid", name="uq_token_uuid"),
    )


# ================================
# TRANSACTION MODEL (LEDGER)
# ================================

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transporter_id = Column(Integer, ForeignKey("transporters.id"))
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=True)

    type = Column(String, nullable=False)
    # freight_added / diesel_redeemed / adjustment

    amount = Column(Float, nullable=False)

    description = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


# ================================
# INDEXES (PERFORMANCE)
# ================================

Index("idx_transporter_id", Transaction.transporter_id)
Index("idx_trip_id", Transaction.trip_id)
Index("idx_token_uuid", DieselToken.token_uuid)