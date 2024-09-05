from fastapi import HTTPException
from sqlalchemy.orm import Session
import models, schemas
from models import WeightEntry
from datetime import datetime, timedelta
from auth import get_password_hash
from sqlalchemy.exc import IntegrityError
import bcrypt
from typing import Optional
from datetime import date
from sqlalchemy import desc
from kafka_producer import send_notification
from models import Notification

#REGISTER AND LOGIN


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)  # Use passlib's hash method
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password  # Store hashed password
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise ValueError("User already exists")
    return db_user


# WEIGHT ENTRIES

def get_weight_entry_by_id(db: Session, entry_id: int):
    return db.query(models.WeightEntry).filter(models.WeightEntry.id == entry_id).first()

def update_weight_entry(db: Session, entry: models.WeightEntry, updated_data: schemas.WeightEntryUpdate):
    if updated_data.weight is not None:
        entry.weight = updated_data.weight

    db.commit()
    db.refresh(entry)  # Refresh the instance with the updated data
    return entry

def delete_weight_entry(db: Session, entry: models.WeightEntry):
    db.delete(entry)
    db.commit()
    return entry

def create_weight_entry(db: Session, user_id: int, entry: schemas.WeightEntryCreate):
    # Create a new weight entry
    db_entry = models.WeightEntry(
        user_id=user_id,
        weight=entry.weight,
        entry_date=datetime.utcnow()
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # Get the previous weight entry (the most recent entry before the current one by ID)
    previous_entry = db.query(models.WeightEntry)\
                       .filter(models.WeightEntry.user_id == user_id)\
                       .filter(models.WeightEntry.id < db_entry.id)\
                       .order_by(desc(models.WeightEntry.id))\
                       .first()

    # Calculate weight change and percentage change
    if previous_entry:
        weight_diff = entry.weight - previous_entry.weight
        percentage_change = round((weight_diff / previous_entry.weight) * 100, 2)
    else:
        weight_diff = 0
        percentage_change = 0

    # Initialize progress dictionary
    progress = {
        "goal_id": None,
        "target_weight": None,
        "weight_diff": weight_diff,
        "percentage_change": percentage_change
    }

    # Get the active weight goal
    goal = get_active_weight_goal(db, user_id)
    if goal:
        weight_diff_to_goal = entry.weight - goal.target_weight 
        if weight_diff_to_goal <= 0:
            weight_diff_to_goal = 0
        progress["goal_id"] = goal.id
        progress["target_weight"] = goal.target_weight
        progress["weight_diff"] = weight_diff_to_goal
        progress["percentage_change"] = percentage_change
        progress["goal_achieved"] = entry.weight <= goal.target_weight

        # Create the message
        progress["message"] = f"{weight_diff_to_goal} kg left until you hit your goal and your total body mass changed by {percentage_change}% since last entry"
    else:
        progress["message"] = "No active weight goal"

    # Convert db_entry to Pydantic WeightEntry
    pydantic_entry = schemas.WeightEntry.from_orm(db_entry)

    # Send Kafka notification
    notification_message = {
        "user_id": user_id,
        "weight_entry": entry.weight,
        "message": "Keep up the good work!"
    }
    send_notification('weight-notifications', notification_message)

    return schemas.WeightEntryWithProgress(entry=pydantic_entry, progress=progress)




def get_weight_entries(db: Session, user_id: int):
    return db.query(models.WeightEntry).filter(models.WeightEntry.user_id == user_id).all()


#GOALS


def create_weight_goal(db: Session, user_id: int, goal: schemas.GoalCreate):
    db_goal = models.Goal(
        user_id=user_id,
        target_weight=goal.target_weight,
        target_date=goal.target_date
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_weight_goals(db: Session, user_id: int):
    return db.query(models.Goal).filter(models.Goal.user_id == user_id).all()

def get_active_weight_goal(db: Session, user_id: int):
    return db.query(models.Goal).filter(
        models.Goal.user_id == user_id,
        models.Goal.achieved == False,
        models.Goal.target_date >= datetime.utcnow().date()
    ).first()

def update_goal(db: Session, goal_id: int, target_weight: Optional[float] = None, target_date: Optional[date] = None, achieved: Optional[bool] = None):
    # Fetch the goal
    db_goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()

    if db_goal:
        # Update fields if new values are provided
        if target_weight is not None:
            db_goal.target_weight = target_weight
        if target_date is not None:
            db_goal.target_date = target_date
        if achieved is not None:
            db_goal.achieved = achieved

        # Commit changes to the database
        db.commit()
        db.refresh(db_goal)

    return db_goal

def delete_weight_goal(db: Session, goal: models.Goal):
    db.delete(goal)
    db.commit()
    return goal

def get_weight_goal_by_id(db: Session, goal_id: int):
    return db.query(models.Goal).filter(models.Goal.id == goal_id).first()

#NOTIFICATIONS

def get_user_notifications(db: Session, user_id: int):
    return db.query(Notification).filter(Notification.user_id == user_id).all()

# def get_weight_changes(db: Session, user_id: int):
#     """Retrieve weight change information for daily, weekly, and monthly intervals."""
#     daily_entries = get_weight_entries(db, user_id, 1)
#     weekly_entries = get_weight_entries(db, user_id, 7)
#     monthly_entries = get_weight_entries(db, user_id, 30)

#     daily_change = calculate_weight_change(daily_entries, 1)
#     weekly_change = calculate_weight_change(weekly_entries, 7)
#     monthly_change = calculate_weight_change(monthly_entries, 30)

#     return {
#         "daily_change": daily_change,
#         "weekly_change": weekly_change,
#         "monthly_change": monthly_change
#     }

