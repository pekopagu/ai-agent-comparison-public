# コードレビュー: target-5

対象: `targets-A/task-app` (target-5)
構成: FastAPI + 生 sqlite3（ORM 不使用） / Vue 3 (CDN, production build)

---

## 概要
唯一 SQLAlchemy を使わず標準の `sqlite3` で実装したターゲット。パラメータ化クエリ、CHECK 制約付きスキーマ、`field_validator` による strip、`/health` エンドポイント、環境変数による DB パス切替（テスト容易性）など、随所に堅実な配慮がある。一方で生 SQL ゆえの保守コストや、初期化の二重呼び出しなどの粗さがある。

---

## 問題点

### High
特になし。SQL は全て `?` プレースホルダでバインドされ、`sort`/`order`/`status` 等は `Literal` で検証されてから SQL に埋め込まれるため、インジェクションの懸念はない。

### Medium
1. **`init_db()` の二重呼び出し**
   モジュール末尾（`main.py` 142 行）と `lifespan` の両方で `init_db()` を実行している。冪等（`CREATE TABLE IF NOT EXISTS`）なので実害は小さいが、ライフサイクル管理として重複しており、片方（lifespan 側に一本化）にすべき。

2. **`row_to_task` が責務過多（404 を送出）**
   行→モデル変換関数が `row is None` のとき `HTTPException(404)` を投げている。`fetch_task` 専用なら成立するが、一覧取得(`list_tasks`)でも同関数を再利用しており、「マッパが HTTP 例外を投げる」設計は読み手を惑わせる。404 判定は `fetch_task` 側に分離する方が明快。

### Low
3. **未使用 import**
   `from models import ORDERS, PRIORITIES, SORT_FIELDS, STATUSES` は `main.py` で使用されていない（デッドコード）。`models.py` 自体がタプル定義のみで実質未活用。

4. **リクエストごとに新規コネクション**
   `get_connection()` を呼び出しごとに開いて閉じている。SQLite ローカル用途では許容範囲だが、コネクション管理が分散しており、依存性注入（FastAPI `Depends`）でセッション/コネクションを供給する形の方が一貫する。

5. **`due_date` NULL のソート順**
   `ORDER BY due_date` で NULL は SQLite では ASC 時に先頭へ来る。明示的な NULLS LAST 制御が無い（軽微）。

6. **インデックス未付与**
   `status`/`priority`/`due_date` にインデックスが無く、件数増加時のフィルタ/ソートが線形。

---

## セキュリティ / パフォーマンス
- パラメータ化クエリ + `Literal` 検証で SQL インジェクションなし（生 SQL 実装としては適切）。
- CHECK 制約（status/priority）により DB レベルでも整合性を担保（良い）。
- CORS は `localhost` と `127.0.0.1` の両 3000 を許可しており実用的。
- `/health` エンドポイントは運用面でプラス。

---

## テストの網羅性
作成/取得・更新（None 化含む）・削除(204)・フィルタ＋ソート(priority)・バリデーション(422)・404（GET/DELETE）をカバー。`TASK_APP_DB` 環境変数でファイル DB を切替え、各テストで unlink → init する分離設計は良い。
未カバー: due_date ソート、priority/status フィルタ単独、部分更新（送信フィールドのみ）の検証、空一覧。テスト数は target-3 と同程度で、target-4 ほど網羅的ではない。

---

## 改善提案
- `init_db()` を lifespan に一本化、モジュール末尾の呼び出しを削除。
- `row_to_task` から 404 ロジックを切り離し、`fetch_task` で None 判定。
- 未使用 import / 未活用 `models.py` を整理。
- 主要列へインデックス付与。
- DB アクセスを `Depends` ベースに集約し、コネクション管理を一元化。

---

## 総合評価: **7 / 10**
生 sqlite3 でありながらインジェクション対策・CHECK 制約・strip・health・テスト用 DB 切替と勘所を押さえた良実装。減点は init の二重化、マッパの責務過多、デッドコード、インデックス欠如。ORM 不使用ゆえの保守コストも考慮し 7 点。
