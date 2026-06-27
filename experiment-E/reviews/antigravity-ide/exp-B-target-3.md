# コードレビュー結果: exp-B-target-3

## 1. バグ・潜在的な不具合
### `TaskUpdate` の一部フィールド（NOT NULLカラム）が明示的に `null` で送られた場合のDB制約違反（IntegrityError） (重大度: high)
`schemas.py` の `TaskUpdate` で `priority: Priority | None = None` や `completed: bool | None = None` のように `None` を許容しています。しかし、データベースの `tasks` テーブル定義では、`priority` に `NOT NULL` 制約および `CHECK(priority IN ('low', 'medium', 'high'))` 制約、`completed` に `NOT NULL` および `CHECK(completed IN (0, 1))` 制約が設定されています。
もしクライアントから明示的に `{"priority": null}` や `{"completed": null}` というJSONがリクエストボディとして送信された場合、Pydanticのスキーマバリデーションを通過してしまいます。そして `repository.py` の `update_task` 内でそのまま `None` をバインドして `UPDATE` クエリを実行するため、`sqlite3.IntegrityError`（NOT NULL制約違反）が発生し、サーバーが 500 Internal Server Error を返してしまいます。

---

## 2. セキュリティ上の問題
特になし。
SQLの組み立てにおいて、文字列結合ではなくバインドパラメータ（プレースホルダー）を適切に使用しており、SQLインジェクションのリスクはありません。また、ソート順の指定などもEnumで保護されています。

---

## 3. パフォーマンス上の問題
### 検索語の LOWER() 使用によるインデックスの無効化 (重大度: low)
`repository.py` の `list_tasks` で、キーワード検索処理にて `LOWER(title) LIKE ?` および `LOWER(description) LIKE ?` としています。SQLiteの `LIKE` 演算子はデフォルトで大文字小文字を区別しません（case-insensitive）。そのため、`LOWER()` 関数をカラムに適用して呼び出すと、カラムにインデックスが作成されていた場合、そのインデックスが利用できなくなりフルスキャンが発生します。

---

## 4. コードの可読性・保守性
### データベース一覧フィルタと統計情報（summary）の計算のズレ (重大度: medium)
`repository.py` の `list_tasks` において、一覧取得は `where` 条件に基づいて絞り込みを行っていますが、レスポンスの `total`, `active`, `completed` の件数を集計する `summary` クエリには `where` 条件が適用されていません。
このため、クライアントが検索キーワードやステータスで一覧を絞り込んだ場合でも、返却される統計情報は常に「データベース全体の全件数」となり、検索結果の件数と不一致が生じるため、フロントエンドの表示バグを招く原因となります。

---

## 5. ベストプラクティスへの準拠
### sqlite3 の `check_same_thread=False` 設定の危険性 (重大度: medium)
`database.py` の `connect` 内で `check_same_thread=False` を設定しています。FastAPIはマルチスレッドで動作するため、複数のリクエスト（スレッド）が同一のSQLite接続オブジェクトを共有するとデータの不整合を引き起こす危険性があります。
本コードでは `Depends(get_db)` を使ってリクエストごとに新しい接続を生成しクローズしているため現在は競合していませんが、不要な `check_same_thread=False` は、将来的に接続ライフサイクルがシングルトン等に変更された際に致命的なバグを隠蔽・誘発する恐れがあります。

---

## 6. テストの網羅性
### 境界値・異常系のテストが一部不足 (重大度: low)
テストコード `test_api.py` では基本的なCRUDやフィルタリングは検証されていますが、前述の「`priority` や `completed` に `null` を送信した際のエラーハンドリング（500エラーの発生）」はテストされていません。また、`due_date` の日付形式エラーのハンドリングテストはあるものの、`due_date` に不正な文字列が渡された場合のテストケースが不足しています。

---

## 改善提案

### 1. スキーマ定義または更新ロジックの修正
`TaskUpdate` にて `priority` や `completed` に `None` が設定された場合にDBエラーにならないよう、以下のようにスキーマ側で `None` を弾く（未指定時のみ無視されるようにする）か、リポジトリ側で `None` の場合に更新対象から除外するよう修正します。

```python
# app/schemas.py (priority の型を制限)
class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    priority: Priority | None = Field(default=None) # バリデータ等で明示的な None 入力を制限する
```

またはリポジトリ側で以下のように対応します：
```python
# app/repository.py
if key in ("priority", "completed") and value is None:
    continue # NOT NULL 制約のあるカラムに None を設定しようとした場合は無視する
```

### 2. 統計クエリへの WHERE 句の適用
`list_tasks` 内の `summary` クエリにも、一覧クエリと同様の `where_sql` と `params` を適用して集計するように変更します。

---

## 総合評価
**6 / 10 点**

### 評価理由
`repository` パターンを導入し、FastAPI の `Depends` を利用したデータベース注入、Pydantic スキーマの適切なバリデーション（特に `field_validator` によるトリミングや日付バリデーション）など、基本的な構造は非常に優れています。しかし、Pydanticスキーマ側で `None` を許容しながらDBでは `NOT NULL` にしている設計上の矛盾による IntegrityError のバグや、一覧絞り込み時に統計情報の値が連動しない仕様上の不備があるため、実用面での品質にいくつかの問題が残っています。
