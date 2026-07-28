# RigorGraph

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

**把 AI 研究转化为可审计的命题—证据图。**

RigorGraph 是本地优先的 CLI、离线报告、GitHub Action 与技能包，用于记录研究命题说了什么、哪些证据支持它、由谁独立检查，以及还有哪些未解缺口。它严格区分证明、文献支持、数值证据、基准测试证据和不确定性。

> RigorGraph 检查工作流程完整性与可追溯性。`VERIFIED` 只表示已被记录的工作流程接受，不代表绝对真理、形式认证、同行评审或专家共识。

![RigorGraph 命题—证据流程](assets/rigorgraph-flow.svg)

## 快速开始

需要 Python 3.11 或更高版本，不需要 API 密钥。目前仍是私有发布候选版，请从源代码安装；只有在获准发布到 PyPI 后，`pip install rigorgraph` 才会可用。

```bash
git clone https://github.com/f0909172434/rigorgraph.git
cd rigorgraph
python -m pip install .
rigorgraph --lang zh-CN demo --scenario math --open
```

演示会创建项目、运行确定性审计，并打开自包含报告。也可以测试刻意设计的错误晋升：

```bash
rigorgraph --lang zh-CN demo invalid-demo --scenario invalid
rigorgraph --lang zh-CN audit invalid-demo
```

审计会拒绝把有限数值扫描当作形式证明。

### 创建自己的项目

```bash
rigorgraph --lang zh-CN init 我的研究 --name "我的研究项目"
rigorgraph --lang zh-CN audit 我的研究
rigorgraph --lang zh-CN report 我的研究 --output 研究报告.html --open
```

项目使用可阅读、可版本控制的记录：

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
| `rigorgraph init` | 初始化项目且不覆盖已有文件 |
| `rigorgraph claim add CLAIM.json` | 添加 `DRAFT` 或 `PROPOSED` 命题 |
| `rigorgraph evidence add EVIDENCE.json` | 添加有明确范围的证据；本地文件必须提供 SHA-256 |
| `rigorgraph verify CLAIM_ID --file REVIEW.json` | 记录独立的 `ACCEPT`、`REJECT` 或 `UNCERTAIN` 结果 |
| `rigorgraph audit` | 检查结构、依赖图、证据类别、独立性与哈希 |
| `rigorgraph report` | 生成可切换四种语言的离线 HTML 报告 |
| `rigorgraph demo` | 创建有效数学、有效 benchmark 或刻意无效的演示 |

可在命令前使用 `--lang en`、`--lang zh-TW`、`--lang zh-CN` 或 `--lang ja`。未指定时依次使用项目设置、操作系统语言和英文。

## 审计保证的流程规则

- ID 唯一且所有链接都能解析。
- 命题依赖不得形成循环。
- 已撤销或已拒绝命题不能暗中支持下游命题。
- 命题作者不能担任自己的独立验证者。
- `VERIFIED` 必须有独立的 `ACCEPT` 记录。
- 形式命题需要证明；文献命题需要精确来源定位；实证与 benchmark 命题需要可复现产物。
- 本地证据路径不得超出项目，且必需的 SHA-256 必须匹配。
- ACCEPT 记录会绑定其实际审查的命题—证据快照。
- 通过工作流验证的综合命题只能依赖当前同样为 `VERIFIED` 的命题。

用户编写的命题、公式、引文和证据保持原始语言；只翻译界面标签。

## Agent Skills 与 Codex plugin

本仓库包含四个聚焦技能：[research-intake](skills/research-intake)、[capture-claim](skills/capture-claim)、[adversarial-verify](skills/adversarial-verify)、[release-audit](skills/release-audit)，并提供原生 `.codex-plugin/plugin.json`。

在 Codex 中可请 `$skill-installer` 从 `f0909172434/rigorgraph` 安装技能，或通过支持的本地／plugin marketplace 流程安装整个仓库。

## 隐私与边界

- 默认只在本地运行；没有账号、遥测、远程数据库或内置付费模型 API。
- HTML 报告为自包含文件，运行时不发出网络请求。
- 确定性门控能发现记录不完整与错误晋升，但不能保证人类或 AI 证明在数学上正确。
- 核心结果仍须接受相应的专家审查。

源代码开发、GitHub Action 与贡献方式请参阅 [英文 README](README.md) 和 [CONTRIBUTING.md](CONTRIBUTING.md)。MIT License。
