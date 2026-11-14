from backend.email_service import send_book_notification

send_book_notification(
    title="The Hobbit",
    author="J.R.R. Tolkien",
    language="English",
    bought_by="Test User"
)

print("Test email sent successfully!")