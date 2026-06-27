# TaskFlow Pro (Task Management Application)

FastAPI (Python) と Vue 3 (CDN) を使った高機能かつモダンなタスク管理Webアプリケーションです。

## ディレクトリ構成
```
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

## 起動方法

### 1. バックエンドの起動
Python 3.13 以上の環境で以下の手順を実行します。

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
バックエンドAPIが `http://localhost:8000` で起動します。

### 2. フロントエンドの起動
別のターミナルを開き、以下の手順を実行します。

```bash
cd frontend
python -m http.server 3000
```
ブラウザで `http://localhost:3000` にアクセスすると、タスク管理アプリが表示されます。

## テストの実行方法
`backend` ディレクトリで以下のコマンドを実行します。

```bash
cd backend
pytest
```
