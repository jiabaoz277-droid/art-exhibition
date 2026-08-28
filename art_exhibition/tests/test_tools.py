"""确定性工具单测。"""
import secrets

import pytest

from db import SessionLocal, Base, engine
from models import Campaign, Applicant, Work
from tools import run_sql, campaign_overview, list_works


@pytest.fixture()
def seeded():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        c = Campaign(title="t", link_token=secrets.token_urlsafe(8), image_formats="jpg,png", max_image_mb=10)
        db.add(c)
        db.flush()
        a = Applicant(campaign_id=c.id, name="甲", phone="1", email="a@x.com", wechat="", status="submitted")
        db.add(a)
        db.flush()
        db.add(Work(applicant_id=a.id, title="w1", medium="油画", school="中央美院"))
        db.add(Work(applicant_id=a.id, title="w2", medium="国画", school="中央美院"))
        db.commit()
        return c.id


def test_run_sql_select(seeded):
    r = run_sql("SELECT COUNT(*) AS n FROM works")
    assert r["row_count"] == 1
    assert r["rows"][0][0] == 2


@pytest.mark.parametrize("sql", [
    "DELETE FROM works",
    "UPDATE works SET title='x'",
    "DROP TABLE works",
    "INSERT INTO works (applicant_id) VALUES (1)",
])
def test_run_sql_rejects_write(seeded, sql):
    with pytest.raises(ValueError):
        run_sql(sql)


def test_run_sql_rejects_multi_statement(seeded):
    with pytest.raises(ValueError):
        run_sql("SELECT 1; DROP TABLE works")


def test_run_sql_rejects_forbidden_keyword(seeded):
    with pytest.raises(ValueError):
        run_sql("SELECT * FROM works; PRAGMA table_info(works)")


def test_overview(seeded):
    o = campaign_overview(seeded)
    assert o["applicant_count"] == 1
    assert o["work_count"] == 2
    assert o["school_distribution"]["中央美院"] == 2
    assert o["medium_distribution"]["油画"] == 1
    assert o["medium_distribution"]["国画"] == 1
    assert "resume_path" in o["artist_list"][0]


def test_list_works_filter(seeded):
    assert len(list_works(seeded)) == 2
    assert len(list_works(seeded, medium="油画")) == 1
    assert len(list_works(seeded, school="不存在")) == 0


def test_list_works_has_resume(seeded):
    # seeded 中的申请人未上传简历
    assert len(list_works(seeded, has_resume="no")) == 2
    assert len(list_works(seeded, has_resume="yes")) == 0
