# target-3 レビュー

## 問題点

- high: `TaskUpdate` が `TaskBase` を継承しているため、`title` が必須になり、部分更新APIとして機能しません。実測でも `PUT /tasks/{id}` に `{"priority":"high"}` だけを送ると 422 になります。該当箇所: `targets-A/target-3/task-app/backend/schemas.py:58`, `targets-A/target-3/task-app/backend/main.py:78`
- medium: `update_task` が `payload.model_dump()` を `exclude_unset=True` なしで全フィールド反映します。仮に `TaskUpdate` を任意項目化しても、未指定フィールドのデフォルト値で既存値を上書きするリスクがあります。該当箇所: `targets-A/target-3/task-app/backend/main.py:80`
- medium: 一覧APIがページングなしで全件取得します。件数増加時の性能劣化が避けられません。該当箇所: `targets-A/target-3/task-app/backend/main.py:32`
- medium: 起動時に `Base.metadata.create_all(bind=engine)` を実行しており、マイグレーション管理がありません。該当箇所: `targets-A/target-3/task-app/backend/main.py:11`
- medium: DB URLが相対パス固定です。環境分離や運用時の設定変更がしづらいです。該当箇所: `targets-A/target-3/task-app/backend/database.py:7`
- low: `due_date` ソートで `NULL` の扱いを明示していません。SQLite依存の順序になり、DB変更時に挙動が変わる可能性があります。該当箇所: `targets-A/target-3/task-app/backend/main.py:58`
- low: テストは6件のみで、部分更新失敗、無効な `sort` / `order`、`priority` フィルタ、期限未設定のソート、フロント操作をカバーしていません。

## 改善提案

- `TaskUpdate` は全フィールドを `Optional` にした専用モデルにし、`payload.model_dump(exclude_unset=True)` だけを反映する。
- 部分更新のテストを追加し、未指定フィールドが保持されることを確認する。
- 一覧APIにページングを追加する。
- Alembicを導入し、起動時 `create_all` を避ける。
- DB URLとCORSを環境変数化する。
- `due_date` の `NULLS LAST` 相当の仕様を明示して実装する。

## 総合評価

6/10

補足: `pytest -q` は 6 passed。ただし部分更新の欠陥は既存テストで検出できていません。
