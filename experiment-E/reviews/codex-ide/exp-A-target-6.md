# target-6 レビュー

## 問題点

- high: テストが収集時点で失敗します。`tests/test_api.py:7-9` が `database` / `main` を直接 import しますが、backend ディレクトリが import path に入っていません。`pytest -q tests` は `ModuleNotFoundError: No module named 'database'` で停止しました。
- medium: 無効な `sort` が 422 にならず、`created_at desc` にフォールバックします（`main.py:72-74`）。無効な `order` も `desc` 以外は実質 `asc` として処理されます（`main.py:58-71`）。API 利用者の入力ミスを隠し、テストでも検出しづらい挙動です。
- medium: API が空白のみのタイトルを許容します。`schemas.py:6` と `schemas.py:16` は `min_length=1` のみで、空白文字だけの文字列を拒否していません。
- medium: `GET /tasks` が全件を無制限に返します（`main.py:76`）。タスク数が増えた場合に性能問題になります。
- low: 削除 API が 204 ではなく 200 + JSON を返します（`main.py:114-122`）。致命的ではありませんが、他の REST API と比べると契約がやや一貫しません。
- low: アプリ import 時にテーブル作成しています（`main.py:12`）。マイグレーション管理やテスト分離の観点では副作用を減らした方がよいです。

## 改善提案

- テスト側で backend ディレクトリを import path に追加するか、アプリをパッケージ化して import を安定させる。
- `sort` と `order` は `Literal` / Enum / `Query` で制限し、不正値は 422 を返す。
- タイトルは validator で `strip()` し、空白のみを拒否する。
- 一覧 API に `limit` / `offset` と最大値を追加する。
- 削除成功時は 204 No Content に揃えるか、200 JSON を採用する理由を API 契約として明記する。
- DB 作成は起動時副作用からマイグレーションへ移す。

## テストの網羅性

`pytest -q tests` は import error で 1 error でした。テストには無効な sort/order、空白のみタイトル、削除ステータスの契約、フロントエンド操作、大量データが含まれていません。

## 総合評価

5/10
