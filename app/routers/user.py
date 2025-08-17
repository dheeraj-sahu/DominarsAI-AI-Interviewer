# routers/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate
from app.models.user import User
from app.database import get_db
from app.routers.auth import get_current_user  
from app.routers.auth import get_password_hash
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/user", tags=["User"])

@router.get("/me")
def get_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/me")
def update_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in user.model_dump().items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/me")
def delete_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_user = db.query(User).filter(User.user_id == current_user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(db_user)
    db.commit()
    return {"msg": "User deleted"}



