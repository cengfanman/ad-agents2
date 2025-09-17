"""庫存監控工具 - 檢查庫存狀態"""
from typing import Dict, Any
from .base import load_mock_data, wrap_tool_run, create_langchain_tool
from agent.errors import DataMissingError


def check_inventory_status(scenario_path: str) -> Dict[str, Any]:
    """
    檢查庫存狀態

    Args:
        scenario_path: 場景路徑

    Returns:
        Dict: 包含特徵的庫存分析結果
    """
    data = load_mock_data(scenario_path, "inventory.json")

    # 檢查必要欄位
    required_fields = ["days_of_inventory"]
    for field in required_fields:
        if field not in data:
            raise DataMissingError("Inventory", field)

    # 提取庫存資料
    days_of_inventory = data.get("days_of_inventory", 0)
    restock_eta_days = data.get("restock_eta_days", 0)
    stockout_risk = data.get("stockout_risk", "low")
    units_available = data.get("units_available", 0)
    avg_daily_sales = data.get("avg_daily_sales", 0)

    # 評估庫存健康度
    inventory_health = _assess_inventory_health(days_of_inventory, stockout_risk)

    # 計算廣告建議
    ad_recommendation = _generate_ad_recommendation(days_of_inventory, stockout_risk, restock_eta_days)

    # 特徵提取
    features = {
        "days_of_inventory": days_of_inventory,
        "stockout_risk": stockout_risk,
        "restock_eta_days": restock_eta_days,
        "inventory_health": inventory_health,
        "units_available": units_available,
        "avg_daily_sales": avg_daily_sales
    }

    return {
        "data": {
            "剩餘庫存天數": f"{days_of_inventory}天",
            "現有庫存": f"{units_available}件",
            "日均銷量": f"{avg_daily_sales}件",
            "缺貨風險": _translate_risk_level(stockout_risk),
            "補貨預計": f"{restock_eta_days}天後",
            "庫存健康度": inventory_health,
            "廣告建議": ad_recommendation
        },
        "features": features
    }


def _assess_inventory_health(days_left: int, risk_level: str) -> str:
    """評估庫存健康度"""
    if days_left >= 30:
        return "健康"
    elif days_left >= 14:
        return "注意"
    elif days_left >= 7:
        return "警告"
    else:
        return "危險"


def _generate_ad_recommendation(days_left: int, risk: str, restock_days: int) -> str:
    """生成廣告投放建議"""
    if days_left < 7:
        if restock_days > days_left:
            return "立即降低廣告支出，避免缺貨"
        else:
            return "維持當前廣告支出，準備補貨"
    elif days_left < 14:
        return "適度控制廣告支出，監控庫存"
    elif days_left < 30:
        return "正常廣告投放，注意庫存消耗"
    else:
        return "可積極投放廣告，庫存充足"


def _translate_risk_level(risk: str) -> str:
    """翻譯風險等級為繁體中文"""
    translations = {
        "low": "低風險",
        "medium": "中等風險",
        "high": "高風險",
        "critical": "極高風險"
    }
    return translations.get(risk, "未知風險")


# 建立 LangChain 工具
def create_inventory_tool(scenario_path: str):
    """建立庫存監控工具"""

    def _run_tool(query: str) -> str:
        result = wrap_tool_run("Inventory", check_inventory_status, scenario_path)
        if result.ok:
            return f"庫存檢查完成：{result.data}"
        else:
            return f"庫存檢查失敗：{result.error}"

    return create_langchain_tool(
        name="Inventory",
        description="監控庫存水準和補貨狀況，評估對廣告策略的影響",
        func=_run_tool
    )