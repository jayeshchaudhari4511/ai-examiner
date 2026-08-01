import os
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', SMTP_USER)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


def send_email(to_email: str, subject: str, html_body: str) -> None:
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASSWORD:
        raise Exception('SMTP is not configured')

    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_email], msg.as_string())


def build_reset_email(to_email: str, token: str) -> dict:
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    subject = 'Reset your AI Examiner password'
    html_body = f"""
    <p>Hi,</p>
    <p>Click the link below to reset your password:</p>
    <p><a href=\"{reset_url}\">Reset Password</a></p>
    <p>If you did not request this, you can ignore this email.</p>
    """
    return {'to': to_email, 'subject': subject, 'html': html_body}
