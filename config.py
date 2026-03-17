import os

# ================================
# DATABASE CONFIGURATION
# ================================

# For development (local)
DATABASE_URL = "sqlite:///./diesel_erp.db"

# For production (uncomment when using PostgreSQL)
# DATABASE_URL = "postgresql://username:password@localhost:5432/diesel_erp"


# ================================
# SECURITY CONFIGURATION
# ================================

SECRET_KEY = "supersecretkey_change_this_in_production"

SESSION_COOKIE = "diesel_erp_session"


# ================================
# QR CODE CONFIGURATION
# ================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "static")

QR_FOLDER = os.path.join(STATIC_DIR, "qrcodes")

# Ensure QR folder exists
os.makedirs(QR_FOLDER, exist_ok=True)


# ================================
# APPLICATION SETTINGS
# ================================

APP_NAME = "Diesel ERP System"

DEBUG = True


# ================================
# BUSINESS LOGIC SETTINGS
# ================================

# Minimum allowed token value
MIN_TOKEN_VALUE = 100

# Prevent issuing token above this (safety)
MAX_TOKEN_VALUE = 100000


# ================================
# ROLE DEFINITIONS
# ================================

ROLES = {
    "ADMIN": "admin",
    "FACTORY": "factory",
    "PUMP": "pump",
    "ACCOUNTS": "accounts"
}


# ================================
# DATE FORMAT
# ================================

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"