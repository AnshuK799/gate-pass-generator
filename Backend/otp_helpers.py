"""Generate and validate six-digit email verification codes."""

import random

from db_helpers import check_email_otp, store_email_otp


def generate_otp(email):
    """Store a random six-digit OTP for the email and return it."""
    if not isinstance(email, str) or not email.strip():
        return None

    otp = f"{random.randint(0, 999999):06d}"
    if store_email_otp(email.strip(), otp):
        return otp
    return None


def check_otp(email, otp):
    """Return True if the email's OTP matches and has not expired."""
    if not isinstance(email, str) or not email.strip():
        return False
    if not isinstance(otp, str) or len(otp) != 6 or not otp.isdigit():
        return False
    return check_email_otp(email.strip(), otp)
