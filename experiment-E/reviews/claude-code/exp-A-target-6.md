# コードレビュー: target-6

対象: `targets-A/target-6/task-app`
構成: FastAPI + SQLAlchemy(ORM, クラシック Column) + SQLite / Vue 3 (CDN)

---

## 概要
CRUD・フィルタ・ソート・統計を満たす動作する実装で、フロントの作り込みも厚い（1158 行）。ただしバックエンドにエラーハンドリングとレスポンスの一貫性に関する設計上の粗さが複数あり、5 ターゲットの中では完成度がやや低い。

---

## 問題点

### High
特になし（動作はする）。

### Medium
1. **クエリパラメータの検証が手動かつ HTTP ステータスが不統一**
   `get_tasks` は `status`/`priority` を `Optional[str]` で受け、`if status not in [...]: raise HTTPException(400)` と手動検証して **400** を返す。一方ボディ側（schemas の `Literal`）の不正値は FastAPI が **422** を返す。同じ「不正な enum 値」で 400 と 422 が混在し一貫性がない。`Literal`/`Enum` をクエリ型に使えば自動 422 化＋ OpenAPI 反映でき、手動検証も不要。

2. **不正な `sort` を黙ってフォールバック**
   `sort` が想定外の値だと例外を出さず `created_at desc` に握りつぶす。`order` に至っては検証が一切なく、`"desc"` 以外は全て昇順扱い。誤ったパラメータがエラーにならず気づけない。target-4 のように 422 を返すべき。

3. **`title` が空白のみを許容**
   `min_length=1` のみで strip が無く `"   "` が保存可能。サーバ側 `field_validator` での strip/空判定が必要。

4. **サマリーがフィルタ後リストから算出**
   フロントの `summary` 計算が取得済み（フィルタ適用済み）リスト基準のため、ステータスフィルタ適用時にダッシュボードの全体件数・overdue 件数がズレる。

### Low
5. **パラメータ名 `status` が `fastapi.status` を隠蔽**
   `get_tasks(status: Optional[str] = None, ...)` が import 済みの `status` を関数スコープで覆う。当該関数内では `fastapi.status` を使っていないため実害はないが、紛らわしいコードスメル。パス引数 `id` も組み込み `id` を隠蔽。

6. **レスポンス形式の不統一**
   DELETE が `200 + {"detail": "Task deleted"}` を返す（target-3/4/5 は 204 No Content）。REST 的には 204 が自然。

7. **`TaskResponse` がフィールドを重複定義**
   `TaskBase` を継承せず全フィールドを再記述しており、スキーマ変更時に二重メンテが必要（DRY 違反）。

8. **Pydantic v1 スタイルの `class Config`**
   `model_config = ConfigDict(...)`（v2 推奨）でなく `class Config: from_attributes = True` を使用。動作はするが非推奨警告の対象。

9. **`datetime.datetime.now()` がナイーブなローカル時刻**／**主要列のインデックス未付与**。

---

## セキュリティ / パフォーマンス
- ORM パラメータバインドで SQL インジェクションなし。Vue による自動エスケープで XSS なし。
- CORS は `localhost`/`127.0.0.1` 限定で妥当。
- フィルタ/ソート列にインデックスが無く、件数増加でスケールしにくい。

---

## テストの網羅性
作成・バリデーション(空/不正 status/不正 priority)・フィルタ(status/priority)・ソート(due_date/priority asc・desc)・ID 取得・404・更新・削除をカバー。基本線は押さえている。
未カバー: **更新時の 404**、**更新時の不正値(422)**、部分更新、空一覧、上記 Medium 2（黙殺フォールバック）の挙動。target-4 と比べ更新系・異常系が手薄。

---

## 改善提案
- クエリの `status`/`priority`/`sort`/`order` を `Enum`/`Literal` 化し、手動検証と黙殺フォールバックを撤廃（不正値は 422 に統一）。
- `title`/`description` に `field_validator`（strip + 空判定）を追加。
- DELETE を 204 に変更し、`TaskResponse` は `TaskBase` を継承して重複解消。
- `class Config` → `model_config = ConfigDict`、`datetime` を UTC 化、主要列へインデックス付与。
- パラメータ名 `status`/`id` のシャドーイングを回避（例: `status_filter`, `task_id`）。
- 集計をフィルタ非依存に分離。

---

## 総合評価: **6 / 10**
要件は満たし動作するが、エラー処理とレスポンスの一貫性（400/422 混在・不正値の黙殺・DELETE の戻り）に粗さがあり、スキーマ重複や v1 スタイルなど保守性面の負債もある。異常系テストも手薄。基礎は出来ているので、上記の一貫性改善で 7〜8 へ引き上げ可能。
