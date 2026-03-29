from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from schemas import (
    TaskCreate, TaskResponse,
    UserCreate, UserLogin, UserResponse
)
from hashing import hash_password, verify_password
from auth import create_access_token
from auth import get_current_user
from typing import List


app = FastAPI()

# deploy fix

# Create tables
models.Base.metadata.create_all(bind=engine)

# -------- Dependency --------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================
# 🔐 USER ROUTES
# ============================

# SIGNUP
@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print("PASSWORD:", user.password,len(user.password))
    
    # check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# LOGIN (version)
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user.id)})

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 1800
    }


# ============================
# 📌 TASK ROUTES
# ============================

# CREATE TASK
@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # 👈 HERE
):
    new_task = models.TaskDB(
        title=task.title,
        owner_id=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


# GET ALL TASKS
@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Task).filter(
        models.Task.owner_id == current_user.id
    ).all()


# GET SINGLE TASK
@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.TaskDB).filter(
        models.TaskDB.id == task_id,
        models.TaskDB.owner_id == current_user.id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


# UPDATE TASK
@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_task = db.query(models.TaskDB).filter(
        models.TaskDB.id == task_id,
        models.TaskDB.owner_id == current_user.id
    ).first()

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.title is not None:
        db_task.title = task.title
    if task.completed is not None:
        db_task.completed = task.completed

    db.commit()
    db.refresh(db_task)

    return db_task

# DELETE TASK
@app.delete("/tasks/{task_id}", status_code=200)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.TaskDB).filter(
        models.TaskDB.id == task_id,
        models.TaskDB.owner_id == current_user.id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}