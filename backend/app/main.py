import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from starlette.responses import Response

from app.config import settings
from app.database import close_redis
from app.routers import access, auth, devices, edge
from app.services.mqtt_worker import mqtt_consumer_loop

REQUEST_COUNT = Counter("yemekhane_http_requests_total", "HTTP requests", ["method", "path"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop = asyncio.Event()
    task = asyncio.create_task(mqtt_consumer_loop(stop))
    yield
    stop.set()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    await close_redis()


app = FastAPI(title="Yemekhane API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.url.path != "/metrics":
        REQUEST_COUNT.labels(request.method, request.url.path).inc()
    return response

app.include_router(auth.router)
app.include_router(access.router)
app.include_router(devices.router)
app.include_router(edge.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
