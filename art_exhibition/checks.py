"""核验逻辑：确定性检查（硬事实，必跑）+ 模型语义核验（增强，可降级）。"""
from pathlib import Path

from config import settings
from schemas import CheckReportOut
from agent import llm_check


def deterministic_check(applicant: dict, works: list, rules: dict) -> dict:
    """确定性核验：缺失项与格式问题，纯函数、可单测。"""
    missing: list = []
    fmt: list = []

    name = (applicant.get("name") or "").strip()
    phone = (applicant.get("phone") or "").strip()
    email = (applicant.get("email") or "").strip()
    wechat = (applicant.get("wechat") or "").strip()
    resume = (applicant.get("resume_path") or "").strip()

    if not name:
        missing.append("姓名未填写")
    if not phone:
        missing.append("电话未填写")
    if not email and not wechat:
        missing.append("邮箱与微信至少填写一项")
    if not resume:
        missing.append("未上传个人简历")
    if not works:
        missing.append("未提交任何作品")

    allowed = [f.strip().lower().lstrip(".") for f in str(rules.get("image_formats", "")).split(",") if f.strip()]
    max_mb = rules.get("max_image_mb")

    for i, w in enumerate(works, 1):
        lab = f"作品{i}"
        for k, cn in [("title", "作品名"), ("dimensions", "尺寸"), ("medium", "画种"),
                      ("school", "毕业院校"), ("price", "价格")]:
            if not (w.get(k) or "").strip():
                missing.append(f"{lab}：{cn}未填写")

        img = (w.get("image_path") or "").strip()
        if not img:
            missing.append(f"{lab}：未上传照片")
        else:
            ext = Path(img).suffix.lstrip(".").lower()
            if allowed and ext not in allowed:
                fmt.append(f"{lab}：照片格式 .{ext} 不在允许范围（{'、'.join(allowed)}）")
            sz = w.get("image_size_mb")
            if sz is not None and max_mb and float(sz) > float(max_mb):
                fmt.append(f"{lab}：照片大小 {sz:.1f}MB 超过上限 {max_mb}MB")
            if w.get("image_parse_error"):
                fmt.append(f"{lab}：照片无法解析（{w['image_parse_error']}），请确认文件完整")

    return {"missing": missing, "format_issues": fmt, "notes": ""}


def run_check(applicant: dict, works: list, rules: dict) -> CheckReportOut:
    """确定性 + 模型合并：确定性负责硬事实，模型补充语义发现。"""
    det = deterministic_check(applicant, works, rules)

    llm = None
    if settings.model_api_key:
        llm = llm_check({
            "applicant": {k: applicant.get(k) for k in ("name", "phone", "email", "wechat")},
            "resume_uploaded": bool((applicant.get("resume_path") or "").strip()),
            "works": [{
                "title": w.get("title"), "dimensions": w.get("dimensions"),
                "medium": w.get("medium"), "school": w.get("school"),
                "price": w.get("price"), "has_image": bool((w.get("image_path") or "").strip()),
                "image_format": (Path(w.get("image_path") or "").suffix.lstrip(".").lower() or None),
                "image_size_mb": w.get("image_size_mb"),
            } for w in works],
            "rules": rules,
        })

    missing = list(det["missing"])
    fmt = list(det["format_issues"])
    notes = det["notes"]

    if llm is not None:
        for m in (llm.missing or []):
            if m and m not in missing:
                missing.append(m)
        for f in (llm.format_issues or []):
            if f and f not in fmt:
                fmt.append(f)
        if llm.notes:
            notes = llm.notes

    return CheckReportOut(missing=missing, format_issues=fmt, notes=notes)
