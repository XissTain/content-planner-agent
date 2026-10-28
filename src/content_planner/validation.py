"""输入及合成数据的边界校验，不依赖模型自律。"""
import math
from datetime import datetime


def parse_time(value):
    if not isinstance(value, str):
        raise ValueError("时间必须是字符串。")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    if parsed.tzinfo is None:
        raise ValueError("时间必须带时区。")
    return parsed


def valid_number(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value >= 0 and (not isinstance(value, float) or math.isfinite(value))


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("version"), str) or not catalog["version"].strip():
        raise ValueError("资料必须有非空 version。")
    assets = catalog.get("assets")
    if not isinstance(assets, list):
        raise ValueError("assets 必须为数组。")
    seen = set()
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("id"), str) or not asset["id"].strip() or asset["id"] in seen:
            raise ValueError("素材 ID 缺失或重复。")
        seen.add(asset["id"])
        if not isinstance(asset.get("title"), str) or not asset["title"].strip():
            raise ValueError("素材缺少 title。")
        for key in ("tags", "facts"):
            if not isinstance(asset.get(key), list) or not asset[key] or any(not isinstance(s, str) or not s.strip() for s in asset[key]):
                raise ValueError("素材必须有非空 tags 和 facts。")
    for key, names in (("script_services", {"premium", "standard", "template"}), ("production_services", {"polished", "simple"})):
        if not isinstance(catalog.get(key), dict) or set(catalog[key]) != names:
            raise ValueError(key + " 必须包含工具声明的全部服务。")
    items = assets + list(catalog["script_services"].values()) + list(catalog["production_services"].values())
    for item in items:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), int) or isinstance(item[k], bool) or item[k] < 0 for k in ("cost", "minutes")):
            raise ValueError("合成成本和分钟数必须是非负整数。")
