# タスク管理Webアプリ

FastAPI + SQLite のバックエンドと、Vue 3 CDN のフロントエンドで構成したタスク管理アプリです。

## 機能

- タスクの追加、一覧、詳細、編集、削除
- ステータス管理: `todo` / `doing` / `done`
- 優先度管理: `low` / `medium` / `high`
- 期限管理と期限切れ警告
- ステータス、優先度によるフィルタ
- 作成日、期限、優先度によるソート
- 全件数、ステータス別件数のサマリー

## セットアップ

```bash
cd backend
pip install -r requirements.txt
```

## 起動方法

バックエンド:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

フロントエンド:

```bash
cd frontend
python -m http.server 3000
```

ブラウザで `http://localhost:3000` を開きます。

## テスト

```bash
cd backend
pytest
```

## API

| メソッド | URL | 説明 |
|---|---|---|
| GET | `/tasks` | 一覧取得。`status`、`priority`、`sort`、`order` に対応 |
| POST | `/tasks` | 新規作成 |
| GET | `/tasks/{id}` | 詳細取得 |
| PUT | `/tasks/{id}` | 更新 |
| DELETE | `/tasks/{id}` | 削除 |
