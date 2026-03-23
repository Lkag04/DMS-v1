import bcrypt
from fastapi import Request, HTTPException, status

from config import ROLES

# ================================
# PASSWORD HASHING
# ================================


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    pwd_bytes = password.encode("utf-8")
    # Use standard bcrypt verify
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))


# ================================
# SESSION-BASED AUTH
# ================================


def get_current_user(request: Request):
    """
    Get logged-in user from session
    """

    user = request.session.get("user")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )

    return user


# ================================
# ROLE-BASED ACCESS CONTROL
# ================================


def require_role(required_role: str):
    """
    Dependency to restrict access by role
    """

    def role_checker(request: Request):

        user = request.session.get("user")

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        if user["role"] != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        return user

    return role_checker


# ================================
# MULTI-ROLE ACCESS (ADVANCED)
# ================================


def require_roles(allowed_roles: list):
    """
    Allow multiple roles
    Example: ["admin", "factory"]
    """

    def role_checker(request: Request):

        user = request.session.get("user")

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

        return user

    return role_checker


# ================================
# OPTIONAL: CREATE DEFAULT USERS
# ================================


def create_default_admin(db, UserModel):
    """
    Run once to create admin user
    """

    existing = db.query(UserModel).filter(UserModel.username == "admin").first()

    if not existing:
        admin = UserModel(
            username="admin", password=hash_password("admin123"), role=ROLES["ADMIN"]
        )

        db.add(admin)
        db.commit()
