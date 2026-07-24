"""按主题推荐:用 GitHub Search API 拉指定 topic 近期活跃的高星项目。"""
from __future__ import annotations

import os
from datetime import date as date_cls, timedelta
from urllib.parse import urlencode

import scraper

API = "https://api.github.com"


def _int_env(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (ValueError, TypeError):
        print(f"[recommender] {key} 值无效, 使用默认值 {default}")
        return default


def get_config() -> dict:
    """从环境变量读主题推荐配置。RECOMMEND_TOPICS 为空则关闭主题功能。"""
    raw = os.environ.get("RECOMMEND_TOPICS", "").strip()
    topics = [t.strip() for t in raw.split(",") if t.strip()]
    return {
        "topics": topics,
        "min_stars": _int_env("RECOMMEND_MIN_STARS", 500),
        "window_days": _int_env("RECOMMEND_WINDOW_DAYS", 30),
        "max_per_topic": _int_env("RECOMMEND_MAX_PER_TOPIC", 5),
        "max_total": _int_env("RECOMMEND_MAX_TOTAL", 15),
    }


def parse_search_results(data: dict, topic: str) -> list[scraper.Repo]:
    """纯解析 GitHub Search API 响应 -> Repo 列表,便于离线测试。"""
    repos: list[scraper.Repo] = []
    for item in data.get("items", []):
        full_name = item.get("full_name", "")
        if not full_name:
            continue
        repos.append(scraper.Repo(
            full_name=full_name,
            url=item.get("html_url", f"https://github.com/{full_name}"),
            description=item.get("description") or "",
            language=item.get("language") or "",
            stars=item.get("stargazers_count", 0),
            stars_today=0,
            topics=item.get("topics", []),
            created_at=(item.get("created_at") or "")[:10],
        ))
    return repos


def fetch_topic_repos(topics: list[str], min_stars: int, window_days: int,
                      max_per_topic: int) -> dict[str, list[scraper.Repo]]:
    """逐主题调 Search API,返回 {topic: [Repo]}。单主题失败不中断(降级)。"""
    since = (date_cls.today() - timedelta(days=window_days)).isoformat()
    headers = scraper._api_headers()
    out: dict[str, list[scraper.Repo]] = {}
    for topic in topics:
        params = {
            "q": f"topic:{topic} stars:>{min_stars} pushed:>{since}",
            "sort": "stars", "order": "desc", "per_page": max_per_topic,
        }
        url = f"{API}/search/repositories?{urlencode(params)}"
        try:
            resp = scraper._get(url, headers=headers)
            if not resp.ok:
                print(f"[recommender] {topic}: HTTP {resp.status_code}, 跳过")
                continue
            out[topic] = parse_search_results(resp.json(), topic)
        except Exception as exc:
            print(f"[recommender] {topic} 失败: {exc}, 跳过")
            continue
    return out
