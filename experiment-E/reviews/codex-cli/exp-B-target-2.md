# target-2 レビュー

## 問題点

- 重大度: medium - 更新 API が `title/status/priority` の明示的な `null` を受け入れ、SQL にそのまま渡します。DB は `NOT NULL` のため、クライアント入力で 500 系エラーを起こせます。該当: `targets-B/target-2/task-app/app/schemas.py:64`, `targets-B/target-2/task-app/app/main.py:169`, `targets-B/target-2/task-app/app/main.py:178`, `targets-B/target-2/task-app/app/database.py:43`
- 重大度: medium - DB スキーマに `status` と `priority` の `CHECK` 制約がありません。API 層は Enum で守っていますが、既存 DB や別経路から不正値が入ると `response_model` や統計が壊れます。該当: `database.py:45`, `database.py:46`
- 重大度: medium - テスト DB が OS の一時ディレクトリ上の固定ファイル名です。並列テストや別プロセスと衝突し、`os.remove()` による競合も起きます。該当: `tests/test_api.py:16`, `tests/test_api.py:28`
- 重大度: low - 検索クエリ `q` に長さ制限がなく、`LIKE '%...%'` の全表走査になります。データが増えると遅くなりやすいです。該当: `main.py:73`, `main.py:92`
- 重大度: low - テストは比較的多いものの、更新時 `null`、DB 不整合値、長大検索語、同時実行時の DB ファイル衝突を検証していません。

## 改善提案

- 更新スキーマで `null` を許さないフィールドは明示的に拒否し、`due_date` のようにクリア可能なフィールドだけ `null` を許可する。
- DB に `CHECK (status IN (...))` と `CHECK (priority IN (...))` を追加する。
- テスト DB は `tmp_path` fixture ごとの一意ファイルにする。
- `q` に `max_length` を設定し、規模が増えるなら index/FTS を検討する。
- 異常系テストに `PUT {"status": null}` などを追加する。

## 総合評価

7/10

既存テストは `22 passed`。SQL インジェクション対策や基本バリデーションは良いですが、更新時の `null` とテスト分離に改善余地があります。
