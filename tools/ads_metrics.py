"""廣告指標工具 - 分析關鍵詞和廣告表現"""
from typing import Dict, Any
from .base import load_mock_data, wrap_tool_run, create_langchain_tool
from agent.errors import DataMissingError


def analyze_ads_metrics(scenario_path: str, mode: str = "keyword") -> Dict[str, Any]:
    """
    分析廣告指標資料
    
    Args:
        scenario_path: 場景路徑
        mode: 分析模式 ("keyword" 或 "campaign")
        
    Returns:
        Dict: 包含特徵的分析結果
    """
    if mode == "keyword":
        data = load_mock_data(scenario_path, "ads_keywords.json")
        return _analyze_keyword_data(data)
    else:
        data = load_mock_data(scenario_path, "ads_campaign.json")
        return _analyze_campaign_data(data)


def _analyze_keyword_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析關鍵詞資料"""
    keywords = data.get("keywords", [])
    category_avg_cpc = data.get("category_avg_cpc", 1.0)
    
    if not keywords:
        raise DataMissingError("AdsMetrics", "keywords")
    
    # 計算指標
    total_impressions = sum(kw.get("impressions", 0) for kw in keywords)
    total_clicks = sum(kw.get("clicks", 0) for kw in keywords)
    total_spend = sum(kw.get("spend", 0) for kw in keywords)
    total_orders = sum(kw.get("orders", 0) for kw in keywords)
    total_sales = sum(kw.get("sales", 0) for kw in keywords)
    
    # 計算平均指標
    avg_cpc = total_spend / total_clicks if total_clicks > 0 else 0
    overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
    overall_acos = total_spend / total_sales if total_sales > 0 else 0
    
    # 分析廣泛匹配關鍵詞
    broad_keywords = [kw for kw in keywords if kw.get("match_type") == "broad"]
    broad_spend = sum(kw.get("spend", 0) for kw in broad_keywords)
    broad_sales = sum(kw.get("sales", 0) for kw in broad_keywords)
    broad_acos = broad_spend / broad_sales if broad_sales > 0 else 0
    
    # 特徵提取
    features = {
        "avg_cpc_ratio": avg_cpc / category_avg_cpc if category_avg_cpc > 0 else 1.0,
        "keyword_count": len(keywords),
        "broad_acos": broad_acos,
        "overall_ctr": overall_ctr,
        "overall_acos": overall_acos,
        "total_impressions": total_impressions,
        "total_clicks": total_clicks
    }
    
    return {
        "data": {
            "總曝光次數": total_impressions,
            "總點擊次數": total_clicks,
            "整體點擊率": f"{overall_ctr:.3f}",
            "整體ACOS": f"{overall_acos:.2f}",
            "關鍵詞數量": len(keywords)
        },
        "features": features
    }


def _analyze_campaign_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """分析廣告活動資料"""
    campaigns = data.get("campaigns", [])
    
    if not campaigns:
        raise DataMissingError("AdsMetrics", "campaigns")
    
    # 計算活動層級指標
    total_spend = sum(camp.get("spend", 0) for camp in campaigns)
    total_sales = sum(camp.get("sales", 0) for camp in campaigns)
    active_campaigns = sum(1 for camp in campaigns if camp.get("status") == "enabled")
    
    acos = total_spend / total_sales if total_sales > 0 else 0
    
    features = {
        "campaign_count": len(campaigns),
        "active_campaign_count": active_campaigns,
        "campaign_acos": acos,
        "avg_campaign_spend": total_spend / len(campaigns) if campaigns else 0
    }
    
    return {
        "data": {
            "活動總數": len(campaigns),
            "啟用活動數": active_campaigns,
            "活動ACOS": f"{acos:.2f}",
            "總支出": f"${total_spend:.2f}"
        },
        "features": features
    }


# 建立 LangChain 工具
def create_ads_metrics_tool(scenario_path: str, mode: str = "keyword"):
    """建立廣告指標工具"""
    
    def _run_tool(query: str) -> str:
        result = wrap_tool_run("AdsMetrics", analyze_ads_metrics, scenario_path, mode)
        if result.ok:
            return f"廣告指標分析完成：{result.data}"
        else:
            return f"廣告指標分析失敗：{result.error}"
    
    return create_langchain_tool(
        name="AdsMetrics",
        description="分析廣告關鍵詞和活動表現，提取CPR、ACOS、點擊率等指標",
        func=_run_tool
    )