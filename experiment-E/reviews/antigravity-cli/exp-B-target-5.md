# コードレビュー結果: target-5 (task-app)

## 1. 問題点

### 更新（PUT）時に一部のフィールドが指定されないとバリデーションエラーになる設計ミス (重大度: high)
- **詳細**: `schemas.py` の `TaskUpdate` は `TaskBase` を継承していますが、`TaskBase` の `title` や `description` は必須またはデフォルト空文字に固定されています。また、`app/main.py` の `api_update_task` では `payload: TaskUpdate` を受け取り、`repository.py` の `update_task` に丸ごと渡しています。この `update_task` 内では：
  ```python
  UPDATE tasks
  SET title = ?, description = ?, priority = ?, due_date = ?, completed = ?, updated_at = ?
  WHERE id = ?
  ```
  として、すべてのカラムを一括で上書き更新しています。
- **影響**: 一部フィールドのみを更新（部分更新/PATCH的な挙動）することができず、クライアント側は毎回全フィールドの最新情報を取得・送信せねばなりません。さらに、`TaskUpdate` に渡された値が指定されない場合、デフォルト値（空文字など）で既存のデータベース情報が上書きされてしまい、データが消失するリスクがあります。

### Toggle処理における並行実行時のレースコンディション (重大度: medium)
- **詳細**: `repository.py` の `toggle_task` 内で、`get_task(task_id)` を呼び出し、その結果を元にメモリ上で `completed` を判定してから `UPDATE` クエリを実行しています。
- **影響**: 同時に同じタスクにトグルが呼ばれた場合、状態のロストアップデートが発生し、意図しない状態になります。

### 外部キー制約の無効化 (重大度: low)
- **詳細**: `database.py` の `get_connection` において、他のターゲットとは異なり `PRAGMA foreign_keys = ON` の実行がありません。
- **影響**: テーブル単体では問題ありませんが、将来タグ機能などの他テーブルを追加した際、リレーショナルな整合性が保てなくなります。

### データベース接続プーリングの欠如 (重大度: low)
- **詳細**: リクエストごとに `sqlite3.connect` を開閉しており、接続プールを使用していません。
- **影響**: パフォーマンス上のボトルネックになります。

### インデックスの欠如 (重大度: low)
- **詳細**: `tasks` テーブルに主キー以外のインデックスが定義されていません。
- **影響**: タスク一覧の並び替え（`completed ASC, priority順, due_date順, created_at DESC`）が非常に複雑であるため、データ件数が多くなった場合にソート負荷が跳ね上がります。

---

## 2. 改善提案

### 部分更新に対応したスキーマ・リポジトリ設計への変更
- `TaskUpdate` のフィールドを全て `Optional`（Pydantic であれば `Optional[str] = None` など）にし、呼び出し側から値が送られてきたフィールドのみを動的にSQL文として構築して更新（`UPDATE`）するロジックに変更してください。

### トグル処理のアトミック化
- `toggle_task` は、データベース側でアトミックに完了状態を反転させるSQL文に変更します：
  ```sql
  UPDATE tasks SET completed = 1 - completed, updated_at = ? WHERE id = ?
  ```

### 外部キー制約の有効化
- `get_connection` 内で `connection.execute("PRAGMA foreign_keys = ON")` を実行し、SQLiteの参照整合性を常に担保させます。

---

## 3. 総合評価
**6.5 / 10**

コードの記述はシンプルですが、`PUT /api/tasks/{task_id}` による更新時のスキーマ定義とSQLの書き方が「全項目上書き」の前提で組まれており、部分更新をしたいユースケース（例: フロントエンドからステータスのみを更新する等）において使い勝手が悪く、データの誤上書きを引き起こしやすい脆弱な設計になっています。
