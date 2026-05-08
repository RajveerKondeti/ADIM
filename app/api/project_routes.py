from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db  # Updated import path
from app.api.deps import get_current_user
from app.services.project_service import create_project, get_projects

router = APIRouter()

@router.post("/")
def create(
    name: str,
    description: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return create_project(db, user, name, description)
# ... rest of your code
@router.get("/")
def list_projects(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return get_projects(db, user)