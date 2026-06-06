from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from .core.config import settings
from .api.v1 import api_router
from .services.ai_service import faiss_service

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 超时和连接处理中间件
@app.middleware("http")
async def add_timeout_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        # 添加连接保活头
        response.headers["Connection"] = "keep-alive"
        response.headers["Keep-Alive"] = "timeout=300"
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        print(f"Request error: {e}")
        return JSONResponse(
            status_code=504,
            content={"detail": "请求处理超时，请稍后重试"}
        )

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Enterprise Knowledge Base API", "version": settings.APP_VERSION}


@app.on_event("startup")
async def startup_event():
    """应用启动时加载FAISS索引"""
    print("Loading FAISS index...")
    faiss_service.load_index()
    print(f"FAISS index loaded, {len(faiss_service.documents)} documents in index")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
