"""OpenAI 報告摘要生成器"""
import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from .templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def generate_summary_report(strategy: Dict[str, Any], tools_executed: List[str]) -> str:
    """
    使用 OpenAI 生成簡潔的報告摘要

    Args:
        strategy: 策略結果
        tools_executed: 執行的工具列表

    Returns:
        str: Markdown 格式的報告
    """
    # 檢查 API Key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _generate_fallback_report(strategy, tools_executed)

    try:
        # 初始化 OpenAI 客戶端
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm = ChatOpenAI(
            model=model,
            temperature=0.3,
            max_tokens=500
        )

        # 準備 prompt 資料
        tools_text = "\n".join([f"• {tool}" for tool in tools_executed])
        actions_text = _format_actions(strategy.get("actions", []))

        user_prompt = USER_PROMPT_TEMPLATE.format(
            primary_hypothesis=strategy.get("primary_hypothesis", "未知"),
            confidence=strategy.get("confidence", 0),
            tools_executed=tools_text,
            actions=actions_text
        )

        # 建立訊息
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt)
        ]

        # 調用 OpenAI
        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        print(f"⚠️  OpenAI 報告生成失敗：{str(e)}")
        return _generate_fallback_report(strategy, tools_executed)


def _format_actions(actions: List[Dict[str, Any]]) -> str:
    """格式化行動建議為文字"""
    if not actions:
        return "無具體行動建議"

    formatted = []
    for i, action in enumerate(actions, 1):
        text = f"{i}. {action.get('description', '')}"
        if action.get('impact'):
            text += f"\n   影響：{action.get('impact')}"
        if action.get('kpi'):
            text += f"\n   KPI：{action.get('kpi')}"
        formatted.append(text)

    return "\n\n".join(formatted)


def _generate_fallback_report(strategy: Dict[str, Any], tools_executed: List[str]) -> str:
    """
    生成本地備援報告（當 OpenAI 不可用時）

    Args:
        strategy: 策略結果
        tools_executed: 執行的工具列表

    Returns:
        str: Markdown 格式的本地報告
    """
    primary = strategy.get("primary_hypothesis", "未知問題")
    confidence = strategy.get("confidence", 0)
    actions = strategy.get("actions", [])

    report = f"""# 📊 Amazon 廣告診斷報告

## 🎯 診斷結論
**{primary}**（置信度：{confidence:.1%}）

## 🚀 建議行動

"""

    # 添加前三個行動建議
    for i, action in enumerate(actions[:3], 1):
        report += f"""### {i}. {action.get('description', '')}
- **預期影響**：{action.get('impact', '提升廣告效果')}
- **風險評估**：{action.get('risk', '需要持續監控')}
- **關鍵指標**：{action.get('kpi', '待確認')}

"""

    report += """## ⏰ 執行時程
- **T+48小時**：檢查初步效果和指標變化
- **T+7天**：評估整體改善幅度並調整策略

## 📋 執行工具
"""

    for tool in tools_executed:
        report += f"- ✅ {tool}\n"

    report += f"""
---
*🤖 本報告由 AI Agent 自動生成 | 生成時間：{_get_current_time()}*
"""

    return report


def _get_current_time() -> str:
    """取得當前時間字串"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# 測試函數
def test_report_generation():
    """測試報告生成功能"""
    test_strategy = {
        "primary_hypothesis": "廣告出價過低",
        "confidence": 0.75,
        "actions": [
            {
                "description": "提高關鍵詞出價 20%",
                "impact": "增加廣告曝光量",
                "risk": "廣告成本上升",
                "kpi": "曝光量提升 30%"
            },
            {
                "description": "優化產品主圖",
                "impact": "提升點擊率",
                "risk": "需要設計投入",
                "kpi": "CTR 提升 15%"
            }
        ]
    }

    test_tools = ["AdsMetrics", "Competitor", "ListingAudit"]

    print("=== 測試報告生成 ===")
    report = generate_summary_report(test_strategy, test_tools)
    print(report)


if __name__ == "__main__":
    test_report_generation()