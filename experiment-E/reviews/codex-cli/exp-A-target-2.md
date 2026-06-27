# target-2 レビュー

## 問題点

- medium: `GET /tasks` がページングなしで全件取得します。件数増加時にDB、API、フロントの負荷が線形に増えます。該当箇所: `targets-A/target-2/task-app/backend/main.py:33`
- medium: アプリ起動時に `Base.metadata.create_all(bind=engine)` を実行しており、スキーマ変更の履歴管理やロールバックができません。該当箇所: `targets-A/target-2/task-app/backend/main.py:15`
- medium: DB URLが `sqlite:///./tasks.db` に固定されています。環境ごとの接続先分離、DockerやCIでの設定変更、本番DB利用がしづらい構成です。該当箇所: `targets-A/target-2/task-app/backend/database.py:7`
- low: `created_at` がローカル時刻の `datetime.now()` で保存されます。タイムゾーンがレスポンスから読み取れず、環境差が出ます。該当箇所: `targets-A/target-2/task-app/backend/models.py:21`
- low: テストDBが `sqlite:///./test_tasks.db` のファイルDBです。テスト失敗時にファイルが残る可能性があり、並列実行にも弱いです。該当箇所: `targets-A/target-2/task-app/backend/tests/test_api.py:19`
- low: テストは比較的厚い一方、`due_date` が `NULL` のソート順、同一ソートキー時の安定順、フロントのAPI連携は未確認です。

## 改善提案

- 一覧APIにページングと最大取得件数を追加する。
- DB URL、CORS許可オリジンを環境変数で設定できるようにする。
- Alembicなどのマイグレーションを導入し、`create_all` は初期開発またはテスト専用にする。
- `created_at` はUTC保存に統一する。
- テストDBは `StaticPool` のインメモリSQLite、または一時ディレクトリのDBを使う。
- `NULL` 期限、同一優先度、同一作成日時など境界条件のテストを追加する。

## 総合評価

8/10

補足: `pytest -q` は 23 passed。
