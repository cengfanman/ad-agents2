"""O→T→A 主循環邏輯"""
import json
import orjson
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from agent.types import ScenarioInput, AgentContext, ToolResult, ActionStrategy
from agent.policy import initialize_hypotheses, select_next_tool, update_beliefs_from_features, decide_actions, should_terminate
from agent.errors import get_fallback_recommendation
from agent import reasoning

# 工具執行函數映射
from tools.ads_metrics import analyze_ads_metrics
from tools.listing_audit import audit_listing_quality
from tools.competitor import analyze_competitors
from tools.inventory import check_inventory_status


def run_agent_loop(scenario: ScenarioInput, mode: str = "keyword",
                  break_tools: Dict[str, bool] = None) -> Dict[str, Any]:
    """
    執行 Agent 主循環

    Args:
        scenario: 場景輸入
        mode: 廣告分析模式
        break_tools: 工具失敗模擬配置 (Dict[工具名, 是否失敗])

    Returns:
        Dict: 執行結果
    """
    if break_tools is None:
        break_tools = {}
    # 初始化 Agent 上下文
    context = AgentContext(
        scenario=scenario,
        step=0,
        tool_results=[],
        hypotheses=initialize_hypotheses(scenario.goal)
    )

    # 初始化執行軌跡
    trace = {
        "scenario": scenario.dict(),
        "start_time": datetime.now().isoformat(),
        "steps": [],
        "final_strategy": None
    }

    reasoning.console.print(f"\n🚀 開始 Agent 診斷流程 - {scenario.asin}")
    reasoning.console.print(f"目標：{scenario.goal}")

    # 主循環
    while context.step < 5:  # 最多5步
        context.step += 1

        # === OBSERVE 階段 ===
        reasoning.log_observe(
            context.step,
            scenario.dict(),
            context.tool_results
        )

        # === THINK 階段 ===
        reasoning.log_hypotheses(context.hypotheses)

        # 檢查終止條件
        should_end, termination_reason = should_terminate(context)
        if should_end:
            reasoning.console.print(f"\n🎯 {termination_reason}")
            reasoning.console.print("準備生成最終策略...")
            break

        # === ACT 階段 ===
        selected_tool, tool_reasoning = select_next_tool(context)

        if not selected_tool:
            reasoning.console.print("\n⚠️ 沒有更多工具可執行，終止循環")
            break

        # 記錄詳細決策推理
        reasoning.log_decide(selected_tool, tool_reasoning)

        # 執行工具
        tool_result = execute_tool(
            selected_tool,
            scenario.scenario_name or "default",
            mode,
            break_tools
        )

        reasoning.log_tool_result(tool_result)

        # 處理工具失敗
        if not tool_result.ok:
            fallback = get_fallback_recommendation(selected_tool)
            reasoning.log_error(tool_result.error, selected_tool, fallback["message"])

            # 記錄失敗的工具結果
            context.tool_results.append(tool_result)
        else:
            # 成功執行，更新信念
            context.tool_results.append(tool_result)

            if tool_result.features:
                belief_updates = update_beliefs_from_features(
                    context.hypotheses,
                    selected_tool,
                    tool_result.features
                )
                reasoning.log_belief_update(belief_updates)

        # 更新上下文
        context.last_tool = selected_tool
        if tool_result.ok and len(context.tool_results) >= 2:
            # 計算信念增益
            current_max = max(h.belief for h in context.hypotheses)
            previous_max = max(h.previous_belief or h.belief for h in context.hypotheses)
            context.last_gain = current_max - previous_max

        # 記錄步驟到軌跡
        step_trace = {
            "step": context.step,
            "selected_tool": selected_tool,
            "tool_result": tool_result.dict(),
            "hypotheses": [h.dict() for h in context.hypotheses]
        }
        trace["steps"].append(step_trace)

        reasoning.log_step_separator()

    # 生成最終策略
    final_strategy = decide_actions(context)
    reasoning.log_action_plan(final_strategy.dict())

    # 完成軌跡記錄
    trace["final_strategy"] = final_strategy.dict()
    trace["end_time"] = datetime.now().isoformat()
    trace["total_steps"] = context.step

    # 保存軌跡
    save_trace(trace)

    reasoning.log_final_summary(
        context.step,
        final_strategy.primary_hypothesis,
        final_strategy.confidence
    )

    return {
        "success": True,
        "strategy": final_strategy.dict(),
        "total_steps": context.step,
        "trace_file": trace.get("trace_file", "")
    }


def execute_tool(tool_name: str, scenario_path: str, mode: str = "keyword",
                break_tools: Dict[str, bool] = None) -> ToolResult:
    """
    執行指定工具

    Args:
        tool_name: 工具名稱
        scenario_path: 場景路徑
        mode: 模式參數
        break_tools: 工具失敗模擬配置

    Returns:
        ToolResult: 工具執行結果
    """
    if break_tools is None:
        break_tools = {}
    import time
    start_time = time.time()

    try:
        # 檢查是否需要模擬工具失敗
        if break_tools.get(tool_name, False):
            raise Exception(f"模擬 {tool_name} 工具失敗")

        if tool_name == "AdsMetrics":
            result = analyze_ads_metrics(scenario_path, mode)
        elif tool_name == "ListingAudit":
            result = audit_listing_quality(scenario_path)
        elif tool_name == "Competitor":
            # 保持向後兼容性
            break_competitor = break_tools.get("Competitor", False)
            result = analyze_competitors(scenario_path, break_competitor)
        elif tool_name == "Inventory":
            result = check_inventory_status(scenario_path)
        else:
            raise ValueError(f"未知工具：{tool_name}")

        latency_ms = int((time.time() - start_time) * 1000)

        return ToolResult(
            tool_name=tool_name,
            ok=True,
            data=result.get("data", {}),
            features=result.get("features", {}),
            latency_ms=latency_ms
        )

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=tool_name,
            ok=False,
            error=str(e),
            latency_ms=latency_ms
        )


def save_trace(trace: Dict[str, Any]) -> str:
    """
    保存執行軌跡到文件

    Args:
        trace: 軌跡資料

    Returns:
        str: 保存的文件路徑
    """
    # 確保 trace 目錄存在
    trace_dir = Path("trace")
    trace_dir.mkdir(exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trace_{timestamp}.json"
    filepath = trace_dir / filename

    # 保存文件
    with open(filepath, 'wb') as f:
        f.write(orjson.dumps(trace, option=orjson.OPT_INDENT_2))

    trace["trace_file"] = str(filepath)
    return str(filepath)


def load_scenario(scenario_path: str) -> ScenarioInput:
    """
    載入場景文件

    Args:
        scenario_path: 場景文件路徑

    Returns:
        ScenarioInput: 場景資料
    """
    with open(scenario_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return ScenarioInput(**data)