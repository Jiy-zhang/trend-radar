"""渲染 HTML 日报并通过 SMTP 发送。"""
from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText

from jinja2 import Template

TEMPLATE = Template(autoescape=True, source="""\
<!DOCTYPE html>
<html><body style="margin:0;padding:24px;background:#f6f8fa;font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:#1f2328;">
<div style="max-width:680px;margin:0 auto;">
  <h1 style="font-size:20px;">🛰 GitHub Trend Radar · {{ date }}</h1>
  <div style="background:#fff;border:1px solid #d1d9e0;border-radius:8px;padding:16px 20px;margin-bottom:20px;line-height:1.7;">
    {{ overview }}
  </div>
  {% for a in analyses %}
  <div style="background:#fff;border:1px solid #d1d9e0;border-radius:8px;padding:16px 20px;margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;">
      <a href="{{ a.url }}" style="font-weight:600;color:#0969da;text-decoration:none;">{{ a.full_name }}</a>{% if a.is_surge %} <span title="star surging">🚀</span>{% endif %}
      <span>{{ "⭐" * a.score }}</span>
    </div>
    <div style="color:#59636e;font-size:13px;margin:4px 0;">
      {{ a.category }}{% if a.language %} · {{ a.language }}{% endif %} · +{{ a.stars_today }} today · {{ a.stars }} stars
    </div>
    <p style="margin:8px 0 4px;line-height:1.6;">{{ a.summary }}</p>
    <p style="margin:4px 0;color:#59636e;font-size:13px;line-height:1.6;">{{ a.problem_solved }} — {{ a.reason }}</p>
  </div>
  {% endfor %}

  {% if topic_groups %}
  <h2 style="font-size:16px;margin:24px 0 8px;">📦 按主题推荐</h2>
  {% for g in topic_groups %}
  <div style="color:#59636e;font-size:13px;margin:12px 0 4px;"># {{ g.topic }}</div>
  {% for a in g.analyses %}
  <div style="background:#fff;border:1px solid #d1d9e0;border-radius:8px;padding:16px 20px;margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;">
      <a href="{{ a.url }}" style="font-weight:600;color:#0969da;text-decoration:none;">{{ a.full_name }}</a>
      <span>{{ "⭐" * a.score }}</span>
    </div>
    <div style="color:#59636e;font-size:13px;margin:4px 0;">
      {{ a.category }}{% if a.language %} · {{ a.language }}{% endif %} · {{ a.stars }} stars
    </div>
    <p style="margin:8px 0 4px;line-height:1.6;">{{ a.summary }}</p>
    <p style="margin:4px 0;color:#59636e;font-size:13px;line-height:1.6;">{{ a.problem_solved }} - {{ a.reason }}</p>
  </div>
  {% endfor %}
  {% endfor %}
  {% endif %}

  <p style="color:#8b949e;font-size:12px;">trend-radar · 自动生成</p>
</div>
</body></html>""")


def render(date: str, overview: str, analyses: list[dict],
           topic_groups: list[dict] | None = None) -> str:
    return TEMPLATE.render(date=date, overview=overview,
                           analyses=analyses, topic_groups=topic_groups or [])


def send(subject: str, html: str) -> None:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    to_addr = os.environ.get("MAIL_TO", user)

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=30) as server:
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_addr], msg.as_string())
