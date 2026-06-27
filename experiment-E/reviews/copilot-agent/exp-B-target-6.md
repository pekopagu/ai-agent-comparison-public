# コードレビュー: exp-B target-6

対象: `targets-B/target-6/task-app`（FastAPI + SQLAlchemy ORM + Vue3 フロントエンド）

構成: フラット構成（main, models, schemas, database）+ `static/`（index.html, app.js）+ `test_main.py`

---

## 問題点

### High

なし。重大な不具合・脆弱性は確認できませんでした。

### Medium

1. **絶対インポート前提のフラット構成で実行ディレクトリに依存**
   `main.py` が `import models` / `import schemas` / `from database import ...` とトップレベルモジュールとして読み込み、`StaticFiles(directory="static")` も相対パスです。`task-app` ディレクトリをカレントにして起動しないと `ModuleNotFoundError` や静的配信失敗が起きます。パッケージ化（`app/` + 相対インポート）か、`__file__` 基準のパス解決にすると堅牢です。

### Low

2. **DELETE が 200 + ボディを返す（REST 慣習から外れる）**
   `delete_task` は `status_code=200` で `{"status": "success", ...}` を返します。削除は `204 No Content` が一般的です（機能上は問題なし）。

3. **`due_date` の妥当性が形式のみ（実在日付を検証しない）**
   `schemas.py` の `pattern=r"^\d{4}-\d{2}-\d{2}$"` は形式のみで、`2026-13-45` のような非実在日付を通します。`date` 型受理にすると確実です。

4. **検索 `contains(q)` がワイルドカードを素通し**
   `models.Task.title.contains(q)` は `LIKE %q%` を生成し、`q` 内の `%`/`_` がエスケープされません（SQL インジェクションではないが検索結果が直感に反する）。パラメータ自体は安全です。

5. **DB URL がハードコードで環境変数による上書き不可**
   `database.py` の `SQLALCHEMY_DATABASE_URL` は固定値。テスト用 DB の差し替えは `dependency_overrides` で対応していますが、運用設定のため環境変数化が望ましいです。

---

## 改善提案

- パッケージ化（`app/__init__.py` + 相対インポート）し、静的パスを `Path(__file__).resolve().parent / "static"` で解決。
- DELETE は `204 No Content` に変更。
- `due_date` を `date` 型受理にして実在日付を保証。
- 検索が前方/部分一致以上の要件を持つ場合はワイルドカードのエスケープを検討。
- DB 接続文字列を環境変数化。

## 良い点

- `status`/`priority`/`due_date` を Pydantic の `pattern` で検証し、不正値は 422。
- 新規作成時に `status="todo"` を強制し、クライアント指定を受け付けない安全な既定。
- 更新は `model_dump(exclude_unset=True)` による部分更新で、未指定フィールドを保持（target-5 が抱える全置換問題を回避できている）。
- SQLAlchemy ORM 利用でクエリは安全にパラメータ化。`updated_at` の `onupdate` 設定も適切。
- ステータス/優先度フィルタは `Query(pattern=...)` で検証済み。

## テストの網羅性

`test_main.py` はインメモリ DB ＋トランザクションロールバック方式で独立性を確保し、作成・バリデーション異常系（空タイトル/不正優先度/不正日付）・一覧/フィルタ/検索・ID 取得・404・更新・削除を網羅しています。不足としては、優先度フィルタの明示テスト、存在しないタスクの**更新/削除での 404**、部分更新で他フィールドが保持されることの検証が挙げられます。

## 総合評価

**7 / 10**

ORM ベースで入力検証・部分更新・安全な既定値が押さえられており、堅実な実装です。一方でフラット構成による実行ディレクトリ依存と相対パスの静的配信は移植性・保守性の面で弱く、パッケージ化とパス解決の改善が望まれます。
