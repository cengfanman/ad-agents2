"""錯誤處理類別"""


class ToolError(Exception):
    """工具執行基礎錯誤"""
    def __init__(self, message: str, tool_name: str = None):
        self.message = message
        self.tool_name = tool_name
        super().__init__(self.message)


class ToolTimeoutError(ToolError):
    """工具執行超時錯誤"""
    def __init__(self, tool_name: str, timeout_seconds: int = 30):
        message = f"工具 '{tool_name}' 執行超時（{timeout_seconds}秒）"
        super().__init__(message, tool_name)
        self.timeout_seconds = timeout_seconds


class DataMissingError(ToolError):
    """資料缺失錯誤"""
    def __init__(self, tool_name: str, missing_field: str):
        message = f"工具 '{tool_name}' 缺少必要資料欄位：{missing_field}"
        super().__init__(message, tool_name)
        self.missing_field = missing_field


class ParseError(ToolError):
    """資料解析錯誤"""
    def __init__(self, tool_name: str, parse_details: str):
        message = f"工具 '{tool_name}' 資料解析失敗：{parse_details}"
        super().__init__(message, tool_name)
        self.parse_details = parse_details


# Fallback 建議映射
FALLBACK_RECOMMENDATIONS = {
    "Competitor": {
        "alternative_tools": ["ListingAudit"],
        "message": "競品分析工具失敗，建議使用產品頁面審核工具檢查競爭力"
    },
    "Inventory": {
        "alternative_tools": ["AdsMetrics"],
        "message": "庫存查詢工具失敗，建議使用廣告指標工具了解投放狀況"
    },
    "ListingAudit": {
        "alternative_tools": ["AdsMetrics", "Competitor"],
        "message": "產品頁面審核失敗，建議使用廣告指標和競品分析工具"
    },
    "AdsMetrics": {
        "alternative_tools": ["Competitor", "ListingAudit"],
        "message": "廣告指標工具失敗，建議使用競品分析和產品審核工具"
    }
}


def get_fallback_recommendation(tool_name: str) -> dict:
    """取得工具失敗時的回退建議"""
    return FALLBACK_RECOMMENDATIONS.get(tool_name, {
        "alternative_tools": [],
        "message": f"工具 '{tool_name}' 失敗，請檢查資料來源或稍後重試"
    })