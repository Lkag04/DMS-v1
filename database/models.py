from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
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
    
    # 2FA Fields
    email = Column(String, unique=True, index=True, nullable=True) # nullable to allow safe migrations
    current_otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


# ================================
# TRANSPORTER MODEL
# ================================
class Transporter(Base):
    __tablename__ = "transporters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    balance = Column(Float, default=0)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    trucks = relationship(
        "Truck", back_populates="transporter", cascade="all, delete-orphan"
    )
    tokens = relationship("DieselToken", back_populates="transporter")
    transactions = relationship("Transaction", back_populates="transporter")


# ================================
# TRUCK MODEL
# ================================
class Truck(Base):
    __tablename__ = "trucks"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String, nullable=False)

    transporter_id = Column(
        Integer, ForeignKey("transporters.id", ondelete="CASCADE"), nullable=False
    )

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transporter = relationship("Transporter", back_populates="trucks")
    trips = relationship("Trip", back_populates="truck", cascade="all, delete-orphan")


# ================================
# TRIP MODEL
# ================================
class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)

    truck_id = Column(
        Integer, ForeignKey("trucks.id", ondelete="CASCADE"), nullable=False
    )

    origin = Column(String)
    destination = Column(String)

    material = Column(String)
    qty_mt = Column(Float)
    driver_name = Column(String)
    driver_number = Column(String)

    freight_amount = Column(Float, nullable=False)
    remaining_balance = Column(Float, nullable=False)

    status = Column(String, default="open")  # open / settled

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    truck = relationship("Truck", back_populates="trips")
    tokens = relationship("DieselToken", back_populates="trip")
    transactions = relationship("Transaction", back_populates="trip")


# ================================
# DIESEL TOKEN MODEL
# ================================
class DieselToken(Base):
    __tablename__ = "diesel_tokens"

    id = Column(Integer, primary_key=True, index=True)

    token_uuid = Column(String, unique=True, nullable=False, index=True)

    trip_id = Column(
        Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    transporter_id = Column(
        Integer, ForeignKey("transporters.id", ondelete="CASCADE"), nullable=False
    )

    value = Column(Float, nullable=False)
    remaining_value = Column(Float, nullable=False, default=0.0)

    overdraft_amount = Column(Float, default=0.0)
    overdraft_status = Column(
        String, default="none"
    )  # none / pending / approved / rejected

    status = Column(
        String, default="issued"
    )  # issued / redeemed / cancelled / pending_overdraft

    created_at = Column(DateTime, server_default=func.now())
    redeemed_at = Column(DateTime, nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="tokens")
    transporter = relationship("Transporter", back_populates="tokens")

    __table_args__ = (UniqueConstraint("token_uuid", name="uq_token_uuid"),)


# ================================
# TRANSACTION MODEL (LEDGER)
# ================================
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    transporter_id = Column(Integer, ForeignKey("transporters.id", ondelete="CASCADE"))
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True)

    type = Column(String, nullable=False)
    # freight_added / diesel_redeemed / adjustment

    amount = Column(Float, nullable=False)

    description = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    transporter = relationship("Transporter", back_populates="transactions")
    trip = relationship("Trip", back_populates="transactions")


# ================================
# INDEXES (PERFORMANCE)
# ================================
Index("idx_transaction_transporter", Transaction.transporter_id)
Index("idx_transaction_trip", Transaction.trip_id)
Index("idx_token_uuid", DieselToken.token_uuid)
