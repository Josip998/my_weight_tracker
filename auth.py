from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import crud
import schemas
from database import get_db

# Configuration settings
SECRET_KEY = "your_secret_key_here"  # Change this to a more secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify the provided password against the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a hashed version of the password."""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user based on username and password."""
    user = crud.get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(user_id: int, expires_delta: timedelta = None) -> str:
    """Create a JWT token with the specified expiration time."""
    to_encode = {"sub": str(user_id)}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.User:
    """Retrieve the current user based on the provided token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))  # Ensure you cast it to an integer
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, user_id)  # Assuming get_user fetches by user_id
    if user is None:
        raise credentials_exception
    return user
