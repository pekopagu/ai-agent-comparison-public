# target-1 コードレビュー

## 問題点

- 重大度: medium - `backend/main.py:23` で `allow_origins=["*"]` かつ `allow_credentials=True` にしており、認証・Cookie を追加した時に危険な CORS 設定になります。現状は認証がないため直ちに漏えいする情報は限定的ですが、公開運用前提では許可 origin を明示すべきです。
- 重大度: medium - `backend/crud.py:80-81` の検索で `description` が NULL のタスクに対して `ilike` を直接適用しています。SQL では NULL 条件は不一致になるため、タイトルではなく説明だけを検索したいケースや NULL 混在時の期待値が分かりにくくなります。`coalesce(description, "")` を使うと挙動が安定します。
- 重大度: medium - `backend/crud.py:43-47` のタグ作成は `name.strip()` 後の空文字や重複名を事前検証していません。DB の UNIQUE 制約違反が `backend/main.py:86` で `str(e)` として返り、内部実装の詳細がレスポンスに出ます。
- 重大度: medium - `backend/main.py:42,49,79,86,102` で広い `except Exception` を捕捉し、例外文字列をそのまま API 応答に返しています。DB パス、SQLAlchemy 例外、制約名などが露出する可能性があります。
- 重大度: low - `backend/schemas.py:24` と `backend/schemas.py:36` でリストのデフォルト値に `[]` を使っています。Pydantic では多くの場合コピーされますが、ベストプラクティスとして `default_factory=list` の方が安全で意図も明確です。
- 重大度: low - `backend/database.py:5` の既定 DB が `sqlite:///./tasks.db` で実行ディレクトリ依存です。起動場所により別 DB が作られ、データが見えない事故につながります。
- 重大度: low - テストは CRUD・フィルタ・タグ・分析を押さえていますが、重複タグ、空白タグ、不正 status/priority、NULL description 検索、CORS/エラー応答の検証が不足しています。

## 改善提案

- CORS は環境変数などで許可 origin を明示し、資格情報が不要なら `allow_credentials=False` にする。
- API レイヤでは想定済みの入力・制約エラーを個別に処理し、内部例外文字列をそのまま返さない。
- タグ名は strip 後に空文字・重複・大文字小文字差分を検証し、IntegrityError 時もロールバックして安定した 409/422 を返す。
- DB パスはアプリディレクトリ基準にするか、環境変数を必須/明示設定にする。
- テストに異常系、DB 制約系、部分検索、タグ重複、未指定フィールド保持のケースを追加する。

## 総合評価

7/10

