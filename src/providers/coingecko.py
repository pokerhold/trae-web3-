import requests
from typing import List, Dict

class CoinGeckoClient:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"

    def fetch_market_data(self, limit: int = 100) -> List[Dict]:
        """获取市值排名"""
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
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            return [self._normalize_market(x) for x in r.json()]
        except Exception as e:
            print(f"[WARN] CoinGecko 价格失败: {e}")
            return []

    def fetch_trending(self) -> List[Dict]:
        """获取热搜币种 (用于生态板块)"""
        url = f"{self.base_url}/search/trending"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            data = r.json().get("coins", [])
            return [self._normalize_trending(x['item']) for x in data[:7]] # 取前7个
        except Exception as e:
            print(f"[WARN] CoinGecko 热搜失败: {e}")
            return []

    @staticmethod
    def _normalize_market(item: Dict) -> Dict:
        return {
            "symbol": item.get("symbol", "").upper(),
            "price": item.get("current_price", 0),
            "change_24h": item.get("price_change_percentage_24h", 0),
            "market_cap": item.get("market_cap", 0),
        }

    @staticmethod
    def _normalize_trending(item: Dict) -> Dict:
        return {
            "name": item.get("name"),
            "symbol": item.get("symbol"),
            "rank": item.get("market_cap_rank"),
            "score": item.get("score") + 1 # 排名 0 开始，改为 1
        }
