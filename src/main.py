import sys
import json
import argparse
from typing import List, Dict, Optional

from src.config import load_config
from src.fetch import fetch_hot_tweets
from src.summarize import summarize, summarize_structured
from src.export_excel import export_structured_to_excel
from src.senders.email_sender import send_email
from src.providers.rootdata import RootDataClient


def _load_tweets_from_jsonl(file_path: str) -> List[Dict]:
    items: List[Dict] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    t = json.loads(line)
                except Exception:
                    continue
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
    except Exception as e:
        print(f"[WARN] 读取 JSONL 推文文件失败: {e}")
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    return items


def run_once(tweets_file: Optional[str] = None):
    cfg = load_config()
    keywords: List[str] = cfg.get("keywords", [])
    since_hours: int = int(cfg.get("since_hours", 24))
    date_mode: str = cfg.get("date_mode", "last_hours")
    timezone: str = cfg.get("timezone", "UTC")
    limit: int = int(cfg.get("limit", 120))
    delivery = cfg.get("delivery", {})
    env = cfg.get("env", {})
    prompt_extra: str = cfg.get("prompt_extra", "")
    trigger_keywords: List[str] = cfg.get("trigger_keywords", [])

    print(f"[INFO] 抓取关键词: {keywords}, 模式: {date_mode}, 时区: {timezone}, 窗口: {since_hours}h, 限制: {limit}")
    tweets: List[Dict] = []
    if tweets_file:
        from pathlib import Path
        if Path(tweets_file).exists():
            print(f"[INFO] 使用本地 JSONL 推文文件: {tweets_file}")
            tweets = _load_tweets_from_jsonl(tweets_file)
            print(f"[INFO] 从文件读取到 {len(tweets)} 条推文（已按热度排序）")
        else:
            print(f"[WARN] 指定的推文文件不存在: {tweets_file}")
    if not tweets:
        try:
            tweets = fetch_hot_tweets(keywords, since_hours=since_hours, limit=limit, date_mode=date_mode, timezone=timezone)
            print(f"[INFO] 抓取到 {len(tweets)} 条推文（已按热度排序）")
        except Exception as e:
            print(f"[WARN] 推文抓取不可用，将仅使用结构化数据源与摘要：{e}")

    # 分榜单：点赞 Top、评论 Top（阅读量若可得在摘要中体现）
    top_like = sorted(tweets, key=lambda x: x.get("likeCount", 0), reverse=True)[:25]
    top_reply = sorted(tweets, key=lambda x: x.get("replyCount", 0), reverse=True)[:25]

    # 关键词触发集合
    triggers = []
    if trigger_keywords:
        kws_lower = [k.lower() for k in trigger_keywords]
        for t in tweets:
            text_l = (t.get("text", "") or "").lower()
            if any(k in text_l for k in kws_lower):
                triggers.append(t)

    # 生成结构化摘要并导出 Excel
    # 生成结构化摘要（如模型不可用则降级为空骨架，后续用 RootData 覆盖）
    try:
        structured = summarize_structured(
            tweets=tweets,
            openai_api_key=env.get("OPENAI_API_KEY", ""),
            model=env.get("OPENAI_MODEL", "gpt-4o-mini"),
            prompt_extra=prompt_extra,
            top_like=top_like,
            top_reply=top_reply,
            triggers=triggers,
            date_mode=date_mode,
        )
    except Exception as e:
        print(f"[WARN] 结构化摘要生成失败，将使用数据源直接填充：{e}")
        structured = {
            "financing": [],
            "airdrops": [],
            "ecosystems": [],
            "tokenomics": [],
            "actions": [],
        }

    # RootData 数据源增强（如可用）
    ds_cfg = cfg.get("data_sources", {}).get("rootdata", {})
    if ds_cfg.get("enabled") and env.get("ROOTDATA_API_KEY"):
        try:
            client = RootDataClient(
                base_url=ds_cfg.get("base_url", "https://api.rootdata.com/open"),
                api_key=env.get("ROOTDATA_API_KEY"),
                auth_header=ds_cfg.get("auth_header", "x-api-key"),
            )
            fr = client.fetch_fundraising()
            tu = client.fetch_token_unlocks()
            ad = client.fetch_airdrops()
            eco = client.fetch_ecosystem()
            structured["financing"] = fr or structured.get("financing", [])
            structured["tokenomics"] = tu or structured.get("tokenomics", [])
            structured["airdrops"] = ad or structured.get("airdrops", [])
            structured["ecosystems"] = eco or structured.get("ecosystems", [])
            print("[INFO] RootData 数据源已接入并覆盖对应模块")
        except Exception as e:
            print(f"[WARN] RootData 数据源接入失败: {e}")

    from datetime import datetime
    from pathlib import Path
    date_str = datetime.utcnow().strftime("%Y%m%d")
    out_file = Path("output") / f"web3_daily_{date_str}.xlsx"
    export_structured_to_excel(structured, out_file)
    print(f"[INFO] Excel 报告已生成: {out_file}")

    # 同时生成文本摘要用于消息正文预览
    # 文本摘要（如模型不可用则用简版文本汇总 RootData 结果）
    try:
        report: str = summarize(
            tweets=tweets,
            openai_api_key=env.get("OPENAI_API_KEY", ""),
            model=env.get("OPENAI_MODEL", "gpt-4o-mini"),
            prompt_extra=prompt_extra,
            top_like=top_like,
            top_reply=top_reply,
            triggers=triggers,
            date_mode=date_mode,
        )
    except Exception as e:
        print(f"[WARN] 文本摘要生成失败，将使用简版汇总：{e}")
        def _brief(module_name: str, rows: List[Dict], fields: List[str]) -> str:
            lines = [f"【{module_name}】共 {len(rows)} 项"]
            for r in rows[:20]:
                vals = [str(r.get(f, "")) for f in fields]
                lines.append(" - " + " | ".join(vals))
            return "\n".join(lines)

        report_parts = []
        report_parts.append(_brief("融资项目", structured.get("financing", []), ["project", "amount", "round", "sector", "date"]))
        report_parts.append(_brief("潜在空投", structured.get("airdrops", []), ["project", "signal", "task", "tge", "note"]))
        report_parts.append(_brief("核心链生态", structured.get("ecosystems", []), ["chain", "changeType", "summary", "metric", "source"]))
        report_parts.append(_brief("代币经济/解锁", structured.get("tokenomics", []), ["token", "change", "unlockTime", "size", "impact"]))
        report_parts.append(_brief("操作清单", structured.get("actions", []), ["title", "action", "reason", "urgency", "timeHint"]))
        report = "\n\n".join([p for p in report_parts if p])
    print("\n===== Web3 每日简报（预览） =====\n")
    print(report)
    print("\n===== 发送中 =====\n")

    # 邮件
    email_cfg = delivery.get("email", {})
    if email_cfg.get("enabled"):
        subject = email_cfg.get("subject", "Web3 日报")
        from_name = email_cfg.get("from_name", "Web3 Reporter")
        try:
            send_email(subject=subject, body=report, env=env, from_name=from_name, attachments=[str(out_file)])
            print("[INFO] 邮件发送成功")
        except Exception as e:
            print(f"[ERROR] 邮件发送失败: {e}")
            tg_cfg = delivery.get("telegram", {})
            if tg_cfg.get("enabled"):
                try:
                    alert = "[ALERT] 邮件发送失败，已通过 Telegram 提供预览与附件"
                    send_telegram(body=alert, env=env)
                    print("[INFO] Telegram 备援通知已发送")
                except Exception as te:
                    print(f"[WARN] Telegram 备援通知发送失败: {te}")

    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Web3 日报生成器")
        parser.add_argument("--tweets-file", type=str, default=None, help="本地 snscrape 导出的 JSONL 推文文件路径")
        parser.add_argument("--email-check", action="store_true", help="仅进行邮件通道健康检查，不生成报告")
        args = parser.parse_args()
        try:
            if args.email_check:
                cfg = load_config()
                env = cfg.get("env", {})
                delivery = cfg.get("delivery", {})
                email_cfg = delivery.get("email", {})
                subject = email_cfg.get("subject", "邮件通道健康检查")
                from_name = email_cfg.get("from_name", "Web3 Reporter")
                body = "这是一封邮件通道健康检查消息。如果您收到此邮件，说明SMTP配置有效。"
                send_email(subject=subject, body=body, env=env, from_name=from_name, attachments=None)
                print("[INFO] 邮件健康检查发送成功")
            else:
                run_once(tweets_file=args.tweets_file)
        except Exception as e:
            print(f"[FATAL] 执行失败: {e}")
            sys.exit(1)
