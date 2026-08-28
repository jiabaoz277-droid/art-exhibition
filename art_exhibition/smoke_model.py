"""真实模型端到端冒烟测试：核验 / 简报 / 问答 三条链路。

用法（需先在 .env 配置 MODEL_API_KEY）：
    ./.venv/bin/python smoke_model.py
"""
import time

from config import settings
from checks import run_check
from services import make_brief, answer_question


def main() -> None:
    print("=== 模型配置 ===")
    print("base_url:", settings.model_base_url)
    print("model:", settings.model_name)
    print("key 已配置:", bool(settings.model_api_key))

    print("\n=== ① 核验 check_submission ===")
    t0 = time.time()
    rep = run_check(
        {"name": "张同学", "phone": "13800000000", "email": "z@x.com", "wechat": "", "resume_path": "r.pdf"},
        [{"title": "作品一号", "dimensions": "60x80cm", "medium": "油画", "school": "中央美院",
          "price": "3000", "image_path": "x.png"}],
        {"image_formats": "jpg,png", "max_image_mb": 10},
    )
    print(f"耗时 {time.time() - t0:.1f}s")
    print("missing:", rep.missing)
    print("format_issues:", rep.format_issues)
    print("notes:", rep.notes[:200])

    print("\n=== ② 简报 generate_brief（默认活动 id=1） ===")
    t0 = time.time()
    b = make_brief(1)
    print(f"source={b['source']}  耗时 {time.time() - t0:.1f}s")
    print(b["brief"][:400])

    print("\n=== ③ 智能问答 answer_query（Agent 工具分发） ===")
    t0 = time.time()
    a = answer_question("本次征集有哪些学校投稿？", 1)
    print(f"used_llm={a['used_llm']}  tool={a['tool']}  耗时 {time.time() - t0:.1f}s")
    print(a["answer"][:400])


if __name__ == "__main__":
    main()
