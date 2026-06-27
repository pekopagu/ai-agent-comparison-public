# タスク管理Webアプリ

シンプルで軽量なタスク管理Webアプリです。FastAPI + SQLite のバックエンドと、Vue 3（CDN）のフロントエンドで構成されています。

## 機能
- タスクの作成・一覧・更新・削除（CRUD）
- 完了 / 未完了のワンクリック切り替え
- 優先度（低 / 中 / 高）と期限の設定
- フィルタ（すべて / 未完了 / 完了）とキーワード検索
- 残タスク数などの統計表示

## 技術スタック
- バックエンド: Python 3.13 + FastAPI + SQLite（標準ライブラリ `sqlite3`）
- フロントエンド: Vue 3（CDN）
- テスト: pytest + FastAPI TestClient
- サーバ: uvicorn

## ディレクトリ構成
```
codex-ide/
├── backend/
│   ├── __init__.py
│   ├── main.py        # FastAPI アプリ本体・ルーティング
│   ├── database.py    # SQLite 操作レイヤ
│   └── schemas.py     # Pydantic スキーマ
├── frontend/
│   ├── index.html     # 画面（Vue テンプレート）
│   ├── app.js         # Vue アプリ
│   └── style.css      # スタイル
├── tests/
│   ├── conftest.py    # テスト用フィクスチャ
│   └── test_api.py    # API テスト
├── requirements.txt
├── plan.md            # 開発プラン
└── README.md
```

## セットアップ
```powershell
# 仮想環境の作成（任意）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 依存パッケージのインストール
python -m pip install -r requirements.txt
```

## 起動方法
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
ブラウザで http://127.0.0.1:8000 を開くとアプリが表示されます。

API ドキュメント（Swagger UI）は http://127.0.0.1:8000/docs で確認できます。

## テスト
```powershell
python -m pytest -v
```

## API エンドポイント
| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/tasks` | タスク一覧（`filter`=all/active/completed, `search`） |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{id}` | タスク単体取得 |
| PUT | `/api/tasks/{id}` | タスク更新 |
| PATCH | `/api/tasks/{id}/toggle` | 完了状態の切り替え |
| DELETE | `/api/tasks/{id}` | タスク削除 |
| GET | `/api/stats` | 統計情報 |

### タスクのデータ構造
```json
{
  "id": 1,
  "title": "牛乳を買う",
  "description": "スーパーで2本",
  "completed": false,
  "priority": "high",
  "due_date": "2026-12-31",
  "created_at": "2026-06-20T00:00:00+00:00",
  "updated_at": "2026-06-20T00:00:00+00:00"
}
```

## 備考
- データは `backend/tasks.db`（SQLite）に保存されます。初回起動時に自動生成されます。
- すべてのソースファイルは UTF-8（BOMなし）で保存されています。
