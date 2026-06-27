# コードレビュー: target-5

対象: `targets-A/target-5/task-app`（FastAPI + 生 sqlite3 バックエンド / Vue 3 フロントエンド）

## 概要
ORM を使わず標準ライブラリ `sqlite3` を直接利用。SQL は全てプレースホルダ（`?`）でパラメータ化されており SQL インジェクション耐性が高い。DB 側に `CHECK` 制約、`TASK_APP_DB` 環境変数によるDBパス切替、`Literal` によるクエリ検証、204 レスポンスの適切な処理など堅実。

---

## 問題点

### 1. リクエストごと（かつ1リクエスト内で複数回）の接続生成（重大度: medium）
`get_connection()` が呼ばれるたびに `sqlite3.connect` する。例えば `create_task` は INSERT 用に接続→commit 後、`fetch_task` で再接続して再取得しており、1操作で複数回の接続/切断が発生する。コネクションプールや再利用がなく、負荷時に非効率。FastAPI 依存性として接続を1リクエスト1本に束ねる設計が望ましい。

### 2. `init_db()` がインポート時とライフスパンで二重実行（重大度: medium）
`lifespan` 内に加えてモジュール末尾でも `init_db()` を呼んでいる。インポート時副作用は import 順や테스트で予期せぬDB生成を招く。ライフスパン一本化が望ましい。

### 3. `due_date` ソート時の NULL の扱いが未制御（重大度: low）
`ORDER BY due_date` の NULL 位置が既定挙動依存。明示的な末尾配置が親切。

### 4. `created_at` が `CURRENT_TIMESTAMP`（UTC 文字列・TZ なし）（重大度: low）
SQLite の `CURRENT_TIMESTAMP` は UTC だが TZ 情報を持たない文字列で保存される。クライアント側で naive datetime として解釈され、ローカル時刻と取り違える恐れ。

### 5. `models.py` がほぼ未使用の定数のみ（重大度: low）
`STATUSES`/`PRIORITIES`/`SORT_FIELDS`/`ORDERS` を定義しているが、検証は `schemas.py` の `Literal` 側で行われ重複気味。実際の参照が薄く、定義と利用の一貫性が低い。

---

## セキュリティ
- パラメータ化クエリで一貫しており、`UPDATE` の SET 句もキーは Pydantic の固定フィールド名のみのため、文字列連結による注入リスクは実質ない。良好。

## テストの網羅性
- 作成・取得・更新（due_date を None 化）・削除・フィルタ＋優先度ソート・バリデーション・404 を網羅。`fresh_db` で各テスト独立。
- 不足: 不正な `sort`/`order` 値の挙動、部分更新で他項目が保持されること、`due_date` NULL ソート、`description` 正規化、255文字超境界。

## 改善提案
- 接続を1リクエスト1本に集約（依存性注入）し、`create`/`update` 後の再取得も同一接続で実施。
- `init_db()` をライフスパンに一本化し、モジュール末尾の呼び出しを削除。
- `ORDER BY due_date` で NULL 末尾配置を明示。

## 総合評価
**7 / 10**

ORM 非依存で軽量、注入対策と DB 制約は良好。一方で接続生成の非効率と `init_db` 二重実行が設計上の弱点で、テストの観点も target-2/3 に比べやや薄い。
