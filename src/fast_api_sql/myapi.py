from fastapi import FastAPI, HTTPException, Depends
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from src.fast_api_sql.database import engine, get_db
from src.fast_api_sql.models import Base, User, UserResponse, UserCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"message" : "Intro to FastAPI with SQL"}

@app.get("/users", response_model=List[UserResponse])
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()


# Read 
@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Create
@app.post("/users/", response_model=UserResponse)
async def create_user(user: UserCreate, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists!")

    # Create new user
    new_user = User(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# Update
@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user: UserCreate, user_id: int, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user.model_dump().items():
        setattr(db_user, field, value)

    await db.commit()
    await db.refresh(db_user)
    return db_user

# Delete
@app.delete("/users/{user_id}")
async def delete_user(user_id: int, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(db_user)
    await db.commit()
    return {"message": "User deleted successfully"}
