import requests
from typing import Dict, List, Union

class RootDataClient:
    def __init__(self, base_url: str, api_key: str, auth_header: str = "x-api-key"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.auth_header = auth_header

    def _get(self, path: str, params: Dict = None) -> Union[Dict, List]:
        """发送 GET 请求，处理 HTTP 错误"""
        if not self.api_key:
            # 打印明显错误，防止静默失败
            print("[ERROR] RootData API Key 未配置！")
            raise RuntimeError("缺少 ROOTDATA_API_KEY")
            
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {self.auth_header: self.api_key}
        
        # 设置超时，防止请求卡死
        r = requests.get(url, headers=headers, params=params or {}, timeout=30)
        r.raise_for_status()  # 如果状态码不是 200，这里会抛出异常
        return r.json()

    def _fetch_list(self, endpoint: str, normalizer_func) -> List[Dict]:
        """通用获取列表的方法，包含容错处理"""
        try:
            data = self._get(endpoint)
            items = []
            
            # 智能解析：兼容直接返回 List 或包含在 data/items 字段中的情况
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get("data") or data.get("items") or []
                
            if not isinstance(items, list):
                print(f"[WARN] {endpoint} 返回的数据格式不是列表，已跳过。")
                return []

            # 过滤掉非字典项，防止解析报错
            return [normalizer_func(x) for x in items if isinstance(x, dict)]

        except Exception as e:
            # 关键：打印错误日志，方便在 GitHub Actions 中排查
            print(f"[WARN] 获取 {endpoint} 失败: {e}")
            return []

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
            "project_name": x.get("project_name") or x.get("project") or x.get("name") or "Unknown",
            "amount": x.get("amount") or x.get("money") or "N/A",
            "round": x.get("round") or x.get("stage") or "Unknown",
            "sector": x.get("sector") or x.get("category") or "",
            "date": x.get("date") or x.get("time") or "",
            "sources": x.get("sources") or x.get("links") or [],
        }

    @staticmethod
    def _normalize_token_unlocks(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or x.get("project") or "Unknown",
            "token": x.get("token") or x.get("symbol") or "",
            "change": x.get("change") or "unlock",
            "unlock_date": x.get("unlock_date") or x.get("date") or "",
            "amount": x.get("amount") or x.get("unlocked_amount") or "0",
            "impact": x.get("impact") or "",
            "source": x.get("source") or x.get("link") or "",
        }

    @staticmethod
    def _normalize_airdrop(x: Dict) -> Dict:
        return {
            "project_name": x.get("project_name") or x.get("project") or "Unknown",
            "signal": x.get("signal") or x.get("desc") or "",
            "task_url": x.get("task_url") or x.get("url") or "",
            "tge_date": x.get("tge_date") or x.get("date") or "",
            "notes": x.get("notes") or "",
        }

    @staticmethod
    def _normalize_ecosystem(x: Dict) -> Dict:
        return {
            "chain": x.get("chain") or x.get("network") or "Unknown",
            "change_type": x.get("change_type") or x.get("type") or "",
            "description": x.get("description") or x.get("desc") or "",
            "metrics": x.get("metrics") or x.get("data") or "",
            "source": x.get("source") or x.get("link") or "",
        }
