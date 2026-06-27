# コードレビュー結果: target-3

## 1. 問題点

### コードの可読性・保守性
*   **タスク更新時の部分更新（PATCH）が不可 (重大度: medium)**
    *   `schemas.py` の `TaskUpdate(TaskBase)` は、`TaskBase` の必須項目（`title` など）をそのまま引き継いでいます。そのため、`main.py` の `update_task` エンドポイントにおいて、例えばステータスのみを更新したい場合であっても、すべての項目（`title`, `status`, `priority` 等）を送信しなければバリデーションエラーになります。一般的には、更新用スキーマ（`TaskUpdate`）の各フィールドは `Optional`（`None`許容）にするべきです。
*   **フロントエンドのサマリー集計バグ (重大度: medium)**
    *   `index.html` 内のサマリー（全件・todo・doing・done）の件数計算が、サーバーから取得した `tasks` （フィルタ適用後のリスト）をベースに算出されています。このため、画面で「進行中 (doing)」などのフィルタをかけた際に、データベース全体の統計数が狂ってしまい、正しく表示されません。

### セキュリティ上の問題
*   **CORS 設定のハードコード (重大度: medium)**
    *   `main.py` において、`allow_origins=["http://localhost:3000"]` とフロントエンドの接続先がハードコードされています。開発環境のポート変更や、別ホスト（`127.0.0.1:3000` など）からの接続時に CORS エラーを引き起こす可能性があります。環境変数等で変更できるようにするか、許可リストを拡充すべきです。

---

## 2. 改善提案

1.  **更新用スキーマの修正 (`schemas.py`)**
    `TaskUpdate` は `TaskBase` を直接継承するのではなく、独自に定義するか、もしくは Pydantic の機能を用いてフィールドをオプショナルにします。
    ```python
    class TaskUpdate(BaseModel):
        title: str | None = Field(default=None, min_length=1, max_length=255)
        description: str | None = None
        status: TaskStatus | None = None
        priority: TaskPriority | None = None
        due_date: date | None = None
        
        # 個別のトリム・空白チェックバリデーターも同様に定義
    ```

2.  **フロントエンドサマリー集計の修正 (`index.html`)**
    *   `target-5` で行われているアプローチのように、フィルタされた `tasks` とは別に、全件取得したデータを保持する変数（例：`allTasks`）を定義し、サマリーの計算には `allTasks` を使用するように修正します。

3.  **CORS 設定の拡充 (`main.py`)**
    *   ローカル開発で一般的な `http://127.0.0.1:3000` やその他のポートからのアクセスを許容するように変更します。

---

## 3. 総合評価

### **8 / 10 点**
*   **評価理由**:
    SQLAlchemy 2.0 に準拠した `Mapped` や `DeclarativeBase` の使用、インメモリ SQLite を使用した適切なテスト設計など、バックエンドコードの設計品質は今回対象となったターゲットの中で非常に高いです。しかし、部分更新ができないスキーマ設計と、フロント側のサマリーバグがマイナスポイントとなっています。
