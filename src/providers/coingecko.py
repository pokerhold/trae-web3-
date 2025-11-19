import requests
from typing import List, Dict

class CoinGeckoClient:
    def __init__(self):
        # 使用 CoinGecko 免费公开 API
        self.base_url = "https://api.coingecko.com/api/v3"

    def fetch_market_data(self, limit: int = 20) -> List[Dict]:
        """获取市值前 N 的代币价格和涨跌幅"""
        url = f"{self.base_url}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h"
        }
        try:
            # 增加超时设置，防止卡死
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            return [self._normalize(x) for x in data]
        except Exception as e:
            print(f"[WARN] CoinGecko 价格抓取失败: {e}")
            return []

    @staticmethod
    def _normalize(item: Dict) -> Dict:
        return {
            "symbol": item.get("symbol", "").upper(),
            "price": item.get("current_price", 0),
            "change_24h": item.get("price_change_percentage_24h", 0),
            "market_cap": item.get("market_cap", 0),
            "last_updated": item.get("last_updated", "")
        }
