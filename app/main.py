import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from app.api.api_router import router
from app.models import Base
from app.db.base import engine
from app.core.config import settings, BASE_DIR
from app.helpers.exception_handler import CustomException, http_exception_handler
from sqlalchemy import text

logging.config.fileConfig(settings.LOGGING_CONFIG_FILE, disable_existing_loggers=False)

with engine.connect() as connection:
    with connection.begin():
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS memotion"))

Base.metadata.create_all(bind=engine)


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME, docs_url="/docs", redoc_url='/re-docs',
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        description='''
        Base frame with FastAPI micro framework + Postgresql
            - Login/Register with JWT
            - Permission
            - CRUD User
            - Unit testing with Pytest
            - Dockerize
        '''
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(DBSessionMiddleware, db_url=settings.DATABASE_URL)
    application.include_router(router, prefix=settings.API_PREFIX)
    application.add_exception_handler(CustomException, http_exception_handler)

    # Health check endpoint
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "services": {
                "database": "connected",
                "pose_detection": "enabled" if os.getenv("POSE_DETECTION_ENABLED", "false").lower() == "true" else "disabled"
            }
        }
    
    os.makedirs("static", exist_ok=True)

    # Add CORS for static files
    @application.get("/static/{path:path}")
    async def serve_static_with_cors(path: str):
        file_path = os.path.join(BASE_DIR, 'static', path)
        if os.path.exists(file_path):
            response = FileResponse(file_path)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="File not found")

    application.mount("/static", StaticFiles(directory="static"), name="static")

    for route in application.routes:
        methods = getattr(route, 'methods', None)
        print(f"Route: {route.path} {methods}")

    return application


app = get_application()
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
