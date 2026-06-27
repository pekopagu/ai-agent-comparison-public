# target-6 レビュー

## 問題点

- 重大度: medium - 更新 API が `title/priority/status` の明示的な `null` を受け入れ、SQLAlchemy モデルへそのまま `setattr()` します。DB の `nullable=False` 制約により 500 系エラーになり得ます。該当: `targets-B/target-6/task-app/schemas.py:13`, `targets-B/target-6/task-app/main.py:63`, `targets-B/target-6/task-app/main.py:71`, `targets-B/target-6/task-app/models.py:12`
- 重大度: medium - `due_date` は正規表現だけで検証しており、`2026-99-99` のような存在しない日付を受け入れます。フロントの期限切れ判定や将来の集計で不整合になります。該当: `schemas.py:7`, `schemas.py:16`
- 重大度: medium - 静的ファイルと SQLite DB がカレントディレクトリ依存です。起動場所が変わると空の `static` を作成して配信したり、意図しない場所に `tasks.db` を作ります。該当: `database.py:4`, `main.py:89`, `main.py:91`
- 重大度: low - `DELETE /api/tasks/{id}` が 200 と JSON ボディを返します。REST としては 204 No Content が一般的で、他 target とも挙動が揃っていません。該当: `main.py:77`
- 重大度: low - 検索は `contains()` による部分一致で全表走査になり、検索語の長さ制限もありません。該当: `main.py:22`, `main.py:32`
- 重大度: low - テストは 6 件で、更新時 `null`、実在しない日付、削除 API のステータス設計、起動ディレクトリ違い、検索・フィルタ境界値を検証していません。

## 改善提案

- `due_date` は `datetime.date` として受け、更新時に `null` を許す項目を明確に分ける。
- DB と static のパスは `Path(__file__).resolve()` 基準または設定値で決める。
- DELETE は 204 に寄せるか、API 仕様として 200 を明文化して全体で統一する。
- `q` に `max_length` を設定し、必要なら index/FTS とページングを追加する。
- 異常系と環境依存のテストを増やす。

## 総合評価

5/10

既存テストは `6 passed`。基本操作は動きますが、日付検証、パス解決、更新時 `null` の扱いが弱く、運用時の不具合につながりやすいです。
