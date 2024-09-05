from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, schemas, crud, auth
from kafka_producer import send_notification
from session_manager import session_manager
from database import SessionLocal, engine
from typing import List
from models import Notification as NotificationModel


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        user_id=user.id, expires_delta=access_token_expires
    )
    session_manager.store_token(access_token, user.id)
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    access_token = token
    # Check if the token exists in Redis
    if not session_manager.get_user_id(access_token):
        raise HTTPException(status_code=400, detail="Token not found or already expired")
    
    # Delete the token
    session_manager.delete_token(access_token)
    return {"message": "Successfully logged out"}




@app.post("/weight_entries", response_model=schemas.WeightEntryWithProgress)
def create_weight_entry(
    weight_entry: schemas.WeightEntryCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int
    result = crud.create_weight_entry(db=db, user_id=user_id, entry=weight_entry)
    return result

@app.delete("/weight-entries/{entry_id}", response_model=schemas.WeightEntry)
def delete_weight_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = int(user_id)  # Convert user_id from bytes to int

    # Check if the weight entry exists and belongs to the user
    entry = crud.get_weight_entry_by_id(db, entry_id=entry_id)

    if entry is None or entry.user_id != user_id:
        raise HTTPException(status_code=404, detail="Weight entry not found or unauthorized")

    # Delete the weight entry
    deleted_entry = crud.delete_weight_entry(db=db, entry=entry)
    
    return deleted_entry

@app.patch("/weight-entries/{entry_id}", response_model=schemas.WeightEntry)
def update_weight_entry(
    entry_id: int,
    entry_update: schemas.WeightEntryUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = int(user_id)  # Convert user_id from bytes to int

    # Retrieve the weight entry by ID
    entry = crud.get_weight_entry_by_id(db, entry_id=entry_id)

    if entry is None or entry.user_id != user_id:
        raise HTTPException(status_code=404, detail="Weight entry not found or unauthorized")

    # Update the weight entry with provided fields
    updated_entry = crud.update_weight_entry(db=db, entry=entry, updated_data=entry_update)
    
    return updated_entry


@app.get("/weight_entries/{user_id}", response_model=List[schemas.WeightEntry])
def read_weight_entries(user_id: int, db: Session = Depends(get_db)):
    return crud.get_weight_entries(db, user_id=user_id)


@app.post("/weight-goals", response_model=schemas.Goal)
def create_weight_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int
    db_goal = crud.create_weight_goal(db=db, user_id=user_id, goal=goal)
    return db_goal

@app.get("/weight-goals", response_model=List[schemas.Goal])
def get_weight_goals(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int
    return crud.get_weight_goals(db, user_id)





@app.get("/weight-goal", response_model=schemas.Goal)
def get_active_weight_goal(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int
    return crud.get_active_weight_goal(db, user_id)

@app.patch("/weight-goal/{goal_id}", response_model=schemas.Goal)
def update_goal(
    goal_id: int,
    goal_update: schemas.GoalUpdate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int

    # Update the goal with provided fields
    updated_goal = crud.update_goal(
        db,
        goal_id,
        target_weight=goal_update.target_weight,
        target_date=goal_update.target_date,
        achieved=goal_update.achieved
    )
    
    if updated_goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return updated_goal

@app.delete("/weight-goals/{goal_id}", response_model=schemas.Goal)
def delete_weight_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    user_id = session_manager.get_user_id(token)  # Retrieve user ID from Redis
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int

    # Check if the goal exists and belongs to the user
    goal = crud.get_weight_goal_by_id(db, goal_id=goal_id)
    
    if goal is None or goal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Goal not found or unauthorized")

    # Delete the goal
    deleted_goal = crud.delete_weight_goal(db=db, goal=goal)
    
    return deleted_goal

@app.get("/notifications", response_model=List[schemas.Notification])
def get_user_notifications(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    # Retrieve user ID from Redis using session_manager
    user_id = session_manager.get_user_id(token)
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = int(user_id)  # Convert user_id from bytes to int
    
    # Query the notifications from the database for the given user
    notifications = db.query(NotificationModel).filter(NotificationModel.user_id == user_id).all()

    if not notifications:
        raise HTTPException(status_code=404, detail="No notifications found for the user.")
    
    return notifications




# @app.get("/weight_changes/{user_id}")
# def read_weight_changes(user_id: int, db: Session = Depends(get_db)):
#     changes = crud.get_weight_changes(db, user_id)
#     if changes:
#         return changes
#     else:
#         raise HTTPException(status_code=404, detail="No weight entries found")
