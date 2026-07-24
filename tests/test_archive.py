import archive


def _a(name="a/b", **kw):
    d = {"url": f"https://github.com/{name}", "full_name": name, "score": 3,
         "category": "AI", "language": "Python", "stars_today": 10, "stars": 100,
         "summary": "s", "problem_solved": "p", "reason": "r", "is_surge": False}
    d.update(kw)
    return d


def test_save_and_index(tmp_path):
    archive.save("2026-07-08", "综述一", [_a()], docs_dir=tmp_path)
    archive.save("2026-07-09", "综述二", [_a(), _a("c/d")], docs_dir=tmp_path)

    report = (tmp_path / "2026-07-08.html").read_text()
    assert "a/b" in report and "综述一" in report

    index = (tmp_path / "index.html").read_text()
    assert index.index("2026-07-09.html") < index.index("2026-07-08.html"), "索引应倒序"
    assert "2 signals" in index and "2 SCANS" in index


def test_report_escapes_injection(tmp_path):
    evil = _a(summary="<script>alert(1)</script>")
    archive.save("2026-07-08", "<b>o</b>", [evil], docs_dir=tmp_path)
    html = (tmp_path / "2026-07-08.html").read_text()
    assert "<script>alert" not in html and "&lt;script&gt;" in html
    assert "<b>o</b>" not in html


def test_surge_badge_and_signal_bars(tmp_path):
    archive.save("2026-07-08", "o", [_a(is_surge=True, score=4)], docs_dir=tmp_path)
    html = (tmp_path / "2026-07-08.html").read_text()
    assert "SURGE" in html
    assert html.count('<i class="on"></i>') == 4


def test_index_ignores_non_date_files(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "notes.html").write_text("x")
    archive.save("2026-07-08", "o", [_a()], docs_dir=tmp_path)
    index = (tmp_path / "index.html").read_text()
    assert "notes.html" not in index and "1 SCANS" in index


def test_save_idempotent(tmp_path):
    archive.save("2026-07-08", "v1", [_a()], docs_dir=tmp_path)
    archive.save("2026-07-08", "v2", [_a(), _a("c/d")], docs_dir=tmp_path)
    assert "v2" in (tmp_path / "2026-07-08.html").read_text()
    index = (tmp_path / "index.html").read_text()
    assert "1 SCANS" in index and "2 signals" in index


def test_save_with_topic_groups(tmp_path):
    a = {"full_name": "a/b", "url": "https://github.com/a/b", "score": 3,
         "category": "AI", "language": "Python", "stars_today": 5, "stars": 100,
         "summary": "s", "problem_solved": "p", "reason": "r", "is_surge": False}
    groups = [{"topic": "llm", "analyses": [dict(a, full_name="c/d")]}]
    path = archive.save("2026-07-08", "综述", [a], topic_groups=groups, docs_dir=tmp_path)
    html = path.read_text(encoding="utf-8")
    assert "按主题推荐" in html
    assert "llm" in html
    assert "c/d" in html
