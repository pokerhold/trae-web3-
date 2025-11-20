import requests
from typing import List, Dict
from deep_translator import GoogleTranslator
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class CryptoPanicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cryptopanic.com/api/v1"
        # 初始化翻译器
        self.translator = GoogleTranslator(source='auto', target='zh-CN')
        
        # --- 新增：配置自动重试机制 ---
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        # ---------------------------

    def fetch_hot_news(self, limit: int = 20) -> List[Dict]:
        """抓取并翻译当前最热的新闻"""
        if not self.api_key:
            print("[WARN] CryptoPanic API Key 未配置")
            return []

        url = f"{self.base_url}/posts/"
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "filter": "hot",
            "kind": "news",
        }
        
        try:
            # 修改：使用 session 发送请求，超时时间加长到 60 秒
            r = self.session.get(url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            
            processed = []
            for item in results[:limit]:
                processed.append(self._normalize(item))
            return processed
            
        except Exception as e:
            # 捕获所有异常，打印警告但不报错崩溃
            print(f"[WARN] CryptoPanic 抓取失败 (已跳过): {e}")
            return []

    def _normalize(self, item: Dict) -> Dict:
        domain = item.get("domain", "unknown")
        source_title = item.get("source", {}).get("title", domain)
        raw_title = item.get("title", "")
        
        try:
            title_zh = self.translator.translate(raw_title)
        except Exception:
            title_zh = raw_title
        
        return {
            "title": title_zh,
            "published_at": item.get("published_at", ""),
            "source": source_title,
            "url": item.get("url", ""),
            "currencies": ", ".join([c.get("code") for c in item.get("currencies") or []])
        }