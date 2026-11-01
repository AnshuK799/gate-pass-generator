import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "mysql")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "gate_pass")
DB_USER = os.getenv("DB_USER", "gate_pass_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")
OTP_DELIVERY = os.getenv("OTP_DELIVERY", "auto").lower()
SMTP_CONFIGURED = all((SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM))
