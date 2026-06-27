# タスク管理アプリ

FastAPI（バックエンド）+ Vue 3（フロントエンド）によるシンプルなタスク管理 Web アプリです。

## 機能

- タスクの CRUD（作成・取得・更新・削除）
- ステータス管理（todo / doing / done）
- 優先度管理（low / medium / high）
- 期限管理（due_date）と期限切れ警告表示
- フィルタ（ステータス・優先度）とソート（作成日時・期限・優先度 / 昇順・降順）
- ステータス・優先度の色分け表示
- サマリー表示（全件数・ステータス別件数・期限切れ件数）
- バリデーションとエラーレスポンス

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
│   ├── main.py          # FastAPI アプリ本体・エンドポイント
│   ├── models.py        # SQLAlchemy モデル
│   ├── database.py      # DB 接続・セッション
│   ├── schemas.py       # Pydantic スキーマ・バリデーション
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py  # pytest による API テスト
├── frontend/
│   └── index.html       # Vue 3 SPA
└── README.md
```

## 起動方法

### 1. バックエンド

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

- API: http://localhost:8000
- 自動生成ドキュメント（Swagger UI）: http://localhost:8000/docs

### 2. フロントエンド

別のターミナルで以下を実行します。

```bash
cd frontend
python -m http.server 3000
```

ブラウザで http://localhost:3000 を開きます。

> **注意:** フロントエンドは `http://localhost:3000`、バックエンドは `http://localhost:8000` で動作する前提です。
> バックエンドの CORS 設定で `http://localhost:3000` からのアクセスを許可しています。

## テストの実行

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

テストはインメモリではなく専用ファイル（`test_tasks.db`）を使い、本番 DB（`tasks.db`）には影響しません。

## API エンドポイント

| メソッド | URL | 説明 |
|---|---|---|
| GET | `/tasks` | 一覧取得（フィルタ・ソート対応） |
| POST | `/tasks` | 新規作成 |
| GET | `/tasks/{id}` | 詳細取得 |
| PUT | `/tasks/{id}` | 更新（部分更新可） |
| DELETE | `/tasks/{id}` | 削除 |

### GET /tasks のクエリパラメータ

| パラメータ | 値 | 説明 |
|---|---|---|
| `status` | todo / doing / done | ステータスでフィルタ |
| `priority` | low / medium / high | 優先度でフィルタ |
| `sort` | created_at / due_date / priority | 並び替えキー（既定: created_at） |
| `order` | asc / desc | 並び順（既定: asc） |

## データモデル（Task）

| フィールド | 型 | 制約 |
|---|---|---|
| id | INTEGER | 主キー, 自動採番 |
| title | VARCHAR(255) | 必須 |
| description | TEXT | 任意 |
| status | VARCHAR(10) | 必須, 既定 todo |
| priority | VARCHAR(10) | 必須, 既定 medium |
| due_date | DATE | 任意 |
| created_at | DATETIME | 必須, 既定 現在時刻 |
