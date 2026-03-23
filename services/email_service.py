import random
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(override=True)

def generate_otp() -> str:
    """Generates a secure 6-digit one-time password."""
    return str(random.randint(100000, 999999))

def send_otp_email(to_email: str, otp: str):
    """
    Sends an OTP via Gmail SMTP.
    Requires SMTP_USERNAME and SMTP_PASSWORD to be exported as environment variables.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Fallback to console mock if credentials aren't supplied
    if not smtp_username or not smtp_password:
        print("\n" + "="*50)
        print(f"[MOCK EMAIL 2FA DISPATCH] (MISSING GMAIL CREDS)")
        print(f"To: {to_email}")
        print(f"Code: {otp}")
        print("="*50 + "\n")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = "Diesel ERP Login Verification"

    body = f"Your secure login code is: {otp}\n\nThis code will expire in 10 minutes.\nIf you did not request this, please contact your administrator."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Successfully sent OTP to {to_email} via Gmail SMTP.")
        return True
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False
