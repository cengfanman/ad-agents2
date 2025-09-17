"""Rich 控制台日誌模組"""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from typing import List, Dict, Any
from agent.types import Hypothesis, ToolResult

console = Console(width=100)


def log_observe(step: int, scenario_info: Dict[str, Any], previous_results: List[ToolResult] = None):
    """記錄觀察階段"""
    console.print()
    console.print(Rule(f"🔍 第 {step} 步：觀察階段", style="blue"))

    info_text = f"""目標：{scenario_info.get('goal', 'unknown')}
ASIN：{scenario_info.get('asin', 'unknown')}
觀察期：{scenario_info.get('lookback_days', 0)} 天"""

    if previous_results:
        info_text += f"\n\n已執行工具："
        for result in previous_results:
            status = "✅" if result.ok else "❌"
            info_text += f"\n  • {result.tool_name}：{status}"

    console.print(Panel(info_text, title="🎯 情境摘要", style="cyan"))


def log_hypotheses(hypotheses: List[Hypothesis]):
    """記錄假設狀態"""
    console.print()
    console.print(Rule("🧠 假設與信念狀態", style="magenta"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("假設", style="cyan", width=15)
    table.add_column("信念值", style="yellow", width=8)
    table.add_column("變化", style="green", width=8)
    table.add_column("說明", style="white")

    for hyp in sorted(hypotheses, key=lambda x: x.belief, reverse=True):
        change = ""
        if hyp.previous_belief is not None:
            diff = hyp.belief - hyp.previous_belief
            if diff > 0:
                change = f"+{diff:.2f} ↗️"
            elif diff < 0:
                change = f"{diff:.2f} ↘️"
            else:
                change = "持平"

        table.add_row(
            hyp.name,
            f"{hyp.belief:.2f}",
            change,
            hyp.description[:50] + "..." if len(hyp.description) > 50 else hyp.description
        )

    console.print(table)


def log_decide(selected_tool: str, reasoning: str):
    """記錄決策階段"""
    console.print()
    console.print(Rule("🎯 決策：工具選擇", style="green"))

    decision_text = f"""選擇工具：{selected_tool}

推理過程：
{reasoning}"""

    console.print(Panel(decision_text, title="🤔 推理邏輯", style="green"))


def log_tool_selection_logic(hypotheses: List, tool_mapping: Dict[str, List[str]]):
    """記錄工具選擇的詳細邏輯"""
    console.print()
    console.print(Rule("🔎 工具選擇邏輯", style="magenta"))

    # 顯示假設排序
    sorted_hyps = sorted(hypotheses, key=lambda h: h.belief, reverse=True)
    logic_text = "假設信念值排序：\n"
    for i, hyp in enumerate(sorted_hyps, 1):
        logic_text += f"{i}. {hyp.name}：{hyp.belief:.2f}\n"

    logic_text += "\n工具映射規則：\n"
    for tool, hyp_list in tool_mapping.items():
        logic_text += f"• {tool} → {', '.join(hyp_list)}\n"

    logic_text += f"\n選擇策略：檢查前2個最高信念假設的對應工具"

    console.print(Panel(logic_text, title="🧠 選擇推理", style="magenta"))


def log_tool_result(result: ToolResult):
    """記錄工具執行結果"""
    console.print()
    console.print(Rule("✅ 執行結果", style="blue" if result.ok else "red"))

    status = "成功" if result.ok else "失敗"
    status_emoji = "✅" if result.ok else "❌"

    result_text = f"""{status_emoji} 工具：{result.tool_name}
狀態：{status}
耗時：{result.latency_ms}ms"""

    if result.error:
        result_text += f"\n錯誤：{result.error}"

    if result.features:
        result_text += "\n\n主要發現："
        for key, value in result.features.items():
            result_text += f"\n  • {key}：{value}"

    console.print(Panel(result_text, title="🔧 工具執行", style="blue" if result.ok else "red"))


def log_belief_update(updates: List[Dict[str, Any]]):
    """記錄信念更新"""
    if not updates:
        return

    console.print()
    console.print(Rule("📊 信念更新", style="yellow"))

    update_text = "根據新證據更新假設信念：\n"
    for update in updates:
        hypothesis = update.get('hypothesis', '')
        evidence = update.get('evidence', '')
        score = update.get('score', 0)
        old_belief = update.get('old_belief', 0)
        new_belief = update.get('new_belief', 0)

        change = new_belief - old_belief
        arrow = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"

        update_text += f"\n{hypothesis}：{old_belief:.2f} → {new_belief:.2f} {arrow}"
        update_text += f"\n  證據：{evidence} (評分：{score:+.2f})\n"

    console.print(Panel(update_text, title="🔄 更新詳情", style="yellow"))


def log_detailed_calculation(feature_name: str, feature_value: float, rule: Dict[str, Any], score: float):
    """記錄詳細計算過程"""
    console.print()
    console.print(Rule(f"🧮 特徵評分計算：{feature_name}", style="cyan"))

    calc_text = f"""特徵值：{feature_name} = {feature_value}
規則類型：{rule.get('type', 'unknown')}
閾值：{rule.get('thr', 'N/A')}
方向：{rule.get('direction', 'N/A')}

計算步驟："""

    rule_type = rule.get("type")
    thr = rule.get("thr", 0)
    direction = rule.get("direction", "")

    if rule_type == "ratio" and direction == "lower_better":
        if feature_value < thr:
            distance = (thr - feature_value) / thr
            calc_text += f"""
1. 特徵值 ({feature_value:.3f}) < 閾值 ({thr}) ✓ 符合「越低越好」條件
2. 計算距離：(閾值 - 特徵值) / 閾值
3. 距離 = ({thr} - {feature_value:.3f}) / {thr} = {distance:.3f}
4. 評分 = min(1.0, {distance:.3f}) = {score:.3f}

解釋：值越低於閾值，評分越高。這表示「出價可能太低」的證據越強。"""
        else:
            calc_text += f"""
1. 特徵值 ({feature_value:.3f}) >= 閾值 ({thr}) → 給予輕微反證
2. 評分 = {score:.3f}

解釋：值高於閾值，不支持「出價太低」假設。"""

    elif rule_type == "count" and direction == "higher_better":
        if feature_value >= thr:
            excess = (feature_value - thr) / thr
            calc_text += f"""
1. 特徵值 ({feature_value}) >= 閾值 ({thr}) ✓ 符合「越多越好」條件
2. 計算超出比例：(特徵值 - 閾值) / 閾值
3. 超出比例 = ({feature_value} - {thr}) / {thr} = {excess:.3f}
4. 評分 = min(1.0, {excess:.3f}) = {score:.3f}

解釋：數量越多於閾值，評分越高。"""
        else:
            calc_text += f"""
1. 特徵值 ({feature_value}) < 閾值 ({thr}) → 不足，給予負評分
2. 評分 = {score:.3f}

解釋：數量不足，支持「關鍵詞不足」假設。"""

    elif rule_type == "threshold":
        if direction == "higher_worse" and feature_value > thr:
            calc_text += f"""
1. 特徵值 ({feature_value}) > 閾值 ({thr}) ✓ 觸發「越高越糟」條件
2. 評分 = 1.0

解釋：超過閾值表示問題存在。"""
        elif direction == "lower_worse" and feature_value < thr:
            severity = (thr - feature_value) / thr
            calc_text += f"""
1. 特徵值 ({feature_value}) < 閾值 ({thr}) ✓ 觸發「越低越糟」條件
2. 計算嚴重程度：(閾值 - 特徵值) / 閾值
3. 嚴重程度 = ({thr} - {feature_value}) / {thr} = {severity:.3f}
4. 評分 = min(1.0, {severity:.3f}) = {score:.3f}

解釋：值越低於閾值，問題越嚴重。"""
        else:
            calc_text += f"""
1. 特徵值 ({feature_value}) 未觸發閾值條件
2. 評分 = {score:.3f}

解釋：在正常範圍內。"""

    else:
        calc_text += f"\n計算邏輯：{rule_type} 類型，最終評分 = {score:.3f}"

    console.print(Panel(calc_text, title="🔍 特徵評分計算", style="cyan"))


def log_belief_update_calculation(hypothesis_name: str, old_belief: float, scores: List[float],
                                new_belief: float, alpha: float = 0.2):
    """記錄信念值更新的詳細計算過程"""
    console.print()
    console.print(Rule(f"📊 信念更新計算：{hypothesis_name}", style="yellow"))

    if not scores:
        calc_text = "沒有新證據，信念值保持不變"
    else:
        avg_score = sum(scores) / len(scores)

        calc_text = f"""原始信念值：{old_belief:.3f}
證據評分：{scores}
平均評分：{avg_score:.3f}
學習率(α)：{alpha}

更新公式："""

        if avg_score > 0:
            # 正證據：向1.0收斂
            change = alpha * avg_score * (1.0 - old_belief)
            calc_text += f"""
正證據更新：belief = belief + α × avg_score × (1.0 - belief)
1. 收斂空間：(1.0 - {old_belief:.3f}) = {1.0 - old_belief:.3f}
2. 更新幅度：{alpha} × {avg_score:.3f} × {1.0 - old_belief:.3f} = {change:.3f}
3. 新信念值：{old_belief:.3f} + {change:.3f} = {new_belief:.3f}

解釋：正證據讓信念值向 1.0 收斂，但收斂速度隨信念值接近 1.0 而放緩。"""
        else:
            # 負證據：向0.0收斂
            change = alpha * avg_score * old_belief
            calc_text += f"""
負證據更新：belief = belief + α × avg_score × belief
1. 衰減基數：{old_belief:.3f}
2. 更新幅度：{alpha} × {avg_score:.3f} × {old_belief:.3f} = {change:.3f}
3. 新信念值：{old_belief:.3f} + {change:.3f} = {new_belief:.3f}

解釋：負證據讓信念值向 0.0 收斂，衰減幅度與當前信念值成正比。"""

        # 總結
        change_direction = "上升" if new_belief > old_belief else "下降"
        change_amount = abs(new_belief - old_belief)
        calc_text += f"""

總結：信念值{change_direction} {change_amount:.3f}，最終為 {new_belief:.3f}"""

    console.print(Panel(calc_text, title="🔢 信念更新公式", style="yellow"))


def log_action_plan(strategy: Dict[str, Any]):
    """記錄最終行動計劃"""
    console.print()
    console.print(Rule("🚀 最終行動計劃", style="bold green"))

    plan_text = f"""主要假設：{strategy.get('primary_hypothesis', 'unknown')}
信心水準：{strategy.get('confidence', 0):.1%}

建議行動："""

    actions = strategy.get('actions', [])
    for i, action in enumerate(actions, 1):
        plan_text += f"\n{i}. {action.get('description', '')}"
        if action.get('impact'):
            plan_text += f"\n   預期影響：{action.get('impact')}"

    reasoning = strategy.get('reasoning', '')
    if reasoning:
        plan_text += f"\n\n推理依據：\n{reasoning}"

    console.print(Panel(plan_text, title="📋 執行建議", style="bold green"))


def log_error(error_msg: str, tool_name: str = None, fallback_msg: str = None):
    """記錄錯誤和回退"""
    console.print()
    console.print(Rule("⚠️ 錯誤處理", style="red"))

    error_text = f"錯誤：{error_msg}"
    if tool_name:
        error_text = f"工具 '{tool_name}' " + error_text

    if fallback_msg:
        error_text += f"\n\n回退策略：{fallback_msg}"

    console.print(Panel(error_text, title="🔧 錯誤與回退", style="red"))


def log_step_separator():
    """步驟分隔線"""
    console.print("\n" + "="*80 + "\n")


def log_final_summary(total_steps: int, primary_hypothesis: str, confidence: float):
    """記錄最終總結"""
    console.print()
    console.print(Rule("🎉 診斷完成", style="bold blue"))

    summary_text = f"""總執行步數：{total_steps}
主要結論：{primary_hypothesis}
置信度：{confidence:.1%}

診斷流程已完成，請查看上方的行動建議。"""

    console.print(Panel(summary_text, title="📊 執行摘要", style="bold blue"))