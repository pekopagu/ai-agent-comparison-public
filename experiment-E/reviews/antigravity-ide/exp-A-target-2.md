# コードレビュー結果: target-2

## 1. 問題点

### 潜在的な不具合 / パフォーマンス
*   **作成日時のタイムゾーン依存 (重大度: medium)**
    *   `models.py` の `created_at = Column(DateTime, nullable=False, default=datetime.now)` において、Python の `datetime.now` がデフォルト値として指定されています。これにより、アプリケーションが起動しているサーバーのローカルタイムゾーンに依存した時間が保存されます。一般的には UTC 等の統一タイムゾーンを使用するか、DBサーバー側の時間（`sqlalchemy.sql.func.now()`）を使用するべきです。
*   **テーブルインデックスの不足 (重大度: low)**
    *   `models.py` でインデックスが `id` のみに張られています。`main.py` の `list_tasks` では `status`、`priority` によるフィルタリングや、`due_date`、`created_at` によるソートが行われるため、データ量が増加した際にパフォーマンス低下の原因になります。これら検索・ソートキーとなるカラムにインデックスを設定することを推奨します。

### セキュリティ上の問題
*   **CORS 設定のハードコード (重大度: medium)**
    *   `main.py` において、`allow_origins=["http://localhost:3000"]` とフロントエンドの接続先がハードコードされています。開発環境のポート変更や、別ホスト（`127.0.0.1:3000` など）からの接続時に CORS エラーを引き起こす可能性があります。環境変数等で変更できるようにするか、許可リストを拡充すべきです。

### ベストプラクティスへの準拠
*   **SQLAlchemy `case` 関数の古い記述 (重大度: low)**
    *   `main.py` で `case(PRIORITY_ORDER, value=models.Task.priority)` のように `case` 式の第1引数に辞書を直接渡しています。これは SQLAlchemy 2.0 では非推奨または警告の原因となるため、SQLAlchemy 推奨の `case((models.Task.priority == "low", 1), ...)` または `case(whens=...)` の形式で書くべきです。

### テストの網羅性 / 保守性
*   **テスト用 SQLite ファイルの後片付け不足 (重大度: low)**
    *   `test_api.py` では `test_tasks.db` ファイルをディスク上に作成してテストを実行していますが、テスト終了後にこのファイルが削除されず残ってしまいます。また、並列でテストが実行される場合に競合するリスクもあります。インメモリ SQLite（`sqlite://`）と `StaticPool` を用いて、ディスクに依存しない設計にすることが望ましいです。

### コードの可読性・保守性
*   **フロントエンドのサマリー集計バグ (重大度: medium)**
    *   `index.html` 内のサマリー（全件・todo・doing・done）の件数計算が、サーバーから取得した `tasks` （フィルタ適用後のリスト）をベースに算出されています。このため、画面で「完了 (done)」などのフィルタをかけた際に、データベース全体の統計数が狂ってしまい、正しく表示されません。

---

## 2. 改善提案

1.  **モデル定義の修正 (`models.py`)**
    ```python
    from sqlalchemy import Column, Date, DateTime, Integer, String, Text, Index
    from datetime import datetime, timezone
    
    class Task(Base):
        ...
        # タイムゾーンに依存しないUTC時間をデフォルトに設定
        created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
        
        # フィルタやソートのパフォーマンス向上のため、インデックスを追加
        status = Column(String(10), nullable=False, default="todo", index=True)
        priority = Column(String(10), nullable=False, default="medium", index=True)
        due_date = Column(Date, nullable=True, index=True)
    ```

2.  **SQLAlchemy `case` 文の修正 (`main.py`)**
    ```python
    priority_order = case(
        (models.Task.priority == "high", 3),
        (models.Task.priority == "medium", 2),
        (models.Task.priority == "low", 1),
        else_=0
    )
    sort_expr = priority_order
    ```

3.  **テストコードのインメモリ化 (`tests/test_api.py`)**
    ```python
    from sqlalchemy.pool import StaticPool
    
    TEST_DATABASE_URL = "sqlite://"
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    ```

4.  **フロントエンドサマリー集計の修正 (`index.html`)**
    *   タスク取得時に、フィルタを適用した `tasks` とは別に、全件のタスクデータを保持する変数（例：`allTasks`）を定義し、サマリーの計算には `allTasks` を使用するように修正します。

---

## 3. 総合評価

### **7 / 10 点**
*   **評価理由**:
    バックエンド・フロントエンドともに必要最小限の機能は実装されており、テストも高い網羅性で書かれています。しかし、サマリー表示のバグ、CORS設定の柔軟性の欠如、ディスクに残るテスト用DBファイルなど、保守性や堅牢性の面でいくつか改善の余地があります。
