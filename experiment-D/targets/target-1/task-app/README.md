# タスク管理Webアプリ (Premium Task Manager)

洗練されたガラスモーフィズムデザインを持つ、FastAPI (Python 3.13) + SQLite と Vue 3 (CDN) のタスク管理アプリケーションです。
タスクの追加・編集・削除(確認ダイアログ付き)・フィルタリング・ソート・期限切れ警告表示、および統計ダッシュボードをサポートしています。

## ディレクトリ構成

```text
task-app/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── schemas.py
│   ├── requirements.txt
│   └── tests/
│       └── test_api.py
└── frontend/
    └── index.html
```

## 起動手順

### 1. バックエンドの起動

Python 3.13 以上がインストールされている環境で、以下のコマンドを実行します。

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

バックエンドAPIが `http://localhost:8000` で起動します。
APIドキュメントは `http://localhost:8000/docs` からアクセスできます。

### 2. フロントエンドの起動

フロントエンド用の静的サーバーを起動します。

```bash
cd frontend
python -m http.server 3000
```

ブラウザで `http://localhost:3000` にアクセスしてアプリケーションを開いてください。

## テストの実行

`pytest` を使用してAPIのエンドポイントの自動テストを実行できます。

```bash
cd backend
pytest
```
