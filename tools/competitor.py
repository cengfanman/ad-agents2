"""競品分析工具 - 分析市場競爭狀況"""
import time
from typing import Dict, Any
from .base import load_mock_data, wrap_tool_run, create_langchain_tool
from agent.errors import DataMissingError, ToolTimeoutError


def analyze_competitors(scenario_path: str, break_competitor: bool = False) -> Dict[str, Any]:
    """
    分析競品競爭狀況

    Args:
        scenario_path: 場景路徑
        break_competitor: 是否模擬工具超時失敗

    Returns:
        Dict: 包含特徵的競品分析結果

    Raises:
        ToolTimeoutError: 當 break_competitor=True 時
    """
    # 模擬工具失敗
    if break_competitor:
        time.sleep(0.1)  # 模擬一些處理時間
        raise ToolTimeoutError("Competitor", 30)

    data = load_mock_data(scenario_path, "competitor.json")

    # 檢查必要欄位
    required_fields = ["avg_competitor_price", "our_price"]
    for field in required_fields:
        if field not in data:
            raise DataMissingError("Competitor", field)

    # 提取競品資料
    avg_comp_price = data.get("avg_competitor_price", 0)
    our_price = data.get("our_price", 0)
    top_competitor_rating = data.get("top_competitor_rating", 0)
    sponsored_share = data.get("sponsored_share", 0)
    market_saturation = data.get("market_saturation", "medium")
    brand_recognition = data.get("brand_recognition", "low")

    # 計算價格差距
    price_gap = (avg_comp_price - our_price) / our_price if our_price > 0 else 0
    price_competitiveness = _assess_price_competitiveness(price_gap)

    # 計算競爭壓力
    competitive_pressure = _calculate_competitive_pressure(
        sponsored_share, top_competitor_rating, market_saturation, brand_recognition
    )

    # 特徵提取
    features = {
        "comp_price_gap": price_gap,
        "sponsored_share": sponsored_share,
        "top_competitor_rating": top_competitor_rating,
        "competitive_pressure": competitive_pressure,
        "price_competitiveness": price_competitiveness
    }

    return {
        "data": {
            "平均競品價格": f"${avg_comp_price:.2f}",
            "我們的價格": f"${our_price:.2f}",
            "價格差距": f"{price_gap:+.1%}",
            "贊助廣告占比": f"{sponsored_share:.1%}",
            "頂級競品評分": f"{top_competitor_rating:.1f}",
            "市場飽和度": market_saturation,
            "競爭壓力": competitive_pressure,
            "價格競爭力": price_competitiveness
        },
        "features": features
    }


def _assess_price_competitiveness(price_gap: float) -> str:
    """評估價格競爭力"""
    if price_gap > 0.1:
        return "價格優勢"
    elif price_gap > -0.05:
        return "價格平衡"
    elif price_gap > -0.15:
        return "價格劣勢"
    else:
        return "價格嚴重劣勢"


def _calculate_competitive_pressure(sponsored_share: float, top_rating: float,
                                  saturation: str, brand_recognition: str) -> str:
    """計算競爭壓力等級"""
    pressure_score = 0

    # 贊助廣告占比
    if sponsored_share > 0.4:
        pressure_score += 3
    elif sponsored_share > 0.25:
        pressure_score += 2
    else:
        pressure_score += 1

    # 頂級競品評分
    if top_rating > 4.5:
        pressure_score += 3
    elif top_rating > 4.0:
        pressure_score += 2
    else:
        pressure_score += 1

    # 市場飽和度
    saturation_scores = {"high": 3, "medium": 2, "low": 1}
    pressure_score += saturation_scores.get(saturation, 2)

    # 品牌識別度
    brand_scores = {"high": 1, "medium": 2, "low": 3}  # 我們品牌識別度低表示壓力大
    pressure_score += brand_scores.get(brand_recognition, 2)

    # 總分轉換為等級
    if pressure_score >= 9:
        return "高壓力"
    elif pressure_score >= 6:
        return "中等壓力"
    else:
        return "低壓力"


# 建立 LangChain 工具
def create_competitor_tool(scenario_path: str, break_competitor: bool = False):
    """建立競品分析工具"""

    def _run_tool(query: str) -> str:
        result = wrap_tool_run("Competitor", analyze_competitors, scenario_path, break_competitor)
        if result.ok:
            return f"競品分析完成：{result.data}"
        else:
            return f"競品分析失敗：{result.error}"

    return create_langchain_tool(
        name="Competitor",
        description="分析市場競爭狀況，評估價格定位和競爭壓力",
        func=_run_tool
    )