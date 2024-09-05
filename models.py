from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Use timezone-aware datetime

    # Relationships
    weight_entries = relationship("WeightEntry", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class WeightEntry(Base):
    __tablename__ = 'weight_entries'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    weight = Column(Float)
    entry_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Use timezone-aware datetime

    # Relationships
    user = relationship("User", back_populates="weight_entries")

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    target_weight = Column(Float)
    target_date = Column(Date)
    achieved = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="goals")

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    message = Column(String(255))  # Adjusted to String(255) for a reasonable length limit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))  # Timezone-aware datetime

    # Relationships
    user = relationship("User", back_populates="notifications")