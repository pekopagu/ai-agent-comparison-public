# Task Manager

FastAPI、SQLite、Vue 3 CDNで作成した軽量なタスク管理Webアプリです。

## 機能

- タスクの作成、一覧表示、編集、削除
- 完了・未完了の切り替え
- 優先度、期限、説明の管理
- 状態、優先度、キーワードによる絞り込み
- pytestによるAPIテスト

## 必要環境

- Python 3.13

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 起動

```powershell
uvicorn app.main:app --reload
```

ブラウザで `http://127.0.0.1:8000` を開きます。

## テスト

```powershell
pytest
```

## API概要

| メソッド | パス | 内容 |
| --- | --- | --- |
| GET | `/health` | ヘルスチェック |
| GET | `/api/tasks` | タスク一覧 |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{task_id}` | タスク取得 |
| PUT | `/api/tasks/{task_id}` | タスク更新 |
| PATCH | `/api/tasks/{task_id}/toggle` | 完了状態切り替え |
| DELETE | `/api/tasks/{task_id}` | タスク削除 |

## データベース

既定ではプロジェクト直下の `tasks.db` を使用します。テストや別環境でDBを分けたい場合は `TASK_DB_PATH` 環境変数でSQLiteファイルのパスを指定できます。
