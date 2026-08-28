"""API 端到端测试（mock 层：无 Key，模型走确定性降级）。"""
import io
import json

from PIL import Image


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "PNG")
    return buf.getvalue()


def _login(client):
    r = client.post("/api/v1/admin/login", json={"admin_key": "test-admin-key"})
    assert r.status_code == 200, r.text


def _create_campaign(client):
    _login(client)
    r = client.post("/api/v1/admin/campaigns", json={
        "title": "测试展", "description": "", "image_formats": "jpg,png", "max_image_mb": 10})
    assert r.status_code == 200, r.text
    return r.json()


def _submit(client, token, works, name="张三", resume=("r.pdf", b"%PDF-1.4 demo", "application/pdf"),
            image=("w.png", None, "image/png")):
    files = []
    if resume:
        files.append(("resume", resume))
    if image:
        files.append(("images", (image[0], image[1] if image[1] is not None else _png(), image[2])))
    return client.post(
        f"/api/v1/campaigns/{token}/submissions",
        data={"name": name, "phone": "138", "email": "z@x.com", "wechat": "",
              "works_json": json.dumps(works, ensure_ascii=False)},
        files=files)


def test_public_campaign_and_submit(client):
    c = _create_campaign(client)
    r = client.get(f"/api/v1/campaigns/{c['link_token']}")
    assert r.status_code == 200 and r.json()["title"] == "测试展"

    works = [{"title": "w", "dimensions": "10x10", "medium": "油画", "school": "某校", "price": "100"}]
    r = _submit(client, c["link_token"], works)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "checked"
    assert "report" in body


def test_submit_missing_name_rejected(client):
    c = _create_campaign(client)
    r = client.post(f"/api/v1/campaigns/{c['link_token']}/submissions",
                    data={"name": "", "phone": "", "email": "", "wechat": ""}, files=[])
    assert r.status_code == 400


def test_admin_requires_login(client):
    assert client.get("/api/v1/admin/campaigns").status_code == 401


def test_bad_image_extension_rejected(client):
    c = _create_campaign(client)
    works = [{"title": "w", "dimensions": "", "medium": "", "school": "", "price": ""}]
    r = _submit(client, c["link_token"], works,
                image=("w.exe", b"MZ", "application/octet-stream"))
    assert r.status_code == 400


def test_overview_works_export_brief(client):
    c = _create_campaign(client)
    works = [{"title": "w1", "dimensions": "", "medium": "油画", "school": "A校", "price": ""}]
    r = _submit(client, c["link_token"], works)
    assert r.status_code == 200, r.text
    cid = c["id"]

    o = client.get(f"/api/v1/admin/campaigns/{cid}/overview")
    assert o.status_code == 200 and o.json()["work_count"] == 1

    w = client.get(f"/api/v1/admin/campaigns/{cid}/works")
    assert w.status_code == 200 and len(w.json()) == 1

    e = client.get(f"/api/v1/admin/campaigns/{cid}/export.csv")
    assert e.status_code == 200 and "姓名" in e.text

    b = client.post(f"/api/v1/admin/campaigns/{cid}/brief", json={})
    assert b.status_code == 200
    assert b.json()["source"] == "deterministic"  # 无 Key 走降级
    assert "工作简报" in b.json()["brief"]


def test_run_sql_endpoint_readonly(client):
    _create_campaign(client)
    r = client.post("/api/v1/admin/run_sql", json={"sql": "SELECT COUNT(*) AS n FROM campaigns"})
    assert r.status_code == 200 and r.json()["row_count"] == 1
    r2 = client.post("/api/v1/admin/run_sql", json={"sql": "DELETE FROM campaigns"})
    assert r2.status_code == 400


def test_export_zip_contains_csv_images_resumes(client):
    import zipfile
    import io as _io

    c = _create_campaign(client)
    works = [{"title": "w1", "dimensions": "", "medium": "油画", "school": "A校", "price": ""}]
    r = _submit(client, c["link_token"], works,
                resume=("r.pdf", b"%PDF-1.4 demo", "application/pdf"),
                image=("w.png", None, "image/png"))
    assert r.status_code == 200, r.text

    e = client.get(f"/api/v1/admin/campaigns/{c['id']}/export.zip")
    assert e.status_code == 200
    assert e.headers["content-type"].startswith("application/zip")
    zf = zipfile.ZipFile(_io.BytesIO(e.content))
    names = zf.namelist()
    assert "export.csv" in names
    assert any(n.startswith("images/") for n in names)
    assert any(n.startswith("resumes/") for n in names)


def test_image_moderation_rejects_sensitive(client, monkeypatch):
    import config
    from schemas import ModerationResult

    monkeypatch.setattr(config.settings, "moderation_enabled", True, raising=False)
    monkeypatch.setattr("services.moderate_image",
                        lambda data: ModerationResult(safe=False, category="色情裸露", reason="含露骨裸露内容"))

    c = _create_campaign(client)
    works = [{"title": "w", "dimensions": "", "medium": "", "school": "", "price": ""}]
    r = _submit(client, c["link_token"], works, image=("w.png", None, "image/png"))
    assert r.status_code == 400
    assert "内容审核" in r.json()["detail"]


def test_image_moderation_passes_safe(client, monkeypatch):
    import config
    from schemas import ModerationResult

    monkeypatch.setattr(config.settings, "moderation_enabled", True, raising=False)
    monkeypatch.setattr("services.moderate_image",
                        lambda data: ModerationResult(safe=True, category="", reason=""))

    c = _create_campaign(client)
    works = [{"title": "w", "dimensions": "", "medium": "油画", "school": "A校", "price": ""}]
    r = _submit(client, c["link_token"], works, image=("w.png", None, "image/png"))
    assert r.status_code == 200


def test_export_xlsx_embeds_images_and_selects_columns(client):
    import openpyxl
    import io as _io

    c = _create_campaign(client)
    works = [{"title": "w1", "dimensions": "", "medium": "油画", "school": "A校", "price": ""}]
    r = _submit(client, c["link_token"], works,
                resume=("r.pdf", b"%PDF-1.4 demo", "application/pdf"),
                image=("w.png", None, "image/png"))
    assert r.status_code == 200, r.text

    e = client.get(f"/api/v1/admin/campaigns/{c['id']}/export.xlsx?columns=name,title,image")
    assert e.status_code == 200
    assert "spreadsheetml" in e.headers["content-type"]
    wb = openpyxl.load_workbook(_io.BytesIO(e.content))
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    assert headers == ["姓名", "作品名", "照片"]
    assert len(ws._images) >= 1  # 图片内嵌，不是文件名
