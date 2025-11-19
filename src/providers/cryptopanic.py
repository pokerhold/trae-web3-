import requests
from typing import List, Dict

class CryptoPanicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cryptopanic.com/api/v1"

    def fetch_hot_news(self, limit: int = 20) -> List[Dict]:
        """抓取当前最热的新闻 (Rising/Hot)"""
        if not self.api_key:
            print("[WARN] CryptoPanic API Key 未配置，跳过舆情抓取")
            return []

        url = f"{self.base_url}/posts/"
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "filter": "rising", # 抓取“飙升”的新闻
            "kind": "news",     # 只看新闻，不看媒体视频
        }
        
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            return [self._normalize(x) for x in results[:limit]]
        except Exception as e:
            print(f"[WARN] CryptoPanic 抓取失败: {e}")
            return []

    @staticmethod
    def _normalize(item: Dict) -> Dict:
        domain = item.get("domain", "unknown")
        source_title = item.get("source", {}).get("title", domain)
        
        return {
            "title": item.get("title", ""),
            "published_at": item.get("published_at", ""),
            "source": source_title,
            "url": item.get("url", ""), # 这是跳转链接
            "currencies": ", ".join([c.get("code") for c in item.get("currencies") or []])
        }