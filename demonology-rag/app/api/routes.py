from fastapi import APIRouter
from app.api.endpoints import upload, query, health, search

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(query.router, tags=["query"])
api_router.include_router(search.router, tags=["search"])

