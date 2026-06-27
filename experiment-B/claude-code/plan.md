# タスク管理Webアプリ 開発プラン

## 1. アプリの目的・ターゲットユーザー

- **目的**: 日々の「やること」をシンプルかつ素早く登録・整理・完了できる、軽量なタスク管理アプリを提供する。
- **ターゲットユーザー**:
  - 個人で ToDo を管理したい人
  - 複雑なプロジェクト管理ツール（Jira 等）はオーバースペックと感じる人
  - 1画面で全タスクを俯瞰し、サクサク操作したい人
- **設計の方針**: 学習・デモ用途も兼ねるため、依存を最小化（FastAPI + SQLite + Vue 3 CDN）し、ビルド工程なしで動くようにする。

## 2. 機能一覧と優先順位

| 優先 | 機能 | 内容 |
|------|------|------|
| P0 | タスク作成 | タイトル・説明・優先度・期限を指定して登録 |
| P0 | タスク一覧表示 | 登録済みタスクを一覧で表示 |
| P0 | ステータス変更 | todo / doing / done を切り替え（チェック含む） |
| P0 | タスク削除 | 不要なタスクを削除 |
| P1 | タスク編集 | タイトル・説明・優先度・期限・ステータスを更新 |
| P1 | フィルタ | ステータス別に絞り込み（all / todo / doing / done）|
| P1 | 検索 | タイトル・説明のキーワード検索 |
| P1 | 統計表示 | 全体／未完了／完了件数の表示 |
| P2 | 並び替え | 優先度・期限・作成日でのソート |

## 3. データモデル設計

### Task テーブル
| カラム | 型 | 制約 | 説明 |
|--------|----|------|------|
| id | INTEGER | PK, AUTOINCREMENT | タスクID |
| title | TEXT | NOT NULL | タイトル（1〜200文字） |
| description | TEXT | NULL可 | 説明（任意） |
| status | TEXT | NOT NULL, default 'todo' | todo / doing / done |
| priority | TEXT | NOT NULL, default 'medium' | low / medium / high |
| due_date | TEXT | NULL可 | 期限（ISO日付 YYYY-MM-DD） |
| created_at | TEXT | NOT NULL | 作成日時（ISO 8601 / UTC） |
| updated_at | TEXT | NOT NULL | 更新日時（ISO 8601 / UTC） |

- ステータス・優先度は enum 的に値を制限（バリデーションは Pydantic で実施）。

## 4. APIエンドポイント設計

ベースパス: `/api`

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/tasks` | タスク一覧取得（クエリ: `status`, `q`, `sort`, `order`） |
| POST | `/api/tasks` | タスク作成 |
| GET | `/api/tasks/{id}` | タスク単体取得 |
| PUT | `/api/tasks/{id}` | タスク更新（部分更新可） |
| DELETE | `/api/tasks/{id}` | タスク削除 |
| GET | `/api/stats` | 件数統計（total / todo / doing / done） |
| GET | `/api/health` | ヘルスチェック |

- レスポンスは JSON。エラーは適切な HTTP ステータス（400 / 404 / 422）と詳細メッセージを返す。
- 静的ファイル（フロントエンド）は `/` で配信。

## 5. UIデザイン方針（レイアウト・カラー）

- **レイアウト**: シングルページ。上部にヘッダー＋統計、その下に「新規追加フォーム」、メインにタスクカードのリスト。フィルタ・検索バーをリスト上部に配置。
- **カラー**:
  - ベース: ライトグレー背景 (`#f4f6f8`) ＋ 白カード
  - アクセント: インディゴ系 (`#4f46e5`)
  - ステータス色: todo=グレー, doing=アンバー, done=グリーン
  - 優先度色: high=レッド, medium=アンバー, low=グリーン
- **UX**: レスポンシブ対応、完了タスクは打ち消し線＋淡色表示。操作は即時反映（楽観的更新ではなく API 応答後に再取得）。

## 6. 開発手順・実装順序

1. プロジェクト構成・依存定義（`requirements.txt`）
2. DB 層（`database.py`）— SQLite 接続・初期化
3. スキーマ（`schemas.py`）— Pydantic モデル
4. API 実装（`main.py`）— CRUD + stats + health + 静的配信
5. フロントエンド（`static/index.html`）— Vue 3 CDN
6. テスト（`tests/test_api.py`）— pytest + FastAPI TestClient
7. 動作確認（サーバ起動・API・UI）、README 整備

## 7. テスト方針

- **対象**: API層を pytest + `fastapi.testclient.TestClient` で検証。
- **分離**: テスト用に一時 SQLite ファイル（または独立 DB）を使い、本番 DB を汚さない。
- **観点**:
  - health / stats が正しく返る
  - タスク CRUD の正常系（作成→取得→更新→削除）
  - バリデーション異常系（空タイトル、不正な status / priority → 422）
  - 404（存在しない ID の取得・更新・削除）
  - フィルタ（status）・検索（q）・ソートの動作
- 全テストが pass することを完了条件とする。

## 構成図

```
claude-code/
├── plan.md
├── README.md
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI アプリ本体
│   ├── database.py      # SQLite 接続・初期化
│   └── schemas.py       # Pydantic スキーマ
├── static/
│   └── index.html       # Vue 3 フロントエンド
└── tests/
    └── test_api.py      # pytest API テスト
```
