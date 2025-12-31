from fastapi import FastAPI, WebSocket, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import engine, get_db
from app import models, schemas, crud, auth
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.config import SECRET_KEY, ALGORITHM

# Create the database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Real-Time Chat App")

# --- Routes ---

@app.get("/")
def read_root():
    return {"status": "Chat API is running"}

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Username already registered"
        )
    
    # 2. Create the new user
    return crud.create_user(db=db, user=user)

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. Find the user in the DB
    user = crud.get_user_by_username(db, username=form_data.username)
    
    # 2. Check if user exists AND if password is correct
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Create the JWT Token
    access_token = auth.create_access_token(data={"sub": user.username})
    
    # 4. Return the token to the user
    return {"access_token": access_token, "token_type": "bearer"}


# This tells FastAPI that the route to get a new token is "/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decode the token using our SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the username from the token
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # 3. Check if the user still exists in the database
    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
        
    return user

# --- WebSocket (Phase 2 Placeholder) ---
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message received in room {room_id}: {data}")

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user