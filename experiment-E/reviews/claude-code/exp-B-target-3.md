# コードレビュー: target-3

対象: `targets-B/target-3/task-app/`
構成: FastAPI + 標準ライブラリ `sqlite3`(生SQL) / Vue3(CDN) / SQLite
特徴: タグ無しのシンプルな ToDo。`lifespan`・`app.state.database_path` でDBパスを注入可能にし、テスト容易性を確保。

---

## 1. 問題点

### High

なし。

### Medium

なし（設計・実装ともに堅実）。

### Low

- **LIKE 検索でワイルドカード未エスケープ** (`repository.py:68-71`)
  `q` に `%` や `_` が含まれると LIKE のワイルドカードとして解釈され、検索結果が直感に反する。パラメータ化されているため SQL インジェクションは無いが、`ESCAPE` 句 + エスケープ処理が望ましい。
- **ヘルスチェックでDBパスを露出** (`main.py:46-48`)
  `HealthResponse.database = str(app.state.database_path)` で絶対パスを返す。情報量としては軽微だが、本番ではサーバーのファイルパスを外部に晒す必要はない。
- **接続を毎リクエスト生成** (`database.py:43-48`)
  `get_db` がリクエスト毎に `sqlite3.connect` する。規模的に問題ないが、高頻度なら接続プール化の余地あり。`get_db` で `try/finally close` しているのは正しい（接続リークなし）。
- **PUT が全項目置換（`exclude_unset` あり）** — `update_task` は `model_dump(exclude_unset=True)` で部分更新に対応しており、これは適切。指摘ではなく良点。

---

## 2. 改善提案

- 検索の LIKE は `term.replace("%","\\%").replace("_","\\_")` 等でエスケープし `ESCAPE '\\'` を付与。
- `HealthResponse` からパスを外す、あるいはファイル名のみ・`exists` 真偽値に変更。
- （任意）規模拡大時に接続管理を見直し。

---

## 3. テスト網羅性

5ターゲット中で**最も網羅性が高い部類**。
- 正常系: health / create+get / list+summary / update / toggle / delete
- 異常系: 404（存在しないID）、422（不正 priority）
- フィルタ＆検索（status=completed / priority / q）

`tmp_path` で毎テスト独立DBを用意し、`app.state.database_path` を差し替えて後始末も行っており、テスト設計が丁寧。強いて言えば、空白タイトルの 422、ソート順（due_asc 等）の検証があると完璧。

---

## 4. 総合評価

**9 / 10**

依存を最小化（標準 `sqlite3`）しつつ、`CHECK` 制約 + Pydantic の `Enum`/`field_validator` で**多層のバリデーション**を実現。`lifespan`/`app.state` による DI でテスト容易性が高く、生SQLはすべてパラメータ化され安全。summary を 1 クエリで集計するなど効率も良い。タグ・分析・カンバンは無くスコープは小さいが、その範囲での**完成度と堅牢性は最も高い**。残る指摘は LIKE エスケープとパス露出という軽微なものに限られる。
