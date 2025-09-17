"""工具基礎類別 - LangChain Tool 包裝"""
import time
import json
from pathlib import Path
from typing import Callable, Any, Dict
from langchain.tools import Tool
from agent.types import ToolResult
from agent.errors import ToolError, ToolTimeoutError, DataMissingError, ParseError


def wrap_tool_run(tool_name: str, func: Callable, *args, **kwargs) -> ToolResult:
    """
    包裝工具執行，統一處理計時和錯誤

    Args:
        tool_name: 工具名稱
        func: 要執行的函數
        *args, **kwargs: 函數參數

    Returns:
        ToolResult: 統一的工具執行結果
    """
    start_time = time.time()

    try:
        # 執行工具函數
        result = func(*args, **kwargs)

        # 計算耗時
        latency_ms = int((time.time() - start_time) * 1000)

        # 如果結果是字典且包含 features，直接使用
        if isinstance(result, dict) and 'features' in result:
            return ToolResult(
                tool_name=tool_name,
                ok=True,
                data=result.get('data', {}),
                features=result['features'],
                latency_ms=latency_ms
            )

        # 否則將整個結果作為 data
        return ToolResult(
            tool_name=tool_name,
            ok=True,
            data=result if isinstance(result, dict) else {"result": result},
            features=result if isinstance(result, dict) else {},
            latency_ms=latency_ms
        )

    except ToolError as e:
        # 工具特定錯誤
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=tool_name,
            ok=False,
            error=str(e),
            latency_ms=latency_ms
        )

    except FileNotFoundError as e:
        # 檔案不存在錯誤
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=tool_name,
            ok=False,
            error=f"找不到資料檔案：{str(e)}",
            latency_ms=latency_ms
        )

    except json.JSONDecodeError as e:
        # JSON 解析錯誤
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=tool_name,
            ok=False,
            error=f"資料格式錯誤：{str(e)}",
            latency_ms=latency_ms
        )

    except Exception as e:
        # 其他未預期錯誤
        latency_ms = int((time.time() - start_time) * 1000)
        return ToolResult(
            tool_name=tool_name,
            ok=False,
            error=f"工具執行失敗：{str(e)}",
            latency_ms=latency_ms
        )


def load_mock_data(scenario_path: str, filename: str) -> Dict[str, Any]:
    """
    從指定場景目錄載入 mock 資料

    Args:
        scenario_path: 場景路徑 (如 "low_impr")
        filename: 檔案名稱 (如 "ads_keywords.json")

    Returns:
        Dict[str, Any]: 載入的資料

    Raises:
        FileNotFoundError: 檔案不存在
        ParseError: JSON 解析失敗
    """
    file_path = Path(f"mock/{scenario_path}/{filename}")

    if not file_path.exists():
        raise FileNotFoundError(f"Mock 資料檔案不存在：{file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise ParseError("MockDataLoader", f"JSON 解析失敗：{str(e)}")


def create_langchain_tool(name: str, description: str, func: Callable) -> Tool:
    """
    建立 LangChain Tool 實例

    Args:
        name: 工具名稱
        description: 工具描述
        func: 工具函數

    Returns:
        Tool: LangChain Tool 實例
    """
    return Tool.from_function(
        name=name,
        description=description,
        func=func,
        return_direct=True
    )