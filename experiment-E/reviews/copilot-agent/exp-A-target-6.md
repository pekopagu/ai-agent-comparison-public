# コードレビュー: target-6

対象: `targets-A/target-6/task-app`（FastAPI + SQLAlchemy バックエンド / Vue 3 フロントエンド）

## 概要
基本的な CRUD・フィルタ・ソートは動作する。ただしクエリパラメータの検証を手動で行っている点や Pydantic v2 の非推奨 API 使用など、他ターゲットに比べ設計の粗さが目立つ。

---

## 問題点

### 1. クエリ検証が手動・不一致な挙動（重大度: high）
`get_tasks` は `status` / `priority` / `sort` / `order` を素の `str` で受け、手動チェックしている。
- 不正な `status`/`priority` は **400** を返す（FastAPI のバリデーション標準である 422 と不一致）。
- 不正な `sort` は **エラーにせず** `created_at desc` に**サイレントフォールバック**する。利用者は誤ったパラメータに気付けず、意図しない並び順を正しい結果と誤認する。
`Literal`/`Enum` を型注釈に使えば 422 で一貫し、サイレント挙動も排除できる。

### 2. 空白のみのタイトルを許容（重大度: medium）
`schemas.py` は `Field(..., min_length=1)` のみで `strip` 検証がない。`"   "` は通過し空タイトルのタスクが作成可能。サーバー側での `field_validator` による検証が必要。

### 3. Pydantic v2 非推奨 API の使用（重大度: medium）
`TaskResponse` が `class Config: from_attributes = True` を使用（v2 では `model_config = ConfigDict(...)` が推奨で非推奨警告対象）。また `TaskResponse` が `TaskBase` を継承せずフィールドを重複定義しており DRY 違反。`database.py` も `sqlalchemy.ext.declarative.declarative_base`（非推奨）を使用。

### 4. DELETE が 200 + ボディを返す（重大度: low）
`delete_task` は `{"detail": "Task deleted"}` を 200 で返す。削除は 204 No Content が REST 慣習。

### 5. `due_date` ソート時の NULL 未制御 / `created_at` が naive ローカル時刻（重大度: low）
NULL の並び位置が既定依存。`created_at` は `datetime.datetime.now`（TZ なしローカル）で UTC 化が望ましい。

### 6. 依存バージョンが未固定（重大度: low）
`requirements.txt` がバージョン指定なし（`fastapi` 等）。再現性が低く、将来の破壊的変更で動作不能になりうる。target-2/3 のようなピン留めが望ましい。

---

## テストの網羅性
- 作成・バリデーション（空/不正status/不正priority）・フィルタ・ソート（due_date/priority asc・desc）・取得・404・更新・削除を一通り網羅。
- 不足: 手動検証パス（不正 status での 400、不正 sort のフォールバック）の確認、空白のみタイトルの拒否、部分更新で他項目保持、`due_date` NULL ソート。

## 改善提案
- クエリパラメータを `Literal`/`Enum` 型注釈に変更し、検証と 422 応答を FastAPI に委譲。不正 sort は明示エラー化。
- `title` に `strip` 検証を追加。
- `ConfigDict` へ移行し、`TaskResponse` は `TaskBase` を継承。`declarative_base` も新 API へ。
- DELETE を 204 化。
- `requirements.txt` をバージョン固定。

## 総合評価
**6 / 10**

機能は満たすが、手動クエリ検証によるサイレントフォールバック・非推奨 API・依存未固定など、堅牢性と保守性の面で本群中もっとも改善余地が大きい。
