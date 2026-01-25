import os
import psycopg
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True, connect_args={"sslmode": "require"})

# Metadata object used for creating tables later (if needed)
metadata = MetaData()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency for FastAPI endpoints.
    Yields a database session and ensures it closes automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()