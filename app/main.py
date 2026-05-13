from fastapi import FastAPI
from app.db.init_db import init_db
from app.api.project_routes import router as project_router
from app.api.auth_routes import router as auth_router
from app.api.agent_routes import router as agent_router

app = FastAPI(title="ADIM - Autonomous Decision Intelligence Mesh")

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def root():
    return {"message": "ADIM is Alive"}

# ✅ CORRECT
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(project_router, prefix="/projects", tags=["Projects"])
app.include_router(agent_router, prefix="/agent", tags=["Agentic Brain"])