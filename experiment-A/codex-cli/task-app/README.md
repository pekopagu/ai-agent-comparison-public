# タスク管理Webアプリ

FastAPI + SQLite のバックエンドと、Vue 3 CDN のフロントエンドで構成したタスク管理アプリです。

## 機能

- タスクの追加、編集、削除、一覧表示
- 状態（todo / doing / done）と優先度（low / medium / high）の管理
- 期限日管理と期限切れ警告
- 状態、優先度によるフィルタ
- 作成日、期限、優先度によるソート
- 全件数と状態別件数のサマリー

## 起動方法

### バックエンド

```bash
cd task-app/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API は `http://localhost:8000` で起動します。

### フロントエンド

```bash
cd task-app/frontend
python -m http.server 3000
```

ブラウザで `http://localhost:3000` を開きます。

## テスト

```bash
cd task-app/backend
pytest
```

テストは一時的な SQLite データベースを使い、実運用用の `tasks.db` には影響しません。
