"""SQLite 榜单历史:记录快照,筛出新上榜项目。"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from scraper import Repo

DB_PATH = Path(os.environ.get("TR_DB_PATH", Path(__file__).parent / "data" / "history.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS sightings (
    full_name   TEXT NOT NULL,
    date        TEXT NOT NULL,
    stars       INTEGER DEFAULT 0,
    stars_today INTEGER DEFAULT 0,
    PRIMARY KEY (full_name, date)
);
CREATE TABLE IF NOT EXISTS reported (
    full_name TEXT PRIMARY KEY,
    date      TEXT NOT NULL
);
"""


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def filter_new(repos: list[Repo], date: str, lookback_days: int = 14,
               db_path: Path = DB_PATH) -> list[Repo]:
    """返回近 lookback_days 天内(不含今天)没上过榜的 repo。"""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT DISTINCT full_name FROM sightings "
            "WHERE date < ? AND date >= date(?, ?)",
            (date, date, f"-{lookback_days} days"),
        ).fetchall()
    seen = {r[0] for r in rows}
    return [r for r in repos if r.full_name not in seen]


def find_surges(repos: list[Repo], date: str, lookback_days: int = 7,
                ratio: float = 1.5, db_path: Path = DB_PATH) -> list[Repo]:
    """在已上过榜的 repo 里,找当前 star 相比近 lookback_days 天内
    最近一次记录暴涨 >= ratio 倍的,标记 is_surge 并返回。"""
    surges: list[Repo] = []
    with _connect(db_path) as conn:
        for repo in repos:
            row = conn.execute(
                "SELECT stars FROM sightings "
                "WHERE full_name = ? AND date < ? AND date >= date(?, ?) "
                "ORDER BY date DESC LIMIT 1",
                (repo.full_name, date, date, f"-{lookback_days} days"),
            ).fetchone()
            if row and row[0] > 0 and repo.stars >= row[0] * ratio:
                repo.is_surge = True
                surges.append(repo)
    return surges


def record(repos: list[Repo], date: str, db_path: Path = DB_PATH) -> None:
    """幂等写入当日快照。"""
    with _connect(db_path) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO sightings (full_name, date, stars, stars_today) "
            "VALUES (?, ?, ?, ?)",
            [(r.full_name, date, r.stars, r.stars_today) for r in repos],
        )
        conn.commit()


def unreported_new(date: str, lookback_days: int = 4, dedup_days: int = 14,
                   db_path: Path = DB_PATH) -> list[Repo]:
    """近 lookback_days 天(含今天)首次上榜、且近 dedup_days 天未进过日报的 repo。

    从 sightings 重建轻量 Repo(取该 repo 最近一次快照的 star 数),
    描述/README 等由后续 enrich 补全。
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT s.full_name, s.stars, s.stars_today
            FROM sightings s
            JOIN (SELECT full_name, MAX(date) AS d FROM sightings
                  WHERE date > date(?, ?) AND date <= ?
                  GROUP BY full_name) latest
              ON latest.full_name = s.full_name AND latest.d = s.date
            WHERE NOT EXISTS (
                SELECT 1 FROM sightings prev
                WHERE prev.full_name = s.full_name
                  AND prev.date <= date(?, ?) AND prev.date >= date(?, ?)
            )
            AND NOT EXISTS (
                SELECT 1 FROM reported r
                WHERE r.full_name = s.full_name AND r.date >= date(?, ?)
            )
            """,
            (date, f"-{lookback_days} days", date,
             date, f"-{lookback_days} days", date, f"-{dedup_days} days",
             date, f"-{dedup_days} days"),
        ).fetchall()
    return [Repo(full_name=name, url=f"https://github.com/{name}",
                 stars=stars, stars_today=stars_today)
            for name, stars, stars_today in rows]


def filter_unreported(repos: list[Repo], date: str, dedup_days: int = 14,
                      db_path: Path = DB_PATH) -> list[Repo]:
    """返回近 dedup_days 天内未进过日报的 repo(查 reported 表)。

    供主题推荐等非 Trending 来源做跨次去重;不写 sightings 表。
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT full_name FROM reported WHERE date >= date(?, ?)",
            (date, f"-{dedup_days} days"),
        ).fetchall()
    reported = {r[0] for r in rows}
    return [r for r in repos if r.full_name not in reported]


def mark_reported(full_names: list[str], date: str, db_path: Path = DB_PATH) -> None:
    """日报发送成功后调用;未标记的候选下次日报自动重试。"""
    with _connect(db_path) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO reported (full_name, date) VALUES (?, ?)",
            [(n, date) for n in full_names],
        )
        conn.commit()
