# Amazon Ads 診斷 Agent (重構版本)

## 📋 專案概述

基於 LangChain 重構的 Amazon 廣告診斷 Agent，解決了原版本的複雜性問題：

- ✅ 使用統一打分器取代硬編碼的工具權重
- ✅ 生成簡潔可讀的繁體中文報告
- ✅ 採用 LangChain 框架提高可維護性
- ✅ 透明的推理過程與決策記錄

## 🤝 改進重點

相較於原版本的主要改進：

1. **解決工具權重管理複雜性** - 統一打分器取代硬編碼權重
2. **報告生成更簡潔易讀** - 專注核心問題與建議
3. **使用成熟框架 LangChain** - 提高代碼可維護性
4. **統一打分器避免過度工程化** - 簡化評分邏輯
5. **透明的繁中推理過程** - 完整記錄決策過程

## 🏗️ 架構設計原則

### Agent vs Workflow
- **動態決策**而非固定流程
- Agent 根據數據特徵動態選擇診斷工具
- 避免硬編碼的工作流程

### 統一打分器
- 避免過度工程化，統一特徵評分邏輯
- 使用 ALPHA=0.2 的調和平均數
- 所有工具共用同一套評分標準

### 透明推理
- Rich 控制台顯示完整決策過程
- 繁體中文推理日誌
- 完整的 trace 記錄保存

## 🔧 核心模組

```
agent/
├── types.py      # 資料類型定義 (Pydantic)
├── scoring.py    # 統一打分器 (ALPHA=0.2)
├── policy.py     # 假設管理和工具選擇策略
├── loop.py       # O→T→A 主循環 (≥3輪)
└── reasoning.py  # 繁中 Rich 日誌

tools/
├── ads_metrics.py    # 廣告數據分析
├── listing_audit.py  # Listing 品質檢查
├── competitor.py     # 競品分析
└── inventory.py      # 庫存檢查

reporter/
├── templates.py   # 報告模板
└── summarizer.py  # OpenAI 報告生成
```

## 💡 假設系統

Agent 基於以下六個核心假設進行診斷：

- **H1: 出價太低** - 檢查 CPC 競爭力
- **H2: 關鍵詞不足** - 分析關鍵詞覆蓋度
- **H3: 競品壓制** - 評估競爭對手影響
- **H4: Listing 品質** - 檢查產品頁面優化
- **H5: 廣泛匹配浪費** - 分析匹配類型效率
- **H6: 庫存不足** - 檢查庫存可用性

## 🚀 快速開始

### 1. 環境設置

```bash
# 複製環境變數設定檔
cp .env.example .env

# 編輯 .env 填入 OpenAI API Key
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 2. 安裝依賴

```bash
pip install -r requirements.txt
```

### 3. 檢查環境

```bash
python demo.py setup
```

**輸出示例：**
```
🔧 檢查環境設定...
🐍 Python 版本：3.10.10
✅ 目錄存在：mock
✅ 目錄存在：scenarios
✅ 目錄存在：trace
✅ 目錄存在：agent
✅ 目錄存在：tools
✅ 目錄存在：reporter
✅ OPENAI_API_KEY 已設定
✅ Mock 資料：low_impr (4 檔案)
✅ Mock 資料：high_acos (4 檔案)
✅ Mock 資料：high_click_low_conv (4 檔案)
```

### 4. 執行診斷

#### 查看所有命令

```bash
python demo.py --help
```

**輸出：**
```
 🤖 Amazon Ads 診斷 Agent

╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ diagnose   執行廣告診斷分析                                                  │
│ test       執行所有測試場景                                                  │
│ setup      檢查環境設定                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### 查看診斷選項

```bash
python demo.py diagnose --help
```

**輸出：**
```
 執行廣告診斷分析

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --scenario     TEXT  場景檔案路徑 (如 scenarios/scenario_low_impr.json)    │
│    --mode         TEXT  廣告分析模式 (keyword/campaign) [default: keyword]   │
│    --break-competitor   模擬競品工具失敗                                      │
│    --report/--no-report 是否生成 OpenAI 報告 [default: report]              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

#### 執行單一場景診斷

```bash
# 低曝光診斷場景（不生成報告，更快執行）
python demo.py diagnose --scenario scenarios/scenario_low_impr.json --no-report

# 高點擊低轉換場景
python demo.py diagnose --scenario scenarios/scenario_high_click_low_conv.json

# 高 ACoS 場景（模擬競品工具失敗）
python demo.py diagnose --scenario scenarios/scenario_high_acos.json --break-competitor
```

#### 執行所有測試場景

```bash
python demo.py test
```

**診斷輸出示例：**
```
🚀 開始 Agent 診斷流程 - B0MOCK001
目標：increase_impressions

─────────────────────────────────────── 🔍 第 1 步：觀察階段 ───────────────────────────────────────
╭────────────────────────────────────────── 🎯 情境摘要 ───────────────────────────────────────────╮
│ 目標：increase_impressions                                                                       │
│ ASIN：B0MOCK001                                                                                  │
│ 觀察期：7 天                                                                                     │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

──────────────────────────────────────── 🧠 假設與信念狀態 ─────────────────────────────────────────
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 假設            ┃ 信念值   ┃ 變化     ┃ 說明                                       ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 出價太低        │ 0.35     │          │ 廣告出價金額太低，無法贏得競爭性關鍵詞     │
│ 關鍵詞不足      │ 0.35     │          │ 目標關鍵詞數量不足，限制了廣告覆蓋範圍     │
│ 競品壓制        │ 0.30     │          │ 強烈的競爭對手壓制，限制廣告表現           │
│ Listing 品質    │ 0.30     │          │ 產品頁面品質影響轉換率和廣告效果           │
│ 廣泛匹配浪費    │ 0.30     │          │ 廣泛匹配關鍵詞產生不相關流量，浪費廣告支出 │
│ 庫存不足        │ 0.30     │          │ 庫存水準影響廣告投放策略和積極性           │
└─────────────────┴──────────┴──────────┴────────────────────────────────────────────┘

──────────────────────────────────────── 🎯 決策：工具選擇 ─────────────────────────────────────────
╭────────────────────────────────────────── 🤔 推理邏輯 ───────────────────────────────────────────╮
│ 選擇工具：AdsMetrics                                                                             │
│                                                                                                  │
│ 推理過程：                                                                                       │
│ 選擇工具 AdsMetrics 來驗證當前最高信念假設                                                       │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

─────────────────────────────────────────── ✅ 執行結果 ────────────────────────────────────────────
╭────────────────────────────────────────── 🔧 工具執行 ───────────────────────────────────────────╮
│ ✅ 工具：AdsMetrics                                                                              │
│ 狀態：成功                                                                                       │
│ 耗時：0ms                                                                                        │
│                                                                                                  │
│ 主要發現：                                                                                       │
│   • avg_cpc_ratio：0.339                                                                         │
│   • keyword_count：2                                                                             │
│   • broad_acos：0.123                                                                            │
│   • overall_ctr：0.04                                                                            │
│   • overall_acos：0.219                                                                          │
│   • total_impressions：200                                                                       │
│   • total_clicks：8                                                                              │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 📊 診斷場景

專案提供三個預設診斷場景：

### 1. 低曝光場景 (scenario_low_impr.json)
- 曝光量不足的廣告活動
- 重點檢查出價和關鍵詞策略

### 2. 高點擊低轉換 (scenario_high_click_low_conv.json)
- 點擊率高但轉換率低
- 重點檢查 Listing 品質和競品

### 3. 高 ACoS 場景 (scenario_high_acos.json)
- 廣告成本過高
- 全面診斷所有可能因素

## 📁 專案結構

```
ads-agent2/
├── agent/          # Agent 核心邏輯
├── tools/          # 診斷工具
├── reporter/       # 報告生成
├── scenarios/      # 測試場景
├── mock/          # 模擬數據
├── trace/         # 執行記錄
├── demo.py        # CLI 入口
└── requirements.txt
```

## 🔍 技術特色

### O→T→A 循環
- **Observe**: 觀察數據特徵
- **Think**: 推理假設驗證
- **Act**: 選擇診斷工具

### LangChain 工具整合
- 所有診斷工具基於 LangChain Tool 包裝
- 統一的工具執行介面和錯誤處理
- 支援工具鏈組合和擴展

### 動態工具選擇
- 根據數據特徵動態評分
- 優先選擇高分工具
- 避免冗余分析

### Rich 控制台輸出
- 彩色繁體中文日誌
- 結構化推理過程
- 即時進度顯示

## 🛠️ LangChain 整合

### 工具包裝模式

所有診斷工具都使用 LangChain Tool 進行標準化包裝：

```python
# tools/base.py
from langchain.tools import Tool

def create_langchain_tool(name: str, description: str, func: Callable) -> Tool:
    """建立 LangChain Tool 實例"""
    return Tool.from_function(
        name=name,
        description=description,
        func=func,
        return_direct=True
    )
```

### 工具實現示例

```python
# tools/ads_metrics.py
def get_ads_metrics_tool():
    """取得 LangChain 包裝的廣告指標工具"""
    return create_langchain_tool(
        name="AdsMetrics",
        description="分析廣告關鍵詞表現，檢測出價、關鍵詞數量等問題",
        func=lambda scenario, mode="keyword": wrap_tool_run(
            "AdsMetrics", analyze_ads_metrics, scenario, mode
        )
    )
```

## ⚙️ 工具配置說明

### 工具映射規則

工具與假設的映射關係定義在 `agent/policy.py` 的 `RULES` 字典中：

```python
RULES = {
    "AdsMetrics": {
        "H1": [  # 出價太低
            {"type": "ratio", "feature": "avg_cpc_ratio", "thr": 0.6, "direction": "lower_better"}
        ],
        "H2": [  # 關鍵詞不足
            {"type": "count", "feature": "keyword_count", "thr": 5, "direction": "higher_better"}
        ]
    },
    "ListingAudit": {
        "H4": [  # Listing 品質
            {"type": "threshold", "feature": "main_image_score", "thr": 0.6, "direction": "lower_worse"},
            {"type": "threshold", "feature": "rating", "thr": 4.0, "direction": "lower_worse"},
            {"type": "count", "feature": "reviews", "thr": 50, "direction": "higher_better"}
        ]
    }
}
```

### 評分規則類型

支援五種評分規則類型：

1. **ratio**: 比率類型 (如 CPC 比率)
2. **count**: 計數類型 (如關鍵詞數量)
3. **threshold**: 閾值類型 (如評分閾值)
4. **gap**: 差距類型 (如價格差距)
5. **categorical**: 分類類型 (如風險等級)

### 新增工具步驟

1. **實現工具函數**: 在 `tools/` 目錄創建新工具
2. **配置映射規則**: 在 `RULES` 中添加工具-假設映射
3. **註冊 LangChain Tool**: 使用 `create_langchain_tool` 包裝
4. **更新主循環**: 在 `agent/loop.py` 中引入工具函數

### 工具執行流程

```
工具調用 → wrap_tool_run → 統一錯誤處理 → ToolResult → 特徵評分 → 信念更新
```

## 🎯 智能終止策略

Agent 採用極簡的智能終止邏輯，確保效率和決策品質：

### 終止條件

```python
def should_terminate(context: AgentContext) -> Tuple[bool, str]:
    """超級簡單的終止邏輯"""

    # 1. 強制最少3步
    if context.step < 3:
        return False, ""

    # 2. 信心達標終止
    max_belief = max(h.belief for h in context.hypotheses)
    if max_belief >= 0.42:
        return True, f"🎯 信心達標終止：信心值 {max_belief:.2f} ≥ 0.42"

    # 3. 步數限制終止
    if context.step >= 5:
        return True, f"⏰ 步數限制終止：已達到最大執行步數"

    return False, ""
```

### 終止策略特點

1. **智能決策**：信心值達到 0.42 時立即終止，無需繼續探索
2. **效率優先**：大多數情況在第3-4步完成診斷
3. **容錯保障**：最多執行5步，確保流程完整性
4. **透明邏輯**：終止原因清晰可見，便於理解和調試

### 實際執行結果

| 診斷場景 | 終止步數 | 終止原因 | 主要假設 |
|---------|---------|---------|---------|
| 低曝光場景 | 第3步 | 🎯 信心達標 | 競品壓制 (0.43) |
| 高點擊低轉換 | 第3步 | 🎯 信心達標 | 競品壓制 (0.43) |
| 高ACoS+工具失敗 | 第5步 | ⏰ 步數限制 | Listing品質 (0.38) |

### Agent vs Workflow 體現

- **Workflow**: 固定執行4個工具，總是5步
- **Agent**: 根據信心值動態決策，3-5步靈活終止
- **智能性**: 不同輸入產生不同執行路徑，體現自主決策能力

## ⚠️ 錯誤處理

### 常見錯誤與解決方案

#### 1. 場景檔案不存在

```bash
python demo.py diagnose --scenario invalid_scenario.json
```

**錯誤輸出：**
```
📁 載入場景檔案：invalid_scenario.json
❌ 檔案不存在：[Errno 2] No such file or directory: 'invalid_scenario.json'
```

**解決方案：** 檢查檔案路徑是否正確，使用 `scenarios/` 目錄下的有效場景檔案。

#### 2. JSON 格式錯誤

**錯誤輸出：**
```
📁 載入場景檔案：test_invalid.json
❌ 執行錯誤：Invalid control character at: line 2 column 31 (char 32)
```

**解決方案：** 檢查場景檔案的 JSON 格式是否正確。

#### 3. 工具執行失敗

使用 `--break-competitor` 可以模擬競品工具失敗：

```bash
python demo.py diagnose --scenario scenarios/scenario_high_acos.json --break-competitor
```

**錯誤輸出：**
```
╭────────────────────────────────────────── 🔧 工具執行 ───────────────────────────────────────────╮
│ ❌ 工具：Competitor                                                                              │
│ 狀態：失敗                                                                                       │
│ 耗時：104ms                                                                                      │
│ 錯誤：工具 'Competitor' 執行超時（30秒）                                                         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯

──────────────────────────────────────────── ⚠️ 錯誤處理 ────────────────────────────────────────────
╭───────────────────────────────────────── 🔧 錯誤與回退 ──────────────────────────────────────────╮
│ 工具 'Competitor' 錯誤：工具 'Competitor' 執行超時（30秒）                                       │
│                                                                                                  │
│ 回退策略：競品分析工具失敗，建議使用產品頁面審核工具檢查競爭力                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

Agent 會自動處理工具失敗，繼續使用其他工具完成診斷。

#### 4. 環境變數未設定

**解決方案：** 執行 `python demo.py setup` 檢查環境設定。

## 📁 輸出檔案

### Trace 記錄

每次執行都會在 `trace/` 目錄生成詳細記錄：

```bash
ls trace/
trace_20250917_081445.json  # 完整執行軌跡
trace_20250917_081516.json
trace_20250917_082134.json
```

### 診斷報告

使用 `--report` 選項會自動生成 OpenAI 摘要報告：

```bash
ls reports/
診斷報告_scenario_low_impr_20250917_081445.md
診斷報告_scenario_high_acos_20250917_081516.md
診斷報告_scenario_high_click_low_conv_20250917_082134.md
```

**報告內容：**
- 📊 診斷結論與置信度
- 🚀 具體行動建議 (含影響、風險、KPI)
- ⏰ 執行時程規劃 (T+48小時、T+7天)
- 📋 使用的診斷工具清單

**格式：** Markdown 檔案，同時在控制台顯示

## 📄 授權

此專案僅供學習和研究使用。
