from fastapi import APIRouter

from app.api.routes import items, login, private, projects, runs, scripts, candidates, evidences, assets, aliases, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(scripts.router, prefix="/scripts", tags=["scripts"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(evidences.router, prefix="/evidences", tags=["evidences"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(aliases.router, prefix="/aliases", tags=["aliases"])


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
