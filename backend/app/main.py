from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import engine, get_db, SessionLocal
from app import models, schemas, crud, auth
from app.socket_manager import manager
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

# --- WebSocket (Real-Time Chat) ---

@app.websocket("/ws/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    await manager.connect(websocket, room_name)
    
    try:
        # Create a dedicated database session for room setup
        db = SessionLocal()
        try:
            db_room = crud.get_room_by_name(db, room_name)
            if not db_room:
                db_room = crud.create_room(db, name=room_name)
            room_id = db_room.id
        finally:
            db.close()
            
        while True:
            data = await websocket.receive_text()
            
            # Create a new database session for each message
            db = SessionLocal()
            try:
                crud.create_message(db, content=data, room_id=room_id, sender_id=None)
            except Exception as db_error:
                print(f"Database error: {str(db_error)}")
            finally:
                db.close()
            
            await manager.broadcast(f"User wrote: {data}", room_name)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_name)
        await manager.broadcast("A user left the chat", room_name)
        
    except Exception as e:
        # --- DEBUGGING: Send the error to the client so you can see it! ---
        error_msg = f"Error: {str(e)}"
        print(error_msg) # Print to terminal
        try:
            await websocket.send_text(error_msg) # Send to browser
        except:
            pass
        # -----------------------------------------------------------------
        manager.disconnect(websocket, room_name)

@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user