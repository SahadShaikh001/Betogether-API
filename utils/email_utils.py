import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "sahadshaikh2209@gmail.com"
SMTP_PASSWORD = "uxzj sdjg snrb zoor"

def send_otp_email(to_email: str, otp_code: str):
    # Read and fill HTML template
    with open("templates/email_otp.html", "r") as f:
        html_template = f.read()

    html_content = html_template.replace("{{otp_code}}", otp_code)
    html_content = html_content.replace("{{date}}", datetime.now().strftime("%d %B %Y"))

    # Create email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    # Attach HTML
    msg.attach(MIMEText(html_content, "html"))

    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
