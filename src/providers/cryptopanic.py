import requests
import time
from typing import List, Dict
from deep_translator import GoogleTranslator

class CryptoPanicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cryptopanic.com/api/v1"
        self.translator = GoogleTranslator(source='auto', target='zh-CN')

    def fetch_hot_news(self, limit: int = 20) -> List[Dict]:
        """抓取并翻译当前最热的新闻 (带手动重试机制)"""
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

        # --- 手动重试机制 (简单粗暴，绝对稳) ---
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 设置 30秒 超时
                r = requests.get(url, params=params, timeout=30)
                r.raise_for_status()
                
                # 如果成功，直接处理数据并返回
                data = r.json()
                results = data.get("results", [])
                
                processed = []
                for item in results[:limit]:
                    processed.append(self._normalize(item))
                return processed

            except Exception as e:
                print(f"[WARN] 第 {attempt + 1} 次尝试抓取失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2) # 休息2秒再试
                else:
                    print("[ERROR] 重试 3 次仍失败，跳过舆情抓取。")
                    return [] # 彻底失败，返回空列表，保证日报能发出去
        # ------------------------------------
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