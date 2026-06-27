# コードレビュー: target-4

対象: `targets-B/target-4/task-app/`
構成: FastAPI + 標準ライブラリ `sqlite3`（`Database` クラスでラップ）/ Vue3(CDN) / SQLite
特徴: タグ無しの ToDo。`Database` クラスに CRUD を集約し、`get_db` 依存でテスト時に差し替え可能。

---

## 1. 問題点

### High

なし。

### Medium

- **`with self._connect()` が接続をクローズしない（接続/FDリーク）** (`database.py:35,63,106,111,159,174,180`)
  `with sqlite3.connect(...) as conn:` の context manager は**トランザクションを commit/rollback するだけで接続を close しない**（sqlite3 の仕様）。本コードは全 CRUD でこのパターンを使い、各操作ごとに新規接続を開くため、リクエストを重ねるたびに接続オブジェクト（およびファイルハンドル）がリークする。長時間運用で `OperationalError: too many open files` 等に至りうる。
  → `try/finally: conn.close()` か、`contextlib.closing` でラップすべき。
- **モジュール import 時に副作用でDBファイル生成** (`main.py:29` `_db = Database()`)
  import しただけで `backend/tasks.db` が作られスキーマ初期化される。実際リポジトリに `tasks.db` がコミットされてしまっている。テストは `get_db` をオーバーライドして回避しているが、グローバル副作用は望ましくない。

### Low

- **LIKE 検索のワイルドカード未エスケープ** (`database.py:95-98`) — target-3 と同様。安全だが検索挙動が崩れる。
- **更新項目ゼロでも `updated_at` を更新** (`database.py:154-156`)
  空の更新でも `updated_at` だけ書き換わる。実害は小さいが意図的か曖昧。
- **`get_stats` が COUNT を 2 回** — 1 クエリ（条件付き SUM）に集約可能。軽微。

---

## 2. 改善提案

- 接続管理を `contextlib.closing(sqlite3.connect(...))` でラップし、確実に close。あるいは `Database` が単一接続を保持し再利用。
- `_db` のグローバル生成をやめ、`lifespan` 内で初期化（target-3 方式）し、`tasks.db` は `.gitignore`（既にあるが既コミット分は削除）。
- LIKE エスケープ対応。
- `due_date` 検証はあり（`field_validator` で `date.fromisoformat`）— 良点。
- `clear_due_date` で「明示的な null クリア」を扱うのは丁寧な設計。

---

## 3. テスト網羅性

**非常に充実**。create（正常/最小/空タイトル422/不正priority422/不正日付422）、list（filter all/active/completed・search）、不正filter 422、get、404、update、`due_date` の明示クリア、toggle、delete、stats と網羅度が高い。`tmp_path` のファイルDBを使う理由（`:memory:` は接続毎に別DBになる）をコメントで明記しており理解度が高い。異常系の網羅は5ターゲットでもトップクラス。

---

## 4. 総合評価

**7 / 10**

クラスでDB層を整理し、`clear_due_date` の扱いや充実した異常系テストなど設計意図が明確で可読性も高い。最大の減点は **`with`接続のクローズ漏れ（リソースリーク）** で、これは運用上の実害が出うる Medium バグ。加えて import 時副作用と `tasks.db` の混入が品質を下げる。テストの網羅性は優秀なだけに、接続管理の詰めの甘さが惜しい。
