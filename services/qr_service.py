import os
import qrcode

from config import QR_FOLDER


# ================================
# ENSURE QR DIRECTORY EXISTS
# ================================

os.makedirs(QR_FOLDER, exist_ok=True)


# ================================
# GENERATE QR CODE
# ================================

def generate_qr(token_uuid: str) -> str:
    """
    Generates QR code image for token
    Returns relative file path for frontend use
    """

    file_name = f"{token_uuid}.png"
    file_path = os.path.join(QR_FOLDER, file_name)

    # Data inside QR (can be expanded later)
    qr_data = token_uuid

    img = qrcode.make(qr_data)
    img.save(file_path)

    return f"/static/qrcodes/{file_name}"


# ================================
# CHECK IF QR EXISTS
# ================================

def qr_exists(token_uuid: str) -> bool:

    file_path = os.path.join(QR_FOLDER, f"{token_uuid}.png")

    return os.path.exists(file_path)


# ================================
# GET QR PATH (SAFE)
# ================================

def get_qr_path(token_uuid: str) -> str:
    """
    Returns QR path, generates if missing
    """

    if not qr_exists(token_uuid):
        return generate_qr(token_uuid)

    return f"/static/qrcodes/{token_uuid}.png"


# ================================
# DELETE QR (OPTIONAL CLEANUP)
# ================================

def delete_qr(token_uuid: str):
    """
    Deletes QR file (used if token cancelled)
    """

    file_path = os.path.join(QR_FOLDER, f"{token_uuid}.png")

    if os.path.exists(file_path):
        os.remove(file_path)