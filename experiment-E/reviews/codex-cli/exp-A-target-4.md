# target-4 レビュー

## 問題点

- medium: `GET /tasks` がページングなしで全件取得します。タスク数が増えるとAPI応答とフロント描画が重くなります。該当箇所: `targets-A/target-4/task-app/backend/main.py:32`
- medium: 起動時の `Base.metadata.create_all(bind=engine)` に依存しています。スキーマ変更の履歴管理、ロールバック、データ移行を扱えません。該当箇所: `targets-A/target-4/task-app/backend/main.py:14`
- medium: DB URLが `sqlite:///./tasks.db` 固定です。環境ごとの切り替えができず、実行ディレクトリにも依存します。該当箇所: `targets-A/target-4/task-app/backend/database.py:6`
- low: デフォルトの一覧順が `id asc` で、README上の主要ソート項目である `created_at` と一貫しません。フロント側は `sort=created_at&order=desc` を送るため通常画面では隠れますが、API単体利用時に期待がずれます。該当箇所: `targets-A/target-4/task-app/backend/main.py:70`
- low: `created_at` がローカル時刻の `datetime.now()` です。タイムゾーンが不明確です。該当箇所: `targets-A/target-4/task-app/backend/models.py:20`
- low: `title` は空文字を弾きますが、空白だけの文字列は通ります。ユーザー入力としては実質空タイトルを許可してしまいます。該当箇所: `targets-A/target-4/task-app/backend/schemas.py:28`, `targets-A/target-4/task-app/backend/schemas.py:42`
- low: `__pycache__` が成果物に含まれています。
- low: テストはCRUDや不正クエリまで比較的広くありますが、空白タイトル、`due_date` が `NULL` のソート、フロント連携、ページング相当の大量データケースは未確認です。

## 改善提案

- 一覧APIにページングと最大件数を追加する。
- Alembicでマイグレーション管理し、起動時 `create_all` を廃止する。
- DB URLとCORS許可オリジンを環境変数化する。
- デフォルト順をAPI仕様として明示し、必要なら `created_at desc` に統一する。
- `field_validator` で `title.strip()` 後の空文字を拒否する。
- `__pycache__` を削除して除外設定を追加する。

## 総合評価

8/10

補足: `pytest -q` は 22 passed。
