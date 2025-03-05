import logging
import sys
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app, CollectorRegistry

import uvicorn
from api.routers.task import router as task_router
from api.routers.parser import router as parser_router
from api.routers.review import router as review_router
from api.routers.profile import router as profile_router
from config import settings
from database import sessionmanager
from logger import init_logger
from fastapi import (
    FastAPI,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from prom.prometheus import (
    PROM_HANDLERS,
    time_request,
)


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if settings.debug_logs else logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()

# app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/api/docs", root_path="/test/parser/")
app = FastAPI(lifespan=lifespan, title=settings.project_name, docs_url="/api/docs")

# CORS
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
@time_request
async def root(request: Request):
    PROM_HANDLERS['request_count'].labels(
        "GET", "/", 200,
    ).inc()
    return {"message": "Hello World"}


# Routers
app.include_router(task_router)
app.include_router(parser_router)
app.include_router(profile_router)
app.include_router(review_router)
# app.include_router(instagram_router)


if __name__ == "__main__":
    # suppress logging
    logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    logger.setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
    # init_logger()
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)
