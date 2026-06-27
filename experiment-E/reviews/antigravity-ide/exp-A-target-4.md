# コードレビュー結果: target-4

## 1. 問題点

### バグ・潜在的な不具合
*   **空白のみのタイトルを許容するバリデーション不備 (重大度: high)**
    *   `schemas.py` の `TaskBase` では `title: str = Field(..., min_length=1)` と定義されていますが、空白文字のみの入力（例: `"   "`）は文字数が 1 以上であるためバリデーションを通過してしまいます。これにより、中身のない空白だけのタスクが作成・更新できてしまいます。
*   **作成日時のタイムゾーン依存 (重大度: medium)**
    *   `models.py` の `created_at = Column(DateTime, nullable=False, default=datetime.now)` において、Python の `datetime.now` がデフォルト値として指定されているため、アプリケーションが起動しているサーバーのローカルタイムゾーンに依存した時間が保存されます。一般的には UTC などの絶対的な基準時間を使用すべきです。
*   **テーブルインデックスの不足 (重大度: low)**
    *   `models.py` でインデックスが `id` のみに張られています。`main.py` の `list_tasks` では `status`、`priority` によるフィルタリングや、`due_date`、`created_at` によるソートが行われるため、データ量が増加した際にパフォーマンス低下の原因になります。

### セキュリティ上の問題
*   **CORS 設定のハードコード (重大度: medium)**
    *   `main.py` において、`allow_origins=["http://localhost:3000"]` とフロントエンドの接続先がハードコードされており、開発環境のポート変更や、別ホスト（`127.0.0.1:3000` など）からの接続時に CORS エラーを引き起こす可能性があります。

### ベストプラクティスへの準拠
*   **SQLAlchemy `case` 関数の古い記述 (重大度: low)**
    *   `main.py` で `case(_PRIORITY_ORDER, value=models.Task.priority)` のように `case` 式の第1引数に辞書を直接渡しています。これは SQLAlchemy 2.0 では非推奨または警告の原因となるため、SQLAlchemy 推奨の `case((models.Task.priority == "low", 1), ...)` または `case(whens=...)` の形式で書くべきです。

### コードの可読性・保守性
*   **フロントエンドのサマリー集計バグ (重大度: medium)**
    *   `index.html` 内のサマリー（全件・todo・doing・done・期限切れ）の件数計算が、サーバーから取得した `tasks` （フィルタ適用後のリスト）をベースに算出されています。このため、画面でフィルタをかけた際に、データベース全体の統計数が狂ってしまい、正しく表示されません。

---

## 2. 改善提案

1.  **タイトルバリデーションの修正 (`schemas.py`)**
    `TaskBase` と `TaskUpdate` に、文字列をトリムし、空白のみの場合はエラーを投げる `@field_validator` を追加します。
    ```python
    from pydantic import field_validator
    
    class TaskBase(BaseModel):
        ...
        @field_validator("title")
        @classmethod
        def title_must_not_be_blank(cls, v: str) -> str:
            if not v.strip():
                raise ValueError("title must not be blank")
            return v.strip()
    ```

2.  **モデル定義の修正 (`models.py`)**
    `created_at` にタイムゾーンを考慮したUTC時間を設定し、フィルタ対象カラムにインデックスを設定します。
    ```python
    from datetime import datetime, timezone
    
    class Task(Base):
        ...
        created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
        status = Column(String(10), nullable=False, default="todo", index=True)
        priority = Column(String(10), nullable=False, default="medium", index=True)
        due_date = Column(Date, nullable=True, index=True)
    ```

3.  **フロントエンドサマリー集計の修正 (`index.html`)**
    *   フィルタされた `tasks` とは別に、全件取得したデータを保持する変数（例：`allTasks`）を定義し、サマリーの計算には `allTasks` を使用するように修正します。

---

## 3. 総合評価

### **7 / 10 点**
*   **評価理由**:
    インメモリ SQLite を使用した適切なテストコード設計や、部分更新を許可するスキーマ設計など、良い点もあります。しかし、空白文字だけのタスク作成を許容するバリデーション不備や、タイムゾーン依存、ソート・フィルタ用カラムのインデックス不足、フロント側のサマリーバグなど、堅牢性とパフォーマンスの面で多くの課題が残っています。
