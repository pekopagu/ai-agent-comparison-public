# コードレビュー: exp-B target-5

対象: `targets-B/target-5/task-app`（FastAPI + 標準ライブラリ `sqlite3` + Vue3 フロントエンド）

構成: `app/`（main, repository, database, schemas）+ `static/`（index.html, app.js）+ `tests/test_api.py` + `pytest.ini`

---

## 問題点

### High

1. **DB 接続がクローズされず、リクエストごとにリーク**
   `repository.py` の各関数（`list_tasks`/`get_task`/`create_task`/`update_task`/`toggle_task`/`delete_task`）は `with get_connection() as connection:` を使っていますが、`sqlite3` の context manager は**トランザクションを確定するだけで接続を閉じません**。そのため API 呼び出しのたびに接続（ファイルハンドル）がリークし、長時間運用で枯渇する恐れがあります。`try/finally` で `connection.close()` するか、`contextlib.closing` を併用してください。

### Medium

2. **PUT が全置換セマンティクスで部分更新に未対応**
   `schemas.py` の `TaskUpdate` は `TaskBase` を継承し、`title` などが必須・`description` が既定 `""`・`completed` が既定 `False` です。`repository.update_task` は全カラムを無条件に上書きするため、クライアントが一部フィールドのみ送ると**未指定フィールドが既定値にリセット**されます（説明が消える、完了状態が戻る等）。`exclude_unset` を用いた部分更新、または全置換であることを API 仕様として明確化すべきです。

### Low

3. **静的ディレクトリを相対パス `"static"` で参照**
   `main.py` の `StaticFiles(directory="static")` と `FileResponse("static/index.html")` はカレントディレクトリ依存です。`app` ディレクトリ基準の絶対パス解決（`Path(__file__).resolve().parent.parent / "static"`）にすべきです（target-2/3 は実施済み）。

4. **検索 `LIKE` が大文字小文字を区別**
   `list_tasks` の検索は `title LIKE ?` で `LOWER()` 正規化がなく、英字の大文字小文字で取りこぼします。

5. **タイトルの空白のみ入力を許容しうる**
   スキーマは `min_length=1` のみで、`repository` 側で `title.strip()` する前にバリデーションを通過するため、空白のみのタイトルがトリム後に空文字として保存され得ます。`field_validator` でのトリム検証が望ましいです。

---

## 改善提案

- 接続管理を `try/finally`／`contextlib.closing`／依存性注入（`Depends`）のいずれかへ変更し、確実にクローズする（最優先）。
- 部分更新を意図するなら `TaskUpdate` を全項目 `Optional` 化し、`model_dump(exclude_unset=True)` で差分更新に変更。
- 静的パスを `__file__` 基準の絶対パスに修正。
- 検索を `LOWER(...) LIKE LOWER(?)` 等で大文字小文字非依存に。

## 良い点

- DB スキーマに `CHECK` 制約（priority/completed）を付与。
- すべての SQL がパラメータ化され、優先度・期限を考慮した実用的なソート順。
- ステータス/優先度のクエリは `main.py` の `pattern` で 422 検証済み。
- レイヤ分割（main / repository / schemas / database）が明快。

## テストの網羅性

`tests/test_api.py` は health・作成/一覧・取得/更新/トグル/削除・フィルタ&検索・不正入力（422）を押さえています。ただし `test_update` は**全フィールドを送っている**ため、上記の部分更新リセット問題を検出できていません。また存在しないタスクの更新/削除（404）、空白タイトルの扱い、接続リークを検出する観点が不足しています。

## 総合評価

**6 / 10**

設計の骨格（CHECK 制約・レイヤ分割・パラメータ化）は良好ですが、**接続リーク**という運用上のクリティカルな欠陥と、PUT の全置換による意図せぬデータ消失リスクが残ります。これらを修正すれば target-3 に近い品質に到達します。
