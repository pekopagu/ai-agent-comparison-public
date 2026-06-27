# コードレビュー: target-5

対象: `targets-B/target-5/task-app/`
構成: FastAPI + 標準ライブラリ `sqlite3`（関数型リポジトリ）/ Vue3(CDN) / SQLite
特徴: タグ無しの ToDo。`TASK_DB_PATH` 環境変数でDBパスを切替。リポジトリは関数群、依存注入は使わずモジュール関数を直接呼ぶ。

---

## 1. 問題点

### High

なし。

### Medium

- **`with get_connection()` が接続をクローズしない（接続/FDリーク）** (`repository.py:57,63,70,98,125,135`)
  target-4 と同根の問題。`with sqlite3.connect(...)` は commit/rollback のみで close しないため、各 CRUD 呼び出しごとに接続がリークする。`create_task` は内部で `get_task` も呼ぶため 1 リクエストで複数接続を開く。長期運用でハンドル枯渇のリスク。`closing()` 等で確実に close すべき。

- **静的ファイルのパスが相対参照（CWD依存）** (`main.py:23,28`)
  `StaticFiles(directory="static")` と `FileResponse("static/index.html")` がカレントディレクトリ基準。`task-app/` 以外から起動すると 404/起動失敗になる。target-3/4 のように `Path(__file__).resolve().parent` 基準にすべき。

### Low

- **PUT が全項目必須（部分更新不可）** (`schemas.py:22-23`)
  `TaskUpdate(TaskBase)` は `TaskBase` の全必須フィールド + `completed` を継承するため、PUT は全項目送信必須。フロントは常にフォーム全体を送るため動作はするが、`title` 等を省くと 422。REST の PUT としては許容範囲だが、API 単体では使いにくい。`exclude_unset` ベースの部分更新（target-3/4）と比べ柔軟性に欠ける。
- **LIKE 検索のワイルドカード未エスケープ** (`repository.py:40-43`) — 安全だが検索挙動が崩れる。
- **`check_same_thread=False` でスレッド安全性は接続使い捨て前提** — 接続リークが直れば問題なし。

---

## 2. 改善提案

- `contextlib.closing` で接続を確実に close、または接続を 1 箇所で管理。
- 静的パスを `BASE_DIR = Path(__file__).resolve().parent.parent` 基準に変更。
- 部分更新が必要なら `TaskUpdate` を全 Optional + `exclude_unset` に。
- LIKE エスケープ対応。
- `list_tasks` の ORDER BY（完了→優先度→期日→作成日）は表現力が高く良点。`CHECK` 制約も適切。

---

## 3. テスト網羅性

`importlib` + `monkeypatch.setenv` で `TASK_DB_PATH` を差し替え、`tmp_path` 上の独立DBでテストする構成は堅実。health / create+list / get+update+toggle+delete の一連 / フィルタ（status・priority・q）/ バリデーション（空タイトル・不正priority 422）をカバー。target-3/4 と比べると**異常系の粒度はやや粗い**（404 単体ケースや日付不正の検証が無い）が、主要パスは押さえている。

---

## 4. 総合評価

**7 / 10**

関数型リポジトリ + `CHECK` 制約 + Pydantic `Literal` で安全性は確保され、ソート順の作り込みなど丁寧さがある。一方、**接続クローズ漏れ（Medium）**と**静的パスの CWD 依存（Medium）**という運用上の弱点を抱える。PUT の全項目必須仕様も使い勝手を下げる。コアロジックは健全だが、target-3 ほどの完成度には一歩届かない。
