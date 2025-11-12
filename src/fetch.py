from datetime import datetime, timedelta
from typing import List, Dict
import subprocess
import json
import sys
from pathlib import Path
import shutil

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

def _build_query(keywords: List[str], since_hours: int = 24, date_mode: str = "last_hours", timezone: str = "UTC") -> str:
    # 使用 OR 连接关键词，并限制时间窗口（支持 yesterday）
    if ZoneInfo and timezone:
        now = datetime.now(ZoneInfo(timezone))
    else:
        now = datetime.utcnow()
    kw = " OR ".join([k.strip() for k in keywords if k.strip()])

    if date_mode == "yesterday":
        y = now.date() - timedelta(days=1)
        since_str = y.strftime("%Y-%m-%d")
        until_str = now.date().strftime("%Y-%m-%d")
        base = f"({kw}) since:{since_str} until:{until_str}"
    else:
        since_dt = now - timedelta(hours=since_hours)
        since_str = since_dt.strftime("%Y-%m-%d")
        base = f"({kw}) since:{since_str}"
    return base


def _find_snscrape_bin() -> str:
    """查找 snscrape 可执行文件路径"""
    # 优先使用系统路径
    p = shutil.which("snscrape")
    if p:
        return p
    # 尝试 venv Scripts 目录
    exe = Path(sys.executable).parent / ("snscrape.exe" if sys.platform.startswith("win") else "snscrape")
    if exe.exists():
        return str(exe)
    raise FileNotFoundError("未找到 snscrape 可执行文件，请确认已安装并在虚拟环境中。")


def fetch_hot_tweets(keywords: List[str], since_hours: int = 24, limit: int = 120, date_mode: str = "last_hours", timezone: str = "UTC") -> List[Dict]:
    """使用 snscrape CLI 抓取热点推文并返回结构化列表。
    每条包含：text, url, date, author, likeCount, retweetCount, replyCount, viewCount, score
    """
    query = _build_query(keywords, since_hours, date_mode, timezone)
    bin_path = _find_snscrape_bin()

    cmd = [bin_path, "--jsonl", "--max-results", str(limit), "twitter-search", query]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(f"snscrape CLI 执行失败: code={proc.returncode}, err={proc.stderr.strip()}")

    items: List[Dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            t = json.loads(line)
        except Exception:
            continue
        # 提取并兼容字段
        text = t.get("content") or t.get("renderedContent") or ""
        url = t.get("url", "")
        date = t.get("date", "")
        like_count = int(t.get("likeCount", 0) or 0)
        retweet_count = int(t.get("retweetCount", 0) or 0)
        reply_count = int(t.get("replyCount", 0) or 0)
        view_count = t.get("viewCount")
        author = (t.get("user") or {}).get("username", "")

        score = (
            (reply_count * 2.5)
            + (retweet_count * 2.0)
            + (like_count * 1.0)
            + ((view_count or 0) * 0.001)
        )

        items.append({
            "text": text,
            "url": url,
            "date": date if isinstance(date, str) else (getattr(date, "isoformat", lambda: "")()),
            "author": author,
            "likeCount": like_count,
            "retweetCount": retweet_count,
            "replyCount": reply_count,
            "viewCount": view_count,
            "score": score,
        })

    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return items