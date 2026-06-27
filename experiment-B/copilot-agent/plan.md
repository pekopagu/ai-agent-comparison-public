# タスク管理Webアプリ 開発プラン

## 1. アプリの目的・ターゲットユーザー
- **目的**: 個人や小規模チームが日々のタスクを登録・管理し、完了状況や優先度を一目で把握できるシンプルで軽量なタスク管理ツールを提供する。
- **ターゲットユーザー**:
  - 軽量なTODO管理を求める個人ユーザー
  - タスクを素早く登録・整理したい開発者やナレッジワーカー
- **コンセプト**: インストール不要・依存最小・すぐ動く。ブラウザを開けばすぐ使える。

## 2. 機能一覧と優先順位
| 優先度 | 機能 | 説明 |
| --- | --- | --- |
| 高 | タスクのCRUD | タスクの作成・一覧取得・更新・削除 |
| 高 | 完了トグル | 完了/未完了をワンクリックで切り替え |
| 中 | 優先度 | low / medium / high の3段階 |
| 中 | 期限(due_date) | 任意で期限日を設定 |
| 中 | フィルタ | 全て / 未完了 / 完了 で絞り込み |
| 中 | 検索 | タイトル・説明文の部分一致検索 |
| 低 | 統計表示 | 全件数・未完了件数・完了件数 |

## 3. データモデル設計
### Task テーブル
| カラム | 型 | 制約 | 説明 |
| --- | --- | --- | --- |
| id | INTEGER | PK, AUTOINCREMENT | タスクID |
| title | TEXT | NOT NULL | タスク名（1〜200文字） |
| description | TEXT | NULL可 | 詳細説明 |
| completed | BOOLEAN | NOT NULL, default 0 | 完了フラグ |
| priority | TEXT | NOT NULL, default 'medium' | low / medium / high |
| due_date | TEXT | NULL可 | 期限日 (YYYY-MM-DD) |
| created_at | TEXT | NOT NULL | 作成日時 (ISO8601) |
| updated_at | TEXT | NOT NULL | 更新日時 (ISO8601) |

## 4. APIエンドポイント設計
| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | /api/health | ヘルスチェック |
| GET | /api/tasks | タスク一覧取得（filter, search クエリ対応） |
| POST | /api/tasks | タスク作成 |
| GET | /api/tasks/{id} | タスク単体取得 |
| PUT | /api/tasks/{id} | タスク更新 |
| PATCH | /api/tasks/{id}/toggle | 完了状態トグル |
| DELETE | /api/tasks/{id} | タスク削除 |
| GET | /api/stats | 統計情報取得 |

- レスポンスは JSON。エラー時は適切な HTTP ステータス（400/404/422）と detail を返す。

## 5. UIデザイン方針（レイアウト・カラー）
- **レイアウト**: 中央寄せの1カラム。ヘッダー（タイトル+統計）→ 入力フォーム → フィルタ/検索バー → タスクカード一覧。
- **カラー**:
  - アクセント: インディゴ (#4f46e5)
  - 背景: ライトグレー (#f3f4f6)
  - カード: 白 (#ffffff)
  - 優先度バッジ: high=赤系 / medium=黄系 / low=緑系
- **その他**: レスポンシブ対応、完了タスクは打ち消し線+淡色表示、ホバー効果。

## 6. 開発手順・実装順序
1. プロジェクト構成の作成（backend/ フロント静的ファイル）
2. バックエンド実装（FastAPI + SQLite、DBレイヤ、Pydanticスキーマ、ルーティング）
3. フロントエンド実装（Vue 3 CDN, index.html）
4. pytest によるAPIテスト作成
5. README.md 作成
6. 依存インストール・サーバ起動・動作確認

## 7. テスト方針
- pytest + FastAPI の TestClient を使用。
- テストごとに一時SQLite DBを使い分離（依存性オーバーライド）。
- カバー範囲:
  - ヘルスチェック
  - タスク作成（正常・バリデーションエラー）
  - 一覧取得（フィルタ・検索）
  - 単体取得（存在/404）
  - 更新（正常/404）
  - トグル
  - 削除（正常/404）
  - 統計

## 技術スタック
- バックエンド: Python 3.13 + FastAPI + SQLite（標準ライブラリ sqlite3）
- フロントエンド: Vue 3（CDN）
- テスト: pytest + httpx(TestClient)
- サーバ: uvicorn
