import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
import smtplib


def send_email(subject: str, body: str, env: dict, from_name: str = "Web3 Reporter", attachments: list = None) -> None:
    host = env.get("EMAIL_SMTP_HOST")
    port = env.get("EMAIL_SMTP_PORT") or 587
    username = (env.get("EMAIL_USERNAME") or "").strip()
    password = (env.get("EMAIL_PASSWORD") or "").strip()
    to_addr = (env.get("EMAIL_TO") or "").strip()
    use_ssl = bool(env.get("EMAIL_USE_SSL")) or str(env.get("EMAIL_SMTP_PORT")) == "465"

    missing = [k for k, v in {
        "EMAIL_SMTP_HOST": host,
        "EMAIL_SMTP_PORT": port,
        "EMAIL_USERNAME": username,
        "EMAIL_PASSWORD": password,
        "EMAIL_TO": to_addr,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"邮件发送缺少必要的环境变量: {', '.join(missing)}")

    msg = MIMEMultipart()
    # 使用“显示名 <邮箱地址>”的格式，提升兼容性
    msg["From"] = f"{from_name} <{username}>"
    msg["Reply-To"] = username
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for fp in attachments or []:
        try:
            if not fp:
                continue
            fn = str(fp)
            if not os.path.exists(fn):
                print(f"[WARN] 附件不存在，已跳过: {fn}")
                continue
            with open(fn, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header("Content-Disposition", "attachment", filename=fn.split("/")[-1].split("\\")[-1])
                msg.attach(part)
        except Exception as ex:
            print(f"[WARN] 附件读取失败，已跳过: {fp} - {ex}")

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(username, password)
                server.sendmail(username, [to_addr], msg.as_string())
        else:
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(username, password)
                server.sendmail(username, [to_addr], msg.as_string())
    except smtplib.SMTPAuthenticationError as e:
        code = getattr(e, "smtp_code", None)
        err = getattr(e, "smtp_error", b"").decode(errors="ignore") if isinstance(getattr(e, "smtp_error", b""), (bytes, bytearray)) else str(getattr(e, "smtp_error", ""))
        raise RuntimeError(f"SMTP 认证失败(code={code}): {err}")
    except smtplib.SMTPException as e:
        code = getattr(e, "smtp_code", None)
        err = getattr(e, "smtp_error", b"").decode(errors="ignore") if isinstance(getattr(e, "smtp_error", b""), (bytes, bytearray)) else str(getattr(e, "smtp_error", ""))
        raise RuntimeError(f"SMTP 错误(code={code}): {err or e}")
