"""產品頁面審核工具 - 檢查 Listing 品質"""
from typing import Dict, Any, List
from .base import load_mock_data, wrap_tool_run, create_langchain_tool
from agent.errors import DataMissingError


def audit_listing_quality(scenario_path: str) -> Dict[str, Any]:
    """
    審核產品頁面品質

    Args:
        scenario_path: 場景路徑

    Returns:
        Dict: 包含特徵的審核結果
    """
    data = load_mock_data(scenario_path, "listing_audit.json")

    # 檢查必要欄位
    required_fields = ["main_image_score", "rating", "reviews"]
    for field in required_fields:
        if field not in data:
            raise DataMissingError("ListingAudit", field)

    # 提取基本指標
    main_image_score = data.get("main_image_score", 0)
    rating = data.get("rating", 0)
    reviews = data.get("reviews", 0)
    a_plus_content = data.get("a_plus_content", False)
    title_keyword_coverage = data.get("title_keyword_coverage", 0)
    bullet_points_count = data.get("bullet_points_count", 0)

    # 計算品質分數
    quality_score = _calculate_quality_score(
        main_image_score, rating, reviews, a_plus_content,
        title_keyword_coverage, bullet_points_count
    )

    # 特徵提取
    features = {
        "main_image_score": main_image_score,
        "rating": rating,
        "reviews": reviews,
        "a_plus": 1 if a_plus_content else 0,
        "title_keyword_coverage": title_keyword_coverage,
        "bullet_points_count": bullet_points_count,
        "quality_score": quality_score
    }

    # 生成建議
    suggestions = _generate_suggestions(features)

    return {
        "data": {
            "主圖評分": f"{main_image_score:.2f}",
            "評分": f"{rating:.1f}",
            "評論數": reviews,
            "A+內容": "有" if a_plus_content else "無",
            "標題關鍵詞覆蓋": f"{title_keyword_coverage:.1%}",
            "品質總分": f"{quality_score:.0f}/100",
            "改善建議": suggestions
        },
        "features": features
    }


def _calculate_quality_score(main_image: float, rating: float, reviews: int,
                           a_plus: bool, title_coverage: float, bullet_count: int) -> float:
    """計算整體品質分數"""
    score = 0.0

    # 主圖評分 (25%)
    score += (main_image * 25)

    # 評分 (20%)
    score += (rating / 5.0 * 20)

    # 評論數量 (15%)
    review_score = min(reviews / 100, 1.0) * 15  # 100個評論為滿分
    score += review_score

    # A+內容 (15%)
    score += (15 if a_plus else 0)

    # 標題關鍵詞覆蓋 (15%)
    score += (title_coverage * 15)

    # 要點數量 (10%)
    bullet_score = min(bullet_count / 5, 1.0) * 10  # 5個要點為滿分
    score += bullet_score

    return min(100.0, score)


def _generate_suggestions(features: Dict[str, Any]) -> List[str]:
    """根據特徵生成改善建議"""
    suggestions = []

    if features["main_image_score"] < 0.7:
        suggestions.append("改善主圖品質和吸引力")

    if features["rating"] < 4.0:
        suggestions.append("提升產品評分，改善客戶滿意度")

    if features["reviews"] < 50:
        suggestions.append("增加產品評論數量")

    if not features["a_plus"]:
        suggestions.append("建立A+內容頁面")

    if features["title_keyword_coverage"] < 0.8:
        suggestions.append("優化標題關鍵詞覆蓋")

    if features["bullet_points_count"] < 5:
        suggestions.append("完善產品要點描述")

    return suggestions


# 建立 LangChain 工具
def create_listing_audit_tool(scenario_path: str):
    """建立產品審核工具"""

    def _run_tool(query: str) -> str:
        result = wrap_tool_run("ListingAudit", audit_listing_quality, scenario_path)
        if result.ok:
            return f"產品頁面審核完成：{result.data}"
        else:
            return f"產品頁面審核失敗：{result.error}"

    return create_langchain_tool(
        name="ListingAudit",
        description="審核產品頁面品質，檢查圖片、評分、內容等影響轉換率的因素",
        func=_run_tool
    )