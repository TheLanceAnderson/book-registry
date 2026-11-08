from sqlalchemy import select

from backend.database import SessionLocal
from backend.models import Book


sample_books = [
    {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "bought_by": "Alice",
        "language": "English",
    },
    {
        "title": "The Lord of the Rings",
        "author": "J.R.R. Tolkien",
        "bought_by": "Bob",
        "language": "English",
    },
    {
        "title": "Harry Potter and the Sorcerer's Stone",
        "author": "J.K. Rowling",
        "bought_by": "Charlie",
        "language": "English",
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "bought_by": "David",
        "language": "English",
    },
    {
        "title": "Dune Messiah",
        "author": "Frank Herbert",
        "bought_by": "Emma",
        "language": "English",
    },
    {
        "title": "Cien años de soledad",
        "author": "Gabriel García Márquez",
        "bought_by": "Fernando",
        "language": "Spanish",
    },
    {
        "title": "El amor en los tiempos del cólera",
        "author": "Gabriel García Márquez",
        "bought_by": "Gabriela",
        "language": "Spanish",
    },
    {
        "title": "Don Quijote de la Mancha",
        "author": "Miguel de Cervantes",
        "bought_by": "Hector",
        "language": "Spanish",
    },
]


def seed_database():
    with SessionLocal() as db:
        for book_data in sample_books:

            # Avoid inserting the same sample book twice
            existing_book = db.scalar(
                select(Book).where(
                    Book.title == book_data["title"],
                    Book.author == book_data["author"],
                    Book.language == book_data["language"],
                )
            )

            if existing_book is None:
                db.add(Book(**book_data))

        db.commit()

    print("Sample books inserted successfully!")


if __name__ == "__main__":
    seed_database()