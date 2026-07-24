import json
from pathlib import Path
import recommender

FIXTURE = Path(__file__).parent / "fixtures" / "search_llm.json"


def test_parse_search_results():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    repos = recommender.parse_search_results(data, "llm")
    assert len(repos) == 2
    r = repos[0]
    assert r.full_name == "owner/llm-project"
    assert r.url == "https://github.com/owner/llm-project"
    assert r.description == "A cool LLM project"
    assert r.language == "Python"
    assert r.stars == 1234
    assert r.topics == ["llm", "ai"]
    assert r.created_at == "2026-06-15"
    assert r.stars_today == 0  # 主题场景无此语义


def test_parse_search_results_empty():
    assert recommender.parse_search_results({"items": []}, "llm") == []


def test_get_config_defaults(monkeypatch):
    for k in ("RECOMMEND_TOPICS", "RECOMMEND_MIN_STARS", "RECOMMEND_WINDOW_DAYS",
              "RECOMMEND_MAX_PER_TOPIC", "RECOMMEND_MAX_TOTAL"):
        monkeypatch.delenv(k, raising=False)
    cfg = recommender.get_config()
    assert cfg["topics"] == []
    assert cfg["min_stars"] == 500
    assert cfg["window_days"] == 30
    assert cfg["max_per_topic"] == 5
    assert cfg["max_total"] == 15


def test_get_config_from_env(monkeypatch):
    monkeypatch.setenv("RECOMMEND_TOPICS", "llm, ai-agents")
    monkeypatch.setenv("RECOMMEND_MIN_STARS", "1000")
    cfg = recommender.get_config()
    assert cfg["topics"] == ["llm", "ai-agents"]
    assert cfg["min_stars"] == 1000
    assert cfg["window_days"] == 30
    assert cfg["max_per_topic"] == 5
    assert cfg["max_total"] == 15
