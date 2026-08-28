"""图片内容审核：用视觉（多模态）模型识别色情裸露/政治敏感/暴力等违规内容。

未配置 MODERATION_MODEL 时审核关闭；审核调用失败时返回 None（fail-open，不阻断上传）。
"""
import base64
from typing import Optional

from openai import OpenAI

from config import settings
from schemas import ModerationResult
from agent import _extract_json

MODERATION_SYSTEM = (
    "你是严格的图片内容安全审核助手，负责识别投稿图片中的违规内容。\n"
    "只输出一个 JSON 对象，结构必须严格为：\n"
    "{\"safe\": true|false, \"category\": \"类别\", \"reason\": \"简短原因\"}\n"
    "违规类别：色情裸露、政治敏感、暴力恐怖、违法违规、其他违规。\n"
    "判定规则：\n"
    "- 图片含色情、淫秽、性暗示、露骨裸露 → safe=false，category=色情裸露\n"
    "- 图片含政治敏感内容（敏感旗帜、标语、敏感人物、争议事件）→ safe=false，category=政治敏感\n"
    "- 图片含血腥暴力、恐怖主义符号 → safe=false，category=暴力恐怖\n"
    "- 图片含违法内容（毒品、枪支、赌博等）→ safe=false，category=违法违规\n"
    "- 正常艺术创作（含古典人体写生、油画、雕塑等艺术性内容，非色情）→ safe=true\n"
    "- 无法判断或图片模糊 → safe=true\n"
    "只输出 JSON，禁止输出 JSON 以外的文字、解释或 Markdown 代码块。"
)


def moderate_image(image_bytes: bytes, mime: str = "image/png") -> Optional[ModerationResult]:
    """审核图片；未配置审核模型或调用失败时返回 None。"""
    if not settings.moderation_enabled:
        return None
    try:
        b64 = base64.b64encode(image_bytes).decode()
        data_url = f"data:{mime};base64,{b64}"
        client = OpenAI(
            base_url=settings.moderation_base_url,
            api_key=settings.moderation_api_key,
            timeout=30.0,
            max_retries=1,
        )
        resp = client.chat.completions.create(
            model=settings.moderation_model,
            messages=[
                {"role": "system", "content": MODERATION_SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": "请审核这张图片"},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ]},
            ],
            temperature=0,
        )
        content = resp.choices[0].message.content or ""
        data = _extract_json(content)
        return ModerationResult(**data)
    except Exception:
        return None
