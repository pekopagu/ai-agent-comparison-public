# target-2 レビュー

## 問題点

- medium: `GET /tasks` が全件を無制限に返します（`main.py:75`）。タスク数が増えると DB/アプリ/ブラウザの負荷が直線的に増えます。
- low: アプリ import 時に `Base.metadata.create_all(bind=engine)` を実行しています（`main.py:15`）。スキーマ変更や環境分離を考えると、マイグレーションで管理する方が安全です。
- low: テストは「インメモリ SQLite」とコメントされていますが、実際には `sqlite:///./test_tasks.db` を使っています（`tests/test_api.py:17-20`）。ローカルファイルが残りやすく、並列テストや実行ディレクトリの違いで影響を受けます。
- low: `due_date` ソートで `NULL` の扱いを明示していません（`main.py:67-73`）。SQLite のデフォルト順に依存するため、DB を変えた場合や UX 要件が変わった場合に結果が揺れます。
- low: フロントエンドが CDN と `http://localhost:8000` に固定されています（`frontend/index.html:7`, `frontend/index.html:405`）。デプロイ環境の切り替えやサプライチェーン対策がしづらい構成です。

## 改善提案

- 一覧 API に `limit` / `offset` を追加し、最大値を設定する。
- DB 作成は起動時処理から切り離し、Alembic 等のマイグレーションに移す。
- テスト DB は `sqlite://` + `StaticPool` などの完全なインメモリ構成、または pytest の `tmp_path` 配下にする。
- `due_date` の `NULLS LAST` 相当を明示する。
- API URL と外部アセットは設定化し、CDN 利用時はバージョン固定と SRI を検討する。

## テストの網羅性

`pytest -q tests` は 23 件すべて成功しました。CRUD、バリデーション、フィルタ、ソートは広く押さえていますが、フロントエンド、ページング、大量データ、`due_date = null` のソート、並列実行時のテスト DB 競合は未検証です。

## 総合評価

8/10
