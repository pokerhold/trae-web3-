import requests
from typing import List, Dict
from deep_translator import GoogleTranslator

class CryptoPanicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cryptopanic.com/api/v1"
        # 初始化翻译器
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def fetch_hot_news(self, limit: int = 20) -> List[Dict]:
        """抓取并翻译当前最热的新闻"""
        if not self.api_key:
            print("[WARN] CryptoPanic API Key 未配置")
            return []

        url = f"{self.base_url}/posts/"
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "filter": "hot",    # 改为 hot，抓取更加热门的
            "kind": "news",
        }
        
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            
            # 只取前 limit 条进行处理，避免翻译太慢
            processed = []
            for item in results[:limit]:
                processed.append(self._normalize(item))
            return processed
            
        except Exception as e:
            print(f"[WARN] CryptoPanic 抓取失败: {e}")
            return []

    def _normalize(self, item: Dict) -> Dict:
        domain = item.get("domain", "unknown")
        source_title = item.get("source", {}).get("title", domain)
        raw_title = item.get("title", "")
        
        # --- 翻译逻辑 ---
        try:
            # 尝试翻译标题
            title_zh = self.translator.translate(raw_title)
        except Exception:
            # 如果翻译失败（比如网络问题），回退到英文
            title_zh = raw_title
        # ----------------
        
        return {
            "title": title_zh,  # 使用翻译后的中文标题
            "published_at": item.get("published_at", ""),
            "source": source_title,
            "url": item.get("url", ""),
            "currencies": ", ".join([c.get("code") for c in item.get("currencies") or []])
        }