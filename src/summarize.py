def parse_amount(amount_str):
    """提取金额数字用于排序"""
    try:
        clean = str(amount_str).replace("$", "").replace(",", "").lower()
        if "m" in clean: return float(clean.replace("m", "")) * 1000000
        if "k" in clean: return float(clean.replace("k", "")) * 1000
        return float(clean)
    except:
        return 0

def generate_market_analysis(fundraising, airdrops, unlocks, ecosystem):
    """基于规则生成 HTML 简报"""
    
    total_raise = len(fundraising)
    total_airdrop = len(airdrops)
    
    # 1. 找最大融资
    top_project = "暂无"
    top_amount = "0"
    if fundraising:
        sorted_fund = sorted(fundraising, key=lambda x: parse_amount(x.get('amount')), reverse=True)
        top = sorted_fund[0]
        top_project = top.get('project_name')
        top_amount = top.get('amount')

    # 2. 生成操作建议
    suggestions = []
    
    # 规则: 大额融资
    for item in fundraising[:3]:
        amt = parse_amount(item.get('amount'))
        if amt > 5000000:
            suggestions.append(f"[⭐⭐⭐⭐⭐] <b>{item.get('project_name')}</b>: 完成 {item.get('amount')} 大额融资，机构关注度高。")
    
    # 规则: 空投机会
    for item in airdrops[:3]:
        suggestions.append(f"[⭐⭐⭐⭐] <b>{item.get('project_name')}</b>: 出现空投/任务信号，建议检查交互资格。")
        
    # 规则: 解锁预警
    for item in unlocks[:2]:
        suggestions.append(f"[⚠️风险] <b>{item.get('project_name')}</b>: 即将解锁 {item.get('amount')} 代币，注意波动。")

    if not suggestions:
        suggestions.append("今日市场平淡，暂无高优先级操作建议。")

    html = f"""
    <h3>📊 市场核心洞察</h3>
    <p>今日监控到 <b>{total_raise}</b> 起融资。最受关注的是 <b>{top_project}</b> (融资 {top_amount})。
    另有 {total_airdrop} 个空投相关信号。</p>
    <hr>
    <h3>📝 建议操作清单 (Top Picks)</h3>
    <ul>
        {''.join([f'<li>{s}</li>' for s in suggestions])}
    </ul>
    """
    return html
