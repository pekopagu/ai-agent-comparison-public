# コードレビュー: target-3

対象: `targets-A/target-3/task-app`（FastAPI + SQLAlchemy 2.0 バックエンド / Vue 3 フロントエンド）

## 概要
SQLAlchemy 2.0 スタイル（`Mapped` / `mapped_column` / `select` / `db.scalars` / `db.get`）を採用し、カラムへの index 付与、`Task.id` による安定ソート、`StaticPool` を用いた真のインメモリテストなど、モダンで質の高い実装。`pytest.ini` で `pythonpath` を設定しておりテスト実行も整っている。

---

## 問題点

### 1. PUT が全置換セマンティクスで部分更新ができない（重大度: medium）
`TaskUpdate(TaskBase)` は `TaskBase` を継承するため、`title` 必須・他フィールドはデフォルト値を持つ。さらに `update_task` は `payload.model_dump()`（`exclude_unset` なし）で全フィールドを上書きする。このため、クライアントが「status だけ変更」しようと `{"status": "doing"}` を送ると `title` 欠落で 422、`title` を付けても他の未指定項目（priority/description/due_date）がデフォルト値にリセットされ、意図しないデータ消失を招く。PUT 全置換として一貫しているとも言えるが、一般的なタスク編集 UI では部分更新（PATCH 的挙動）が期待されることが多く、仕様との齟齬になりうる。

### 2. `due_date` ソート時の NULL の扱いが未制御（重大度: low）
`Task.due_date` を直接 `asc/desc`。期限なしタスクの並び位置が NULL の既定挙動依存。明示的な末尾配置が望ましい。

### 3. `description` の strip により空文字が None 化（重大度: low）
`strip_description` が空白を `None` に正規化する。更新で「説明を空にしたい」意図とは合致するが、`""` と `None` を区別したいケースでは情報が落ちる。仕様次第。

---

## テストの網羅性
- 作成・取得、バリデーション（空白タイトル/不正status）、更新、削除、フィルタ＋ソート（status/due_date/priority）、404 を網羅。`StaticPool` で独立性も高い。
- 不足: PUT による部分更新時の他項目保持（＝上記問題1）を検証するテストがなく、全置換による消失を見逃している。`due_date` NULL ソート、255文字超境界も未確認。

## 改善提案
- 部分更新を意図するなら、`TaskUpdate` を全 Optional 化し `model_dump(exclude_unset=True)` で更新。全置換を意図するなら README に明記し、その旨のテストを追加。
- `due_date` ソートで NULL 末尾配置を明示。
- 部分更新の挙動を検証するテストを追加。

## 総合評価
**8 / 10**

技術的完成度（2.0 構文・index・安定ソート・インメモリテスト）は本群で最も高い。PUT の全置換による潜在的データ消失が唯一の実質的懸念で、仕様明確化とテスト追加で容易に解消できる。
