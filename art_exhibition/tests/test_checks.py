"""核验逻辑单测（确定性检查 + 合并）。"""
from checks import deterministic_check


def _ok_applicant():
    return {"name": "张三", "phone": "138", "email": "z@x.com", "wechat": "", "resume_path": "r.pdf"}


def _ok_work():
    return {"title": "t", "dimensions": "d", "medium": "油画", "school": "中央美院",
            "price": "100", "image_path": "x.png"}


def test_missing_contact_and_resume():
    det = deterministic_check({"name": "", "phone": "", "email": "", "wechat": "", "resume_path": ""},
                              [], {"image_formats": "jpg,png", "max_image_mb": 10})
    assert "姓名未填写" in det["missing"]
    assert "电话未填写" in det["missing"]
    assert "邮箱与微信至少填写一项" in det["missing"]
    assert "未上传个人简历" in det["missing"]
    assert "未提交任何作品" in det["missing"]


def test_email_only_is_ok():
    det = deterministic_check(_ok_applicant(), [_ok_work()], {"image_formats": "jpg,png", "max_image_mb": 10})
    assert "邮箱与微信至少填写一项" not in det["missing"]


def test_missing_work_fields():
    w = {"title": "", "dimensions": "", "medium": "", "school": "", "price": "", "image_path": "x.png"}
    det = deterministic_check(_ok_applicant(), [w], {"image_formats": "jpg,png", "max_image_mb": 10})
    for field in ["作品名", "尺寸", "画种", "毕业院校", "价格"]:
        assert any(f"作品1：{field}未填写" in m for m in det["missing"])


def test_bad_extension_is_format_not_missing():
    w = _ok_work()
    w["image_path"] = "x.gif"
    det = deterministic_check(_ok_applicant(), [w], {"image_formats": "jpg,png", "max_image_mb": 10})
    assert any("照片格式 .gif" in f for f in det["format_issues"])
    assert "作品1：未上传照片" not in det["missing"]


def test_oversize_is_format_issue():
    w = _ok_work()
    w["image_size_mb"] = 11.0
    det = deterministic_check(_ok_applicant(), [w], {"image_formats": "jpg,png", "max_image_mb": 10})
    assert any("超过上限" in f for f in det["format_issues"])


def test_parse_error_is_format_issue_not_missing():
    w = _ok_work()
    w["image_parse_error"] = "broken"
    det = deterministic_check(_ok_applicant(), [w], {"image_formats": "jpg,png", "max_image_mb": 10})
    assert any("照片无法解析" in f for f in det["format_issues"])
    assert "作品1：未上传照片" not in det["missing"]
