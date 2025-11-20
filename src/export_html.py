import os
from datetime import datetime

def save_to_html(data_map: dict, output_dir: str = "output") -> str:
    """
    Generate HTML report
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_name = f"Web3_Daily_Report_{date_str}.html"
    file_path = os.path.join(output_dir, file_name)

    # CSS Styles
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
        .tag-gray { background: #f3f4f6; color: #4b5563; }
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

    # Generate Content
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
            contents_html += '<div class="empty-tip">No Data Today</div>'
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
                    
                    # [Fix: Simplified logic to avoid syntax errors]
                    if "http" in val:
                        # Changed quotes and removed special arrow char
                        val = f"<a href='{val}' target='_blank'>Link</a>"
                    elif "%" in val and "-" in val:
                        val = f'<span class="tag tag-red">{val}</span>'
                    elif "%" in val:
                        val = f'<span class="tag tag-green">{val}</span>'
                    elif k == "amount" and "m" in val.lower():
                         val = f'<span class="tag tag-blue">{val}</span>'
                    
                    contents_html += f'<td>{val}</td>'
                contents_html += '</tr>'
            contents_html += '</tbody></table>'
            
        contents_html += '</div>'
        is_first = False

    tabs_html += '</div>'

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web3 Daily Report</title>
        {css}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Web3 Daily Insight</h1>
                <p>{date_str} • Generated by GitHub Actions</p>
            </div>
            {tabs_html}
            {contents_html}
        </div>
        {js}
    </body>
    </html>
    """

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        print(f"[INFO] HTML Report Generated: {file_path}")
        return file_path
    except Exception as e:
        print(f"[ERROR] Failed to generate HTML: {e}")
        return None
