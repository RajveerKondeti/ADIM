from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.agent import ChatRequest, ChatResponse
from app.services.agent_engine import generate_response

router = APIRouter()

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the ADIM agent",
)
def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    context = (
        "You are ADIM (Autonomous Decision Intelligence Mesh), "
        "an AI operations assistant. Be precise and actionable."
    )
    project_context_used = False

    if body.project_id:
        project = (
            db.query(Project)
            .filter(Project.id == body.project_id, Project.user_id == current_user.id)
            .first()
        )
        if project:
            context += (
                f"\n\n[PROJECT CONTEXT]\n"
                f"Name: {project.name}\n"
                f"Description: {project.description or 'No description provided.'}"
            )
            project_context_used = True

    full_prompt = f"{context}\n\n[USER]\n{body.prompt}"
    response_text = generate_response(full_prompt)

    return ChatResponse(
        response=response_text,
        project_context_used=project_context_used,
    )