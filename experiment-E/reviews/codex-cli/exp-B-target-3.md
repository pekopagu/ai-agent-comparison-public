# target-3 レビュー

## 問題点

- 重大度: medium - `TaskUpdate` が `title/priority/completed` の明示的な `null` を許容し、repository が `None` を SQL に渡します。DB の `NOT NULL` / `CHECK` 制約により 500 系エラーになり得ます。該当: `targets-B/target-3/task-app/app/schemas.py:51`, `targets-B/target-3/task-app/app/repository.py:109`, `targets-B/target-3/task-app/app/repository.py:124`, `targets-B/target-3/task-app/app/database.py:26`
- 重大度: low - `/api/health` が DB の絶対パスを返します。運用環境では内部ディレクトリ構造を不要に公開します。該当: `app/main.py:48`
- 重大度: low - 検索は `LOWER(title) LIKE` / `LOWER(description) LIKE` の全表走査で、件数増加時に遅くなります。該当: `repository.py:68`, `repository.py:69`
- 重大度: low - 一覧取得時に常に全体サマリを別クエリで計算します。画面要件としては妥当ですが、ページングなしの一覧取得と合わせてスケールしにくいです。該当: `repository.py:86`
- 重大度: low - テストは 9 件で、空タイトル、無効日付、ソート順、更新時 `null`、削除済みデータの一覧影響などのカバレッジが不足しています。

## 改善提案

- 更新時は `exclude_unset=True` に加えて、`None` を許すフィールドを限定する。`due_date` 以外の `null` は 422 にする。
- `/api/health` では DB パスを返さず、必要なら環境名や接続可否だけにする。
- 一覧に `limit/offset` を追加し、検索用 index または FTS を検討する。
- 異常系とソート・検索境界値のテストを増やす。

## 総合評価

8/10

既存テストは `9 passed`。構成はシンプルで SQL の組み立ても安全寄りですが、更新時 `null` とスケール面の詰めが残っています。
