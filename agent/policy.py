"""策略規則與工具選擇模組"""
from typing import List, Dict, Any, Optional, Tuple
from agent.types import Hypothesis, AgentContext, GoalType, ActionStrategy
from agent.scoring import score_feature, update_belief, calculate_information_gain, ALPHA


# 假設定義 - H1~H6
HYPOTHESIS_DEFINITIONS = {
    "H1": {
        "name": "出價太低",
        "description": "廣告出價金額太低，無法贏得競爭性關鍵詞"
    },
    "H2": {
        "name": "關鍵詞不足",
        "description": "目標關鍵詞數量不足，限制了廣告覆蓋範圍"
    },
    "H3": {
        "name": "競品壓制",
        "description": "強烈的競爭對手壓制，限制廣告表現"
    },
    "H4": {
        "name": "Listing 品質",
        "description": "產品頁面品質影響轉換率和廣告效果"
    },
    "H5": {
        "name": "廣泛匹配浪費",
        "description": "廣泛匹配關鍵詞產生不相關流量，浪費廣告支出"
    },
    "H6": {
        "name": "庫存不足",
        "description": "庫存水準影響廣告投放策略和積極性"
    }
}

# 工具與假設的映射規則
RULES = {
    "AdsMetrics": {
        "H1": [  # 出價太低
            {"type": "ratio", "feature": "avg_cpc_ratio", "thr": 0.6, "direction": "lower_better"}
        ],
        "H2": [  # 關鍵詞不足
            {"type": "count", "feature": "keyword_count", "thr": 5, "direction": "higher_better"}
        ],
        "H5": [  # 廣泛匹配浪費
            {"type": "threshold", "feature": "broad_acos", "thr": 0.6, "direction": "higher_worse"}
        ]
    },
    "ListingAudit": {
        "H4": [  # Listing 品質
            {"type": "threshold", "feature": "main_image_score", "thr": 0.6, "direction": "lower_worse"},
            {"type": "threshold", "feature": "rating", "thr": 4.0, "direction": "lower_worse"},
            {"type": "count", "feature": "reviews", "thr": 50, "direction": "higher_better"}
        ]
    },
    "Competitor": {
        "H3": [  # 競品壓制
            {"type": "threshold", "feature": "sponsored_share", "thr": 0.35, "direction": "higher_worse"},
            {"type": "gap", "feature": "comp_price_gap", "thr": -0.05, "direction": "lower_worse"}
        ]
    },
    "Inventory": {
        "H6": [  # 庫存不足
            {"type": "threshold", "feature": "days_of_inventory", "thr": 14, "direction": "lower_worse"},
            {"type": "categorical", "feature": "stockout_risk", "bad_values": ["high", "critical"]}
        ]
    }
}


def initialize_hypotheses(goal: GoalType) -> List[Hypothesis]:
    """
    根據目標初始化假設信念值

    Args:
        goal: 診斷目標

    Returns:
        List[Hypothesis]: 初始化的假設列表
    """
    hypotheses = []
    base_belief = 0.30  # 基礎信念值

    for hyp_id, hyp_info in HYPOTHESIS_DEFINITIONS.items():
        belief = base_belief

        # 根據目標調整初始信念
        if goal == GoalType.INCREASE_IMPRESSIONS:
            if hyp_id in ["H1", "H2"]:  # 出價太低、關鍵詞不足
                belief += 0.05
        elif goal == GoalType.REDUCE_ACOS:
            if hyp_id == "H5":  # 廣泛匹配浪費
                belief += 0.05
        elif goal == GoalType.IMPROVE_CONVERSION:
            if hyp_id == "H4":  # Listing 品質
                belief += 0.05

        hypothesis = Hypothesis(
            id=hyp_id,
            name=hyp_info["name"],
            description=hyp_info["description"],
            belief=belief
        )
        hypotheses.append(hypothesis)

    return hypotheses


def select_next_tool(context: AgentContext) -> Optional[str]:
    """
    選擇下一個要執行的工具

    Args:
        context: Agent 上下文

    Returns:
        Optional[str]: 選擇的工具名稱，None 表示無工具可選
    """
    # 獲取已執行的工具
    executed_tools = {result.tool_name for result in context.tool_results if result.ok}

    # 按信念值排序假設
    sorted_hypotheses = sorted(context.hypotheses, key=lambda h: h.belief, reverse=True)

    # 選擇工具的優先級策略
    for hypothesis in sorted_hypotheses[:2]:  # 只考慮前兩個最高信念的假設
        # 找出該假設對應的工具
        for tool_name, tool_rules in RULES.items():
            if hypothesis.id in tool_rules and tool_name not in executed_tools:
                # 檢查是否應該避免重複使用同一工具
                if (context.last_tool == tool_name and
                    context.last_gain < 0.05 and
                    len(executed_tools) > 0):
                    continue
                return tool_name

    # 如果沒有優先工具，選擇任何未執行的工具
    all_tools = set(RULES.keys())
    remaining_tools = all_tools - executed_tools
    return next(iter(remaining_tools)) if remaining_tools else None


def update_beliefs_from_features(hypotheses: List[Hypothesis], tool_name: str,
                                features: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根據工具返回的特徵更新假設信念

    Args:
        hypotheses: 假設列表
        tool_name: 執行的工具名稱
        features: 工具返回的特徵

    Returns:
        List[Dict]: 更新詳情列表
    """
    updates = []

    if tool_name not in RULES:
        return updates

    tool_rules = RULES[tool_name]

    for hypothesis in hypotheses:
        if hypothesis.id not in tool_rules:
            continue

        # 保存舊信念值
        hypothesis.previous_belief = hypothesis.belief

        # 計算該假設的所有證據分數
        scores = []
        evidence_descriptions = []

        for rule in tool_rules[hypothesis.id]:
            feature_name = rule["feature"]
            if feature_name in features:
                feature_value = features[feature_name]
                score = score_feature(feature_value, rule)
                scores.append(score)

                # 記錄證據描述
                evidence_descriptions.append(f"{feature_name}={feature_value}(分數:{score:+.2f})")

        if scores:
            # 更新信念
            new_belief, change = update_belief(hypothesis.belief, ALPHA, scores)
            hypothesis.belief = new_belief

            # 記錄更新詳情
            update_info = {
                "hypothesis": hypothesis.name,
                "evidence": "; ".join(evidence_descriptions),
                "score": sum(scores) / len(scores),
                "old_belief": hypothesis.previous_belief,
                "new_belief": hypothesis.belief,
                "change": change
            }
            updates.append(update_info)

    return updates


def decide_actions(context: AgentContext) -> ActionStrategy:
    """
    根據當前信念狀態決定最終行動策略

    Args:
        context: Agent 上下文

    Returns:
        ActionStrategy: 行動策略
    """
    # 找到信念值最高的假設
    top_hypothesis = max(context.hypotheses, key=lambda h: h.belief)

    # 根據主要假設生成具體行動
    actions = _generate_actions_for_hypothesis(top_hypothesis, context)

    # 生成推理說明
    reasoning = f"""基於 {len(context.tool_results)} 個工具的分析結果，
主要問題診斷為「{top_hypothesis.name}」（信心度：{top_hypothesis.belief:.1%}）。

分析過程：
"""

    for i, result in enumerate(context.tool_results, 1):
        status = "✅" if result.ok else "❌"
        reasoning += f"\n{i}. {result.tool_name}：{status}"
        if result.ok and result.features:
            key_features = list(result.features.keys())[:3]  # 顯示前3個特徵
            reasoning += f" - 關鍵指標：{', '.join(key_features)}"

    return ActionStrategy(
        primary_hypothesis=top_hypothesis.name,
        confidence=top_hypothesis.belief,
        actions=actions,
        reasoning=reasoning.strip()
    )


def _generate_actions_for_hypothesis(hypothesis: Hypothesis, context: AgentContext) -> List[Dict[str, Any]]:
    """根據假設生成具體行動建議"""
    actions = []

    if hypothesis.id == "H1":  # 出價太低
        actions.extend([
            {
                "description": "提高關鍵詞出價 15-25%",
                "impact": "增加廣告曝光和點擊",
                "risk": "廣告成本上升",
                "kpi": "曝光量增加 20-40%"
            },
            {
                "description": "關注高轉換關鍵詞的出價",
                "impact": "提升整體投資回報率",
                "risk": "部分關鍵詞成本過高",
                "kpi": "ACOS 下降 5-15%"
            }
        ])

    elif hypothesis.id == "H2":  # 關鍵詞不足
        actions.extend([
            {
                "description": "擴展目標關鍵詞清單",
                "impact": "增加廣告覆蓋面",
                "risk": "可能帶來不相關流量",
                "kpi": "關鍵詞數量增加至 15-20 個"
            },
            {
                "description": "使用自動廣告挖掘新關鍵詞",
                "impact": "發現潛在高價值關鍵詞",
                "risk": "初期可能產生浪費",
                "kpi": "新增 5-10 個有效關鍵詞"
            }
        ])

    elif hypothesis.id == "H3":  # 競品壓制
        actions.extend([
            {
                "description": "調整價格策略提升競爭力",
                "impact": "改善廣告競爭地位",
                "risk": "利潤率下降",
                "kpi": "廣告位置排名提升"
            },
            {
                "description": "專注長尾關鍵詞避開競爭",
                "impact": "降低競爭壓力",
                "risk": "流量可能較少",
                "kpi": "長尾詞轉換率提升"
            }
        ])

    elif hypothesis.id == "H4":  # Listing 品質
        actions.extend([
            {
                "description": "優化主圖和產品圖片",
                "impact": "提升點擊率和轉換率",
                "risk": "需要時間和設計成本",
                "kpi": "轉換率提升 10-30%"
            },
            {
                "description": "改善產品標題和要點",
                "impact": "提高搜索相關性",
                "risk": "可能影響現有排名",
                "kpi": "自然搜索流量增加"
            },
            {
                "description": "建立或優化 A+ 內容",
                "impact": "增強產品吸引力",
                "risk": "需要額外製作時間",
                "kpi": "頁面停留時間增加"
            }
        ])

    elif hypothesis.id == "H5":  # 廣泛匹配浪費
        actions.extend([
            {
                "description": "添加否定關鍵詞過濾無關流量",
                "impact": "降低廣告浪費",
                "risk": "可能過度過濾有效流量",
                "kpi": "ACOS 下降 10-20%"
            },
            {
                "description": "將廣泛匹配改為詞組或精確匹配",
                "impact": "提高流量精準度",
                "risk": "總曝光量下降",
                "kpi": "轉換率提升 15-25%"
            }
        ])

    elif hypothesis.id == "H6":  # 庫存不足
        actions.extend([
            {
                "description": "立即安排緊急補貨",
                "impact": "避免缺貨影響銷售",
                "risk": "庫存成本增加",
                "kpi": "庫存天數恢復至 30 天以上"
            },
            {
                "description": "暫時降低廣告支出避免缺貨",
                "impact": "確保有庫存滿足需求",
                "risk": "短期銷量下降",
                "kpi": "庫存週轉率穩定"
            }
        ])

    return actions[:3]  # 最多返回3個行動建議


def should_terminate(context: AgentContext) -> bool:
    """
    判斷是否應該終止診斷

    Args:
        context: Agent 上下文

    Returns:
        bool: 是否應該終止
    """
    # 強制要求至少執行3步
    if context.step < 3:
        return False

    # 獲取最高信念值
    max_belief = max(h.belief for h in context.hypotheses)

    # 高信心終止（≥ 0.8）
    if max_belief >= 0.8:
        return True

    # 中等信心 + 工具完成終止（≥ 0.7）
    if max_belief >= 0.7:
        # 檢查主要假設的工具是否都已執行
        top_hypothesis = max(context.hypotheses, key=lambda h: h.belief)
        executed_tools = {result.tool_name for result in context.tool_results if result.ok}

        required_tools = set()
        for tool_name, tool_rules in RULES.items():
            if top_hypothesis.id in tool_rules:
                required_tools.add(tool_name)

        if required_tools.issubset(executed_tools):
            return True

    # 達到最大步數限制
    if context.step >= 5:
        return True

    return False