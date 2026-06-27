# target-1 レビュー

## 問題点

- medium: API が空白のみのタイトルを許容します。`schemas.py:7` と `schemas.py:17` は `min_length=1` のみで、`main.py:79` でも `strip()` せず保存しているため、`"   "` のようなタスクが作成・更新できます。テストも空文字のみで、空白文字のケースを検出できていません。
- medium: `GET /tasks` が全件を無制限に返します。`main.py:74` の `query.all()` は件数増加時にレスポンス遅延とメモリ使用量増大を招きます。
- low: アプリ起動時に `models.Base.metadata.create_all(bind=engine)` を実行しています（`main.py:14`）。小規模な試作では動きますが、実運用ではマイグレーション管理ができず、起動時副作用も大きくなります。
- low: `created_at` に naive な `datetime.now()` を使っています（`main.py:84`, `models.py:15`）。タイムゾーンが不明確で、クライアント表示や複数環境での並び順がずれやすくなります。
- low: フロントエンドが CDN と `http://localhost:8000` に固定されています（`frontend/index.html:12`, `frontend/index.html:1001`, `frontend/index.html:1003`）。本番配布やオフライン実行、サプライチェーン対策の面で弱いです。

## 改善提案

- Pydantic の `field_validator` でタイトルを `strip()` し、空白のみを 422 にする。更新時も同じバリデーションを適用する。
- `GET /tasks` に `limit` / `offset` または cursor pagination を追加し、最大件数を設ける。
- DB 初期化は Alembic などのマイグレーションに寄せ、アプリ import 時の副作用を減らす。
- `created_at` は UTC aware datetime で統一する。
- CDN はバージョン固定・SRI 追加、またはビルド済みアセットに同梱する。API URL は設定から注入する。

## テストの網羅性

`pytest -q tests` は 6 件すべて成功しました。一方で、空白のみタイトル、無効な sort/order、期限日 null のソート、フロントエンド操作、件数増加時の挙動は未検証です。

## 総合評価

7/10
