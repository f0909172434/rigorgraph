# RigorGraph

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

**把 AI 研究轉化為可稽核的命題—證據圖。**

RigorGraph 是本機優先的 CLI、離線報告、GitHub Action 與技能包，用來記錄研究命題說了什麼、哪些證據支持它、由誰獨立檢查，以及還有哪些未解缺口。它嚴格區分證明、文獻支持、數值證據、基準測試證據與不確定性。

> RigorGraph 檢查工作流程完整性與可追溯性。`VERIFIED` 只表示已被記錄的工作流程接受，不代表絕對真理、形式認證、同儕審查或專家共識。

> **公開 Beta：**RigorGraph 會在確定性品質閘門通過後持續發布，不以固定的外部使用者人數阻塞開發。請執行 demo，並透過 [Beta 回饋表](https://github.com/f0909172434/rigorgraph/issues/new?template=beta-feedback.yml) 告訴我們第一個令人困惑的步驟。請勿提交私人研究資料。

![RigorGraph 命題—證據流程](assets/rigorgraph-flow.svg)

## 快速開始

需要 Python 3.11 以上，不需要 API 金鑰。公開 Beta 期間請安裝已標記的原始碼版本；只有在核准發布到 PyPI 後，`pip install rigorgraph` 才會可用。

```bash
python -m pip install "git+https://github.com/f0909172434/rigorgraph.git@v0.1.0-beta.1"
rigorgraph --lang zh-TW demo --scenario math --open
```

示範會建立專案、執行確定性稽核，並開啟自包含報告。也可以測試刻意設計的錯誤晉升：

```bash
rigorgraph --lang zh-TW demo invalid-demo --scenario invalid
rigorgraph --lang zh-TW audit invalid-demo
```

稽核會拒絕把有限數值掃描當成形式證明。

### 建立自己的專案

```bash
rigorgraph --lang zh-TW quickstart 我的研究 --name "我的研究專案" --author "你的名字" --type formal --statement "每個有界數列都具有性質 P。" --open
```

這會用你輸入的原始語言建立一個真實的 `DRAFT` 命題，並開啟離線報告。命題會列在「未解缺口」；RigorGraph 不會捏造證據或將它晉升為 `VERIFIED`。專案使用可閱讀、可版本控制的紀錄：

```text
我的研究/
├── rigorgraph.yaml
└── .rigorgraph/
    ├── claims.jsonl
    ├── evidence.jsonl
    └── verifications.jsonl
```

## 命令

| 命令 | 用途 |
| --- | --- |
| `rigorgraph quickstart` | 不捏造證據，建立首個 `DRAFT` 命題與可閱讀離線報告 |
| `rigorgraph init` | 初始化專案且不覆寫既有檔案 |
| `rigorgraph claim add CLAIM.json` | 新增 `DRAFT` 或 `PROPOSED` 命題 |
| `rigorgraph evidence add EVIDENCE.json` | 新增具範圍的證據；本機檔案必須提供 SHA-256 |
| `rigorgraph verify CLAIM_ID --file REVIEW.json` | 記錄獨立的 `ACCEPT`、`REJECT` 或 `UNCERTAIN` 結果 |
| `rigorgraph audit` | 檢查結構、依賴圖、證據類別、獨立性與雜湊 |
| `rigorgraph report` | 產生可切換四語的離線 HTML 報告 |
| `rigorgraph demo` | 建立有效數學、有效 benchmark 或刻意無效的示範 |

可在命令前使用 `--lang en`、`--lang zh-TW`、`--lang zh-CN` 或 `--lang ja`。未指定時依序使用專案設定、作業系統語系與英文。

## 稽核保證的流程規則

- ID 唯一且所有連結都能解析。
- 命題依賴不得形成循環。
- 已撤銷或已拒絕命題不能暗中支持下游命題。
- 命題作者不能擔任自己的獨立驗證者。
- `VERIFIED` 必須有獨立的 `ACCEPT` 紀錄。
- 形式命題需要證明；文獻命題需要精確來源定位；實證與 benchmark 命題需要可重現產物。
- 本機證據路徑不得超出專案，且必要的 SHA-256 必須相符。
- ACCEPT 紀錄會綁定它實際審查的命題—證據快照。
- 已通過工作流驗證的綜合命題只能依賴目前同樣為 `VERIFIED` 的命題。

使用者撰寫的命題、公式、引文及證據保持原始語言；只翻譯介面標籤。

## Agent Skills 與 Codex plugin

本 repo 包含四個聚焦技能：[research-intake](skills/research-intake)、[capture-claim](skills/capture-claim)、[adversarial-verify](skills/adversarial-verify)、[release-audit](skills/release-audit)，並提供原生 `.codex-plugin/plugin.json`。

在 Codex 中可請 `$skill-installer` 從 `f0909172434/rigorgraph` 安裝技能，或透過支援的本機／plugin marketplace 流程安裝整個 repo。

## 隱私與邊界

- 預設只在本機運作；沒有帳號、遙測、遠端資料庫或內建付費模型 API。
- HTML 報告為自包含檔案，執行時不發出網路請求。
- 確定性閘門能發現紀錄不完整與錯誤晉升，但不能保證人類或 AI 證明在數學上正確。
- 核心結果仍須接受相應的專家審查。

原始碼開發、GitHub Action 與貢獻方式請參閱 [英文 README](README.md) 與 [CONTRIBUTING.md](CONTRIBUTING.md)；發布條件請參閱 [Beta 發布政策](docs/BETA_POLICY.md)。MIT License。
