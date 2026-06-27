# コードレビュー: target-1

対象: `targets-A/target-1/task-app`（FastAPI + SQLAlchemy バックエンド / Vue 3 CDN フロントエンド）

## 概要
タスク管理 CRUD・フィルタ・ソートを実装。バックエンドは `Literal` によるクエリ検証、`due_date` の NULL ソート挙動を明示的に制御しており丁寧。フロントエンドは Vue 3 で UI が作り込まれている。

---

## 問題点

### 1. バックエンドで空白のみのタイトルを許容（重大度: medium）
`schemas.py` の `title` は `Field(..., min_length=1, max_length=255)` のみで、`strip()` を伴うバリデーションがない。`"   "`（空白3文字）は `min_length=1` を通過するため、空タイトルのタスクが API 経由で作成できる。フロントは `trim()` するが、API を直接叩けば回避される。バリデーションはサーバー境界で行うべき。

### 2. 統計取得のための追加全件フェッチ（重大度: medium）
`calculateStats()` が `updateAll()` のたびに `GET /tasks`（フィルタなし全件）を別途実行する。`fetchTasks()` と合わせて毎回2リクエストが飛び、件数が増えると非効率。また2リクエスト間でデータが変わるとサマリーと一覧が不整合になりうる。

### 3. `created_at` がローカル naive 時刻（重大度: low）
`models.py` の `default=datetime.now` はタイムゾーン非対応のローカル時刻。サーバーのTZに依存し、フロントの `new Date()` パースと組み合わせると表示ずれの恐れ。UTC（`datetime.now(timezone.utc)`）推奨。

### 4. PUT 更新時にタイトルの空白チェックが弱い（重大度: low）
`TaskUpdate.title` も `min_length=1` のみで `strip` 検証がなく、更新で空白タイトルに変更可能。

### 5. トーストが単一要素（重大度: low）
`toast` は単一オブジェクトで、連続操作時に通知が上書きされる。配列管理が望ましい。

### 6. CORS 設定とフロント配信元の不一致（重大度: low）
`allow_origins=["http://localhost:3000"]` だが、フロントの `API_URL` は `:8000`。フロントを 3000 以外（ファイル直開き等）で開くと CORS で弾かれる可能性。

---

## テストの網羅性
- 作成・取得・更新・削除・404・フィルタ・ソート（priority/due_date）と主要パスを網羅。
- 不足: 空白のみタイトルの拒否確認、`due_date` が NULL のソート挙動、部分更新（`exclude_unset`）の確認、不正な `sort`/`order` 値の挙動。

## 改善提案
- `schemas.py` に `field_validator("title")` を追加し `strip()` 後の空文字を 422 とする。
- サマリーは一覧と同一データソースから算出するか、専用集計エンドポイントを設けて1リクエスト化。
- `created_at` を UTC 化。
- トーストをキュー（配列）化。
- 上記の追加テストケースを補強。

## 総合評価
**7 / 10**

`due_date` の NULL ソート制御や `Literal` 検証など堅実な実装。一方でサーバー側の空白タイトル許容と統計用の二重フェッチが主な減点要因。
