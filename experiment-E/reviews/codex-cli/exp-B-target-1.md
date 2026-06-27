# target-1 レビュー

## 問題点

- 重大度: medium - `TaskUpdate` が `title/status/priority` に明示的な `null` を許容し、`crud.update_task()` がそのまま `setattr()` するため、DB の `nullable=False` 制約に当たって 500 系エラーになり得ます。該当: `targets-B/target-1/task-app/backend/schemas.py:26`, `targets-B/target-1/task-app/backend/crud.py:117`, `targets-B/target-1/task-app/backend/models.py:17`
- 重大度: medium - `status`、`priority`、`due_date` が文字列長以外ほぼ未検証です。任意のステータスや不正日付が保存でき、フロントのカンバン列や分析集計から消えるタスクが作れます。該当: `schemas.py:19`, `schemas.py:20`, `schemas.py:21`, `crud.py:142`
- 重大度: medium - CORS が `allow_origins=["*"]` かつ `allow_credentials=True` です。認証を追加した時点で危険な設定になり、現在も不要に広い公開面です。該当: `main.py:23`, `main.py:24`
- 重大度: low - `tags: Optional[List[str]] = []`、`tags: List[Tag] = []` は可変デフォルトで、Pydantic では致命傷になりにくいものの保守上避けるべきです。該当: `schemas.py:24`, `schemas.py:38`
- 重大度: low - 例外を広く捕捉して `detail=str(e)` を返すため、DB エラーなど内部情報を API レスポンスに漏らします。該当: `main.py:38`, `main.py:83`, `main.py:99`
- 重大度: low - テストは CRUD の正常系中心で、不正な `status/priority/due_date`、更新時の `null`、重複タグ、CORS/エラー応答の検証が不足しています。

## 改善提案

- `status` と `priority` は `Enum`、`due_date` は `date | None` で受け、DB 側にも `CHECK` 制約を追加する。
- 更新 API では明示的な `null` を拒否する項目と、クリア可能な項目を分ける。`exclude_unset=True` だけでなく項目ごとのバリデーションを入れる。
- CORS は実際のフロントエンド origin に限定し、認証を使わないなら `allow_credentials=False` にする。
- Pydantic のリストデフォルトは `Field(default_factory=list)` にする。
- 例外応答は汎用メッセージにし、詳細はログへ出す。
- 異常系と境界値の API テストを追加する。

## 総合評価

6/10

既存テストは `6 passed`。基本 CRUD は動きますが、入力検証とエラー処理が甘く、データ整合性の破綻が起きやすい実装です。
