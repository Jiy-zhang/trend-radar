from scraper import Repo
import main


def test_build_topic_groups_excludes_trending_and_cross_topic_dup():
    by_topic = {
        "llm": [Repo("o/a", "u"), Repo("o/b", "u")],
        "ai-agents": [Repo("o/b", "u"), Repo("o/c", "u")],  # o/b 跨主题重复
    }
    trending_names = {"o/a"}  # o/a 已在 Trending,排除
    analyses_by_name = {
        "o/a": {"full_name": "o/a"},
        "o/b": {"full_name": "o/b"},
        "o/c": {"full_name": "o/c"},
    }
    groups = main.build_topic_groups(by_topic, trending_names, analyses_by_name)
    assert groups[0]["topic"] == "llm"
    assert [a["full_name"] for a in groups[0]["analyses"]] == ["o/b"]
    assert groups[1]["topic"] == "ai-agents"
    assert [a["full_name"] for a in groups[1]["analyses"]] == ["o/c"]


def test_build_topic_groups_skips_missing_analysis():
    by_topic = {"llm": [Repo("o/a", "u"), Repo("o/b", "u")]}
    analyses_by_name = {"o/a": {"full_name": "o/a"}}  # o/b 分析失败
    groups = main.build_topic_groups(by_topic, set(), analyses_by_name)
    assert len(groups) == 1
    assert [a["full_name"] for a in groups[0]["analyses"]] == ["o/a"]
