def parse_amount(amount_str):
    """提取金额数字"""
    try:
        clean = str(amount_str).replace("$", "").replace(",", "").lower()
        if "m" in clean: return float(clean.replace("m", "")) * 1000000
        if "k" in clean: return float(clean.replace("k", "")) * 1000
        return float(clean)
    except:
        return 0

def generate_market_analysis(fundraising, airdrops, unlocks, ecosystem, markets):
    """
    包含【市场行情】的规则生成引擎
    """
    # 1. 市场行情分析
    market_summary = "暂无数据"
    top_gainers = []
    top_losers = []
    btc_price = "N/A"
    
    if markets:
        # 找 BTC 价格
        btc_obj = next((x for x in markets if x['symbol'] == 'BTC'), None)
        if btc_obj:
            btc_price = f"${btc_obj['price']:,}"
        
        # 找涨跌幅榜
        sorted_mkt = sorted(markets, key=lambda x: x['change_24h'] or 0, reverse=True)
        top_gainers = [x for x in sorted_mkt[:3] if x['change_24h'] > 3] # 涨超3%才算
        top_losers = [x for x in sorted_mkt[-3:] if x['change_24h'] < -3] # 跌超3%才算
        
        market_summary = f"BTC 现价 <b>{btc_price}</b>。"
        if top_gainers:
            g_str = ", ".join([f"{x['symbol']} (+{x['change_24h']:.1f}%)" for x in top_gainers])
            market_summary += f" 今日领涨: {g_str}。"
        elif top_losers:
            l_str = ", ".join([f"{x['symbol']} ({x['change_24h']:.1f}%)" for x in top_losers])
            market_summary += f" 今日领跌: {l_str}。"
        else:
            market_summary += " 主流市场波动较小。"

    # 2. 融资分析
    top_project = "暂无"
    top_amount = "0"
    if fundraising:
        sorted_fund = sorted(fundraising, key=lambda x: parse_amount(x.get('amount')), reverse=True)
        top = sorted_fund[0]
        top_project = top.get('project_name')
        top_amount = top.get('amount')

    # 3. 生成建议清单
    suggestions = []
    
    # 规则: 暴跌抄底机会? (仅示例，非投资建议)
    for item in top_losers:
        suggestions.append(f"[📉关注] <b>{item['symbol']}</b>: 24小时跌幅达 {item['change_24h']:.1f}%，关注超卖反弹机会。")

    # 规则: 大额融资
    for item in fundraising[:3]:
        amt = parse_amount(item.get('amount'))
        if amt > 5000000:
            suggestions.append(f"[💰融资] <b>{item.get('project_name')}</b>: 完成 {item.get('amount')} 大额融资。")
    
    # 规则: 空投
    for item in airdrops[:3]:
        suggestions.append(f"[🪂空投] <b>{item.get('project_name')}</b>: 出现空投/任务信号。")
        
    # 规则: 解锁
    for item in unlocks[:2]:
        suggestions.append(f"[⚠️解锁] <b>{item.get('project_name')}</b>: 即将解锁 {item.get('amount')} 代币。")

    if not suggestions:
        suggestions.append("今日市场平淡，暂无高优先级操作建议。")

    html = f"""
    <h3>📈 市场行情 (CoinGecko)</h3>
    <p>{market_summary}</p>
    <hr>
    <h3>📊 链上数据洞察</h3>
    <p>今日融资 <b>{len(fundraising)}</b> 起 (最大: {top_project} - {top_amount})。
    监控到 {len(airdrops)} 个空投信号。</p>
    <hr>
    <h3>📝 重点关注清单</h3>
    <ul>
        {''.join([f'<li>{s}</li>' for s in suggestions])}
    </ul>
    """
    return html
