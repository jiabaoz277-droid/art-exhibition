"""API 路由（前缀 /api/v1）：公开投稿侧 + 管理员侧。"""
import csv
import hashlib
import hmac
import io
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from config import settings
from db import get_db
from models import Campaign
from schemas import CampaignCreate, CampaignOut, LoginRequest, SQLQuery, QueryRequest
from services import (create_campaign, submit_submission, build_overview, export_rows,
                      export_zip, export_xlsx, make_brief, answer_question)
from tools import run_sql as run_sql_tool, list_works as list_works_tool

router = APIRouter()


def _signed() -> str:
    return hmac.new(settings.admin_key.encode(), b"admin-session", hashlib.sha256).hexdigest()


def require_admin(request: Request) -> bool:
    if not hmac.compare_digest(request.cookies.get("admin_session", ""), _signed()):
        raise HTTPException(401, "需要管理员登录")
    return True


def _campaign_or_404(db: Session, token: str) -> Campaign:
    camp = db.query(Campaign).filter(Campaign.link_token == token).first()
    if not camp:
        raise HTTPException(404, "活动不存在或链接无效")
    return camp


def _run(fn, *args, **kwargs):
    """工具/服务异常转 HTTP 错误，不泄露堆栈。"""
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        status = 404 if "活动不存在" in str(e) else 400
        raise HTTPException(status, str(e))


# ---------------- 公开：投稿侧 ----------------
@router.get("/campaigns/{token}")
def public_campaign(token: str, db: Session = Depends(get_db)):
    return CampaignOut.model_validate(_campaign_or_404(db, token))


@router.post("/campaigns/{token}/submissions")
def submit(token: str,
           db: Session = Depends(get_db),
           name: str = Form(""),
           phone: str = Form(""),
           email: str = Form(""),
           wechat: str = Form(""),
           resume: UploadFile = File(default=None),
           works_json: str = Form("[]"),
           images: List[UploadFile] = File(default=[])):
    camp = _campaign_or_404(db, token)
    try:
        works_data = json.loads(works_json or "[]")
    except Exception:
        raise HTTPException(400, "作品数据格式错误")
    applicant, report = submit_submission(db, camp, name, phone, email, wechat,
                                          resume, works_data, images or [])
    return {"applicant_id": applicant.id, "status": applicant.status, "report": report.model_dump()}


# ---------------- 管理员侧 ----------------
@router.post("/admin/login")
def admin_login(body: LoginRequest, response: Response):
    if not hmac.compare_digest(body.admin_key or "", settings.admin_key):
        raise HTTPException(401, "密钥错误")
    response.set_cookie("admin_session", _signed(), httponly=True, samesite="lax")
    return {"ok": True}


@router.post("/admin/logout")
def admin_logout(response: Response):
    response.delete_cookie("admin_session")
    return {"ok": True}


@router.get("/admin/campaigns")
def admin_campaigns(_: bool = Depends(require_admin), db: Session = Depends(get_db)):
    camps = db.query(Campaign).order_by(Campaign.id.desc()).all()
    return [CampaignOut.model_validate(c).model_dump() for c in camps]


@router.post("/admin/campaigns")
def admin_create_campaign(body: CampaignCreate, _: bool = Depends(require_admin),
                          db: Session = Depends(get_db)):
    return CampaignOut.model_validate(create_campaign(db, body)).model_dump()


@router.get("/admin/campaigns/{cid}/overview")
def admin_overview(cid: int, _: bool = Depends(require_admin)):
    return _run(build_overview, cid)


@router.get("/admin/campaigns/{cid}/works")
def admin_works(cid: int, medium: Optional[str] = None, school: Optional[str] = None,
                has_resume: Optional[str] = None, _: bool = Depends(require_admin)):
    return _run(list_works_tool, cid, medium=medium, school=school, has_resume=has_resume)


@router.get("/admin/campaigns/{cid}/export.csv")
def admin_export(cid: int, medium: Optional[str] = None, school: Optional[str] = None,
                 _: bool = Depends(require_admin)):
    rows = _run(export_rows, cid, medium=medium, school=school)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["姓名", "电话", "邮箱", "微信", "作品名", "尺寸", "画种", "毕业院校", "价格", "投稿状态"])
    w.writerows(rows)
    data = out.getvalue().encode("utf-8-sig")
    return StreamingResponse(io.BytesIO(data), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": "attachment; filename=export.csv"})


@router.get("/admin/campaigns/{cid}/export.zip")
def admin_export_zip(cid: int, medium: Optional[str] = None, school: Optional[str] = None,
                     _: bool = Depends(require_admin)):
    data = _run(export_zip, cid, medium=medium, school=school)
    return Response(content=data, media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=export.zip"})


@router.get("/admin/campaigns/{cid}/export.xlsx")
def admin_export_xlsx(cid: int, columns: Optional[str] = None, medium: Optional[str] = None,
                      school: Optional[str] = None, has_resume: Optional[str] = None,
                      _: bool = Depends(require_admin)):
    cols = [c.strip() for c in (columns or "").split(",") if c.strip()]
    data = _run(export_xlsx, cid, columns=cols, medium=medium, school=school,
                has_resume=has_resume)
    return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment; filename=export.xlsx"})


@router.post("/admin/campaigns/{cid}/brief")
def admin_brief(cid: int, _: bool = Depends(require_admin)):
    return _run(make_brief, cid)


@router.post("/admin/campaigns/{cid}/query")
def admin_query(cid: int, body: QueryRequest, _: bool = Depends(require_admin)):
    q = (body.question or "").strip()
    if not q:
        raise HTTPException(400, "问题不能为空")
    return _run(answer_question, q, cid)


@router.post("/admin/run_sql")
def admin_run_sql(body: SQLQuery, _: bool = Depends(require_admin)):
    return _run(run_sql_tool, body.sql)
