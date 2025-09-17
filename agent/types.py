"""資料類型定義模組"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum


class GoalType(str, Enum):
    """目標類型"""
    INCREASE_IMPRESSIONS = "increase_impressions"
    REDUCE_ACOS = "reduce_acos"
    IMPROVE_CONVERSION = "improve_conversion"


class ScenarioInput(BaseModel):
    """場景輸入資料結構"""
    asin: str
    goal: GoalType
    lookback_days: int
    notes: Optional[str] = None
    scenario_name: Optional[str] = None


class ToolResult(BaseModel):
    """工具執行結果"""
    tool_name: str
    ok: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    latency_ms: int
    features: Optional[Dict[str, Any]] = None


class Hypothesis(BaseModel):
    """假設資料結構"""
    id: str  # H1, H2, H3, H4, H5, H6
    name: str
    description: str
    belief: float  # 0.0-1.0
    previous_belief: Optional[float] = None


class ScoringRule(BaseModel):
    """評分規則"""
    type: str  # ratio, count, threshold, gap, categorical
    feature: str
    thr: Optional[float] = None
    direction: Optional[str] = None  # lower_better, higher_better, lower_worse, higher_worse
    bad_values: Optional[List[str]] = None  # for categorical


class AgentContext(BaseModel):
    """Agent 上下文"""
    scenario: ScenarioInput
    step: int
    tool_results: List[ToolResult]
    hypotheses: List[Hypothesis]
    last_tool: Optional[str] = None
    last_gain: float = 0.0


class ActionStrategy(BaseModel):
    """行動策略"""
    primary_hypothesis: str
    confidence: float
    actions: List[Dict[str, Any]]
    reasoning: str