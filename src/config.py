import os
from pathlib import Path
import yaml
from dotenv import load_dotenv


def load_config(config_path: str = "config.yaml") -> dict:
    """加载 YAML 配置与 .env 环境变量。若不存在 config.yaml，则回退到示例默认。"""
    load_dotenv()

    cfg = {}
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        # 默认示例配置
        cfg = {
            "keywords": ["web3", "defi", "nft", "ethereum", "solana", "layer2", "打新", "预售", "空投"],
            "since_hours": 24,
            "date_mode": "last_hours",  # last_hours | yesterday
            "timezone": "Asia/Shanghai",  # UTC+8
            "limit": 120,
            "delivery": {
                "email": {
                    "enabled": False,
                    "subject": "Web3 日报",
                    "from_name": "Web3 Reporter",
                },
                "telegram": {"enabled": True},
            },
            "trigger_keywords": [
                "打新", "预售", "空投", "whitelist", "presale", "airdrop", "IDO", "IEO", "mint", "launch"
            ],
            "data_sources": {
                "rootdata": {
                    "enabled": True,
                    "base_url": "https://api.rootdata.com/open",
                    "auth_header": "x-api-key",
                    "endpoints": {
                        "fundraising": "fundraising_projects",
                        "token_unlocks": "token_unlocks",
                        "airdrops": "airdrops",
                        "ecosystem": "ecosystem_changes"
                    }
                }
            },
            "prompt_extra": "",
        }

    # 环境变量注入（OpenAI & 通道）
    cfg.setdefault("env", {})
    cfg["env"].update({
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "OPENAI_MODEL": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "ROOTDATA_API_KEY": os.getenv("ROOTDATA_API_KEY", ""),
        "EMAIL_SMTP_HOST": os.getenv("EMAIL_SMTP_HOST", ""),
        "EMAIL_SMTP_PORT": int(os.getenv("EMAIL_SMTP_PORT", "587")),
        "EMAIL_USERNAME": os.getenv("EMAIL_USERNAME", ""),
        "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", ""),
        "EMAIL_TO": os.getenv("EMAIL_TO", "wanghzhepoker@gmail.com"),
        "EMAIL_USE_SSL": os.getenv("EMAIL_USE_SSL", "").strip().lower() in ("1", "true", "yes", "on"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", ""),
    })

    # 通过环境变量可覆盖发送通道的启用状态
    email_enabled_env = os.getenv("EMAIL_ENABLED")
    if email_enabled_env is not None:
        try:
            enabled_val = email_enabled_env.strip().lower() in ("1", "true", "yes", "on")
            cfg.setdefault("delivery", {}).setdefault("email", {})["enabled"] = enabled_val
        except Exception:
            pass
    tg_enabled_env = os.getenv("TELEGRAM_ENABLED")
    if tg_enabled_env is not None:
        try:
            enabled_val = tg_enabled_env.strip().lower() in ("1", "true", "yes", "on")
            cfg.setdefault("delivery", {}).setdefault("telegram", {})["enabled"] = enabled_val
        except Exception:
            pass

    # 若使用 Gmail，自动设置主机与端口默认
    if cfg["env"].get("EMAIL_USERNAME", "").endswith("@gmail.com"):
        cfg["env"].setdefault("EMAIL_SMTP_HOST", "smtp.gmail.com")
        cfg["env"].setdefault("EMAIL_SMTP_PORT", 587)

    return cfg
