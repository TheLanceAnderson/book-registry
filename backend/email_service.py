import os
import smtplib

from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL")


def send_book_notification(title, language, bought_by):
    message = EmailMessage()

    message["Subject"] = f"New Book Added: {title}"
    message["From"] = GMAIL_ADDRESS
    message["To"] = NOTIFICATION_EMAIL

    message.set_content(
        f"""A new book has been added to the registry!

Language: {language}
Added by: {bought_by}
"""
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as smtp:
        smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        smtp.send_message(message)