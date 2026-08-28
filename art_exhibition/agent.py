"""国内模型 Agent：OpenAI 兼容接口调用 + 宽容 JSON 解析 + 结构化校验。

所有模型调用失败均返回 None，由调用方走确定性降级，绝不抛出未捕获异常。
"""
import json
from typing import Optional

from openai import OpenAI

from config import settings
from schemas import CheckReportOut

CHECK_SYSTEM = (
    "你是高校艺术赛事投稿材料的核验助手。根据征集规则与投稿材料摘要，输出核验报告。\n"
    "只输出一个 JSON 对象，结构必须严格为：\n"
    "{\"missing\": [\"缺失内容\"], \"format_issues\": [\"格式问题\"], \"notes\": \"总体说明(1-3句)\"}\n"
    "规则：\n"
    "- missing：语义层面发现缺失的内容（纯字段缺失由系统确定性检查负责，可少列或留空）。\n"
    "- format_issues：格式问题，如照片清晰度不足、简历与作品疑似不符、尺寸填写异常等。\n"
    "- notes：总体说明，1-3 句话。\n"
    "只输出 JSON，禁止输出 JSON 以外的文字、解释或 Markdown 代码块。"
)

BRIEF_SYSTEM = (
    "你是艺术赛事征集工作的后台简报撰写助手。根据给定统计数据，生成工作简报。\n"
    "必须包含四部分：1. 艺术家信息；2. 学校分布；3. 作品数量；4. 作品种类。\n"
    "用中文、条理清晰，直接输出简报正文（Markdown 列表），不要额外解释。"
)

QUERY_SYSTEM = (
    "你是数据查询规划助手。根据用户问题，从以下工具中选一个并给出参数：\n"
    "1) overview：活动统计总览（无需参数）\n"
    "2) list_works：作品明细筛选（可选参数 medium/school）\n"
    "3) run_sql：只读 SQL 查询（参数 sql，仅允许 SELECT/WITH）\n"
    "只输出一个 JSON 对象：{\"tool\": \"overview|list_works|run_sql\", \"args\": {}}。\n"
    "禁止输出 JSON 以外的内容。"
)

SYNTHESIS_SYSTEM = (
    "你是数据查询助手，把查询结果整理成简洁清晰的中文回答，直接输出回答正文，不要额外解释。"
)


def _client() -> OpenAI:
    if not settings.model_api_key:
        raise RuntimeError("未配置 MODEL_API_KEY")
    return OpenAI(
        base_url=settings.model_base_url,
        api_key=settings.model_api_key,
        timeout=60.0,
        max_retries=2,
    )


def _extract_json(text: str):
    """宽容解析：剥离代码块围栏，截取首个 JSON 对象。"""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:].lstrip()
    s = t.find("{")
    e = t.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("未找到 JSON 对象")
    return json.loads(t[s:e + 1])


def _chat(system: str, user: str) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=settings.model_name,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


def llm_check(payload: dict) -> Optional[CheckReportOut]:
    """语义核验；失败返回 None。"""
    try:
        content = _chat(CHECK_SYSTEM, json.dumps(payload, ensure_ascii=False))
        data = _extract_json(content)
        return CheckReportOut(**data)
    except Exception:
        return None


def llm_brief(overview: dict) -> Optional[str]:
    try:
        return _chat(BRIEF_SYSTEM, json.dumps(overview, ensure_ascii=False))
    except Exception:
        return None


def plan_query(question: str, campaign_id: int) -> Optional[dict]:
    try:
        content = _chat(QUERY_SYSTEM, json.dumps({"question": question, "campaign_id": campaign_id}, ensure_ascii=False))
        return _extract_json(content)
    except Exception:
        return None


def synthesize_answer(question: str, result) -> Optional[str]:
    try:
        return _chat(SYNTHESIS_SYSTEM, json.dumps({"question": question, "result": result}, ensure_ascii=False, default=str))
    except Exception:
        return None
