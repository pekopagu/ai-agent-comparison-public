# SleekTask - タスク管理Webアプリケーション

SleekTaskは、FastAPI (Python 3.13) + SQLite と Vue 3 (CDN) + Vanilla CSS で構築された、プレミアムで美しいデザインのシングルページタスク管理Webアプリケーションです。

---

## 主な機能
- **直感的なカンバンボード**: ドラッグ＆ドロップまたはクイック移動ボタンによるスムーズなステータス変更（未着手・進行中・完了）
- **タスク管理 (CRUD)**: 詳細な説明、優先度（高・中・低）、期限、タグの設定と編集
- **タグ管理機能**: タグの動的な作成、色指定、および削除（削除時に全タスクから自動関連解除）
- **リアルタイム検索・フィルタリング**: キーワード、ステータス、優先度、およびタグによる動的検索・絞り込み
- **進捗ダッシュボード**: 完了率の進捗ゲージ、各種ステータス別のタスク数や期限切れタスク数をリアルタイムで視覚化
- **極上のUI/UX**: ガラスモーフィズム（透過ブラー効果）と深宇宙をイメージしたダークテーマ、心地よいマイクロアニメーション

---

## ディレクトリ構成
```text
antigravity-ide/
├── backend/
│   ├── database.py       # SQLAlchemy接続・セッション設定
│   ├── models.py         # SQLAlchemyのテーブル定義 (tasks, tags, task_tags)
│   ├── schemas.py        # Pydanticモデル (リクエスト・レスポンス検証用)
│   ├── crud.py           # データベースCRUD操作・統計集計ロジック
│   ├── main.py           # FastAPI本体・ルーティング・静的ファイル配信
│   └── tests/
│       ├── conftest.py   # テスト用DB・クライアント設定 (インメモリSQLite)
│       └── test_api.py   # pytest API結合テスト
├── frontend/
│   ├── index.html        # Vue 3 CDNを使用したSPAテンプレート
│   ├── style.css         # 完全独自デザインのCSSスタイルシート
│   └── app.js            # Vue 3 アプリケーションロジック・API通信
├── plan.md               # 開発計画書
├── requirements.txt      # Python依存パッケージ
└── README.md             # 本ドキュメント
```

---

## 必要要件
- Python 3.13 以上
- 各種ブラウザ（Chrome, Edge, Firefox, Safari等）

---

## 起動方法

### 1. 依存ライブラリのインストール
ターミナルを開き、プロジェクトのルートディレクトリで以下のコマンドを実行します。
```bash
pip install -r requirements.txt
```

### 2. バックエンドサーバーの起動
Uvicornを使用してFastAPIサーバーを起動します。
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 3. アプリケーションへのアクセス
ブラウザで以下のURLを開きます。
- アプリケーション画面: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- APIドキュメント (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## テストの実行方法
`pytest`を使用してAPIの結合テストを一括実行します。テスト用には自動的にインメモリSQLiteデータベース (`sqlite:///:memory:`) が割り当てられ、ローカルの開発用データには影響を与えません。

```bash
python -m pytest backend/tests/
```

---

## API仕様

### タスク関連 (Tasks)
- `GET /api/tasks` : タスク一覧の取得 (クエリパラメータ: `status`, `priority`, `tag`, `search`)
- `POST /api/tasks` : 新規タスク作成
- `GET /api/tasks/{task_id}` : タスク詳細取得
- `PUT /api/tasks/{task_id}` : タスクの更新 (部分更新対応)
- `DELETE /api/tasks/{task_id}` : タスクの削除

### タグ関連 (Tags)
- `GET /api/tags` : タグ一覧の取得
- `POST /api/tags` : タグの新規作成
- `DELETE /api/tags/{tag_id}` : タグの削除

### 分析関連 (Analytics)
- `GET /api/analytics` : 総タスク数、完了率、状態別カウント、期限切れカウントを含む統計情報の取得
