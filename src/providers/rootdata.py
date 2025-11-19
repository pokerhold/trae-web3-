import requests
from typing import Dict, List, Union

class RootDataClient:
    def __init__(self, base_url: str = "https://api.rootdata.com/open", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get(self, path: str, params: Dict = None) -> Union[Dict, List]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        # 如果你有 Key，可以取消注释下面这行
        # headers = {"x-api-key": self.api_key}
        headers = {} 
        try:
            r = requests.get(url, headers=headers, params=params or {}, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[WARN] 请求 {path} 失败: {e}")
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

    def fetch_ecosystem(self) -> List[Dict]:
        return self._fetch_list("ecosystem_changes", self._normalize_ecosystem)

    @staticmethod
    def _normalize_fundraising(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or x.get("name") or "Unknown",
            "amount": x.get("amount") or x.get("money") or "N/A",
            "round": x.get("round") or x.get("stage") or "",
            "investors": x.get("investors") or x.get("institution") or "",
            "date": x.get("date") or x.get("time") or "",
        }

    @staticmethod
    def _normalize_token_unlocks(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or "Unknown",
            "token": x.get("token") or x.get("symbol") or "",
            "unlock_date": x.get("unlock_date") or x.get("date") or "",
            "amount": x.get("amount") or "0",
            "percent": x.get("percent") or "",
        }

    @staticmethod
    def _normalize_airdrop(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or "Unknown",
            "status": x.get("status") or x.get("desc") or "",
            "url": x.get("url") or "",
        }

    @staticmethod
    def _normalize_ecosystem(x: Dict) -> Dict:
        return {
            "chain": x.get("chain") or "Unknown",
            "type": x.get("type") or "",
            "desc": x.get("description") or x.get("desc") or "",
        }
