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
    """全能规则引擎 (适配兜底数据)"""
    
    # 1. 市场行情
    market_summary = "暂无数据"
    if markets:
        btc = next((x for x in markets if x['symbol'] == 'BTC'), None)
        btc_price = f"${btc['price']:,}" if btc else "N/A"
        sorted_mkt = sorted(markets, key=lambda x: x['change_24h'] or 0, reverse=True)
        gainers = [x for x in sorted_mkt[:3] if x['change_24h'] > 0]
        g_str = ", ".join([f"{x['symbol']} +{x['change_24h']:.1f}%" for x in gainers])
        market_summary = f"BTC {btc_price}。领涨: {g_str}。"

    # 2. 舆情列表 (前 50 条)
    news_html_list = ""
    if news:
        for n in news[:50]: 
            tags = f"<span style='background:#f0f0f0; color:#666; padding:2px 6px; border-radius:4px; font-size:10px; margin-left:5px'>{n['currencies']}</span>" if n['currencies'] else ""
            news_html_list += f"""
            <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px dashed #eee;">
                <a href='{n['url']}' style='text-decoration:none; color:#0366d6; font-size:13px; font-weight:500; display:block; margin-bottom:2px;'>{n['title']}</a>
                <div style="font-size: 11px; color: #999;">
                    {n['source']} {tags}
                </div>
            </div>
            """
    else:
        news_html_list = "<div style='color:#999; padding:10px'>暂无热点新闻</div>"

    # 3. 热搜列表
    trending_html = ""
    if ecosystem: 
        for t in ecosystem:
            trending_html += f"""
            <span style="display:inline-block; background:#fff; border:1px solid #ddd; border-radius:20px; padding:4px 10px; margin:4px 4px 4px 0; font-size:13px;">
                <span style="color:#e02f2f; font-weight:bold;">#{t['score']}</span> {t['name']} ({t['symbol']})
            </span>
            """
    else:
        trending_html = "暂无热搜"

    # 4. 智能操作建议 (适配兜底数据)
    suggestions = []
    
    # A. 融资/热门建议
    # 如果 amount 包含 Rank，说明是热搜填充数据；如果是数字，说明是融资数据
    for item in fundraising[:3]:
        amt = str(item.get('amount', ''))
        name = item.get('project_name', 'Unknown')
        if "Rank" in amt:
            suggestions.append(f"[🔥热门] <b>{name}</b>: 社区热度高，位列 {amt}。")
        elif parse_amount(amt) > 5000000:
            suggestions.append(f"[💰融资] <b>{name}</b>: 获得大额融资 {amt}。")
        elif "News" in name: # 从新闻提取的
             suggestions.append(f"[📰关注] <b>{item.get('info')}</b>")

    # B. 空投建议
    for item in airdrops[:3]:
        suggestions.append(f"[🪂空投] <b>{item.get('project_name')}</b>: {item.get('info', '出现相关信号')}。")
        
    # C. 解锁/风险建议
    for item in unlocks[:3]:
        # 如果是跌幅数据
        if "Drop" in str(item.get('unlock_date', '')):
             suggestions.append(f"[📉超卖] <b>{item.get('project_name')}</b>: 24H跌幅 {item.get('amount')}，注意风险或反弹。")
        else:
             suggestions.append(f"[⚠️解锁] <b>{item.get('project_name')}</b>: 即将解锁 {item.get('amount')}。")

    if not suggestions:
        suggestions.append("今日市场平淡，暂无高优先级信号。")

    # 5. 组装 HTML
    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 800px; margin: 0 auto; color: #333;">
        <div style="text-align: center; padding-bottom: 20px;">
            <h2 style="margin: 0;">Web3 Daily Insight</h2>
            <p style="margin: 5px 0 0; color: #666; font-size: 14px;">全网舆情 · 市场行情 · 链上数据</p>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
            <div style="flex: 1; min-width: 300px;">
                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📈 市场概况</h3>
                    <p style="font-size:14px; line-height:1.5;">{market_summary}</p>
                </div>
                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">🔥 今日热搜</h3>
                    <div style="line-height: 1.6;">{trending_html}</div>
                </div>
                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📝 重点关注</h3>
                    <ul>{''.join([f'<li>{s}</li>' for s in suggestions])}</ul>
                </div>
            </div>

            <div style="flex: 1; min-width: 300px;">
                <div style="background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">🌍 舆情热点 (Top 50)</h3>
                    {news_html_list}
                </div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #aaa;">
            📎 完整数据请查看附件 HTML<br>Generated by Web3 Auto-Reporter
        </div>
    </div>
    """
    return html
