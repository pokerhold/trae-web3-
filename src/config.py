import copy
import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

from src.config_template import DEFAULT_CONFIG_TEMPLATE


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any], source_map: Dict[str, Any], source: str) -> Dict[str, Any]:
    """深度合并配置，并记录来源（default/yaml/env）。"""
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            source_map.setdefault(key, {})
            base[key] = _deep_merge(base[key], value, source_map[key], source)
        else:
            base[key] = value
            source_map[key] = source
    return base


def _ensure_config_file_exists(path: Path, template_path: Path) -> None:
    if path.exists():
        return
    raise FileNotFoundError(
        f"未找到 {path.name}，请复制模板：cp {template_path.name} {path.name} 并按需修改。"
    )


def _validate_required(cfg: Dict[str, Any]) -> None:
    env_cfg = cfg.get("env", {})
    rootdata_enabled = cfg.get("data_sources", {}).get("rootdata", {}).get("enabled", False)
    if rootdata_enabled and not env_cfg.get("ROOTDATA_API_KEY"):
        raise ValueError(
            "缺少 ROOTDATA_API_KEY，请在环境变量或 config.yaml 的 env.ROOTDATA_API_KEY 中填写（建议使用环境变量）。"
        )

    email_enabled = cfg.get("delivery", {}).get("email", {}).get("enabled", False)
    if email_enabled:
        required_email_fields = [
            "EMAIL_SMTP_HOST",
            "EMAIL_SMTP_PORT",
            "EMAIL_USERNAME",
            "EMAIL_PASSWORD",
            "EMAIL_TO",
        ]
        missing = [field for field in required_email_fields if not env_cfg.get(field)]
        if missing:
            raise ValueError(
                "邮件通道已启用，但缺少必要字段："
                + ", ".join(missing)
                + "。请设置对应的环境变量，或在 config.yaml 的 env 段落中配置。"
            )


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置：优先级 环境变量 > YAML > 默认模板，并输出来源调试日志。"""
    load_dotenv()

    config_file = Path(config_path)
    template_path = Path("config.template.yaml")
    _ensure_config_file_exists(config_file, template_path)

    cfg = copy.deepcopy(DEFAULT_CONFIG_TEMPLATE)
    source_map: Dict[str, Any] = {k: "default" for k in cfg}

    with open(config_file, "r", encoding="utf-8") as f:
        user_cfg = yaml.safe_load(f) or {}
    _deep_merge(cfg, user_cfg, source_map, "yaml")

    # 环境变量注入（OpenAI & 通道）
    cfg.setdefault("env", {})
    source_map.setdefault("env", {})

    def _apply_env(key: str, env_var: str, parser=lambda x: x):
        value = os.getenv(env_var)
        if value is not None:
            try:
                parsed = parser(value)
            except Exception:
                parsed = value
            cfg["env"][key] = parsed
            source_map["env"][key] = "env"
            logger.info("配置 %s 取自环境变量 %s", key, env_var)
        elif key not in cfg["env"]:
            cfg["env"][key] = DEFAULT_CONFIG_TEMPLATE.get("env", {}).get(key, "")
            source_map["env"][key] = "default"

    bool_parser = lambda v: v.strip().lower() in ("1", "true", "yes", "on")
    int_parser = lambda v: int(v) if str(v).isdigit() else v

    env_defaults = {
        "OPENAI_API_KEY": "OPENAI_API_KEY",
        "OPENAI_MODEL": "OPENAI_MODEL",
        "ROOTDATA_API_KEY": "ROOTDATA_API_KEY",
        "EMAIL_SMTP_HOST": "EMAIL_SMTP_HOST",
        "EMAIL_SMTP_PORT": "EMAIL_SMTP_PORT",
        "EMAIL_USERNAME": "EMAIL_USERNAME",
        "EMAIL_PASSWORD": "EMAIL_PASSWORD",
        "EMAIL_TO": "EMAIL_TO",
        "EMAIL_USE_SSL": "EMAIL_USE_SSL",
        "TELEGRAM_BOT_TOKEN": "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID": "TELEGRAM_CHAT_ID",
    }

    for key, env_var in env_defaults.items():
        parser = bool_parser if key in ("EMAIL_USE_SSL",) else int_parser if key in ("EMAIL_SMTP_PORT",) else (lambda x: x)
        _apply_env(key, env_var, parser)

    # 通过环境变量可覆盖发送通道的启用状态
    cfg.setdefault("delivery", {}).setdefault("email", {})
    cfg.setdefault("delivery", {}).setdefault("telegram", {})
    source_map.setdefault("delivery", {}).setdefault("email", {})
    source_map.setdefault("delivery", {}).setdefault("telegram", {})

    def _apply_flag(env_var: str, target: Dict[str, Any]):
        flag_val = os.getenv(env_var)
        if flag_val is not None:
            enabled_val = bool_parser(flag_val)
            target["enabled"] = enabled_val
            logger.info("通道 %s 来自环境变量 %s", "/".join([env_var]), env_var)

    _apply_flag("EMAIL_ENABLED", cfg["delivery"]["email"])
    _apply_flag("TELEGRAM_ENABLED", cfg["delivery"]["telegram"])

    # 若使用 Gmail，自动设置主机与端口默认
    if cfg["env"].get("EMAIL_USERNAME", "").endswith("@gmail.com"):
        cfg["env"].setdefault("EMAIL_SMTP_HOST", "smtp.gmail.com")
        cfg["env"].setdefault("EMAIL_SMTP_PORT", 587)
        logger.info("检测到 Gmail 账号，SMTP 默认使用 smtp.gmail.com:587")

    _validate_required(cfg)

    logger.info("配置加载完成（ENV > YAML > 默认）。关键字段来源：%s", source_map.get("env", {}))
    return cfg
