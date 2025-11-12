from pathlib import Path
from typing import Dict, List
import pandas as pd


def _to_df(items: List[dict], columns: List[str]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=columns)
    # 只保留需要的列并按列顺序输出
    rows = []
    for it in items:
        row = {col: it.get(col, "") for col in columns}
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)


def export_structured_to_excel(structured: Dict, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 定义各模块的列
    financing_cols = ["project_name", "amount", "round", "sector", "date", "sources"]
    airdrop_cols = ["project_name", "signal", "task_url", "tge_date", "notes"]
    eco_cols = ["chain", "change_type", "description", "metrics", "source"]
    token_cols = ["project_name", "token", "change", "unlock_date", "amount", "impact", "source"]
    action_cols = ["title", "action", "reason", "urgency_score", "due_hint"]

    financing = structured.get("financing", [])
    airdrops = structured.get("airdrops", [])
    ecosystems = structured.get("ecosystems", [])
    tokenomics = structured.get("tokenomics", [])
    actions = structured.get("actions", [])

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        _to_df(financing, financing_cols).to_excel(writer, sheet_name="融资项目", index=False)
        _to_df(airdrops, airdrop_cols).to_excel(writer, sheet_name="潜在空投", index=False)
        _to_df(ecosystems, eco_cols).to_excel(writer, sheet_name="核心链生态", index=False)
        _to_df(tokenomics, token_cols).to_excel(writer, sheet_name="代币经济", index=False)
        _to_df(actions, action_cols).to_excel(writer, sheet_name="操作清单", index=False)

    return out_path