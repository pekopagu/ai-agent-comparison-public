# コードレビュー: exp-B target-2

対象: `targets-B/target-2/task-app`（FastAPI + 標準ライブラリ `sqlite3` + Vue3 フロントエンド）

構成: `app/`（main, database, schemas）+ `static/index.html`（Vue を埋め込み）+ `tests/test_api.py`

---

## 問題点

### High

なし。重大な不具合・脆弱性は確認できませんでした。

### Medium

1. **ソート式に `priority` 以外はカラム名を直接埋め込み（ただしホワイトリストで防御済み）**
   `list_tasks` で `order_expr = sort` をそのまま SQL に文字列連結していますが、直前に `allowed_sort` のホワイトリスト検証があるため SQL インジェクションは成立しません。安全ではありますが、検証とクエリ構築箇所が離れているとリグレッションで穴が開きやすいため、ソートキー→SQL 式のマッピングを 1 つの辞書に集約するとより堅牢です。

### Low

2. **リクエストごとに DB 接続を生成・破棄**
   各エンドポイントで `get_connection()` → `conn.close()` しています。SQLite では許容範囲ですが、依存性注入（`Depends`）で接続のライフサイクルを一元管理すると重複が減り、テスト容易性も上がります。

3. **`due_date` を文字列で保持**
   検証は `date.fromisoformat` で行っており妥当ですが、保存・比較は文字列のままです。ISO 形式に限定されているため実害は小さいです。

4. **`stats` は既知ステータスのみ集計**
   `todo`/`doing`/`done` のみを合計しています。スキーマで Enum 制約済みのため未知値は入りませんが、定義の二重管理になっています。

---

## 改善提案

- ソートキーのホワイトリストと SQL 式を 1 つの `dict`（例 `SORT_EXPR = {"priority": "CASE ...", "created_at": "created_at", ...}`）に統合し、`if sort not in SORT_EXPR` で一括検証する。
- DB 接続を `Depends(get_db)` に切り出し、`try/finally` のボイラープレートを排除。
- 必要に応じて一覧にページネーション（`limit`/`offset`）を追加。

## 良い点

- すべての SQL がパラメータ化されており、SQL インジェクション対策が徹底。
- ソート・順序をホワイトリストで検証し、ユーザー入力を式に直接使わない設計。
- `Status`/`Priority` を `Enum` 化し、`due_date` も形式検証。空白タイトルも `field_validator` で弾く。
- `lifespan` で DB 初期化、`try/finally` で接続を確実にクローズ。
- 同一オリジン配信のため不要な CORS を付けていない（攻撃面を増やさない）。

## テストの網羅性

`tests/test_api.py` は health/stats、CRUD 正常系、**異常系（空タイトル・不正 status/priority・不正 due_date・各 404）**、フィルタ・検索・ソート・不正ソートキー、静的配信まで幅広く網羅しており、5 ターゲット中でも特に充実しています。部分更新で他フィールドが保持されることまで検証しており良質です。

## 総合評価

**9 / 10**

設計・セキュリティ・テストいずれも高水準で、外部 ORM に依存せず堅実に実装されています。指摘はほぼリファクタリング提案にとどまり、本番運用に最も近い品質です。
