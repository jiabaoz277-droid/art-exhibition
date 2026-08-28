"""pytest 固定环境：测试前注入临时 SQLite/上传目录/无 Key，再导入应用。"""
import os
import sys
import tempfile
from pathlib import Path

# 必须在导入应用前设置环境
_TMP = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP.name) / 'test.db'}"
os.environ["UPLOAD_DIR"] = str(Path(_TMP.name) / "uploads")
os.environ["ADMIN_KEY"] = "test-admin-key"
os.environ["MODEL_API_KEY"] = ""  # 无 Key：模型相关能力走确定性降级

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import models  # noqa: F401,E402  注册模型
from db import Base, engine  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c
