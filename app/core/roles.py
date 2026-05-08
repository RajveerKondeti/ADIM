from fastapi import HTTPException

def require_role(user, role: str):
    if user.role != role:
        raise HTTPException(status_code=403, detail="Forbidden")