import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()  # pull DATABASE_URL / SECRET_KEY etc. out of the .env file into the environment

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/oreon")  

engine = create_engine(DATABASE_URL)  
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  
Base = declarative_base()  


def get_db():
    db = SessionLocal()  
    try:
        yield db  
    finally:
        db.close()  
