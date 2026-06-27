# コードレビュー: target-4

対象: `targets-A/target-4/task-app`
構成: FastAPI + SQLAlchemy(ORM, クラシック Column) + SQLite / Vue 3 (CDN)

---

## 概要
バランスの取れた堅実な実装。Enum によるステータス/優先度のバリデーション、部分更新(`exclude_unset`)対応、丁寧な docstring/日本語コメント、そして 5 ターゲット中で最も網羅的なテストスイートが特長。バックエンドは読みやすい。減点要因は sort/order を `str` で受けて手動検証している点などの細かな非慣用性。

---

## 問題点

### High
特になし。

### Medium
1. **`title` が空白のみを許容**
   `min_length=1` のみで `field_validator` による strip が無いため、`"   "` が保存可能。サーバ側で strip/空判定を追加すべき（target-3/5 は対応）。フロント実装にもよるが API 単体では穴になる。

2. **サマリーがフィルタ後リストから算出**
   フロントの `summary` 計算が取得済み（フィルタ適用済み）タスクに基づくため、ステータスフィルタ適用時にダッシュボードの全体件数・overdue 件数が実際の全体像とズレる。全件ベース集計に分離するのが望ましい。

### Low
3. **`sort`/`order` を `str` で受けて手動バリデーション**
   `order not in ("asc","desc")` を if で検査して 422 を raise している。`status`/`priority` 同様に `Literal`/`Enum` で受ければ FastAPI が自動で 422 を返し、OpenAPI ドキュメントにも候補が載る。慣用的でない。

4. **`case(_PRIORITY_ORDER, value=...)` の辞書呼び出し形式**
   SQLAlchemy 2.0 では位置引数の whens が推奨。現状動作するが将来の非推奨化リスク。

5. **`datetime.now()` がナイーブなローカル時刻**
   UTC 保持が望ましい。

6. **`sort` 未指定時は `id` 昇順がデフォルト**
   フロントの既定ソートは `created_at`。バックエンド単体の既定（id 昇順）と差異があり、API 仕様としての既定値が分かりにくい。`created_at` 既定に揃えると一貫する。

---

## セキュリティ / パフォーマンス
- ORM パラメータバインドで SQL インジェクションなし。
- CORS はオリジン限定で妥当。
- インデックスは PK のみ（target-3 のような status/priority/due_date への付与は無い）。件数が増えるとフィルタ/ソートが遅くなりうる。

---

## テストの網羅性
5 ターゲット中で最も充実。作成（最小/全項目）・title 必須/空・不正 status/priority・空一覧・複数件・status/priority フィルタ・priority/due_date ソート・不正 sort/order(422)・ID 取得・404・更新・**部分更新**・更新 404・更新時不正値(422)・削除・削除 404 を網羅。autouse フィクスチャで各テスト前後にテーブル再生成し分離性も確保。優秀。

---

## 改善提案
- `title`/`description` に `field_validator` を追加（strip + 空判定）。
- `sort`/`order` を `Enum`/`Literal` 化し、手動 422 を撤廃。
- 集計をフィルタ非依存（全件）に分離。
- 主要フィルタ/ソート列へインデックス付与。
- 既定ソートをフロントと統一。

---

## 総合評価: **8 / 10**
読みやすく、テストの網羅性は群を抜く。減点は空白タイトルの許容、手動パラメータ検証の非慣用性、インデックス未付与など。これらを整えれば target-3 に肉薄する品質。
