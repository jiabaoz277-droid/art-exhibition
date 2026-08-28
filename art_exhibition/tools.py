"""确定性工具：run_sql（只读）/ campaign_overview（总览）/ list_works（筛选）。"""
import re

from sqlalchemy import text

from db import SessionLocal
from models import Campaign, Applicant, Work

MAX_SQL_ROWS = 200
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|ATTACH|DETACH|REPLACE|TRUNCATE|GRANT|REVOKE|PRAGMA|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)


def run_sql(sql: str) -> dict:
    """只读 SQL 查询（仅 SELECT/WITH，≤200 行）。"""
    s = (sql or "").strip()
    if not s:
        raise ValueError("SQL 语句为空")
    if ";" in s.rstrip(";"):
        raise ValueError("仅允许单条语句")
    s = s.rstrip(";").strip()
    head = s.lstrip().upper()
    if not (head.startswith("SELECT") or head.startswith("WITH")):
        raise ValueError("仅允许 SELECT/WITH 只读查询")
    if _FORBIDDEN.search(s):
        raise ValueError("SQL 含禁止关键字")

    with SessionLocal() as db:
        result = db.execute(text(s))
        rows = result.fetchmany(MAX_SQL_ROWS + 1)
        if len(rows) > MAX_SQL_ROWS:
            raise ValueError(f"查询结果超过 {MAX_SQL_ROWS} 行")
        cols = list(result.keys())
        return {"columns": cols, "rows": [list(r) for r in rows], "row_count": len(rows)}


def campaign_overview(campaign_id: int) -> dict:
    with SessionLocal() as db:
        camp = db.get(Campaign, campaign_id)
        if not camp:
            raise ValueError("活动不存在")
        applicants = db.query(Applicant).filter(Applicant.campaign_id == campaign_id).all()
        works = db.query(Work).join(Applicant).filter(Applicant.campaign_id == campaign_id).all()

        school_dist: dict = {}
        medium_dist: dict = {}
        for w in works:
            s = (w.school or "").strip() or "未填写"
            m = (w.medium or "").strip() or "未填写"
            school_dist[s] = school_dist.get(s, 0) + 1
            medium_dist[m] = medium_dist.get(m, 0) + 1

        artist_list = [{
            "name": a.name,
            "phone": a.phone,
            "email": a.email,
            "wechat": a.wechat,
            "work_count": len(a.works),
            "status": a.status,
            "resume_path": a.resume_path,
        } for a in applicants]

        return {
            "campaign_id": campaign_id,
            "campaign_title": camp.title,
            "applicant_count": len(applicants),
            "work_count": len(works),
            "school_distribution": school_dist,
            "medium_distribution": medium_dist,
            "artist_list": artist_list,
        }


def list_works(campaign_id: int, medium: str | None = None, school: str | None = None,
               has_resume: str | None = None) -> list:
    with SessionLocal() as db:
        q = db.query(Work).join(Applicant).filter(Applicant.campaign_id == campaign_id)
        if medium:
            q = q.filter(Work.medium == medium)
        if school:
            q = q.filter(Work.school == school)
        if has_resume == "yes":
            q = q.filter(Applicant.resume_path != "")
        elif has_resume == "no":
            q = q.filter(Applicant.resume_path == "")
        rows = q.order_by(Work.id).all()
        return [{
            "work_id": w.id,
            "title": w.title,
            "dimensions": w.dimensions,
            "medium": w.medium,
            "school": w.school,
            "price": w.price,
            "image_path": w.image_path,
            "resume_path": w.applicant.resume_path,
            "applicant_id": w.applicant.id,
            "applicant_name": w.applicant.name,
            "applicant_phone": w.applicant.phone,
            "applicant_email": w.applicant.email,
            "applicant_wechat": w.applicant.wechat,
        } for w in rows]
