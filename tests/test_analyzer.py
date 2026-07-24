import analyzer
from scraper import Repo


def test_extract_json_plain():
    assert analyzer._extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_fenced():
    assert analyzer._extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_surrounding_text():
    assert analyzer._extract_json('前缀 {"a": 1} 后缀') == {"a": 1}


def _ok_response(_kwargs):
    content = '{"summary":"s","category":"AI","problem_solved":"p","score":4,"reason":"r"}'
    msg = type("M", (), {"content": content})()
    return type("R", (), {"choices": [type("C", (), {"message": msg})()]})()


def _rf_error(kwargs):
    if "response_format" in kwargs:
        raise RuntimeError("response_format not supported")
    return _ok_response(kwargs)


class _FakeCompletions:
    def __init__(self, behavior):
        self.behavior = behavior
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.behavior(kwargs)


class _FakeClient:
    def __init__(self, behavior):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(behavior)})()


def test_analyze_repo_fallback_when_response_format_unsupported():
    fake = _FakeClient(_rf_error)
    repo = Repo("o/a", "https://github.com/o/a", description="d",
                language="Python", stars=100, stars_today=5)
    result = analyzer.analyze_repo(repo, client=fake)
    assert result is not None
    assert result["full_name"] == "o/a"
    assert result["url"] == "https://github.com/o/a"
    assert result["summary"] == "s"
    assert result["score"] == 4
    calls = fake.chat.completions.calls
    assert len(calls) == 2
    assert "response_format" in calls[0]   # 首次带 json_object
    assert "response_format" not in calls[1]  # 降级为纯 prompt
