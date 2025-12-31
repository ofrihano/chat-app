from pydantic import BaseModel
from datetime import datetime

# 1. Base Schema (Shared properties)
class UserBase(BaseModel):
    username: str

# 2. Schema for creating a user (Registration)
# We need the password here so the user can sign up
class UserCreate(UserBase):
    password: str

# 3. Schema for reading a user (Response)
# We DO NOT include the password here for security
class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        # This tells Pydantic to treat the SQLAlchemy model as a dictionary
        from_attributes = True