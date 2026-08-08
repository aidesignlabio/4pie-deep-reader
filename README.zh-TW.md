# 4PIE Deep Reader

一套可追蹤、可反證的四派命理深讀框架，核心系統為八字、紫微斗數、西洋占星與吠陀占星。技術中間資料可以標記不足，但正式報告不接受降級輸出：任何核心模組不足時，流程停止且不生成 PDF。

四派先各自解盤，再比較不同人生版本。相似術語不會自動變成共識；模型會保留限制、衝突、單派訊號和判錯條件。

## 輸出

- 四派排盤與資料驗證；
- 四份單派Dossier；
- 競爭人生版本與跨派裁決；
- 順勢度、潛力、阻力、證據信心；
- 繁體中文本命與流年報告；
- 預設 Plain Deep Report PDF（封面、目錄、評分、時間索引、深讀正文）；
- 可選的擴展 Dashboard PDF。

分數是閱讀索引，不是命中率、人格價值或事件保證。

## 最簡流程

```text
出生資料
-> 四派排盤
-> 技術驗證
-> 四派獨立深讀
-> 競爭版本裁決
-> 四維評分
-> Production Approval
-> Markdown / PDF
```

## 正式輸出硬門檻

```powershell
.\.venv\Scripts\python scripts\4pie.py production-check private_cases\case_name --start-year 2026
.\.venv\Scripts\python scripts\4pie.py render private_cases\case_name private_cases\case_name\report.pdf --start-year 2026 --subject "出生資料摘要"
```

`render` 會再次執行完整驗證。四派 L0、八字 L1、四份 Dossier、跨派裁決、八領域四維評分或連續五年流年只要有一項缺失、`insufficient` 或失敗，命令會以非零狀態結束，不建立 PDF，也不保留半成品。

正式 PDF 固定使用 `4PIE_20020312_Plain_Deep_Report_v1` 的視覺模板：山形路線封面、卡片式目錄、八領域 Dashboard、五年垂直時間軸、淡藍章節標題帶，以及相同的頁首、頁尾、字級、行距與留白。個案資料全部由輸入動態產生。

## 一鍵安裝

Windows：

```powershell
.\setup.ps1
```

若 Windows 的 `python` 指向已失效的啟動器，可明確指定可用直譯器：

```powershell
.\setup.ps1 -Python "C:\path\to\python.exe"
```

macOS／Linux：

```bash
./setup.sh
```

安裝器會建立隔離的 `.venv`、按正確順序安裝吠陀及PDF依賴、把版本鎖定的 Noto Sans TC 字體下載到已忽略的本地資產目錄、安裝固定版本 `iztro@2.5.8`，最後實算一個合成四派命盤。Windows、macOS、Linux 因此不需要預先安裝繁中字體，也能維持相同 PDF 字型。成功時必須同時出現 `FONT_READY`、`FOUR_SYSTEM_SMOKE_OK` 和 `4PIE_READY`。

安裝只需執行一次。如果重試時看到 `SETUP_WAITING`，代表上一個安裝程序仍在執行；安裝器會等待，不會再啟動第二個 pip/npm。讓原程序完成後，再用 `.venv\Scripts\python scripts\4pie.py doctor` 做數秒級檢查，不應為每個案例重新安裝依賴或複製 `node_modules`。紫微子程序固定使用 UTF-8，不需要手動設定 `PYTHONUTF8`。

詳細工作方式見 [SKILL.md](SKILL.md)。真實個案必須放入已忽略的 `private_cases/`，公開前執行：

```powershell
python scripts/privacy_scan.py .
```

目前版本為 1.0.3 正式發佈版。計算流程、Production Gate 與 PDF 渲染均有回歸測試；命理解讀本身不宣稱科學驗證或預測準確率。Production Approval 代表資料與流程完整，不代表命理結論經科學驗證。

## 點 Star 或支持作者

如果 4PIE 對你有幫助，歡迎先為[這個倉庫點一個 Star ⭐](https://github.com/aidesignlabio/4pie-deep-reader)，讓更多人找到這個專案。

如果你也想支持作者繼續開發，可到 [SUPPORT.md](SUPPORT.md) 按所在地選擇：

1. 香港 — PayMe
2. 中國內地 — 支付寶
3. 國際 — PayPal
