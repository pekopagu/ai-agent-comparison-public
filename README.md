# AIエージェント比較実験：同じタスク管理アプリを6つのコーディングエージェントに作らせてみた

6つのAIコーディングエージェント（Claude Code・Codex CLI・Antigravity CLI・Codex IDE・Antigravity IDE・GitHub Copilot Agent）に、同一のタスク管理アプリ（FastAPI + Vue 3）を実装させ、テスト・相互コードレビュー・自己評価・他者テスト修正までを横断的に比較した実験のデータ一式です。

## この実験で何をしたか

| 実験 | 内容 |
|---|---|
| 実験A | 詳細仕様書を渡しての実装比較（6エージェント） |
| 実験B | 最小仕様＋プランニングを任せての実装比較（6エージェント） |
| 実験D | 他者が実装したコードに合わせてテストを修正する作業（6エージェント×5本＝30セッション） |
| 実験E | 他エージェントの実装を匿名でコードレビューする作業（A/B合計60件） |

各エージェントには、共通の仕様書・共通のテストスイート（pytest 18本＋Playwright 6本）を使い、同一条件で実装させています。実験Cとして「既存のテストを見ずに専用プロンプトで自己テストを追加作成させる」という計画もありましたが、専用プロンプトは一度も送られておらず未実施です。

## 対象エージェント

| エージェント | ベンダー | インターフェース |
|---|---|---|
| Claude Code | Anthropic | CLI |
| Codex CLI | OpenAI | CLI |
| Antigravity CLI | Google | CLI |
| Codex IDE | OpenAI | IDE拡張 |
| Antigravity IDE | Google | IDE拡張 |
| GitHub Copilot Agent | Microsoft（Claude Opus経由） | IDE統合 |

## リポジトリ構成

```
.
├── common/                  共通テストスイート・評価データ（evaluation/）
├── experiment-A/            実験A：6エージェントの詳細仕様実装
├── experiment-B/            実験B：6エージェントの最小仕様実装
├── experiment-D/            実験D：他者テスト修正の成果物
├── experiment-E/            実験E：相互コードレビューの結果
├── competition-articles/    Zenn第7回・Qiita第9回の競作6本ずつ
　　　　　　　　　　　　　 （6エージェントに同じデータ・同じ指示で執筆させ、
　　　　　　　　　　　　　 そのうち1本だけをZenn/Qiitaに実際に公開しています）
├── dashboard.html           比較ダッシュボード（ブラウザで直接開けます。
　　　　　　　　　　　　　 Claude.aiとの協働で作成したツールであり、
　　　　　　　　　　　　　 6エージェント比較の実験対象ではありません）
├── full-report.md           全実験（A・B・D・E）の点数・評価・コメント全文をまとめたレポート
　　　　　　　　　　　　　 （実験記録の生データから公開用に抜粋・整形したものです）
├── experiment-plan.md       実験全体の設計・採点基準
└── screenshots/             各エージェントの実装画面（実験A・B）
```

## ダッシュボードの見方

`dashboard.html` をブラウザで直接開くと、6エージェントの総合ランキング・実験ごとの詳細データ・自己評価と人間評価のギャップなどを確認できます。ビルド不要（Vue 3 + Chart.jsをCDN経由で読み込む単一HTMLファイル）です。

## 共通テストの実行方法

各エージェントの実装（`experiment-A/<agent>/task-app/`など）に対して、共通テストを実行できます。

```bash
# バックエンドテスト（pytest 18本）
cd common/test-original
pip install requests pytest
pytest test_api.py -v
# 対象の実装を http://localhost:8000 で起動した状態で実行してください

# フロントエンドテスト（Playwright 6本）
pip install playwright pytest-playwright
playwright install chromium
pytest test_ui.py -v
# 対象の実装を http://localhost:3000 で起動した状態で実行してください
```

スコア計算式や各テストの内容は `experiment-plan.md` を参照してください。

## 主な発見（要約）

- **開発時間は最大5倍の差**：最速4分（Claude Code・Antigravity CLI）〜最長20分（Antigravity IDE）
- **共通テスト合格率は全6エージェントが91.7%以上、4エージェントが100%**だったが、自己評価ではこの実態をうまく認識できていないケースがあった
- **他者テスト修正（実験D）で、6エージェント中3エージェントに指示違反が発覚**：テストの期待値やレスポンス値を書き換えて、本来失敗すべき検証を通過させる行為が見つかった
- **コードレビューでは「均質化トラップ」（同系統ベンダーへの評価が甘くなる傾向）が一部で観測されたが、常に起きる現象ではなかった**
- **自己評価ギャップの原因は一様ではない**：「ツール操作ミスによる誤診断」と「実装の見落とし」は、どちらも数値上は同じ「過小評価」に見えるが、性質が異なる

実験の詳細な分析・考察は、下記の記事一覧で公開しています。

## 関連記事

実験の設計過程や各エージェントの詳しいレポートは、記事として公開予定です。記事一覧は [ARTICLES.md](./ARTICLES.md) を参照してください（公開後、URLを追記します）。

## ライセンス

[LICENSE](./LICENSE) を参照してください。
