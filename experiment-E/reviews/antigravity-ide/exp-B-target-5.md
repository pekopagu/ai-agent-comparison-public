# コードレビュー結果: exp-B-target-5

## 1. バグ・潜在的な不具合
### `update_task` で未指定の項目（`completed` など）がデフォルト値で上書きされてしまうバグ (重大度: high)
`schemas.py` の `TaskUpdate` は `TaskBase` をそのまま継承した上で `completed: bool = False` と定義されています。この設計により、クライアントが一部のフィールドのみを更新したい場合であっても、すべての値をリクエストに含めて送信しなければならない「PUT型（完全上書き）」の動作を強要しています。
特に、既存の完了済みタスク（`completed = True`）のタイトルを変更しようとした際、リクエストボディに `"completed": true` を明示的に含めなかった場合、スキーマのデフォルト値である `completed = False` が適用され、データベース上のタスク状態が強制的に「未完了」に巻き戻されてしまいます。

### 更新パラメータ不足時のサーバークラッシュ（AttributeError / TypeError） (重大度: high)
`repository.py` の `update_task` では以下のようにパラメータの取得と加工を行っています。
```python
payload.title.strip()
payload.description.strip()
int(payload.completed)
```
もし `TaskUpdate` にて将来的にフィールドの省略を許可した（`Optional` にした）場合や、未定義の入力があった際に、これらの値が `None` になると `.strip()` の呼び出しで `AttributeError` が発生し、また `int(None)` によって `TypeError` が発生し、サーバーが 500 クラッシュを起こします。

---

## 2. セキュリティ上の問題
特になし。
プレースホルダーを用いたバインドパラメータ処理が行われており、SQLインジェクション対策は適切に機能しています。

---

## 3. パフォーマンス上の問題
データベースの都度開閉によるオーバーヘッドはありますが、SQLiteのファイルサイズが小さい間は大きな問題にはなりません。しかし、高並行アクセス時の競合・遅延のリスクは残されています。

---

## 4. コードの可読性・保守性
### テスト分離設計の重大な欠陥（`importlib` を用いたモジュールキャッシュ干渉） (重大度: high)
`tests/test_api.py` の `make_client` 内で、環境変数 `TASK_DB_PATH` を変更した後に `importlib.import_module("app.database")` や `"app.main"` を動的に呼び出すことで、テストごとにDBを差し替えようとしています。
しかし、Pythonのモジュールインポートはキャッシュされます。2回目以降の `import_module` 呼び出しは単にキャッシュされたモジュール（本番用や最初のテスト実行時の設定）をそのまま返してしまい、環境変数の変更が反映されません。
結果として、テストの独立性（Isolation）が失われ、テスト間でデータが干渉するだけでなく、本番用データベース（`tasks.db`）がテスト実行の副作用で上書き・破壊される極めて危険な設計になっています。

---

## 5. ベストプラクティスへの準拠
### 静的ファイル用ディレクトリの相対パス依存 (重大度: medium)
`main.py` にて `StaticFiles(directory="static")` や `FileResponse("static/index.html")` を相対パス `"static"` で直接指定しています。
このため、アプリケーションの起動時およびテスト実行時の「カレントディレクトリ」がプロジェクトルート以外の場所であった場合、静的ファイルディレクトリが見つからず、アプリの起動エラーや 404 エラーが発生します。

---

## 6. テストの網羅性
### テストの分離が機能していない (重大度: high)
前述の `importlib` によるモジュールキャッシュ問題により、テストコード全体の信頼性が失われています。テスト自体は実行できているように見えても、実行順序や環境によって偽陽性（バグがあるのにパスする）や予期しない失敗を引き起こしやすくなっています。

---

## 改善提案

### 1. `TaskUpdate` および `update_task` ロジックの部分更新（PATCH）対応
未指定の項目をデフォルト値で上書きしてしまわないよう、`TaskUpdate` の全フィールドを `Optional` かつデフォルト `None` に変更し、リポジトリ層で動的に SQL を組み立てるようにします。

```python
# app/schemas.py
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[Priority] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
```

```python
# app/repository.py (動的SQL生成)
def update_task(task_id: int, payload: TaskUpdate) -> dict[str, Any] | None:
    if get_task(task_id) is None:
        return None
        
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return get_task(task_id)
        
    fields = []
    params = []
    for key, value in updates.items():
        fields.append(f"{key} = ?")
        if key in ("title", "description") and isinstance(value, str):
            params.append(value.strip())
        elif key == "due_date" and value is not None:
            params.append(value.isoformat())
        elif key == "completed":
            params.append(1 if value else 0)
        else:
            params.append(value)
            
    fields.append("updated_at = ?")
    params.append(utc_now())
    params.append(task_id)
    
    with get_connection() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    return get_task(task_id)
```

### 2. テスト用DB差し替えの標準化
トリッキーな `importlib` によるロードを廃止し、FastAPI の `app.dependency_overrides` を使ってデータベースパスを取得する関数（または接続そのもの）をテスト用の差し替え関数にオーバーライドする設計に改善します。

### 3. 静的ファイルパスの絶対パス化
`main.py` の静的ディレクトリパス指定を `Path(__file__).resolve().parent.parent / "static"` のように絶対パス化します。

---

## 総合評価
**4 / 10 点**

### 評価理由
更新処理における「部分更新の考慮漏れ」によって、クライアントが一部のフィールドのみを更新した際に意図せずタスク完了状態が `False`（未完了）に上書きされてしまう致命的な不具合があります。また、テストコードにおける `importlib` を用いた無理のあるDB差し替え設計は、本番DBを上書きする危険性をはらんでおり、ソフトウェア全体の信頼性・品質が極めて低いと判断し、厳しい評価となりました。
