"""Visitor registration, email verification, and time-limited gate passes."""

import base64
import hashlib
import hmac
import io
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

import mysql.connector
import qrcode
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("gatepass")
app = FastAPI(title="Visitor Hub API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

OTP_TTL_MINUTES = int(os.getenv("OTP_TTL_MINUTES", "10"))
PASS_TTL_HOURS = int(os.getenv("PASS_TTL_HOURS", "8"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
APP_ENV = os.getenv("APP_ENV", "development").lower()


class VisitorSubmission(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address: str = Field(min_length=4, max_length=2000)
    email: EmailStr
    purpose: str = Field(min_length=3, max_length=2000)


class OtpVerification(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")


class PassScan(BaseModel):
    token: str = Field(min_length=32, max_length=128)


def db_connection():
    """Open a fresh connection so request handlers do not share DB state."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "gate_pass_user"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gate_pass"),
        connection_timeout=5,
    )


def keyed_digest(value: str) -> str:
    secret_value = os.getenv("APP_SECRET", "local-development-secret-change-me")
    if APP_ENV == "production" and len(secret_value) < 32:
        raise RuntimeError("APP_SECRET must be at least 32 characters in production")
    secret = secret_value.encode()
    return hmac.new(secret, value.encode(), hashlib.sha256).hexdigest()


def send_otp(email: str, otp: str) -> None:
    """Send email through SMTP, or log it in development console mode."""
    delivery = os.getenv("OTP_DELIVERY", "console").lower()
    if delivery == "console":
        if APP_ENV == "production":
            raise RuntimeError("Console OTP delivery cannot be used in production")
        logger.info("Development OTP for %s: %s", email, otp)
        return
    if delivery != "smtp":
        raise RuntimeError("OTP_DELIVERY must be 'console' or 'smtp'")
    host, username, password, sender = (os.getenv(key) for key in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM"))
    if not all((host, username, password, sender)):
        raise RuntimeError("SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM are required")
    message = EmailMessage()
    message["Subject"] = "Your Visitor Hub verification code"
    message["From"] = sender
    message["To"] = email
    message.set_content(f"Your verification code is {otp}. It expires in {OTP_TTL_MINUTES} minutes.")
    with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=15) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(message)


def qr_data_url(payload: str) -> str:
    qr = qrcode.QRCode(box_size=8, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#14211d", back_color="white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


@app.get("/api/health")
def health():
    try:
        connection = db_connection()
        connection.close()
        return {"status": "ok", "database": "connected"}
    except mysql.connector.Error as exc:
        logger.warning("Database health check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Database is unavailable") from exc


@app.post("/api/submit_form", status_code=201)
def submit_form(visitor: VisitorSubmission):
    """Save visitor details and send an email OTP before issuing a pass."""
    otp = f"{secrets.randbelow(1_000_000):06d}"
    connection = None
    try:
        connection = db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO visitors (name, address, email, purpose) VALUES (%s, %s, %s, %s)",
            (visitor.name.strip(), visitor.address.strip(), visitor.email.lower(), visitor.purpose.strip()),
        )
        visitor_id = cursor.lastrowid
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=OTP_TTL_MINUTES)
        cursor.execute(
            "INSERT INTO email_otps (visitor_id, otp_hash, expires_at) VALUES (%s, %s, %s)",
            (visitor_id, keyed_digest(otp), expires_at),
        )
        connection.commit()
        send_otp(visitor.email.lower(), otp)
        response = {"message": "Verification code sent. Check your email to continue.", "email": visitor.email.lower()}
        if APP_ENV != "production" and os.getenv("OTP_DELIVERY", "console").lower() == "console":
            response["development_otp"] = otp
        return response
    except (mysql.connector.Error, RuntimeError, smtplib.SMTPException, OSError) as exc:
        if connection:
            connection.rollback()
        logger.exception("Unable to start visitor registration")
        raise HTTPException(status_code=503, detail="Could not start registration. Check the service configuration and try again.") from exc
    finally:
        if connection:
            connection.close()


@app.post("/api/verify_otp", status_code=201)
def verify_otp(request: OtpVerification):
    """Verify the latest code for an email address and issue a QR gate pass."""
    connection = None
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT o.id AS otp_id, o.otp_hash, o.expires_at, o.attempts,
                      v.id AS visitor_id, v.name, v.email, v.purpose
               FROM email_otps o JOIN visitors v ON v.id = o.visitor_id
               WHERE v.email = %s AND o.verified_at IS NULL
               ORDER BY o.id DESC LIMIT 1""",
            (request.email.lower(),),
        )
        record = cursor.fetchone()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not record or record["attempts"] >= OTP_MAX_ATTEMPTS or record["expires_at"] <= now:
            raise HTTPException(status_code=400, detail="The code is invalid or has expired. Request a new one.")
        cursor.execute("UPDATE email_otps SET attempts = attempts + 1 WHERE id = %s", (record["otp_id"],))
        if not hmac.compare_digest(record["otp_hash"], keyed_digest(request.otp)):
            connection.commit()
            raise HTTPException(status_code=400, detail="That verification code is incorrect.")
        cursor.execute("UPDATE email_otps SET verified_at = %s WHERE id = %s", (now, record["otp_id"]))
        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(hours=PASS_TTL_HOURS)
        cursor.execute(
            "INSERT INTO gate_passes (visitor_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (record["visitor_id"], keyed_digest(token), expires_at),
        )
        connection.commit()
        return {
            "message": "Email verified. Your gate pass is ready.",
            "visitor": {"name": record["name"], "email": record["email"], "purpose": record["purpose"]},
            "token": token,
            "expires_at": expires_at.replace(tzinfo=timezone.utc).isoformat(),
            "qr_code": qr_data_url(token),
        }
    except HTTPException:
        raise
    except mysql.connector.Error as exc:
        if connection:
            connection.rollback()
        logger.exception("Unable to verify visitor OTP")
        raise HTTPException(status_code=503, detail="Verification is temporarily unavailable") from exc
    finally:
        if connection:
            connection.close()


@app.get("/api/analyse_visitors")
def analyse_visitors(
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
):
    """Return visitor counts and daily totals for a time window."""
    end = date_to or datetime.now(timezone.utc).replace(tzinfo=None)
    start = date_from or (end - timedelta(days=30))
    if end.tzinfo is not None:
        end = end.astimezone(timezone.utc).replace(tzinfo=None)
    if start.tzinfo is not None:
        start = start.astimezone(timezone.utc).replace(tzinfo=None)
    if start > end:
        raise HTTPException(status_code=422, detail="date_from must be before date_to")
    connection = None
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT COUNT(DISTINCT v.id) AS total_visitors,
                      COUNT(DISTINCT CASE WHEN o.verified_at IS NOT NULL THEN v.id END) AS verified_visitors,
                      COUNT(DISTINCT CASE WHEN g.id IS NOT NULL THEN v.id END) AS passes_issued
               FROM visitors v
               LEFT JOIN email_otps o ON o.visitor_id = v.id
               LEFT JOIN gate_passes g ON g.visitor_id = v.id
               WHERE v.created_at BETWEEN %s AND %s""",
            (start, end),
        )
        counts = cursor.fetchone()
        cursor.execute(
            "SELECT DATE(created_at) AS visit_date, COUNT(*) AS visitors FROM visitors "
            "WHERE created_at BETWEEN %s AND %s GROUP BY DATE(created_at) ORDER BY visit_date",
            (start, end),
        )
        daily = cursor.fetchall()
        return {
            "date_from": start.isoformat(), "date_to": end.isoformat(),
            "total_visitors": counts["total_visitors"], "verified_visitors": counts["verified_visitors"],
            "passes_issued": counts["passes_issued"],
            "daily": [{"date": str(row["visit_date"]), "visitors": row["visitors"]} for row in daily],
        }
    except mysql.connector.Error as exc:
        logger.exception("Unable to load visitor analytics")
        raise HTTPException(status_code=503, detail="Analytics are temporarily unavailable") from exc
    finally:
        if connection:
            connection.close()


@app.post("/api/validate_pass")
def validate_pass(scan: PassScan):
    """Consume a valid, unexpired QR pass once at the entry gate."""
    connection = None
    try:
        connection = db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """SELECT g.id AS pass_id, g.expires_at, g.scanned_at, v.name, v.purpose
               FROM gate_passes g JOIN visitors v ON v.id = g.visitor_id
               WHERE g.token_hash = %s LIMIT 1""",
            (keyed_digest(scan.token),),
        )
        record = cursor.fetchone()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not record or record["expires_at"] <= now or record["scanned_at"] is not None:
            return {"valid": False, "message": "Pass is invalid, expired, or has already been used."}
        cursor.execute("UPDATE gate_passes SET scanned_at = %s WHERE id = %s AND scanned_at IS NULL", (now, record["pass_id"]))
        if cursor.rowcount != 1:
            connection.rollback()
            return {"valid": False, "message": "Pass has already been used."}
        connection.commit()
        return {"valid": True, "message": "Entry approved", "visitor": record["name"], "purpose": record["purpose"]}
    except mysql.connector.Error as exc:
        logger.exception("Unable to validate gate pass")
        raise HTTPException(status_code=503, detail="Pass validation is temporarily unavailable") from exc
    finally:
        if connection:
            connection.close()
