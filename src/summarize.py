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
    全能规则引擎 (高密度版)
    ecosystem 参数传入的是 trending (热搜) 数据
    """
    
    # 1. 市场行情摘要
    market_summary = "暂无数据"
    top_losers = []
    if markets:
        btc = next((x for x in markets if x['symbol'] == 'BTC'), None)
        btc_price = f"${btc['price']:,}" if btc else "N/A"
        
        sorted_mkt = sorted(markets, key=lambda x: x['change_24h'] or 0, reverse=True)
        gainers = [x for x in sorted_mkt[:3] if x['change_24h'] > 0]
        top_losers = [x for x in sorted_mkt[-3:] if x['change_24h'] < 0]
        
        g_str = ", ".join([f"{x['symbol']} +{x['change_24h']:.1f}%" for x in gainers])
        market_summary = f"BTC {btc_price}。领涨: {g_str}。"

    # 2. 舆情热点摘要 (已扩容到 50 条)
    news_html_list = ""
    if news:
        # [修改] 这里改成了 [:50]，展示前 50 条新闻
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

    # 3. 今日热搜板块
    trending_html = ""
    if ecosystem: 
        for t in ecosystem:
            trending_html += f"""
            <span style="display:inline-block; background:#fff; border:1px solid #ddd; border-radius:20px; padding:4px 10px; margin:4px 4px 4px 0; font-size:13px;">
                <span style="color:#e02f2f; font-weight:bold;">#{t['score']}</span> {t['name']} ({t['symbol']})
            </span>
            """
    else:
        trending_html = "暂无热搜数据"

    # 4. 操作建议清单
    suggestions = []
    
    for item in fundraising[:3]:
        amt = parse_amount(item.get('amount'))
        if amt > 5000000:
            suggestions.append(f"[💰融资] <b>{item.get('project_name')}</b>: 完成 {item.get('amount')} 大额融资。")
    
    for item in airdrops[:3]:
        suggestions.append(f"[🪂空投] <b>{item.get('project_name')}</b>: 出现空投/任务信号。")
        
    for item in top_losers:
        if item['change_24h'] < -5:
            suggestions.append(f"[📉超卖] <b>{item['symbol']}</b>: 跌幅 {item['change_24h']:.1f}%，关注反弹。")

    if not suggestions:
        suggestions.append("今日市场平淡，暂无高优先级操作建议。")

    # 5. 组装最终 HTML
    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; color: #333;">
        
        <div style="text-align: center; padding-bottom: 20px;">
            <h2 style="margin: 0; color: #111;">Web3 Daily Insight</h2>
            <p style="margin: 5px 0 0; color: #666; font-size: 14px;">全网舆情 · 市场行情 · 链上数据</p>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 20px;">
            
            <div style="flex: 1; min-width: 300px;">
                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📈 市场概况</h3>
                    <p style="font-size:14px; line-height:1.5;">{market_summary}</p>
                </div>

                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">🔥 今日热搜 (Top 20)</h3>
                    <div style="line-height: 1.6;">
                        {trending_html}
                    </div>
                </div>

                <div style="background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px;">📝 重点关注</h3>
                    <ul>
                        {''.join([f'<li>{s}</li>' for s in suggestions])}
                    </ul>
                </div>
            </div>

            <div style="flex: 1; min-width: 300px;">
                <div style="background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 15px;">
                    <h3 style="margin-top: 0; font-size: 16px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px;">🌍 全网热点 (Top 50)</h3>
                    {news_html_list}
                </div>
            </div>
            
        </div>
        
        <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #aaa;">
            📎 完整 200+ 条数据请查看附件 HTML<br>
            Generated by Web3 Auto-Reporter
        </div>

    </div>
    """
    return html
