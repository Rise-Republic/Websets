from fastapi import HTTPException, status, Depends
from app.models.user import User

def get_current_active_user(current_user: User = Depends(lambda: None)) -> User:
    if not current_user or not getattr(current_user, 'is_active', False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
