import random
from datetime import datetime, timedelta

def generate_otp():
    """Returns a 4-digit OTP and expiry time (2 min)."""
    otp_code = str(random.randint(1000, 9999))  # 4-digit
    otp_expiry = datetime.utcnow() + timedelta(minutes=2)
    return otp_code, otp_expiry

