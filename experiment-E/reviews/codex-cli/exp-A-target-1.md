# target-1 レビュー

## 問題点

- medium: `GET /tasks` が全件を無制限に返すため、データ件数が増えるとレスポンス時間、メモリ使用量、フロント描画負荷が悪化します。該当箇所: `targets-A/target-1/task-app/backend/main.py:28`
- medium: `Base.metadata.create_all(bind=engine)` をアプリ起動時に直接実行しています。簡易アプリとしては動きますが、本番運用ではマイグレーション管理ができず、起動時の副作用も大きくなります。該当箇所: `targets-A/target-1/task-app/backend/main.py:14`
- medium: DBファイルが `sqlite:///./tasks.db` の相対パス固定で、環境変数による切り替えができません。実行ディレクトリ次第でDBの作成場所が変わり、開発・テスト・本番の分離も弱いです。該当箇所: `targets-A/target-1/task-app/backend/database.py:5`
- low: `created_at` にローカル時刻の `datetime.now()` を使っており、タイムゾーンが不明確です。API利用者が複数環境にまたがると並び順や表示の解釈がずれます。該当箇所: `targets-A/target-1/task-app/backend/models.py:15`, `targets-A/target-1/task-app/backend/main.py:88`
- low: `__pycache__` が配布物に含まれています。レビュー対象のコードとして不要で、差分や成果物を汚します。
- low: テストはCRUD、基本バリデーション、代表的なフィルタ・ソートを確認していますが、不正な `sort` / `order`、空白だけのタイトル、`due_date` が `NULL` の混在、フロント連携は未確認です。

## 改善提案

- `GET /tasks` に `limit` / `offset` またはカーソルページングを追加し、上限値を設ける。
- Alembicなどでマイグレーションを管理し、起動時の `create_all` は開発用途に限定する。
- DB URLとCORS許可オリジンを環境変数化する。
- `created_at` はUTCで保存し、レスポンス仕様にもタイムゾーン方針を明記する。
- `__pycache__` を削除し、`.gitignore` で除外する。
- 不正クエリ、空白タイトル、期限未設定タスク、フロントの主要操作をテストに追加する。

## 総合評価

7/10

補足: `pytest -q` は 6 passed。
