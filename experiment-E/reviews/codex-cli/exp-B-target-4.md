# target-4 レビュー

## 問題点

- 重大度: medium - 更新 API で `title` や `priority` に明示的な `null` を送っても、DB 層が `None` を「未指定」と同じ扱いで無視し、200 を返します。不正な入力を成功扱いするためクライアントのバグを隠します。該当: `targets-B/target-4/task-app/backend/schemas.py:46`, `targets-B/target-4/task-app/backend/database.py:135`, `targets-B/target-4/task-app/backend/database.py:144`
- 重大度: medium - DB に `priority` や `completed` の制約がありません。API 経由では Pydantic が守りますが、`Database` クラスを直接使うテスト・管理処理・将来の別 API から不正値が保存できます。該当: `database.py:42`, `database.py:43`
- 重大度: low - DB パスが `backend/tasks.db` 固定で、環境変数などによる本番/開発/テストの切り替え口がありません。該当: `database.py:10`
- 重大度: low - 検索は `LIKE '%...%'` の全表走査で、ページングもありません。件数が増えると遅くなります。該当: `database.py:95`, `database.py:96`
- 重大度: low - テストは正常系・異常系を広く押さえていますが、明示的 `null` の扱い、DB 制約、検索の大文字小文字・空文字、並び順のテストが不足しています。

## 改善提案

- 更新スキーマで `null` を許す項目を限定し、`title/priority` の `null` は 422 にする。
- DB スキーマに `CHECK (completed IN (0, 1))` と `CHECK (priority IN ('low','medium','high'))` を追加する。
- DB パスを環境変数や設定オブジェクトで差し替え可能にする。
- 一覧 API にページングを追加し、検索対象に応じて index/FTS を検討する。
- `PUT {"title": null}` などの不正入力テストを追加する。

## 総合評価

7/10

既存テストは、通常実行では一時ディレクトリ権限により失敗しましたが、`--basetemp .pytest-tmp` 指定では `19 passed`。API の基本品質は高めですが、入力の成功/失敗 semantics と DB 制約が弱いです。
