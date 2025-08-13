import smtplib
from email.mime.text import MIMEText

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "sahadshaikh2209@gmail.com"
SMTP_PASSWORD = "uxzj sdjg snrb zoor"

def send_otp_email(to_email: str, otp_code: str):
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp_code}. It will expire in 10 minutes."
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
