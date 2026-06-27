# コードレビュー: target-6

対象: `targets-B/target-6/task-app/`
構成: FastAPI + SQLAlchemy(ORM) / Vue3(CDN) / SQLite
特徴: ステータス3状態（todo/in_progress/done）+ カンバン（ドラッグ&ドロップ）+ 優先度・検索。タグ・分析は無し。エンドポイント/モデルともコンパクト。

---

## 1. 問題点

### High

なし。

### Medium

- **モジュール直 import（パッケージ化されていない）** (`main.py:8-10`, `models.py:3`)
  `import models` / `import schemas` / `from database import ...` とトップレベル絶対 import を使用。`task-app/` をカレントにして起動しないと `ModuleNotFoundError` になり、別ディレクトリからの実行や `uvicorn package.main:app` 形式に対応できない。target-1/3/4 のようにパッケージ（`backend`/`app`）化すべき。

### Low

- **DELETE が 204 でなく 200 + ボディ** (`main.py:77-84`)
  `{"status":"success",...}` を返す。動作はするが、他ターゲット・REST 慣習（204 No Content）と不一致。フロントは `res.ok` のみ見るので実害は無い。
- **`updated_at` の二重更新** (`main.py:68` と `models.py:18` `onupdate`)
  `update_task` が手動で `updated_at` をセットし、かつモデルにも `onupdate=get_utc_now_iso` がある。結果は同じだが冗長で、どちらが正なのか分かりにくい。
- **検索 `.contains(q)` の LIKE ワイルドカード未エスケープ** (`main.py:30-33`) — パラメータ化され安全だが `%`/`_` で挙動が崩れる。
- **CORS 無し**: 同一オリジン配信のため問題なし（むしろ target-1 の過剰許可より健全）。
- **DB パスがハードコード** (`database.py:4` `sqlite:///./tasks.db`) — 相対パスで CWD 依存。環境変数で上書きできると良い。

良点:
- `status`/`priority`/`due_date` を Pydantic の `pattern` で厳格にバリデーション（不正値は 422）。
- 更新は `model_dump(exclude_unset=True)` による部分更新で、カンバンの「status だけ送る」ドラッグ操作に正しく対応。
- ORM 利用でクエリは安全。

---

## 2. 改善提案

- `app/` などのパッケージに移し相対 import（`from . import models`）または `from app.x import` に統一。
- DELETE を `204 No Content`（`Response(status_code=204)`）に統一。
- `updated_at` の更新は ORM の `onupdate` に一本化し、`main.py` の手動セットを削除。
- DB パスを環境変数化（テスト/本番切替の容易化）。
- 検索 LIKE のエスケープ対応。

---

## 3. テスト網羅性

`test_main.py` は connection+transaction を張り、テスト毎に rollback する堅実な分離パターン。create（正常）/ バリデーション異常系（空タイトル・不正priority・不正日付の 422 を3種）/ list+フィルタ+検索 / get（正常・404）/ update / delete（+削除後404）をカバーし、**異常系まで含めてバランス良い**。一方で **toggle 相当（カンバンの status 遷移=PUT で status のみ更新）の検証や、更新時 404 ケースが無い**。フロントの中核機能であるドラッグ移動の API パスがテストされていないのは惜しい。

---

## 4. 総合評価

**7 / 10**

カンバン + 優先度 + 検索を ORM でコンパクトに実装し、Pydantic `pattern` による厳格なバリデーションと `exclude_unset` の部分更新で**機能面の正しさは高い**。テストも異常系を含め良好。減点は主に**パッケージ化されていない import 構成（移植性・起動の脆さ）**と、DELETE のステータス不統一・`updated_at` 二重更新といった一貫性の粗さ。致命的な不具合は無く、実用水準だが「作り込みの丁寧さ」で target-3 に劣る。
