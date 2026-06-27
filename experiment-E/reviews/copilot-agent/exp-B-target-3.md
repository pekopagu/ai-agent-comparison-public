# コードレビュー: exp-B target-3

対象: `targets-B/target-3/task-app`（FastAPI + 標準ライブラリ `sqlite3` + Vue3 フロントエンド）

構成: `app/`（main, repository, database, schemas）+ `static/`（index.html, app.js）+ `tests/test_api.py` + `pytest.ini`

---

## 問題点

### High

なし。重大な不具合・脆弱性は確認できませんでした。

### Medium

なし。

### Low

1. **`init_db` の接続がクローズされない**
   `database.py` の `init_db` は `with connect(...) as connection:` を使用していますが、`sqlite3` の context manager はトランザクションをコミット／ロールバックするだけで**接続自体は閉じません**。起動時 1 回のみのため実害は小さいですが、`try/finally` で明示的に `close()` するのが正確です（リクエスト処理の `get_db` は正しくクローズしています）。

2. **検索が `LOWER(...) LIKE` でインデックス非効率**
   `list_tasks` の検索は `LOWER(title) LIKE ?` で全件スキャンになります。データ量が増えると遅くなります（小規模なら問題なし）。

3. **DB 接続をリクエストごとに生成**
   `get_db` が毎回新規接続を開きます。SQLite では許容範囲ですが、規模拡大時は接続戦略の見直し余地があります。

---

## 改善提案

- `init_db` を `try/finally` で接続クローズするか、`contextlib.closing` を併用する。
- 検索の高速化が必要なら FTS5 等の全文検索インデックスを検討（現状の規模では不要）。
- `status` クエリは `StatusFilter` Enum で 422 検証されており、ソートも `SortOrder` Enum 化済みで堅牢。維持を推奨。

## 良い点

- **DB スキーマに `CHECK` 制約**（`priority IN (...)`, `completed IN (0,1)`）を付与し、アプリ層とDB層の二重防御を実現。
- すべての SQL がパラメータ化。ソート式は `SortOrder` Enum → SQL 式の辞書マッピングで安全に構築。
- 依存性注入（`Depends(get_db)`）で接続ライフサイクルを管理し、`get_db` は `finally` で確実にクローズ。
- 一覧 API が `items` に加え `total`/`active`/`completed` のサマリを返し、UI 側の集計負荷を軽減。
- `due_date` を `date` 型で受け、NULL を末尾に並べるソート（`due_date IS NULL, ...`）など細部が丁寧。
- `toggle` エンドポイントなど UX に配慮した API 設計。

## テストの網羅性

`tests/test_api.py` は `tmp_path` で独立 DB を用い、health・CRUD・サマリ付き一覧・更新・トグル・削除・404・不正 priority（422）・フィルタ&検索を網羅しています。Enum バリデーションにより不正ソート等は自動的に 422 となるため明示テストは省略されていますが、安全側に倒すなら不正 `status`/`sort` の異常系を 1 件追加するとなお良いです。

## 総合評価

**9 / 10**

レイヤ分割（main / repository / schemas / database）が明快で、DB の CHECK 制約・DI・Enum 検証・サマリ集計まで設計が洗練されています。target-2 と並ぶ高品質で、指摘は軽微な改善にとどまります。
