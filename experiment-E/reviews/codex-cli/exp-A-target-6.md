# target-6 レビュー

## 問題点

- high: テストが通常の実行方法で収集エラーになります。`pytest -q` を `backend` で実行すると `ModuleNotFoundError: No module named 'database'` が発生します。`tests/test_api.py` が `sys.path` 調整やパッケージ化をしていないためです。該当箇所: `targets-A/target-6/task-app/backend/tests/test_api.py:7`
- medium: `sort` と `order` が自由文字列で、無効値でも422になりません。実測で `GET /tasks?sort=bad` と `GET /tasks?order=bad` はどちらも 200 を返します。誤ったクライアント入力を検知できません。該当箇所: `targets-A/target-6/task-app/backend/main.py:29`, `targets-A/target-6/task-app/backend/main.py:30`, `targets-A/target-6/task-app/backend/main.py:73`
- medium: `status` / `priority` の不正値を400で返していますが、リクエストバリデーションとしては他target同様422に揃える方がFastAPI/Pydanticの慣習に合います。該当箇所: `targets-A/target-6/task-app/backend/main.py:27`, `targets-A/target-6/task-app/backend/main.py:38`, `targets-A/target-6/task-app/backend/main.py:43`
- medium: 一覧APIがページングなしで全件取得します。件数増加時に性能問題になります。該当箇所: `targets-A/target-6/task-app/backend/main.py:26`
- medium: 起動時に `models.Base.metadata.create_all(bind=engine)` を実行しています。マイグレーション管理がなく、本番運用に不向きです。該当箇所: `targets-A/target-6/task-app/backend/main.py:12`
- medium: DB URLが `sqlite:///./tasks.db` 固定です。環境ごとの切り替えや本番DB接続に向きません。該当箇所: `targets-A/target-6/task-app/backend/database.py:5`
- low: Pydantic v2環境で class-based `Config` を使っており、非推奨警告が出ています。該当箇所: `targets-A/target-6/task-app/backend/schemas.py:31`
- low: `DELETE /tasks/{id}` が200とJSON本文を返します。他targetや一般的なREST慣習に合わせるなら204の方が自然です。該当箇所: `targets-A/target-6/task-app/backend/main.py:115`
- low: テストは無効な `sort` / `order`、404更新、404削除、空白タイトル、期限未設定ソートをカバーしていません。

## 改善提案

- `tests` 実行時にbackendルートが必ずimport対象になるよう、`pytest.ini` の `pythonpath = .`、パッケージ化、またはテスト内の適切なパス設定を追加する。
- `sort` / `order` / `status` / `priority` は `Literal` または `Enum` で宣言し、FastAPIの422バリデーションに任せる。
- 一覧APIにページングを追加する。
- Alembicを導入し、起動時 `create_all` を避ける。
- DB URLとCORSを環境変数化する。
- Pydantic v2向けに `ConfigDict(from_attributes=True)` へ移行する。
- DELETEは `status_code=204` にし、本文なしに統一する。

## 総合評価

5/10

補足: 通常の `pytest -q` は収集エラー。`PYTHONPATH=.` を補うと 6 passed ですが、非推奨警告が2件出ます。
