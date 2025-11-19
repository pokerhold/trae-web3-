def parse_amount(amount_str):
    """提取金额数字"""
    try:
        clean = str(amount_str).replace("$", "").replace(",", "").lower()
        if "m" in clean: return float(clean.replace("m", "")) * 1000000
        if "k" in clean: return float(clean.replace("k", "")) * 1000
        return float(clean)
    except:
        return 0

def generate_market_analysis(fundraising, airdrops, unlocks, ecosystem, markets, news):
    """
    生成美观的 HTML 日报
    """
    
    # --- 1. 准备行情数据 ---
    btc_card = ""
    market_rows = ""
    
    if markets:
        # BTC 顶部卡片
        btc = next((x for x in markets if x['symbol'] == 'BTC'), None)
        if btc:
            color = "#e02f2f" if btc['change_24h'] < 0 else "#22a06b" # 跌红涨绿
            arrow = "▼" if btc['change_24h'] < 0 else "▲"
            btc_card = f"""
            <div style="background: {color}; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                <span style="font-size: 14px; opacity: 0.9;">Bitcoin (BTC)</span><br>
                <span style="font-size: 24px; font-weight: bold;">${btc['price']:,}</span>
                <span style="font-size: 16px; margin-left: 10px;">{arrow} {btc['change_24h']:.2f}%</span>
            </div>
            """
        
        # 领涨领跌表格
        sorted_mkt = sorted(markets, key=lambda x: x['change_24h'] or 0, reverse=True)
        top_movers = sorted_mkt[:3] + sorted_mkt[-3:] # 前3和后3
        
        for coin in top_movers:
            c_color = "red" if coin['change_24h'] < 0 else "green"
            market_rows += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 8px;"><b>{coin['symbol']}</b></td>
                <td style="padding: 8px; text-align: right;">${coin['price']:,}</td>
                <td style="padding: 8px; text-align: right; color: {c_color};">{coin['change_24h']:.2f}%</td>
            </tr>
            """

    # --- 2. 准备舆情列表 ---
    news_html = ""
    if news:
        for n in news[:6]: # 只展示前6条
            tags = f"<span style='background:#f0f0f0; color:#666; padding:2px 6px; border-radius:4px; font-size:10px; margin-left:5px'>{n['currencies']}</span>" if n['currencies'] else ""
            news_html += f"""
            <div style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #eee;">
                <a href='{n['url']}' style='text-decoration:none; color:#333; font-size:15px; font-weight:500; display:block; margin-bottom:4px;'>{n['title']}</a>
                <div style="font-size: 12px; color: #999;">
                    {n['source']} {tags}
                </div>
            </div>
            """
    else:
        news_html = "<div style='color:#999; padding:10px'>暂无热点新闻</div>"

    # --- 3. 准备操作建议 ---
    suggestions_html = ""
    
    # 融资高亮
    for item in fundraising[:3]:
        amt = parse_amount(item.get('amount'))
        if amt > 5000000:
            suggestions_html += f"""
            <div style="background:#eef6ff; border-left:4px solid #0366d6; padding:10px; margin-bottom:10px; font-size:14px;">
                <span style="color:#0366d6; font-weight:bold;">[💰大额融资]</span> 
                <b>{item.get('project_name')}</b> 获得 {item.get('amount')} 融资。
            </div>
            """
            
    # 空投高亮
    for item in airdrops[:2]:
        suggestions_html += f"""
            <div style="background:#fff8ee; border-left:4px solid #f2994a; padding:10px; margin-bottom:10px; font-size:14px;">
                <span style="color:#d97706; font-weight:bold;">[🪂空投信号]</span> 
                <b>{item.get('project_name')}</b>: {item.get('status', '关注任务')}。
            </div>
            """

    if not suggestions_html:
        suggestions_html = "<div style='color:#999; padding:10px'>今日暂无高优先级信号</div>"

    # --- 4. 组装整体 HTML ---
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
        
        <div style="text-align: center; padding-bottom: 20px;">
            <h2 style="margin: 0; color: #111;">Web3 Daily Insight</h2>
            <p style="margin: 5px 0 0; color: #666; font-size: 14px;">全网舆情 · 市场行情 · 链上数据</p>
        </div>

        {btc_card}

        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
            
            <div style="flex: 1; min-width: 260px;">
                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📈 重点异动</h3>
                    <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                        {market_rows}
                    </table>
                </div>

                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📝 操作笔记</h3>
                    {suggestions_html}
                </div>
            </div>

            <div style="flex: 1; min-width: 260px;">
                <div style="background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">🔥 舆情热点 (24H)</h3>
                    {news_html}
                </div>
            </div>
            
        </div>
        
        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #aaa;">
            📎 完整 50+ 条数据请查看邮件附件 Excel<br>
            Generated by Web3 Auto-Reporter
        </div>

    </div>
    """
    return html