from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# For local development, we'll use a SQLite file named "chat_app.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat_app.db"

# The engine is the entry point to the database
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of SessionLocal will be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models to inherit from
Base = declarative_base()

# Dependency to get a DB session for our routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()