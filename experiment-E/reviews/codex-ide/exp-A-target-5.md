# target-5 レビュー

## 問題点

- high: テストが収集時点で失敗します。`tests/test_api.py:11` が `database` を import しますが、テスト実行時に backend ディレクトリが import path に追加されていません。`pytest -q tests` は `ModuleNotFoundError: No module named 'database'` で停止しました。
- medium: `GET /tasks` が全件を無制限に返します（`main.py:73-76`）。SQLite 直書き実装でも件数増加時の性能問題は同じです。
- medium: SQL の `ORDER BY` 句を f-string で組み立てています（`main.py:73`）。`sort` / `order` は `Literal` で制限されているため現状の注入リスクは低いですが、将来パラメータが増えた際に危険なパターンです。
- low: DB 初期化が lifespan と module import の両方で呼ばれています（`main.py:15-18`, `main.py:142`）。import だけで DB ファイル作成が走るため、テストやツール実行時の副作用が大きいです。
- low: `TASK_APP_DB` の値をそのまま DB パスとして使い、親ディレクトリも作成します（`database.py:13-26`）。設定としては便利ですが、実行環境で環境変数を制御できる場合は意図しない場所へのファイル作成につながります。

## 改善提案

- `tests/test_api.py` の先頭で backend ディレクトリを `sys.path.insert(0, ...)` する、またはパッケージ化して `python -m pytest` で安定して import できる構成にする。
- 一覧 API にページングを追加する。
- `ORDER BY` は許可済みキーから SQL 断片を辞書で選択し、f-string に直接ユーザー入力由来の値を混ぜない方針を徹底する。
- `init_db()` は lifespan に一本化し、import 時の呼び出しを避ける。
- DB パスは設定バリデーションを入れ、少なくとも本番では許可ディレクトリ配下に制限する。

## テストの網羅性

`pytest -q tests` は import error で 1 error でした。テスト内容自体も 6 件で、無効な sort/order、空の更新、ページング、大量データ、フロントエンドは未検証です。

## 総合評価

6/10
