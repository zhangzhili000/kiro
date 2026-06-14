from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Add client_encoding parameter for PostgreSQL
DATABASE_URL = settings.DATABASE_URL
if "?" not in DATABASE_URL:
    DATABASE_URL += "?client_encoding=utf8"
else:
    DATABASE_URL += "&client_encoding=utf8"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
