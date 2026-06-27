# コードレビュー結果: exp-B-target-4

## 1. バグ・潜在的な不具合
### `update_task` において `description` を `null` や空文字に更新できないバグ (重大度: high)
`main.py` の `update_task` で、Pydanticモデルの `payload` から `title`, `description` などを個別の名前付き引数として `db.update_task` メソッドに渡しています。
`TaskUpdate` スキーマでは `description: Optional[str] = Field(None)` となっているため、クライアントから `description` が送られなかった場合、`payload.description` は `None` になります。しかし、クライアントが「既存の説明文を消去して空にする」目的で `{"description": null}` を送信した場合も、同様に `payload.description` は `None` になります。
`database.py` の `db.update_task` では `if description is not None:` が真の場合のみ SQL UPDATE 文のカラムに追加するロジックとなっているため、`None` が渡された場合は「値の更新要求がない」と判断されてしまい、無視されます。
結果として、一度設定した `description` を空 (`NULL` や空文字) に更新することが不可能になっています。
※ `due_date` に関しては `clear_due_date` フラグを別途渡すハックで解決していますが、`description` は対策されていません。

---

## 2. セキュリティ上の問題
特になし。
`sqlite3` を使用するにあたり、プレースホルダーを用いたプリペアドステートメントによるクエリ構築が徹底されており、SQLインジェクション脆弱性はありません。

---

## 3. パフォーマンス上の問題
### `get_stats` におけるクエリの重複実行による非効率性 (重大度: medium)
`database.py` の `get_stats()` メソッド内で、全タスクの件数（`total`）と完了済みタスクの件数（`completed`）を取得するために、`SELECT COUNT(*)` クエリを別々に2回実行しています。
タスク数が増大した場合、データベースに対して2回スキャンをかけるため非効率です。1回のクエリに統合することでパフォーマンスを改善できます。

---

## 4. コードの可読性・保守性
### 更新処理における個別引数受け渡しの冗長性 (重大度: medium)
`main.py` で `payload.model_dump(exclude_unset=True)` を作成して `clear_due_date` の判定などを行っているにもかかわらず、`db.update_task` には各フィールドの値を個別引数として渡しています。この設計により、今後テーブルにカラムを追加した際に `main.py` と `database.py` の両方の引数リスト・呼出部を書き換える必要があり、保守性が低くなっています。

---

## 5. ベストプラクティスへの準拠
### 静的ファイル用ディレクトリ非存在時の処理 (重大度: low)
`main.py` の静的ファイルマウント処理で、`FRONTEND_DIR.exists()` が真のときのみ `app.mount` を実行しています。もしデプロイミスなどで `frontend` ディレクトリが存在しない場合、エラーを吐かずに無言でマウントをスキップしてしまい、ブラウザからアクセスされた際に初めて 404 エラーが出るため、インフラのデプロイミスに気付きにくくなっています。

---

## 6. テストの網羅性
### テスト用DBの分離が非常に優れている (重大度: なし)
`conftest.py` にて `tmp_path` フィクスチャを活用し、テストごとにユニークな一時ディレクトリを作成しつつ `app.dependency_overrides` を使って `get_db` 依存性を上書きしています。
他の実装ターゲットで見られたような「並列テストでのファイル競合」や「モジュールキャッシュの干渉」が発生せず、テストの分離設計は非常に高い完成度となっています。

---

## 改善提案

### 1. 更新パラメータの辞書受け渡しへのリファクタリング
`update_task` で個別引数を受け取るのをやめ、`exclude_unset=True` で出力された更新フィールド辞書をそのまま受け取って SQL を動的生成する形に変更します。これにより、`description` の `null` 更新も正しく処理でき、引数の数も減って保守性が向上します。

```python
# database.py
def update_task(self, task_id: int, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
    existing = self.get_task(task_id)
    if existing is None:
        return None
    if not updates:
        return existing

    fields = []
    params = []
    for key, value in updates.items():
        fields.append(f"{key} = ?")
        # completed の bool 変換
        if key == "completed":
            params.append(1 if value else 0)
        else:
            params.append(value)
            
    fields.append("updated_at = ?")
    params.append(_now_iso())
    params.append(task_id)
    # ... SQL 実行 ...
```

### 2. `get_stats` クエリの1回への統合
`total` と `completed` を1回のスキャンで集計するように変更します。

```python
# database.py
def get_stats(self) -> dict[str, int]:
    with self._connect() as conn:
        row = conn.execute(
            """
            SELECT 
                COUNT(*) AS total,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed
            FROM tasks
            """
        ).fetchone()
    total = row["total"] or 0
    completed = row["completed"] or 0
    return {
        "total": total,
        "completed": completed,
        "active": total - completed,
    }
```

---

## 総合評価
**7 / 10 点**

### 評価理由
`conftest.py` を用いたテスト用DBの分離が完璧に行われており、テスト実行の堅牢性はレビュー対象の中でも群を抜いて優れています。しかし、部分更新 (UPDATE) において `description` を `null` に更新できないという実用上重大なバグがあること、および `get_stats` のクエリ発行が非効率で重複している点がマイナスとなり、この点数となりました。
