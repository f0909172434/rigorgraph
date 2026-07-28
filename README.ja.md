# RigorGraph

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md)

**AI リサーチを監査可能な主張—証拠グラフに変換します。**

RigorGraph は、研究上の主張、支持する証拠、独立検証者、未解決のギャップを記録するローカルファーストの CLI、オフラインレポート、GitHub Action、スキルパックです。証明、文献上の支持、数値証拠、ベンチマーク証拠、不確実性を明確に区別します。

> RigorGraph はワークフローの完全性と追跡可能性を確認します。`VERIFIED` は記録されたワークフローで受理されたことを意味するだけで、絶対的な真理、形式認証、査読、専門家の合意を意味しません。

> **公開ベータ：**最初の外部ユーザー 5 名を募集しています。デモを実行し、レポートを開くまでの時間を測り、最初に分かりにくかった手順を [ベータフィードバックフォーム](https://github.com/f0909172434/rigorgraph/issues/new?template=beta-feedback.yml) で共有してください。非公開の研究データは含めないでください。

![RigorGraph 主張—証拠フロー](assets/rigorgraph-flow.svg)

## クイックスタート

Python 3.11 以降が必要です。API キーは不要です。公開ベータ期間中はタグ付きソース版をインストールしてください。`pip install rigorgraph` は、PyPI への公開が承認された後に利用可能になります。

```bash
python -m pip install "git+https://github.com/f0909172434/rigorgraph.git@v0.1.0-beta.1"
rigorgraph --lang ja demo --scenario math --open
```

デモはプロジェクトを作成し、決定的監査を実行して、自己完結型レポートを開きます。意図的に無効な昇格も確認できます。

```bash
rigorgraph --lang ja demo invalid-demo --scenario invalid
rigorgraph --lang ja audit invalid-demo
```

有限の数値走査を形式的な証明として扱う試みは、監査で拒否されます。

### 自分のプロジェクトを作成する

```bash
rigorgraph --lang ja init my-research --name "私の研究プロジェクト"
rigorgraph --lang ja audit my-research
rigorgraph --lang ja report my-research --output research-report.html --open
```

プロジェクトは、人間が読めてバージョン管理できるレコードを保存します。

```text
my-research/
├── rigorgraph.yaml
└── .rigorgraph/
    ├── claims.jsonl
    ├── evidence.jsonl
    └── verifications.jsonl
```

## コマンド

| コマンド | 用途 |
| --- | --- |
| `rigorgraph init` | 既存ファイルを上書きせずに初期化 |
| `rigorgraph claim add CLAIM.json` | `DRAFT` または `PROPOSED` の主張を追加 |
| `rigorgraph evidence add EVIDENCE.json` | 範囲を限定した証拠を追加。ローカルファイルには SHA-256 が必須 |
| `rigorgraph verify CLAIM_ID --file REVIEW.json` | 独立した `ACCEPT`、`REJECT`、`UNCERTAIN` を記録 |
| `rigorgraph audit` | 構造、依存グラフ、証拠区分、独立性、ハッシュを確認 |
| `rigorgraph report` | 4 言語を切り替えられるオフライン HTML を生成 |
| `rigorgraph demo` | 有効な数学、ベンチマーク、意図的に無効なデモを作成 |

コマンドの前に `--lang en`、`--lang zh-TW`、`--lang zh-CN`、`--lang ja` を指定できます。未指定の場合はプロジェクト設定、OS 言語、英語の順で選択します。

## 監査が強制するワークフロー規則

- ID は一意で、すべてのリンクが解決できること。
- 主張の依存関係に循環がないこと。
- 取り消し済みまたは却下済みの主張が下流の主張を暗黙に支えないこと。
- 著者自身が独立検証者にならないこと。
- `VERIFIED` には独立した `ACCEPT` レコードがあること。
- 形式的主張には証明、文献上の主張には正確な位置指定、実証・ベンチマーク主張には再現可能な成果物があること。
- ローカル証拠パスがプロジェクト外を指さず、必須の SHA-256 が一致すること。
- ACCEPT レコードが、実際にレビューした主張—証拠スナップショットに結び付くこと。
- ワークフロー検証済みの統合主張は、現在 `VERIFIED` の主張だけに依存すること。

利用者が書いた主張、数式、引用、証拠は原文のまま保持し、画面ラベルだけを翻訳します。

## Agent Skills と Codex plugin

このリポジトリには [research-intake](skills/research-intake)、[capture-claim](skills/capture-claim)、[adversarial-verify](skills/adversarial-verify)、[release-audit](skills/release-audit) と、ネイティブ `.codex-plugin/plugin.json` が含まれます。

Codex では `$skill-installer` に `f0909172434/rigorgraph` からのインストールを依頼するか、対応するローカル／plugin marketplace フローを使用してください。

## プライバシーと境界

- 既定ではローカルのみ。アカウント、テレメトリ、リモート DB、組み込み有料モデル API はありません。
- HTML レポートは自己完結型で、実行時にネットワーク要求を行いません。
- 決定的ゲートは不完全な記録や不正な昇格を検出できますが、人間や AI の証明が数学的に正しいことを保証しません。
- 重要な結果には適切な専門家レビューが必要です。

ソース開発、GitHub Action、貢献方法は [英語 README](README.md) と [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。MIT License。
