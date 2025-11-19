import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def send_email(subject: str, body: str, env: dict, from_name: str = "Web3 Reporter", attachments: list = None) -> None:
    host = env.get("EMAIL_SMTP_HOST")
    
    # [修复 1] 确保端口是整数 (int)，防止 ValueError
    try:
        port = int(env.get("EMAIL_SMTP_PORT") or 587)
    except ValueError:
        port = 587

    username = (env.get("EMAIL_USERNAME") or "").strip()
    password = (env.get("EMAIL_PASSWORD") or "").strip()
    to_addr = (env.get("EMAIL_TO") or "").strip()

    # [修复 2] 修复 SSL 判断逻辑，防止 "false" 字符串被误判为 True
    use_ssl_str = str(env.get("EMAIL_USE_SSL", "")).lower()
    use_ssl = use_ssl_str in ("true", "1", "yes", "on") or port == 465

    # 检查必要参数
    missing = [k for k, v in {
        "EMAIL_SMTP_HOST": host,
        "EMAIL_USERNAME": username,
        "EMAIL_PASSWORD": password,
        "EMAIL_TO": to_addr,
    }.items() if not v]
    
    if missing:
        raise RuntimeError(f"邮件发送缺少必要的环境变量: {', '.join(missing)}")

    msg = MIMEMultipart()
    # 使用“显示名 <邮箱地址>”的格式
    msg["From"] = f"{from_name} <{username}>"
    msg["Reply-To"] = username
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    # 处理附件
    for fp in attachments or []:
        try:
            if not fp:
                continue
            fn = str(fp)
            if not os.path.exists(fn):
                print(f"[WARN] 附件不存在，已跳过: {fn}")
                continue
            
            # [修复 3] 使用标准库提取文件名，兼容性更好
            file_name = os.path.basename(fn)
            
            with open(fn, "rb") as f:
                part = MIMEApplication(f.read())
                part.add_header("Content-Disposition", "attachment", filename=file_name)
                msg.attach(part)
        except Exception as ex:
            print(f"[WARN] 附件读取失败，已跳过: {fp} - {ex}")

    # 发送邮件
    try:
        if use_ssl:
            # SSL 模式 (通常是 465 端口)
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(username, password)
                server.sendmail(username, [to_addr], msg.as_string())
        else:
            # TLS 模式 (通常是 587 端口)
            with smtplib.SMTP(host, port) as server:
                server.starttls() # 只有非 SSL 连接才需要 starttls
                server.login(username, password)
                server.sendmail(username, [to_addr], msg.as_string())
                
    except smtplib.SMTPAuthenticationError as e:
        # 优化错误信息提取
        err_msg = str(getattr(e, "smtp_error", e))
        raise RuntimeError(f"SMTP 认证失败 (Code: {getattr(e, 'smtp_code', '?')}): {err_msg}")
    except smtplib.SMTPException as e:
        err_msg = str(getattr(e, "smtp_error", e))
        raise RuntimeError(f"SMTP 发送错误: {err_msg}")
    except Exception as e:
        raise RuntimeError(f"发送邮件时发生未知错误: {str(e)}")
