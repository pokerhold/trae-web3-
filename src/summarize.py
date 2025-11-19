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
    包含【行情 + 舆情】的全能规则引擎
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

    # 2. 舆情热点摘要 (新增)
    news_html_list = ""
    if news:
        # 取前 5 条热点新闻
        for n in news[:5]:
            # 如果有代币标签，加粗显示
            tags = f" <span style='color:#666; font-size:12px'>[{n['currencies']}]</span>" if n['currencies'] else ""
            news_html_list += f"<li><a href='{n['url']}' style='text-decoration:none; color:#0366d6'>{n['title']}</a>{tags} <span style='color:#999; font-size:12px'>- {n['source']}</span></li>"
    else:
        news_html_list = "<li>暂无重大舆情更新</li>"

    # 3. 操作建议清单
    suggestions = []
    
    # 融资建议
    for item in fundraising[:3]:
        amt = parse_amount(item.get('amount'))
        if amt > 5000000:
            suggestions.append(f"[💰融资] <b>{item.get('project_name')}</b>: 完成 {item.get('amount')} 大额融资。")
    
    # 空投建议
    for item in airdrops[:3]:
        suggestions.append(f"[🪂空投] <b>{item.get('project_name')}</b>: 出现空投/任务信号。")
        
    # 暴跌反弹关注
    for item in top_losers:
        if item['change_24h'] < -5:
            suggestions.append(f"[📉超卖] <b>{item['symbol']}</b>: 跌幅 {item['change_24h']:.1f}%，关注反弹。")

    if not suggestions:
        suggestions.append("今日市场平淡，暂无高优先级操作建议。")

    # 4. 组装最终 HTML
    html = f"""
    <h3>🔥 全网舆情热点 (CryptoPanic)</h3>
    <ul>
        {news_html_list}
    </ul>
    <hr>
    <h3>📈 市场行情 (CoinGecko)</h3>
    <p>{market_summary}</p>
    <hr>
    <h3>📝 重点关注清单</h3>
    <ul>
        {''.join([f'<li>{s}</li>' for s in suggestions])}
    </ul>
    """
    return html