"""配置读取：所有敏感信息与模型参数通过环境变量 / .env 注入，不硬编码。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV = os.getenv("ENV", "dev").strip().lower()
load_dotenv(BASE_DIR / ".env")


def _is_writable(path: Path) -> bool:
    try:
        probe = path / ".write_probe"
        probe.touch()
        probe.unlink()
        return True
    except Exception:
        return False


def _resolve_db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        if url.startswith("sqlite:///"):
            p = url[len("sqlite:///"):]
            if p.startswith("./"):
                return f"sqlite:///{BASE_DIR / p[2:]}"
        return url
    # 生产环境或代码目录只读（veFaaS 实例）→ 落到 /tmp
    if ENV == "prod" or not _is_writable(BASE_DIR):
        return "sqlite:////tmp/data/app.db"
    return f"sqlite:///{BASE_DIR / 'data' / 'app.db'}"


def _resolve_upload_dir() -> Path:
    v = os.getenv("UPLOAD_DIR", "").strip()
    if v:
        return Path(v)
    if ENV == "prod" or not _is_writable(BASE_DIR):
        return Path("/tmp/uploads")
    return BASE_DIR / "data" / "uploads"


class Settings:
    env: str = ENV

    # 模型（OpenAI 兼容接口）
    model_base_url: str = os.getenv("MODEL_BASE_URL", "https://api.deepseek.com/v1")
    model_api_key: str = os.getenv("MODEL_API_KEY", "")
    model_name: str = os.getenv("MODEL_NAME", "deepseek-chat")

    # 后台管理员密钥
    admin_key: str = os.getenv("ADMIN_KEY", "change-me-admin-key")

    # 持久化
    database_url: str = _resolve_db_url()
    upload_dir: Path = _resolve_upload_dir()

    # 征集规则默认值（可被活动覆盖）
    default_image_formats: str = os.getenv("DEFAULT_IMAGE_FORMATS", "jpg,jpeg,png,webp")
    default_max_image_mb: float = float(os.getenv("DEFAULT_MAX_IMAGE_MB", "10"))
    resume_formats: list = ["pdf", "docx"]
    resume_max_mb: float = float(os.getenv("RESUME_MAX_MB", "20"))

    # 服务
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
