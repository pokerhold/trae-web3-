import os
from pathlib import Path
from typing import List, Dict, Tuple

from openai import OpenAI
import json


def load_system_prompt() -> str:
    p = Path("prompts/system_prompt.txt")
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "你是专业的 Web3 行业分析师，请生成结构化中文日报。"


def _format_tweets(tweets: List[Dict], cap: int = 40) -> str:
    lines = []
    for t in tweets[:cap]:
        vc = t.get('viewCount')
        vc_txt = f" 👁{vc}" if vc else ""
        line = (
            f"- @{t.get('author','')} | ❤{t.get('likeCount',0)} ↻{t.get('retweetCount',0)} 💬{t.get('replyCount',0)}{vc_txt}\n"
            f"  {t.get('text','').strip()}\n"
            f"  {t.get('url','')}\n"
        )
        lines.append(line)
    return "\n".join(lines)


def build_messages(
    tweets: List[Dict],
    prompt_extra: str,
    top_like: List[Dict],
    top_reply: List[Dict],
    triggers: List[Dict],
    date_mode: str,
) -> list:
    system_prompt = load_system_prompt()
    tweets_text = _format_tweets(tweets, cap=60)
    top_like_text = _format_tweets(top_like, cap=25)
    top_reply_text = _format_tweets(top_reply, cap=25)
    trigger_text = _format_tweets(triggers, cap=40)

    window_desc = "昨日" if date_mode == "yesterday" else "过去24小时"
    user_prompt = (
        f"【总体数据】{window_desc} Web3 相关热点推文样本（含热度指标）：\n\n{tweets_text}\n\n"
        f"【阅读量/评论量 Top】按阅读量(如可得)与评论量挑选：\n{top_reply_text}\n\n"
        f"【点赞 Top】按点赞排序挑选：\n{top_like_text}\n\n"
        f"【打新/预售/空投 触发条目】关键词触发集合：\n{trigger_text}\n\n"
        f"请基于以上信息生成《Web3 每日简报》（中文），严格包含：\n"
        f"1) 阅读量与评论量最大的条目概览（若阅读量不可得则以评论/转发/点赞综合替代），附影响与风险；\n"
        f"2) 仅{window_desc} 的打新相关热点（预售、打新、空投、博主与项目方观点），按点赞与评论衡量；\n"
        f"3) 关键词触发的项目信息（预售/打新/空投等），简要摘要并给出观察建议；\n"
        f"4) 按板块（DeFi / NFT / 基础设施 / 公链生态 / 安全事件）整理与要点；\n"
        f"5) 明确标注不确定信息；保持简洁要点化。\n"
        f"{prompt_extra or ''}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def summarize(
    tweets: List[Dict],
    openai_api_key: str,
    model: str,
    prompt_extra: str = "",
    top_like: List[Dict] = None,
    top_reply: List[Dict] = None,
    triggers: List[Dict] = None,
    date_mode: str = "last_hours",
) -> str:
    if not openai_api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，用于摘要生成。")

    client = OpenAI(api_key=openai_api_key)
    messages = build_messages(
        tweets=tweets,
        prompt_extra=prompt_extra,
        top_like=top_like or [],
        top_reply=top_reply or [],
        triggers=triggers or [],
        date_mode=date_mode,
    )

    resp = client.chat.completions.create(
        model=model or "gpt-4o-mini",
        messages=messages,
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()


def summarize_structured(
    tweets: List[Dict],
    openai_api_key: str,
    model: str,
    prompt_extra: str = "",
    top_like: List[Dict] = None,
    top_reply: List[Dict] = None,
    triggers: List[Dict] = None,
    date_mode: str = "last_hours",
) -> Dict:
    """让模型输出严格的 JSON 结构，满足 Excel 导出需求。"""
    if not openai_api_key:
        raise RuntimeError("缺少 OPENAI_API_KEY，用于摘要生成。")

    client = OpenAI(api_key=openai_api_key)

    # 构造消息（复用文本型但添加 JSON schema 指令）
    messages = build_messages(
        tweets=tweets,
        prompt_extra=(
            (prompt_extra or "")
            + "\n\n请严格按照下述 JSON 结构输出（仅返回 JSON，不要任何解释或Markdown）：\n"
            + "{"
            + "\"financing\": [{\"project_name\": str, \"amount\": str, \"round\": str, \"sector\": str, \"date\": str, \"sources\": [str]}],"
            + "\"airdrops\": [{\"project_name\": str, \"signal\": str, \"task_url\": str, \"tge_date\": str, \"notes\": str}],"
            + "\"ecosystems\": [{\"chain\": str, \"change_type\": str, \"description\": str, \"metrics\": str, \"source\": str}],"
            + "\"tokenomics\": [{\"project_name\": str, \"token\": str, \"change\": str, \"unlock_date\": str, \"amount\": str, \"impact\": str, \"source\": str}],"
            + "\"actions\": [{\"title\": str, \"action\": str, \"reason\": str, \"urgency_score\": int, \"due_hint\": str}]"
            + "}"
            + "\n各模块最多输出 20 条，缺失信息请留空字符串。"
        ),
        top_like=top_like or [],
        top_reply=top_reply or [],
        triggers=triggers or [],
        date_mode=date_mode,
    )

    resp = client.chat.completions.create(
        model=model or "gpt-4o-mini",
        messages=messages,
        temperature=0.2,
    )
    content = resp.choices[0].message.content.strip()

    try:
        data = json.loads(content)
    except Exception:
        # 兜底：若模型未严格返回 JSON，尝试截取第一个花括号段
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            data = json.loads(content[start : end + 1])
        else:
            raise RuntimeError("模型未返回可解析的 JSON 结构。")
    return data