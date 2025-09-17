"""統一打分器模組"""
from typing import List, Tuple
import math

# 全域步長參數
ALPHA = 0.2


def score_feature(value: float, rule: dict) -> float:
    """
    根據規則對特徵值進行評分

    Args:
        value: 特徵值
        rule: 評分規則 {type, feature, thr, direction, bad_values}

    Returns:
        float: 評分 (-1.0 ~ 1.0)
    """
    rule_type = rule.get("type")
    thr = rule.get("thr", 0)
    direction = rule.get("direction", "")

    if rule_type == "ratio":
        if direction == "lower_better":
            # 值越低越好，低於閾值給正證據
            if value < thr:
                # 距離閾值越遠，分數越高
                distance = (thr - value) / thr
                return min(1.0, distance)
            else:
                # 高於閾值給輕微反證
                return -0.3

    elif rule_type == "count":
        if direction == "higher_better":
            # 數量越多越好
            if value >= thr:
                return min(1.0, (value - thr) / thr)
            else:
                return -0.2

    elif rule_type == "threshold":
        if direction == "higher_worse":
            # 高於閾值表示問題
            if value > thr:
                return 1.0
            else:
                return -0.2
        elif direction == "lower_worse":
            # 低於閾值表示問題
            if value < thr:
                # 越低問題越嚴重
                distance = (thr - value) / thr
                return min(1.0, distance)
            else:
                return -0.2

    elif rule_type == "gap":
        if direction == "lower_worse":
            # 負值差距表示問題（如價格劣勢）
            if value < thr:
                # 值越低（負得越多），問題越嚴重
                severity = abs(value - thr) / abs(thr) if thr != 0 else 1.0
                return min(1.0, severity)
            else:
                return -0.1

    elif rule_type == "categorical":
        bad_values = rule.get("bad_values", [])
        if str(value) in bad_values:
            return 1.0
        else:
            return -0.2

    # 預設情況
    return 0.0


def update_belief(belief: float, alpha: float, scores: List[float]) -> Tuple[float, float]:
    """
    更新假設的信念值

    Args:
        belief: 當前信念值 (0.0-1.0)
        alpha: 學習率
        scores: 證據評分列表

    Returns:
        Tuple[float, float]: (新信念值, 信念變化量)
    """
    if not scores:
        return belief, 0.0

    # 計算平均證據強度
    avg_score = sum(scores) / len(scores)

    # 記錄舊信念值
    old_belief = belief

    # 使用指數移動平均更新信念
    # 正證據增強信念，負證據削弱信念
    if avg_score > 0:
        # 正證據：向1.0收斂
        belief = belief + alpha * avg_score * (1.0 - belief)
    else:
        # 負證據：向0.0收斂
        belief = belief + alpha * avg_score * belief

    # 確保信念值在有效範圍內
    belief = max(0.0, min(1.0, belief))

    # 計算變化量
    change = belief - old_belief

    return belief, change


def calculate_information_gain(hypothesis_belief: float, tool_used: bool) -> float:
    """
    計算使用工具的資訊增益潛力

    Args:
        hypothesis_belief: 假設的當前信念值
        tool_used: 工具是否已被使用

    Returns:
        float: 資訊增益分數 (0.0-1.0)
    """
    if tool_used:
        return 0.0  # 已使用的工具沒有新增益

    # 信念值接近0.5時，資訊增益最大（最不確定）
    uncertainty = 1.0 - 2 * abs(hypothesis_belief - 0.5)
    return uncertainty


def get_evidence_description(score: float) -> str:
    """
    將評分轉換為繁體中文證據描述

    Args:
        score: 評分值

    Returns:
        str: 證據強度描述
    """
    if score >= 0.8:
        return "🔴 強烈正證據"
    elif score >= 0.4:
        return "🟡 中等正證據"
    elif score >= 0.1:
        return "🟢 輕微正證據"
    elif score > -0.1:
        return "⚪ 中性證據"
    elif score > -0.4:
        return "🔵 輕微反證據"
    else:
        return "🟣 強烈反證據"


# 用於測試的範例規則
EXAMPLE_RULES = {
    "低點擊成本比率": {
        "type": "ratio",
        "feature": "avg_cpc_ratio",
        "thr": 0.6,
        "direction": "lower_better"
    },
    "關鍵詞數量不足": {
        "type": "count",
        "feature": "keyword_count",
        "thr": 3,
        "direction": "higher_better"
    },
    "廣泛匹配浪費": {
        "type": "threshold",
        "feature": "broad_acos",
        "thr": 0.6,
        "direction": "higher_worse"
    },
    "價格劣勢": {
        "type": "gap",
        "feature": "comp_price_gap",
        "thr": -0.05,
        "direction": "lower_worse"
    },
    "庫存風險": {
        "type": "categorical",
        "feature": "stockout_risk",
        "bad_values": ["high", "critical"]
    }
}