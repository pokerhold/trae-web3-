import os
import sys
from datetime import datetime
from src.providers.rootdata import RootDataClient
from src.providers.coingecko import CoinGeckoClient
from src.providers.cryptopanic import CryptoPanicClient
from src.senders.email_sender import send_email
from src.summarize import generate_market_analysis

# --- 👇 这里直接植入 HTML 生成逻辑，不再依赖外部文件 👇 ---
def save_to_html(data_map: dict, output_dir: str = "output") -> str:
    """直接在主程序中生成 HTML 报告"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_name = f"Web3_Daily_Report_{date_str}.html"
    file_path = os.path.join(output_dir, file_name)

    # CSS 样式
    css = """
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 20px; color: #333; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }
        .header { background: #0366d6; color: white; padding: 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0 0; opacity: 0.8; font-size: 14px; }
        .tabs { display: flex; background: #f0f2f5; border-bottom: 1px solid #ddd; overflow-x: auto; }
        .tab-btn { padding: 15px 20px; cursor: pointer; border: none; background: none; font-weight: 600; color: #666; white-space: nowrap; }
        .tab-btn:hover { background: #e6e8eb; }
        .tab-btn.active { color: #0366d6; border-bottom: 3px solid #0366d6; background: white; }
        .content { padding: 20px; display: none; }
        .content.active { display: block; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; padding: 12px; background: #f9fafb; border-bottom: 2px solid #eee; color: #555; position: sticky; top: 0; }
        td { padding: 12px; border-bottom: 1px solid #eee; vertical-align: middle; }
        tr:hover { background: #f8f9fa; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500; }
        .tag-green { background: #e6fffa; color: #047857; }
        .tag-red { background: #fef2f2; color: #b91c1c; }
        .tag-blue { background: #eff6ff; color: #1d4ed8; }
        a { color: #0366d6; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .empty-tip { text-align: center; padding: 40px; color: #999; }
    </style>
    """

    # JavaScript
    js = """
    <script>
        function openTab(evt, tabName) {
            var i, x, tablinks;
            x = document.getElementsByClassName("content");
            for (i = 0; i < x.length; i++) { x[i].className = x[i].className.replace(" active", ""); }
            tablinks = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
            document.getElementById(tabName).className += " active";
            evt.currentTarget.className += " active";
        }
    </script>
    """

    tabs_html = '<div class="tabs">'
    contents_html = ''
    is_first = True
    
    for title, data in data_map.items():
        clean_title = title.split('.', 1)[-1] if '.' in title else title
        tab_id = f"tab_{clean_title.replace(' ', '_')}"
        active_class = " active" if is_first else ""
        
        tabs_html += f'<button class="tab-btn{active_class}" onclick="openTab(event, \'{tab_id}\')">{clean_title} ({len(data)})</button>'
        contents_html += f'<div id="{tab_id}" class="content{active_class}">'
        
        if not data:
            contents_html += '<div class="empty-tip">No Data</div>'
        else:
            headers = data[0].keys()
            contents_html += '<table><thead><tr>'
            for h in headers:
                contents_html += f'<th>{h.replace("_", " ").title()}</th>'
            contents_html += '</tr></thead><tbody>'
            
            for item in data:
                contents_html += '<tr>'
                for k, v in item.items():
                    val = str(v)
                    if "http" in val: val = f"<a href='{val}' target='_blank'>Link</a>"
                    elif "%" in val and "-" in val: val = f'<span class="tag tag-red">{val}</span>'
                    elif "%" in val: val = f'<span class="tag tag-green">{val}</span>'
                    elif k == "amount" and "m" in val.lower(): val = f'<span class="tag tag-blue">{val}</span>'
                    contents_html += f'<td>{val}</td>'
                contents_html += '</tr>'
            contents_html += '</tbody></table>'
            
        contents_html += '</div>'
        is_first = False

    tabs_html += '</div>'
    full_html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Report</title>{css}</head><body><div class="container"><div class="header"><h1>🚀 Web3 Daily Insight</h1><p>{date_str}</p></div>{tabs_html}{contents_html}</div>{js}</body></html>"""

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"[INFO] HTML Report Generated: {file_path}")
        return file_path
    except Exception as e:
        print(f"[ERROR] HTML Gen Failed: {e}")
        return None
# ----------------------------------------------------------

def main():
    print(">>> [1/4] 启动抓取任务...")
    
    # 1. RootData
    rd = RootDataClient()
    fund = rd.fetch_fundraising()
    air = rd.fetch_airdrops()
    eco = rd.fetch_ecosystem()
    unl = rd.fetch_token_unlocks()
    
    # 2. CoinGecko
    cg = CoinGeckoClient()
    markets = cg.fetch_market_data(limit=30)
    
    # 3. CryptoPanic
    cp_key = os.getenv("CRYPTOPANIC_API_KEY", "")
    cp = CryptoPanicClient(api_key=cp_key)
    news = cp.fetch_hot_news(limit=20)
    
    print(f"    - 融资:{len(fund)} | 行情:{len(markets)} | 新闻:{len(news)}")

    print(">>> [2/4] 生成分析简报...")
    summary_html = generate_market_analysis(fund, air, unl, eco, markets, news)

    print(">>> [3/4] 生成 HTML 报告附件...")
    # 直接调用上面的内部函数，不再引用外部文件
    report_path = save_to_html({
        "0.市场行情": markets,
        "1.舆情热点": news,
        "2.融资事件": fund,
        "3.潜在空投": air,
        "4.代币解锁": unl,
        "5.生态变化": eco
    })

    print(">>> [4/4] 发送邮件...")
    email_body = f"""
    <h2>Web3 每日投研简报</h2>
    <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #0366d6;">
        {summary_html}
    </div>
    <p style="margin-top: 20px;">📎 <b>完整交互式数据请查看附件 HTML 文件 (推荐用浏览器打开)。</b></p>
    <hr>
    <small>Generated by GitHub Actions</small>
    """
    
    attachments = [report_path] if report_path else []
    
    try:
        send_email(
            subject=f"🚀 Web3 日报: {len(news)}条热点 | 融资{len(fund)}起",
            body=email_body,
            env=os.environ,
            attachments=attachments
        )
        print("✅ 任务成功完成！")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
