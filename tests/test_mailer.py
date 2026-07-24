import mailer

ANALYSIS = {
    "url": "https://github.com/a/b", "full_name": "a/b", "score": 4,
    "category": "AI", "language": "Python", "stars_today": 10, "stars": 100,
    "summary": "s", "problem_solved": "p", "reason": "r", "is_surge": False,
}


def test_render_basic():
    html = mailer.render("2026-07-08", "综述", [ANALYSIS])
    assert "a/b" in html and "⭐⭐⭐⭐" in html and "综述" in html


def test_render_escapes_html_injection():
    evil = dict(ANALYSIS, summary="<script>alert(1)</script>",
                full_name="<img src=x onerror=e()>")
    html = mailer.render("2026-07-08", "<b>o</b>", [evil])
    assert "<script>" not in html
    assert "<img src=x" not in html
    assert "&lt;script&gt;" in html


def test_render_surge_badge():
    html = mailer.render("d", "o", [dict(ANALYSIS, is_surge=True)])
    assert "🚀" in html


def test_render_topic_groups():
    groups = [{"topic": "llm", "analyses": [dict(ANALYSIS, full_name="a/llm")]}]
    html = mailer.render("2026-07-08", "综述", [ANALYSIS], topic_groups=groups)
    assert "按主题推荐" in html
    assert "llm" in html
    assert "a/llm" in html


def test_render_without_topic_groups_backward_compat():
    html = mailer.render("2026-07-08", "综述", [ANALYSIS])
    assert "按主题推荐" not in html
    assert "a/b" in html
