import pandas as pd
import os
from datetime import datetime

def save_to_excel(data_map: dict, output_dir: str = "output") -> str:
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_name = f"Web3_Daily_Report_{date_str}.xlsx"
    file_path = os.path.join(output_dir, file_name)

    try:
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            has_data = False
            for sheet_name, data_list in data_map.items():
                if not data_list:
                    pd.DataFrame({"Info": ["暂无数据"]}).to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    df = pd.DataFrame(data_list)
                    # 特殊处理：如果是行情数据，格式化一下
                    if "price" in df.columns:
                        df['price'] = df['price'].apply(lambda x: f"${x}")
                        df['change_24h'] = df['change_24h'].apply(lambda x: f"{x:.2f}%")
                    
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    has_data = True
            
            if not has_data:
                pd.DataFrame({"Status": ["今日无数据"]}).to_excel(writer, sheet_name="Summary", index=False)
                
        print(f"[INFO] Excel 已生成: {file_path}")
        return file_path
    except Exception as e:
        print(f"[ERROR] Excel 生成失败: {e}")
        return None
