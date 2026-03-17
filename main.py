from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse



from database.db import SessionLocal
from database.models import User
from utils.security import hash_password
from config import ROLES




from starlette.middleware.sessions import SessionMiddleware

from sqlalchemy.orm import Session

from database.db import Base, engine, get_db
from database.models import Transporter, Trip, DieselToken

from routers import (
    auth_router,
    transporter_router,
    trip_router,
    token_router,
    report_router
)

from utils.security import get_current_user
from config import SECRET_KEY


# ================================
# APP INITIALIZATION
# ================================

app = FastAPI(title="Diesel ERP System")

# Create DB tables
Base.metadata.create_all(bind=engine)

# ================================
# DEFAULT ADMIN SEEDER
# ================================

def create_default_admin():
    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == "admin").first()

        if not existing:
            admin = User(
                username="admin",
                password=hash_password("admin123"),
                role=ROLES["ADMIN"]
            )
            db.add(admin)
            db.commit()
            print("✅ Default admin created")
        else:
            print("ℹ️ Admin already exists")

    finally:
        db.close()


# ================================
# STARTUP EVENT
# ================================

@app.on_event("startup")
def startup_event():
    print("🚀 Starting Diesel ERP...")

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed default admin
    create_default_admin()


# ================================
# MIDDLEWARE (SESSIONS)
# ================================

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)


# ================================
# STATIC FILES + TEMPLATES
# ================================

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ================================
# ROUTERS
# ================================

app.include_router(auth_router.router)
app.include_router(transporter_router.router)
app.include_router(trip_router.router)
app.include_router(token_router.router)
app.include_router(report_router.router)


# ================================
# DASHBOARD (HOME PAGE)
# ================================

@app.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    # Redirect if not logged in
    if not request.session.get("user"):
        return RedirectResponse("/login")

    # Fetch metrics
    transporters_count = db.query(Transporter).count()

    trips = db.query(Trip).all()
    tokens = db.query(DieselToken).all()

    total_pending = sum([t.remaining_balance for t in trips])
    total_diesel = sum([t.value for t in tokens])

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "transporters": transporters_count,
            "pending": total_pending,
            "diesel": total_diesel,
            "trips": len(trips),
            "user": request.session.get("user")
        }
    )


# ================================
# HEALTH CHECK (OPTIONAL)
# ================================

@app.get("/health")
def health():
    return {"status": "OK"}