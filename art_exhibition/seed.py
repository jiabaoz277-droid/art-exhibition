"""种子数据：示例活动 + 示例投稿，便于演示与验收（python seed.py）。"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PIL import Image  # noqa: E402

from db import SessionLocal, init_db  # noqa: E402
from models import Campaign  # noqa: E402
from schemas import CampaignCreate  # noqa: E402
from services import create_campaign, submit_submission  # noqa: E402


def _png(color):
    buf = io.BytesIO()
    Image.new("RGB", (60, 60), color).save(buf, "PNG")
    return buf.getvalue()


class FakeUpload:
    def __init__(self, filename, data):
        self.filename = filename
        self.file = io.BytesIO(data)


def seed():
    init_db()
    with SessionLocal() as db:
        if db.query(Campaign).count() > 0:
            print("数据库已有数据，跳过种子。")
            return
        camp = create_campaign(db, CampaignCreate(
            title="2025 高校美术作品展征集",
            description="面向高校学子的纯艺/设计类原创作品征集，题材、风格、数量不限。",
            image_formats="jpg,jpeg,png,webp",
            max_image_mb=10,
        ))
        print(f"活动已创建，投递链接：/s/{camp.link_token}")

        samples = [
            ("张同学", "中央美术学院", "油画", (200, 60, 60)),
            ("李同学", "中国美术学院", "国画", (60, 120, 200)),
            ("王同学", "四川美术学院", "版画", (60, 160, 90)),
        ]
        for name, school, medium, color in samples:
            resume = FakeUpload(f"{name}简历.pdf", b"%PDF-1.4 demo resume content")
            img = FakeUpload(f"{name}作品.png", _png(color))
            applicant, report = submit_submission(
                db, camp, name=name, phone="13800000000", email=f"{name}@example.com",
                wechat=f"wx_{name}", resume_file=resume,
                works_data=[{"title": "作品一号", "dimensions": "60x80cm",
                             "medium": medium, "school": school, "price": "3000"}],
                image_files=[img],
            )
            print(f"已创建投稿：{name}（applicant_id={applicant.id}），核验缺失项={report.missing}")
    print("种子数据完成。")


if __name__ == "__main__":
    seed()
