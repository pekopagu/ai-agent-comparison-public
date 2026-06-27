# Task Flow

FastAPI、SQLite、Vue 3 CDNで作ったシンプルなタスク管理Webアプリです。

## 機能

- タスクの作成、一覧表示、編集、削除
- 完了・未完了の切り替え
- 優先度と期限の管理
- 状態、優先度、キーワードによる絞り込み
- 作成日、期限、優先度による並び替え
- SQLiteによる永続化
- pytestによるAPIテスト

## 必要環境

- Python 3.13
- FastAPI
- Uvicorn
- pytest

依存関係を追加する場合は次を実行します。

```bash
python -m pip install -r requirements.txt
```

## 起動方法

```bash
uvicorn app.main:app --reload
```

ブラウザで次を開きます。

```text
http://127.0.0.1:8000
```

## テスト方法

```bash
pytest
```

## 主なAPI

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/tasks` | タスク一覧取得 |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{task_id}` | タスク詳細取得 |
| PUT | `/api/tasks/{task_id}` | タスク更新 |
| PATCH | `/api/tasks/{task_id}/toggle` | 完了状態切り替え |
| DELETE | `/api/tasks/{task_id}` | タスク削除 |

`GET /api/tasks` では次のクエリを利用できます。

- `status`: `all` / `active` / `completed`
- `priority`: `low` / `medium` / `high`
- `q`: 検索キーワード
- `sort`: `created_desc` / `created_asc` / `due_asc` / `due_desc` / `priority`

## データ保存先

通常起動ではプロジェクト直下の `tasks.db` に保存します。テストでは一時ディレクトリ内のSQLiteファイルを使うため、通常データには影響しません。

## 今後の拡張候補

- タグ管理
- プロジェクト別タスク管理
- 認証とユーザー別データ
- CSVエクスポート
