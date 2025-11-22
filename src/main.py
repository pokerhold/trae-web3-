import os
import sys
import re
from datetime import datetime
from src.providers.rootdata import RootDataClient
from src.providers.coingecko import CoinGeckoClient
from src.providers.cryptopanic import CryptoPanicClient
from src.senders.email_sender import send_email
from src.summarize import generate_market_analysis

# --- 辅助：从新闻中提取数据的补救函数 ---
def extract_data_from_news(news_list, keywords):
    """从新闻标题中筛选符合关键词的内容，作为备用数据"""
    extracted = []
    for n in news_list:
        title = n.get('title', '').lower()
        # 如果标题包含任一关键词
        if any(k in title for k in keywords):
            extracted.append({
                "project_name": n.get('currencies') or "News", # 尝试用币种标签作为项目名
                "info": n.get('title'),
                "url": n.get('url'),
                "date": n.get('published_at', '')[:10]
            })
    return extracted
# --------------------------------------

def save_to_html(data_map: dict, output_dir: str = "output") -> str:
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = os.path.join(output_dir, f"Web3_Daily_Report_{date_str}.html")

    # CSS 保持简洁美观
    css = """
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f6f8; padding: 20px; color: #333; }
        .container { max-width: 1000px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow: hidden; }
        .header { background: #0366d6; color: white; padding: 20px; text-align: center; }
        .tabs { display: flex; background: #f0f2f5; border-bottom: 1px solid #ddd; overflow-x: auto; }
        .tab-btn { padding: 15px 20px; cursor: pointer; border: none; background: none; font-weight: 600; color: #666; white-space: nowrap; }
        .tab-btn.active { color: #0366d6; border-bottom: 3px solid #0366d6; background: white; }
        .content { padding: 20px; display: none; }
        .content.active { display: block; }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; padding: 12px; background: #f9fafb; border-bottom: 2px solid #eee; }
        td { padding: 12px; border-bottom: 1px solid #eee; }
        .tag-red { background: #fef2f2; color: #b91c1c; padding: 2px 6px; border-radius: 4px; }
        .tag-green { background: #e6fffa; color: #047857; padding: 2px 6px; border-radius: 4px; }
        a { color: #0366d6; text-decoration: none; }
    </style>
    """
    js = """
    <script>
        function openTab(evt, tabName) {
            var i, x, tablinks;
            x = document.getElementsByClassName("content");
            for (i = 0; i < x.length; i++) { x[i].style.display = "none"; }
            tablinks = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tablinks.length; i++) { tablinks[i].className = tablinks[i].className.replace(" active", ""); }
            document.getElementById(tabName).style.display = "block";
            evt.currentTarget.className += " active";
        }
    </script>
    """

    tabs_html = '<div class="tabs">'
    contents_html = ''
    is_first = True
    
    for title, data in data_map.items():
        clean_title = title.split('.', 1)[-1]
        tab_id = f"tab_{clean_title.replace(' ', '_')}"
        active_class = " active" if is_first else ""
        display_style = "block" if is_first else "none"
        
        tabs_html += f'<button class="tab-btn{active_class}" onclick="openTab(event, \'{tab_id}\')">{clean_title} ({len(data)})</button>'
        
        contents_html += f'<div id="{tab_id}" class="content" style="display:{display_style}">'
        if not data:
            contents_html += '<div style="text-align:center; padding:40px; color:#999">暂无数据</div>'
        else:
            headers = data[0].keys()
            contents_html += '<table><thead><tr>'
            for h in headers: contents_html += f'<th>{h.title()}</th>'
            contents_html += '</tr></thead><tbody>'
            for item in data:
                contents_html += '<tr>'
                for k, v in item.items():
                    val = str(v)
                    if k == "market_cap": # 市值 B 单位优化
                        try: val = f"${float(v)/1000000000:,.2f}B"
                        except: pass
                    elif "http" in val: val = f"<a href='{val}' target='_blank'>Link</a>"
                    elif "%" in val and "-" in val: val = f'<span class="tag-red">{val}</span>'
                    elif "%" in val: val = f'<span class="tag-green">{val}</span>'
                    contents_html += f'<td>{val}</td>'
                contents_html += '</tr>'
            contents_html += '</tbody></table>'
        contents_html += '</div>'
        is_first = False

    tabs_html += '</div>'
    full_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'>{css}</head><body><div class='container'><div class='header'><h1>🚀 Web3 Daily Insight</h1><p>{date_str}</p></div>{tabs_html}{contents_html}</div>{js}</body></html>"

    with open(file_path, "w", encoding="utf-8") as f: f.write(full_html)
    return file_path

def main():
    print(">>> [1/4] 启动全网数据抓取...")
    
    # 1. 获取核心数据 (CoinGecko & CryptoPanic)
    # 这两个是最稳的，绝对有数据
    cg = CoinGeckoClient()
    markets = cg.fetch_market_data(limit=100)
    trending = cg.fetch_trending() # 新增：抓取热搜榜
    
    cp_key = os.getenv("CRYPTOPANIC_API_KEY", "")
    cp = CryptoPanicClient(api_key=cp_key)
    news = cp.fetch_hot_news(limit=50)
    
    # 2. 尝试获取 RootData (可能为空)
    rd = RootDataClient()
    fund = rd.fetch_fundraising()
    air = rd.fetch_airdrops()
    unl = rd.fetch_token_unlocks()
    
    # 3. 智能补全逻辑 (如果 RootData 没数据，从新闻里挖！)
    if not fund:
        print("⚠️ RootData 融资数据为空，正在从新闻中智能提取...")
        fund = extract_data_from_news(news, ["raise", "funding", "invest", "backed", "融资", "投资", "千万"])
    
    if not air:
        print("⚠️ RootData 空投数据为空，正在从新闻中智能提取...")
        air = extract_data_from_news(news, ["airdrop", "snapshot", "claim", "testnet", "空投", "快照", "测试网"])

    print(f"    - 融资:{len(fund)} | 行情:{len(markets)} | 热搜:{len(trending)}")

    print(">>> [2/4] 生成分析简报...")
    # 把 trending 传给 ecosystem 参数
    summary_html = generate_market_analysis(fund, air, unl, trending, markets, news)

    print(">>> [3/4] 生成 HTML 报告附件...")
    report_path = save_to_html({
        "0.市场行情": markets,
        "1.舆情热点": news,
        "2.融资事件": fund,
        "3.潜在空投": air,
        "4.今日热搜": trending, # 用热搜替代生态变化
        "5.代币解锁": unl
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
            subject=f"🚀 Web3 日报: {len(news)}条热点 | {len(fund)}起融资动态",
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
