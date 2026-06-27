# 📋 タスク管理Webアプリ

シンプルで軽量なタスク管理アプリです。**FastAPI + SQLite + Vue 3 (CDN)** で構成され、ビルド工程なしで動作します。

## 特徴

- タスクの作成・一覧・編集・削除（CRUD）
- ステータス管理（未着手 / 作業中 / 完了）と完了チェック
- 優先度（高 / 中 / 低）・期限の設定、期限超過の強調表示
- ステータス絞り込み・キーワード検索・並び替え（作成日 / 期限 / 優先度 / タイトル）
- 件数統計（全体 / 未着手 / 作業中 / 完了）
- レスポンシブな1画面 UI

## 技術スタック

| 層 | 技術 |
|----|------|
| バックエンド | Python 3.13 / FastAPI / SQLite (標準ライブラリ sqlite3) |
| フロントエンド | Vue 3（CDN・ビルド不要） |
| テスト | pytest / FastAPI TestClient |

## ディレクトリ構成

```
claude-code/
├── plan.md              # 開発プラン
├── README.md            # 本ファイル
├── requirements.txt     # 依存パッケージ
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI アプリ本体（API + 静的配信）
│   ├── database.py      # SQLite 接続・初期化
│   └── schemas.py       # Pydantic スキーマ
├── static/
│   └── index.html       # Vue 3 フロントエンド
└── tests/
    ├── __init__.py
    └── test_api.py      # pytest API テスト
```

## セットアップ

```bash
# （任意）仮想環境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 依存インストール
pip install -r requirements.txt
```

## 起動方法

プロジェクトルート（このファイルがあるディレクトリ）で実行します。

```bash
uvicorn app.main:app --reload
```

ブラウザで <http://127.0.0.1:8000/> を開くとアプリが表示されます。

- API ドキュメント（Swagger UI）: <http://127.0.0.1:8000/docs>
- DB ファイル `tasks.db` は初回起動時に自動生成されます。

## API 一覧

ベースパス: `/api`

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/tasks` | タスク一覧（クエリ: `status`, `q`, `sort`, `order`） |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{id}` | タスク取得 |
| PUT | `/api/tasks/{id}` | タスク更新（部分更新可） |
| DELETE | `/api/tasks/{id}` | タスク削除 |
| GET | `/api/stats` | 件数統計 |

### クエリパラメータ（GET /api/tasks）

- `status`: `todo` / `doing` / `done` で絞り込み
- `q`: タイトル・説明のキーワード検索
- `sort`: `created_at`（既定）/ `updated_at` / `due_date` / `priority` / `title` / `id`
- `order`: `asc` / `desc`（既定は `desc`）

### リクエスト例

```bash
# 作成
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"報告書を作成","priority":"high","due_date":"2026-07-01"}'

# 完了に更新
curl -X PUT http://127.0.0.1:8000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"done"}'
```

## テスト実行

```bash
pytest
```

テストは一時 SQLite DB（OS のテンポラリ領域）を使うため、本番 `tasks.db` には影響しません。

## データモデル

| カラム | 型 | 説明 |
|--------|----|------|
| id | INTEGER | タスクID（自動採番） |
| title | TEXT | タイトル（必須・1〜200文字） |
| description | TEXT | 説明（任意） |
| status | TEXT | `todo` / `doing` / `done` |
| priority | TEXT | `low` / `medium` / `high` |
| due_date | TEXT | 期限（`YYYY-MM-DD`・任意） |
| created_at | TEXT | 作成日時（ISO 8601 / UTC） |
| updated_at | TEXT | 更新日時（ISO 8601 / UTC） |

## 補足

- 外部 ORM を使わず標準ライブラリ `sqlite3` のみで実装しています（依存を最小化）。
- DB パスは環境変数 `TASKS_DB_PATH` で変更できます。
