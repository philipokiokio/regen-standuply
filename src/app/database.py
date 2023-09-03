from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.app.config import database_settings


SQL_DATABASE_URL = f"postgresql://{database_settings.db_username}:{database_settings.db_password}@{database_settings.db_host_}:{database_settings.db_port}/{database_settings.db_name}"


engine = create_engine(SQL_DATABASE_URL)

SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


# Base

Base = declarative_base()


# DB SESSION


def get_db():
    with SessionLocal() as session:
        yield session
