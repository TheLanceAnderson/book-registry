from backend.database import engine
from backend.models import base

def create_tables():
    base.metadata.create_all(bind=engine)
    print("Tables created successfully")

if __name__ == "__main__":
    create_tables()