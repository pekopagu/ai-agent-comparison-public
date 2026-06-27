# target-5 コードレビュー

## 問題点

- 重大度: high - `app/repository.py:93-121` の PUT 更新は `TaskUpdate` が `TaskBase` を継承しているため、部分更新ではなく全フィールド更新になります。`app/schemas.py:18-19` のデフォルトにより、例えば `{"completed": true}` だけを送ると title が必須で 422 になるか、送信側が不足分を補わないと既存値を維持できません。REST の PUT として全置換なら許容できますが、フロントや toggle と混在しており、部分更新を期待しやすい API です。
- 重大度: medium - `app/main.py:23` と `app/main.py:28` で静的ファイルパスが `"static"` の相対パスです。起動ディレクトリが `task-app` 以外だと静的配信が壊れます。DB は `BASE_DIR` 基準なのに静的配信だけ実行ディレクトリ依存です。
- 重大度: medium - `app/repository.py:41-45` の検索は `%` と `_` をワイルドカードとして扱い、`description LIKE ?` は NULL に弱いです。現スキーマでは description は NOT NULL DEFAULT '' ですが、将来変更時に挙動差が出ます。
- 重大度: low - `app/database.py:17` で `check_same_thread=False` を指定していますが、接続はリクエストごとに生成しており必要性が薄いです。SQLite の並行書き込み対策としては `timeout` や WAL の方が重要です。
- 重大度: low - API は `/health` だけ `/api` プレフィックス外です。設計として問題ではありませんが、target 内の他 API と一貫性がありません。
- 重大度: low - テストは主要 CRUD、フィルタ、バリデーションを押さえていますが、部分更新の仕様、静的配信の起動ディレクトリ依存、検索特殊文字、フロント操作、同時書き込みは未検証です。

## 改善提案

- 更新 API を全置換 PUT とするなら README とテストに明記し、部分更新用に PATCH を追加する。部分更新にしたいなら `TaskUpdate` は全項目 Optional にし、`exclude_unset=True` で更新する。
- 静的ファイルは `Path(__file__).resolve().parent.parent / "static"` を使って絶対パスで配信する。
- LIKE 検索は特殊文字をエスケープし、NULL 安全な条件にする。
- SQLite 接続に `timeout` と必要に応じて WAL を設定する。
- テストに「completed だけ更新」「title だけ更新」「起動ディレクトリ違いで静的配信できるか」を追加する。

## 総合評価

7/10

