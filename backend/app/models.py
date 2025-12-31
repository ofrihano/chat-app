from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Table
from sqlalchemy.orm import relationship  
from datetime import datetime
from .database import Base


room_members = Table(
    "room_members",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("room_id", ForeignKey("rooms.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    rooms = relationship("Room", secondary=room_members, back_populates="members")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)  # Null for private DMs
    is_private = Column(Boolean, default=False) # True for 1-on-1 chats
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("User", secondary=room_members, back_populates="rooms")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sender_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    sender = relationship("User")
    room = relationship("Room")