# タスク管理Webアプリ 開発プラン

## 1. アプリの目的・ターゲットユーザー

目的は、個人または小規模チームが日々のタスクを登録し、優先度・期限・完了状態で管理できる軽量なWebアプリを提供することです。

ターゲットユーザーは、複雑なプロジェクト管理ツールまでは不要だが、ブラウザ上でタスクを素早く追加・更新・完了管理したいユーザーです。

## 2. 機能一覧と優先順位

優先度高:

- タスク一覧表示
- タスク新規作成
- タスク編集
- タスク削除
- 完了・未完了の切り替え
- 優先度、期限、説明の管理

優先度中:

- ステータス、優先度、キーワードによる絞り込み
- 期限順・優先度順を考慮した一覧表示
- APIテスト

優先度低:

- ユーザー認証
- 複数プロジェクト管理
- ドラッグアンドドロップ並び替え

今回の実装では、優先度高と優先度中を対象にします。

## 3. データモデル設計

SQLiteの `tasks` テーブルを使用します。

| カラム | 型 | 内容 |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY AUTOINCREMENT | タスクID |
| title | TEXT NOT NULL | タイトル |
| description | TEXT NOT NULL DEFAULT '' | 説明 |
| priority | TEXT NOT NULL | 優先度。low, medium, high |
| due_date | TEXT NULL | 期限日。YYYY-MM-DD |
| completed | INTEGER NOT NULL DEFAULT 0 | 完了状態。0または1 |
| created_at | TEXT NOT NULL | 作成日時。ISO 8601 |
| updated_at | TEXT NOT NULL | 更新日時。ISO 8601 |

## 4. APIエンドポイント設計

| メソッド | パス | 内容 |
| --- | --- | --- |
| GET | `/api/tasks` | タスク一覧取得。`status`, `priority`, `q` で絞り込み |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{task_id}` | タスク単体取得 |
| PUT | `/api/tasks/{task_id}` | タスク更新 |
| PATCH | `/api/tasks/{task_id}/toggle` | 完了状態切り替え |
| DELETE | `/api/tasks/{task_id}` | タスク削除 |
| GET | `/health` | ヘルスチェック |

## 5. UIデザイン方針（レイアウト・カラー）

レイアウト:

- デスクトップでは左側に入力・フィルター、右側にタスク一覧を配置
- モバイルでは縦積み表示
- タスクはカードではなく密度のあるリストとして表示し、日常的な管理画面らしくする

カラー:

- 背景は明るいグレー
- 主要操作は落ち着いた青
- 優先度は high を赤、medium を黄、low を緑で表示
- 完了済みタスクは控えめな色と取り消し線で視認性を調整

## 6. 開発手順・実装順序

1. プロジェクト構成と依存関係ファイルを作成
2. SQLite接続、テーブル作成、CRUD処理を実装
3. FastAPIのAPIエンドポイントを実装
4. Vue 3 CDNによるフロントエンドを実装
5. pytestでAPIテストを作成
6. READMEに起動方法・テスト方法を記載
7. pytestと簡易起動確認を実行

## 7. テスト方針

- `pytest` と `fastapi.testclient.TestClient` を使用
- テストごとに一時SQLite DBを使い、実データと分離
- 作成、一覧、取得、更新、完了切り替え、削除、バリデーションを確認
- フロントエンドはブラウザでの手動確認を想定し、今回はAPIの自動テストを主対象にする
