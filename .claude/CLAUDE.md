# Amazon Ads 診斷 Agent (重構版本)

## 專案概述
基於 LangChain 重構的 Amazon 廣告診斷 Agent，解決了原版本的複雜性問題：
- 使用統一打分器取代硬編碼的工具權重
- 生成簡潔可讀的繁體中文報告
- 採用 LangChain 框架提高可維護性

## 架構設計原則
- **Agent vs Workflow**: 動態決策而非固定流程
- **統一打分器**: 避免過度工程化，統一特徵評分邏輯
- **透明推理**: Rich 控制台顯示完整決策過程
- **LangChain 整合**: 工具封裝使用 LangChain Tool

## 核心模組
- `agent/types.py`: 資料類型定義 (Pydantic)
- `agent/scoring.py`: 統一打分器 (ALPHA=0.2)
- `agent/policy.py`: 假設管理和工具選擇策略
- `agent/loop.py`: O→T→A 主循環 (≥3輪)
- `agent/reasoning.py`: 繁中 Rich 日誌
- `tools/`: 四個診斷工具 (AdsMetrics, ListingAudit, Competitor, Inventory)
- `reporter/`: OpenAI 報告生成 (僅負責摘要轉寫)

## 假設系統
- H1: 出價太低
- H2: 關鍵詞不足
- H3: 競品壓制
- H4: Listing 品質
- H5: 廣泛匹配浪費
- H6: 庫存不足

## 常用指令
```bash
python demo.py --scenario scenarios/scenario_low_impr.json
python demo.py --scenario scenarios/scenario_high_click_low_conv.json
python demo.py --scenario scenarios/scenario_high_acos.json --break-competitor
```

## 環境變數
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## 改進重點
1. 解決工具權重管理複雜性問題
2. 報告生成更簡潔易讀
3. 使用成熟框架 LangChain
4. 統一打分器避免過度工程化
5. 透明的繁中推理過程