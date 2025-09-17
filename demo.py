#!/usr/bin/env python3
"""Amazon Ads 診斷 Agent CLI 介面"""
import os
import sys
import typer
from pathlib import Path
from typing import Optional
from datetime import datetime

# 載入環境變數 (強制覆蓋系統環境變數)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # 強制覆蓋現有環境變數
except ImportError:
    # 如果沒有安裝 python-dotenv，手動讀取 .env
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# 添加專案根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

from agent.loop import run_agent_loop, load_scenario
from reporter.summarizer import generate_summary_report
from rich.console import Console

app = typer.Typer(help="🤖 Amazon Ads 診斷 Agent")
console = Console()


@app.command()
def diagnose(
    scenario: str = typer.Option(..., "--scenario", help="場景檔案路徑 (如 scenarios/scenario_low_impr.json)"),
    mode: str = typer.Option("keyword", "--mode", help="廣告分析模式 (keyword/campaign)"),
    break_competitor: bool = typer.Option(False, "--break-competitor", help="模擬競品工具失敗"),
    generate_report: bool = typer.Option(True, "--report/--no-report", help="是否生成 OpenAI 報告")
):
    """執行廣告診斷分析"""

    try:
        # 載入場景
        console.print(f"📁 載入場景檔案：{scenario}")
        scenario_data = load_scenario(scenario)

        # 執行 Agent 主循環
        console.print("🚀 開始執行診斷...")
        result = run_agent_loop(scenario_data, mode, break_competitor)

        if result["success"]:
            console.print("\n✅ 診斷完成！")
            console.print(f"📊 執行步數：{result['total_steps']}")
            console.print(f"📄 軌跡檔案：{result.get('trace_file', 'N/A')}")

            # 生成報告
            if generate_report:
                console.print("\n📝 生成詳細報告...")

                # 從軌跡中提取真實執行的工具和發現
                tools_executed = []
                tool_findings = {}

                # 讀取軌跡檔案獲取詳細的工具執行情況
                trace_file = result.get('trace_file')
                if trace_file and Path(trace_file).exists():
                    import json
                    with open(trace_file, 'r', encoding='utf-8') as f:
                        trace_data = json.load(f)

                    for step in trace_data.get('steps', []):
                        tool_result = step.get('tool_result', {})
                        if tool_result.get('ok'):
                            tool_name = tool_result.get('tool_name')
                            tools_executed.append(tool_name)
                            tool_findings[tool_name] = tool_result.get('features', {})

                report = generate_summary_report(result["strategy"], tools_executed, tool_findings)

                # 儲存 Markdown 報告到檔案
                report_dir = Path("reports")
                report_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                scenario_name = Path(scenario).stem  # 取得場景檔案名稱
                report_file = report_dir / f"診斷報告_{scenario_name}_{timestamp}.md"

                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(report)

                console.print(f"\n📄 報告已儲存：{report_file}")
                console.print("\n" + "="*60)
                console.print("📋 AI 生成報告")
                console.print("="*60)
                console.print(report)

        else:
            console.print("❌ 診斷失敗")
            return 1

    except FileNotFoundError as e:
        console.print(f"❌ 檔案不存在：{e}")
        return 1
    except Exception as e:
        console.print(f"❌ 執行錯誤：{e}")
        return 1

    return 0


@app.command()
def test():
    """執行所有測試場景"""
    scenarios = [
        "scenarios/scenario_low_impr.json",
        "scenarios/scenario_high_acos.json",
        "scenarios/scenario_high_click_low_conv.json"
    ]

    console.print("🧪 執行所有測試場景...")

    for scenario_path in scenarios:
        console.print(f"\n{'='*50}")
        console.print(f"🎯 測試場景：{scenario_path}")
        console.print('='*50)

        try:
            scenario_data = load_scenario(scenario_path)
            result = run_agent_loop(scenario_data, "keyword", False)

            if result["success"]:
                console.print(f"✅ {scenario_path} - 成功")
            else:
                console.print(f"❌ {scenario_path} - 失敗")

        except Exception as e:
            console.print(f"❌ {scenario_path} - 錯誤：{e}")


@app.command()
def setup():
    """檢查環境設定"""
    console.print("🔧 檢查環境設定...")

    # 檢查 Python 版本
    python_version = sys.version_info
    console.print(f"🐍 Python 版本：{python_version.major}.{python_version.minor}.{python_version.micro}")

    # 檢查必要目錄
    required_dirs = ["mock", "scenarios", "trace", "reports", "agent", "tools", "reporter"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            console.print(f"✅ 目錄存在：{dir_name}")
        else:
            console.print(f"❌ 目錄缺失：{dir_name}")

    # 檢查環境變數
    if os.getenv("OPENAI_API_KEY"):
        console.print("✅ OPENAI_API_KEY 已設定")
    else:
        console.print("⚠️  OPENAI_API_KEY 未設定 (將使用本地報告生成)")

    # 檢查 Mock 資料
    mock_scenarios = ["low_impr", "high_acos", "high_click_low_conv"]
    for scenario in mock_scenarios:
        mock_dir = Path(f"mock/{scenario}")
        if mock_dir.exists():
            files = list(mock_dir.glob("*.json"))
            console.print(f"✅ Mock 資料：{scenario} ({len(files)} 檔案)")
        else:
            console.print(f"❌ Mock 資料缺失：{scenario}")


if __name__ == "__main__":
    app()