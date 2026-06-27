# コードレビュー: target-2

対象: `targets-A/target-2/task-app`（FastAPI + SQLAlchemy バックエンド / Vue 3 フロントエンド）

## 概要
`Enum`（Status/Priority）による型安全なバリデーション、`title` の `strip` 検証、docstring 完備、ヘルスチェック用 root、依存バージョン固定など、全体的に丁寧で保守性が高い。テストケースも豊富。

---

## 問題点

### 1. テストDBが「インメモリ」ではなくファイルベース（重大度: medium）
`test_api.py` のコメントは「インメモリ SQLite を使用」とあるが、実際は `sqlite:///./test_tasks.db` でファイルを生成する。実体と説明が食い違い、テスト実行ごとに `test_tasks.db` が残存する。`autouse` の `create_all`/`drop_all` で各テストは独立するが、`StaticPool` + `sqlite:///:memory:` による真のインメモリ化が望ましい。また `client` / `dependency_overrides` がモジュールレベルでグローバルに設定されており、並列実行や他テストとの干渉に弱い。

### 2. `due_date` ソート時の NULL の扱いが未制御（重大度: low）
`sort_expr = models.Task.due_date` をそのまま `asc/desc` する。SQLite では NULL が端に寄るが、期限なしタスクの並び順が直感に反する場合がある。明示的な NULL 末尾配置が親切。

### 3. ソートに安定した第2キーがない（重大度: low）
`created_at` 等が同値の場合の並び順が不定。`Task.id` を第2ソートキーに加えると決定的になる。

### 4. 更新時の Enum 変換が冗長（重大度: low）
`update_task` で `isinstance(value, schemas.Status)...` による手動文字列変換を行っているが、`model_dump(mode="json")` 等で簡潔化できる。動作上は問題なし。

---

## テストの網羅性
- 作成（最小/全項目/空白/未指定/不正status/不正priority）、取得、一覧、フィルタ、ソート（asc/desc/due_date）、不正 sort/order、更新（全体/部分/404/不正）、削除（204/404）と非常に網羅的。
- 不足: `due_date` NULL を含むソート、長文 description、`title` 255文字超の境界。

## 改善提案
- テストを真のインメモリ（`sqlite://` + `StaticPool`）化し、`client` を `pytest.fixture` で生成して独立性を確保。
- `due_date` ソートで NULL 末尾配置を明示。
- 全ソートに `Task.id` の第2キーを付与。

## 総合評価
**8 / 10**

設計・検証・ドキュメント・テストのバランスが良く、実装品質は高い。テストの「インメモリ」誤記とファイル残留が主な減点要因。
