# target-4 コードレビュー

## 問題点

- 重大度: high - `backend/main.py:91-98` は `TaskUpdate` の各属性を直接 `db.update_task` に渡しており、リクエストで未指定の `description` と `due_date` が `None` になります。`backend/database.py:138-152` 側では `None` を「未指定」として扱うため、説明を明示的に `null` にして消すことができません。`due_date` だけは `clear_due_date` で特別処理されていますが、description には同等の処理がありません。
- 重大度: medium - `backend/database.py:96-99` の検索で `description LIKE ?` を直接使っており、description が NULL のタスクは説明検索の扱いが一貫しません。また `%` と `_` がワイルドカードとして解釈されます。
- 重大度: medium - `backend/database.py:10` の既定 DB パスが `backend/tasks.db` 固定で、README や運用環境での配置変更に弱いです。環境変数で切り替えられず、本番・開発・テストの分離がしにくい構成です。
- 重大度: low - `backend/database.py:154-165` は更新項目がなくても `updated_at` だけを更新します。空 PUT が成功扱いになるため、API の意図が曖昧です。
- 重大度: low - コメント・docstring が文字化けしており、`backend/main.py`、`backend/database.py`、`backend/schemas.py` の可読性を落としています。
- 重大度: low - テストは CRUD・フィルタ・トグル・統計をよく押さえていますが、description の null クリア、検索特殊文字、空 PUT、DB パス切り替え、フロント操作は未検証です。

## 改善提案

- `payload.model_dump(exclude_unset=True)` の結果をそのままリポジトリに渡し、「未指定」と「明示的な null」を区別する。description も clear フラグまたは更新 dict 方式で扱う。
- DB パスを環境変数で指定可能にし、デフォルトもアプリルート基準に整理する。
- 検索では `IFNULL(description, '')` と LIKE エスケープを使う。
- 空 PUT の扱いを 400/422、no-op、updated_at 更新のいずれかに仕様化し、テストを追加する。
- 文字化けを修正し、コメントは実装意図が必要な箇所に絞る。

## 総合評価

7/10

