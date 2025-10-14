import smtplib, ssl, dns.resolver
from email.message import EmailMessage
from .config import EMAIL_SENDER, EMAIL_PASSWORD

def validate_email_exists(email: str) -> bool:
    try:
        domain = email.split('@')[1]
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except Exception:
        return False

def send_email(recipient: str, subject: str, text_body: str, html_body: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)
