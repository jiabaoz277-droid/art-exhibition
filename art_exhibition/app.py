"""FastAPI 入口：页面路由 + API 挂载 + 文件服务。"""
import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from config import settings
from db import init_db, SessionLocal
from models import Campaign
from api import router

BASE = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="高校艺术赛事投稿助手", lifespan=lifespan)
app.include_router(router, prefix="/api/v1")
templates = Jinja2Templates(directory=str(BASE / "templates"))


@app.get("/", response_class=HTMLResponse)
def index():
    return RedirectResponse("/admin")


@app.get("/s/{token}", response_class=HTMLResponse)
def submit_page(token: str, request: Request):
    with SessionLocal() as db:
        camp = db.query(Campaign).filter(Campaign.link_token == token).first()
    if not camp:
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:40px'>活动不存在或链接无效</h2>",
                            status_code=404)
    return templates.TemplateResponse(request, "submit.html", {
        "token": token,
        "campaign": {"title": camp.title, "description": camp.description,
                     "image_formats": camp.image_formats, "max_image_mb": camp.max_image_mb},
    })


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin.html", {})


@app.get("/files/{name}")
def serve_file(name: str):
    safe = Path(name).name  # 防路径遍历
    path = settings.upload_dir / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(404, "文件不存在")
    mt = mimetypes.guess_type(safe)[0] or "application/octet-stream"
    return FileResponse(path, media_type=mt)
