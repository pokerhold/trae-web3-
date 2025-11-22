import requests
from typing import Dict, List, Union

class RootDataClient:
    def __init__(self, base_url: str = "https://api.rootdata.com/open", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        # [优化] 伪装成浏览器
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*"
        }
        if api_key:
            self.headers["x-api-key"] = api_key

    def _get(self, path: str, params: Dict = None) -> Union[Dict, List]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            r = requests.get(url, headers=self.headers, params=params or {}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            # 这里不打印错误，静默失败，交给 main.py 的备用方案处理
            return {}

    def _fetch_list(self, endpoint: str, normalizer_func) -> List[Dict]:
        data = self._get(endpoint)
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("data") or data.get("items") or []
        
        if not isinstance(items, list):
            return []
            
        return [normalizer_func(x) for x in items if isinstance(x, dict)]

    def fetch_fundraising(self) -> List[Dict]:
        return self._fetch_list("fundraising_projects", self._normalize_fundraising)

    def fetch_token_unlocks(self) -> List[Dict]:
        return self._fetch_list("token_unlocks", self._normalize_token_unlocks)

    def fetch_airdrops(self) -> List[Dict]:
        return self._fetch_list("airdrops", self._normalize_airdrop)

    @staticmethod
    def _normalize_fundraising(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or x.get("name") or "Unknown",
            "amount": x.get("amount") or x.get("money") or "N/A",
            "investors": x.get("investors") or "",
            "date": x.get("date") or "",
        }

    @staticmethod
    def _normalize_token_unlocks(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or "Unknown",
            "token": x.get("token") or x.get("symbol") or "",
            "amount": x.get("amount") or "0",
            "unlock_date": x.get("unlock_date") or "",
        }

    @staticmethod
    def _normalize_airdrop(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or "Unknown",
            "status": x.get("status") or "Active",
        }
