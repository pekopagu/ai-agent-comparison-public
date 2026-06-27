# タスク管理アプリ

Python(FastAPI) + Vue 3 で構築したシンプルなタスク管理Webアプリです。
タスクのCRUD、ステータス/優先度管理、期限管理、フィルタ・ソート、期限切れ警告、サマリー表示に対応しています。

## 技術スタック

| 種別 | 技術 |
|---|---|
| バックエンド | Python 3.13 + FastAPI + SQLite (SQLAlchemy) |
| フロントエンド | Vue 3（CDN）+ CSS |
| テスト | pytest |

## ディレクトリ構成

```
task-app/
├── backend/
│   ├── main.py            # FastAPIアプリ本体・APIエンドポイント
│   ├── models.py          # SQLAlchemyモデル（Taskテーブル）
│   ├── database.py        # DB接続・セッション管理
│   ├── schemas.py         # Pydanticスキーマ（バリデーション）
│   ├── requirements.txt   # Python依存パッケージ
│   └── tests/
│       └── test_api.py    # pytestによるAPIテスト
└── frontend/
    └── index.html         # Vue 3製のシングルページUI
```

## 起動方法

### 1. バックエンド

```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- API: http://localhost:8000
- ドキュメント(Swagger UI): http://localhost:8000/docs

### 2. フロントエンド

別のターミナルを開いて、以下を実行します。

```powershell
cd frontend
python -m http.server 3000
```

- ブラウザで http://localhost:3000 を開く

> バックエンドのCORSは `http://localhost:3000` からのアクセスのみ許可しています。
> フロントエンドは必ずポート3000で起動してください。

## APIエンドポイント

| メソッド | URL | 説明 |
|---|---|---|
| GET | /tasks | 一覧取得（フィルタ・ソート対応） |
| POST | /tasks | 新規作成 |
| GET | /tasks/{id} | 詳細取得 |
| PUT | /tasks/{id} | 更新 |
| DELETE | /tasks/{id} | 削除 |

### フィルタ・ソート（GET /tasks）

| パラメータ | 値 |
|---|---|
| status | todo / doing / done |
| priority | low / medium / high |
| sort | created_at / due_date / priority |
| order | asc / desc |

例: `GET /tasks?status=todo&priority=high&sort=due_date&order=asc`

## データモデル（Task）

| フィールド | 型 | 制約 |
|---|---|---|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NULL許可 |
| status | VARCHAR(10) | NOT NULL, デフォルト: todo |
| priority | VARCHAR(10) | NOT NULL, デフォルト: medium |
| due_date | DATE | NULL許可 |
| created_at | DATETIME | NOT NULL, デフォルト: 現在時刻 |

## テスト

```powershell
cd backend
pip install -r requirements.txt
pytest
```

テストはインメモリSQLiteを使用するため、開発用DB(`tasks.db`)には影響しません。

## 主な機能

- タスクの追加・編集・削除（削除は確認ダイアログあり）
- ステータス（todo / doing / done）と優先度（low / medium / high）の色分け表示
- 期限（due_date）の管理と期限切れ警告表示
- ステータス・優先度でのフィルタ、作成日時・期限・優先度でのソート
- サマリー表示（全件数・ステータス別件数・期限切れ件数）
- フォームのバリデーションエラー表示
