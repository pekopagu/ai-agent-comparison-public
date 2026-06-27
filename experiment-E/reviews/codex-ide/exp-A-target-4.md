# target-4 レビュー

## 問題点

- medium: API が空白のみのタイトルを許容します。`schemas.py:28` と `schemas.py:42` は `min_length=1` のみで、`main.py:79` と `main.py:109-113` でも正規化していません。
- medium: 無指定の一覧取得では `id` 昇順になります（`main.py:35`, `main.py:68-70`）。一方でフロントエンドは `created_at` / `desc` を初期値として送るため、API 単体利用時と UI 利用時でデフォルトの並びが変わります。
- medium: `GET /tasks` が全件を無制限に返します（`main.py:72`）。件数増加時の性能劣化が避けられません。
- low: アプリ import 時にテーブル作成しています（`main.py:14`）。本番運用ではマイグレーション管理に寄せるべきです。
- low: フロントエンドが CDN と `http://localhost:8000` に固定されています（`frontend/index.html:489`, `frontend/index.html:492`）。

## 改善提案

- `TaskCreate` / `TaskUpdate` にタイトルの `strip()` と空白のみ拒否の validator を追加する。
- 一覧 API のデフォルトソートを明文化し、フロントエンド初期値と揃える。
- `limit` / `offset` を導入し、最大取得件数を制限する。
- DB 初期化はマイグレーションへ移行する。
- API URL と外部アセット取得先を環境設定化する。

## テストの網羅性

`pytest -q tests` は 22 件すべて成功しました。基本機能はよく確認されていますが、空白のみタイトル、priority の asc、`due_date = null`、フロントエンド操作、API デフォルトソートの契約は未検証です。

## 総合評価

7/10
