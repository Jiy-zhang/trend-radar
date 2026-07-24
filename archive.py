"""日报网页版存档到 docs/,供 GitHub Pages 发布。

邮件版(mailer.py)保持内联样式以兼容邮件客户端;
网页版在这里单独渲染,视觉走"雷达遥测图纸"方向。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from jinja2 import Template

DOCS_DIR = Path(__file__).parent / "docs"
REPO_URL = "https://github.com/DawnZYC/trend-radar"

_SHELL_CSS = """
:root {
  --paper: #ECF1F2; --grid: rgba(23, 62, 71, .10); --card: rgba(255, 255, 255, .75);
  --ink: #10282E; --dim: #5C7379; --line: #C8D7DB;
  --blip: #177A5B; --surge: #D14E0C;
}
* { box-sizing: border-box; }
body {
  margin: 0; color: var(--ink); background-color: var(--paper);
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 28px 28px;
  font-family: "IBM Plex Sans", -apple-system, sans-serif;
  line-height: 1.65;
}
.wrap { max-width: 760px; margin: 0 auto; padding: 48px 20px 72px; }
a { color: inherit; }
a:focus-visible { outline: 2px solid var(--blip); outline-offset: 3px; }
header.site { display: flex; align-items: center; gap: 20px; margin-bottom: 8px; }
.dial { flex: none; width: 62px; height: 62px; border-radius: 50%;
  border: 1.5px solid var(--ink); position: relative; overflow: hidden;
  background:
    repeating-radial-gradient(circle at 50% 50%, transparent 0 9px, var(--grid) 9px 10px),
    var(--paper); }
.dial::after { content: ""; position: absolute; inset: 0; border-radius: 50%;
  background: conic-gradient(from 0deg, rgba(23,122,91,.5), transparent 80deg);
  animation: sweep 5s linear infinite; }
@keyframes sweep { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .dial::after { animation: none; } }
.masthead h1 { margin: 0; font-family: "Saira Condensed", sans-serif;
  font-weight: 600; font-size: 40px; letter-spacing: .14em; text-transform: uppercase; }
.masthead .eyebrow { font-family: "IBM Plex Mono", monospace; font-size: 12px;
  letter-spacing: .18em; color: var(--dim); text-transform: uppercase; }
.rule { border: 0; border-top: 1.5px solid var(--ink); margin: 22px 0 0; }
.rule + .sub { display: flex; justify-content: space-between; gap: 12px;
  font-family: "IBM Plex Mono", monospace; font-size: 12px; color: var(--dim);
  padding-top: 6px; margin-bottom: 40px; flex-wrap: wrap; }
.mono { font-family: "IBM Plex Mono", monospace; }
footer.site { margin-top: 56px; font-family: "IBM Plex Mono", monospace;
  font-size: 12px; color: var(--dim); }
footer.site a { color: var(--dim); }
"""

_FONTS = (
  '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
  '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
  '<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@600'
  '&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600'
  '&display=swap" rel="stylesheet">'
)

INDEX_TEMPLATE = Template(autoescape=True, source="""\
<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trend Radar — GitHub Trending 扫描日志</title>
{{ fonts|safe }}
<style>
{{ shell|safe }}
.log { list-style: none; margin: 0; padding: 0; }
.log li { border-bottom: 1px solid var(--line); }
.log a { display: flex; align-items: baseline; gap: 14px; padding: 15px 6px;
  text-decoration: none; transition: background .12s; }
.log a:hover { background: var(--card); }
.log a:hover .d::before { background: var(--blip); box-shadow: 0 0 0 4px rgba(23,122,91,.18); }
.d { font-family: "IBM Plex Mono", monospace; font-weight: 500; white-space: nowrap; }
.d::before { content: ""; display: inline-block; width: 7px; height: 7px;
  border-radius: 50%; border: 1.5px solid var(--ink); margin-right: 12px;
  vertical-align: 1px; transition: all .12s; }
.leader { flex: 1; border-bottom: 1.5px dotted var(--line); transform: translateY(-4px); }
.n { font-family: "IBM Plex Mono", monospace; font-size: 13px; color: var(--dim);
  white-space: nowrap; }
</style></head>
<body><div class="wrap">
<header class="site">
  <div class="dial" aria-hidden="true"></div>
  <div class="masthead">
    <div class="eyebrow">github trending · ai digest</div>
    <h1>Trend Radar</h1>
  </div>
</header>
<hr class="rule">
<div class="sub"><span>SCAN LOG · 每周一 / 三 / 五</span><span>{{ dates|length }} SCANS</span></div>
<ul class="log">
{% for d in dates %}
  <li><a href="{{ d.date }}.html">
    <span class="d">{{ d.date }}</span>
    <span class="leader" aria-hidden="true"></span>
    <span class="n">{% if d.count %}{{ d.count }} signals{% else %}view →{% endif %}</span>
  </a></li>
{% endfor %}
</ul>
<footer class="site">tracked by <a href="{{ repo_url }}">trend-radar</a> · 抓取 → 去重 → AI 分析,全自动</footer>
</div></body></html>
""")

REPORT_TEMPLATE = Template(autoescape=True, source="""\
<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trend Radar · {{ date }}</title>
{{ fonts|safe }}
<style>
{{ shell|safe }}
.back { font-family: "IBM Plex Mono", monospace; font-size: 13px;
  text-decoration: none; color: var(--dim); }
.back:hover { color: var(--ink); }
header.site { margin-top: 18px; }
.overview { border-left: 3px solid var(--ink); background: var(--card);
  padding: 18px 22px; margin: 0 0 36px; }
.overview .tag { font-family: "IBM Plex Mono", monospace; font-size: 11px;
  letter-spacing: .18em; color: var(--dim); display: block; margin-bottom: 8px; }
.card { background: var(--card); border: 1px solid var(--line); padding: 18px 22px;
  margin-bottom: 14px; }
.card .head { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
.card .name { font-family: "IBM Plex Mono", monospace; font-weight: 500;
  font-size: 16px; text-decoration: none; }
.card .name:hover { color: var(--blip); }
.sig { display: inline-flex; gap: 3px; align-items: baseline; }
.sig i { width: 5px; border-radius: 1px; background: var(--line); }
.sig i.on { background: var(--blip); }
.sig i:nth-child(1) { height: 6px; } .sig i:nth-child(2) { height: 9px; }
.sig i:nth-child(3) { height: 12px; } .sig i:nth-child(4) { height: 15px; }
.sig i:nth-child(5) { height: 18px; }
.badge { font-family: "IBM Plex Mono", monospace; font-size: 11px;
  letter-spacing: .1em; color: #fff; background: var(--surge);
  padding: 2px 7px; border-radius: 2px; }
.meta { font-family: "IBM Plex Mono", monospace; font-size: 12px;
  color: var(--dim); margin: 6px 0 10px; }
.card p { margin: 6px 0; }
.card .why { color: var(--dim); font-size: 14px; }
</style></head>
<body><div class="wrap">
<a class="back" href="index.html">&larr; SCAN LOG</a>
<header class="site">
  <div class="dial" aria-hidden="true"></div>
  <div class="masthead">
    <div class="eyebrow">scan report · {{ analyses|length }} signals</div>
    <h1>{{ date }}</h1>
  </div>
</header>
<hr class="rule">
<div class="sub"><span>TREND RADAR</span><span>github trending · ai digest</span></div>
<div class="overview"><span class="tag">OVERVIEW</span>{{ overview }}</div>
{% for a in analyses %}
<article class="card">
  <div class="head">
    <a class="name" href="{{ a.url }}">{{ a.full_name }}</a>
    <span class="sig" role="img" aria-label="关注度 {{ a.score }}/5">
      {%- for i in range(5) %}<i class="{{ 'on' if i < a.score }}"></i>{% endfor -%}
    </span>
    {% if a.is_surge %}<span class="badge">SURGE</span>{% endif %}
  </div>
  <div class="meta">{{ a.category }}{% if a.language %} · {{ a.language }}{% endif %}
    · +{{ a.stars_today }} today · {{ a.stars }} stars</div>
  <p>{{ a.summary }}</p>
  <p class="why">{{ a.problem_solved }} — {{ a.reason }}</p>
</article>
{% endfor %}
{% if topic_groups %}
<hr class="rule">
<div class="sub"><span>按主题推荐</span><span>{{ topic_groups|length }} TOPICS</span></div>
{% for g in topic_groups %}
<div class="overview" style="margin-bottom:8px;"><span class="tag"># {{ g.topic }}</span></div>
{% for a in g.analyses %}
<article class="card">
  <div class="head">
    <a class="name" href="{{ a.url }}">{{ a.full_name }}</a>
    <span class="sig" role="img" aria-label="关注度 {{ a.score }}/5">
      {%- for i in range(5) %}<i class="{{ 'on' if i < a.score }}"></i>{% endfor -%}
    </span>
    {% if a.is_surge %}<span class="badge">SURGE</span>{% endif %}
  </div>
  <div class="meta">{{ a.category }}{% if a.language %} · {{ a.language }}{% endif %}
    · {{ a.stars }} stars</div>
  <p>{{ a.summary }}</p>
  <p class="why">{{ a.problem_solved }} - {{ a.reason }}</p>
</article>
{% endfor %}
{% endfor %}
{% endif %}
<footer class="site">tracked by <a href="{{ repo_url }}">trend-radar</a></footer>
</div></body></html>
""")


def save(date: str, overview: str, analyses: list[dict],
         topic_groups: list[dict] | None = None,
         docs_dir: Path = DOCS_DIR) -> Path:
    """渲染当日网页版日报、更新 manifest 与索引,返回日报路径。"""
    docs_dir.mkdir(parents=True, exist_ok=True)
    report = docs_dir / f"{date}.html"
    report.write_text(REPORT_TEMPLATE.render(
        date=date, overview=overview, analyses=analyses,
        topic_groups=topic_groups or [],
        fonts=_FONTS, shell=_SHELL_CSS, repo_url=REPO_URL), encoding="utf-8")

    manifest_path = docs_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[date] = {"count": len(analyses) + sum(len(g["analyses"]) for g in (topic_groups or []))}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                             encoding="utf-8")

    rebuild_index(docs_dir)
    return report


def rebuild_index(docs_dir: Path = DOCS_DIR) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = docs_dir / "manifest.json"
    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    dates = sorted(
        (p.stem for p in docs_dir.glob("*.html")
         if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem)),
        reverse=True,
    )
    entries = [{"date": d, "count": manifest.get(d, {}).get("count")} for d in dates]
    (docs_dir / "index.html").write_text(
        INDEX_TEMPLATE.render(dates=entries, fonts=_FONTS, shell=_SHELL_CSS,
                              repo_url=REPO_URL), encoding="utf-8")
