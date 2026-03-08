from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.notes import router as notes_router
from app.api.v1.projects import router as projects_router
from app.api.v1.relations import router as relations_router
from app.api.v1.tasks import router as tasks_router
from app.core.config import get_settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
from app.models import User  # noqa: F401
from app.models import Note, Project, ProjectRelation, Task  # noqa: F401
from sqlalchemy import select

settings = get_settings()


def create_default_admin() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.username == settings.ADMIN_USERNAME))
        if existing:
            return
        user = User(
            username=settings.ADMIN_USERNAME,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role='admin',
        )
        db.add(user)
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    create_default_admin()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health_check():
    return {'ok': True}


app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
app.include_router(relations_router, prefix=settings.API_V1_PREFIX)
app.include_router(notes_router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
