from app.models.project import Project

def create_project(db, user, name, description):
    project = Project(
        name=name,
        description=description,
        user_id=user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_projects(db, user):
    return db.query(Project).filter(Project.user_id == user.id).all()