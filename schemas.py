from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class WeightEntryBase(BaseModel):
    weight: float


class WeightEntryCreate(WeightEntryBase):
    pass

class WeightEntry(WeightEntryBase):
    id: int
    user_id: int
    entry_date: datetime

    class Config:
        from_attributes = True

class WeightEntryWithProgress(BaseModel):
    entry: WeightEntry
    progress: Optional[dict] = None

    class Config:
        from_attributes = True

class WeightEntryUpdate(BaseModel):
    weight: Optional[float] = None

    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    target_weight: float
    target_date: date
    achieved: Optional[bool] = False

class GoalCreate(GoalBase):
    pass

class Goal(GoalBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class GoalUpdate(BaseModel):
    target_weight: Optional[float] = None
    target_date: Optional[date] = None
    achieved: Optional[bool] = None

class NotificationBase(BaseModel):
    message: str
    created_at: Optional[datetime] = None  # Use datetime instead of date

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class User(UserBase):
    id: int

    class Config:
        from_attributes = True

class WeightChangeResponse(BaseModel):
    daily_change: Optional[dict] = None
    weekly_change: Optional[dict] = None
    monthly_change: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class TokenData(BaseModel):
    email: Optional[str] = None
