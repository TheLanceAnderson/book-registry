from fastapi import FastAPI, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas import BookCreate

from fastapi import BackgroundTasks
from backend.email_service import send_book_notification

from backend.database import SessionLocal
from backend.models import Book

import re
import unicodedata

app = FastAPI(title="Book Registry API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

# Creates a database session for each request
def get_db():
    with SessionLocal() as db:
        yield db

STOP_WORDS = {
    # English
    "a", "an", "and", "as", "at", "by", "for",
    "from", "in", "into", "of", "on", "or",
    "the", "to", "with",

    # Spanish
    "a", "al", "de", "del", "el", "en", "la",
    "las", "los", "o", "para", "por", "un",
    "una", "unas", "unos", "y"
}

def normalize_words(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.casefold())

    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    words = re.findall(r"[a-z0-9]+", text)

    return {
        word for word in words
        if word not in STOP_WORDS
    }

@app.get("/")
def home():
    return {"message": "Book Registry API is running!"}



@app.get("/books/search")
def search_books(
    q: str = Query(min_length=2),
    author: str | None = None,
    db: Session = Depends(get_db)
):
    import difflib

    search_title = q.strip()
    query_words = normalize_words(search_title)
    author_words = normalize_words(author) if author else set()

    books = db.scalars(select(Book)).all()

    strong_matches = []
    weak_matches = []

    for book in books:
        book_title_words = normalize_words(book.title)
        book_author_words = normalize_words(book.author)

        # Compare meaningful title words
        shared_title_words = query_words & book_title_words
        # Match complete author words from either search field
        author_search_words = query_words | author_words

        shared_author_words = author_search_words & book_author_words

        # Also allow minor misspellings of author names
        fuzzy_author_match = any(
            difflib.SequenceMatcher(
                None, search_word, author_word
            ).ratio() >= 0.80
            for search_word in author_search_words
            for author_word in book_author_words
            if len(search_word) >= 4 and len(author_word) >= 4
        )

        # Compare full normalized titles
        search_clean = " ".join(sorted(query_words))
        title_clean = " ".join(sorted(book_title_words))

        title_similarity = difflib.SequenceMatcher(
            None,
            search_clean,
            title_clean
        ).ratio()

        # Find misspelled individual words
        fuzzy_word_match = any(
            difflib.SequenceMatcher(
                None, query_word, book_word
            ).ratio() >= 0.75
            for query_word in query_words
            for book_word in book_title_words
            if len(query_word) >= 4 and len(book_word) >= 4
        )

        # How much of the entered title matches?
        title_coverage = (
            len(shared_title_words) / len(query_words)
            if query_words else 0
        )

        # Classify results
        if (
            query_words
            and title_coverage == 1.0
            and len(query_words) > 1
        ):
            category = "strong"

        elif (
            title_similarity >= 0.80
            and title_coverage >= 0.60
        ):
            category = "strong"

        elif (
            shared_title_words
            or shared_author_words
            or fuzzy_word_match
            or fuzzy_author_match
            or title_similarity >= 0.60
        ):
            category = "weak"

        else:
            continue

        book_data = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "bought_by": book.bought_by,
            "language": book.language,
            "similarity": round(title_similarity, 3)
        }

        if category == "strong":
            strong_matches.append(book_data)
        else:
            weak_matches.append(book_data)

    strong_matches.sort(
        key=lambda book: book["similarity"],
        reverse=True
    )
    weak_matches.sort(
        key=lambda book: book["similarity"],
        reverse=True
    )

    return {
        "strong_matches": strong_matches[:20],
        "weak_matches": weak_matches[:20]
    }



@app.post("/books", status_code=status.HTTP_201_CREATED)
def add_book(
    book: BookCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check whether this exact book already exists
    existing_book = db.scalar(
        select(Book).where(
            func.lower(Book.title) == book.title.strip().lower(),
            func.lower(Book.author) == book.author.strip().lower(),
            Book.language == book.language
        )
    )

    if existing_book:
        raise HTTPException(
            status_code=409,
            detail="This book is already on the list."
        )

    # Create a new book
    new_book = Book(
        title=book.title.strip(),
        author=book.author.strip(),
        bought_by=book.bought_by.strip(),
        language=book.language
    )

    # Save it to PostgreSQL
    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    background_tasks.add_task(
        send_book_notification,
        title=new_book.title,
        author=new_book.author,
        language=new_book.language,
        bought_by=new_book.bought_by
    )

    return {
        "message": "Book added successfully!",
        "id": new_book.id,
        "title": new_book.title,
        "author": new_book.author,
        "bought_by": new_book.bought_by,
        "language": new_book.language
    }