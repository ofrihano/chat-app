from sqlalchemy.orm import Session
from app import models, schemas
from passlib.context import CryptContext

# This tells Passlib to use "bcrypt", a powerful hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Helper function to hash passwords
def get_password_hash(password):
    return pwd_context.hash(password)

# Verify if a plain password matches the hashed one
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# We need this to check if a username already exists before registering
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Hash the password so we never store it in plain text
    hashed_password = get_password_hash(user.password)
    
    # Create the database model
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    
    # Add to the DB session, save (commit), and refresh
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user