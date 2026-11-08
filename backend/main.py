from fastapi import FastAPI, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from fastapi import HTTPException, status
from backend.schemas import BookCreate

from backend.database import SessionLocal
from backend.models import Book


app = FastAPI(title="Book Registry API")


# Creates a database session for each request
def get_db():
    with SessionLocal() as db:
        yield db


@app.get("/")
def home():
    return {"message": "Book Registry API is running!"}


@app.get("/books/search")
def search_books(
    q: str = Query(min_length=2),
    db: Session = Depends(get_db)
):
    # Normalize the search query
    search = func.lower(func.unaccent(q.strip()))

    # Normalize titles and authors
    title = func.lower(func.unaccent(Book.title))
    author = func.lower(func.unaccent(Book.author))

    # Similarity calculations
    title_similarity = func.similarity(title, search)
    partial_similarity = func.word_similarity(search, title)
    author_similarity = func.similarity(author, search)
    author_partial = func.word_similarity(search, author)

    # Score used to find relevant books
    relevance = func.greatest(
        title_similarity,
        partial_similarity * 0.9,
        author_similarity * 0.7,
        author_partial * 0.6
    )

    # Score used to determine strong vs weak matches
    completeness = func.least(
        1.0,
        func.length(search) / func.greatest(func.length(title), 1)
    )

    # Final classification score
    score = relevance * completeness

    statement = (
        select(Book, score.label("score"))
        .where(
            or_(
                title_similarity >= 0.2,
                partial_similarity >= 0.4,
                author_similarity >= 0.3,
                author_partial >= 0.5
            )
        )
        .order_by(score.desc())
        .limit(20)
    )

    results = db.execute(statement).all()

    strong_matches = []
    weak_matches = []

    for book, similarity_score in results:
        book_data = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "bought_by": book.bought_by,
            "language": book.language,
            "similarity": round(similarity_score, 3)
        }

        if similarity_score >= 0.65:
            strong_matches.append(book_data)
        else:
            weak_matches.append(book_data)

    return {
        "strong_matches": strong_matches,
        "weak_matches": weak_matches
    }

@app.post("/books", status_code=status.HTTP_201_CREATED)
def add_book(
    book: BookCreate,
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

    return {
        "message": "Book added successfully!",
        "id": new_book.id,
        "title": new_book.title,
        "author": new_book.author,
        "bought_by": new_book.bought_by,
        "language": new_book.language
    }