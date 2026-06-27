# コードレビュー: exp-B target-1

対象: `targets-B/target-1/task-app`（FastAPI + SQLAlchemy + Vue3 フロントエンド / カンバン式タスク管理）

構成: `backend/`（main, crud, models, schemas, database）+ `frontend/`（app.js, index.html, style.css）+ `backend/tests/`

---

## 問題点

### High

1. **CORS 設定が安全でない（`allow_origins=["*"]` + `allow_credentials=True`）**
   `backend/main.py` の CORS ミドルウェアで全オリジン許可とクレデンシャル許可を同時に指定しています。これは CORS 仕様上も不正（ブラウザはこの組み合わせを拒否する）で、本来は認証付きリクエストを任意オリジンへ晒すリスク設定です。同一オリジン配信（`StaticFiles` を `/` にマウント）しているため、そもそも CORS は不要か、必要でも特定オリジンに限定すべきです。

2. **ステータス・優先度の値が検証されていない**
   `schemas.py` の `status` / `priority` は `str` + `max_length` のみで、列挙値（`todo`/`in_progress`/`done`、`low`/`medium`/`high`）に制限されていません。任意文字列が DB に保存可能で、カンバン UI の前提（列の振り分け）や分析集計（`get_analytics`）の整合性が壊れます。`Enum` または `Literal` で制約すべきです。

### Medium

3. **広範な `except Exception` で内部エラーを露出**
   各エンドポイントで `except Exception as e: raise HTTPException(..., detail=str(e))` としており、スタックや DB エラーの内部詳細がクライアントに漏れます（情報漏えい）。例外は握りつぶさず、ログ出力＋汎用メッセージに置き換えるべきです。

4. **タグの get-or-create がループ内で都度コミット／競合に弱い**
   `crud.get_or_create_tags_by_name` はタグごとに `db.commit()` しており、複数タグ作成時の性能が低下します。また並行リクエストで同名タグが同時作成されると `name` の UNIQUE 制約違反（`IntegrityError`）が発生し得ますが、ハンドリングがありません。まとめてコミットし、一意制約違反をリトライ／無視する設計が望ましいです。

5. **タイムスタンプ・期限日を文字列で保存**
   `created_at`/`updated_at`/`due_date` を `String` として保持しています。`get_analytics` の期限切れ判定は ISO 文字列の辞書順比較に依存しており、フォーマット揺れ（空文字や別形式）に脆弱です。`Date`/`DateTime` 型の採用を推奨します。

### Low

6. **タグ作成の重複エラーが汎用 400 に丸められる**
   `create_tag` は UNIQUE 制約違反時も `str(e)` を返すのみで、フロント側は「重複の可能性」という曖昧なメッセージを出します。409 等の明確なステータスとメッセージが望ましいです。

7. **一覧取得にページネーションがない**
   `get_tasks` は全件返却。タスク増加時にレスポンスが肥大化します。

8. **色のバリデーションがない**
   `Tag.color` は任意文字列を受理。HEX 形式の検証（`pattern`）があると堅牢です。

---

## 改善提案

- CORS は同一オリジン配信なら削除、必要なら `allow_origins` を明示列挙し `allow_credentials` の整合を取る。
- `status`/`priority` を `Enum`（または `Literal`）化し、Pydantic レベルで 422 を返す。
- 例外処理は個別化（想定外のみログ＋500、業務エラーは適切なステータス）。`str(e)` の返却を廃止。
- タグ生成はバルク化し、UNIQUE 制約違反をハンドリング。
- 日付・時刻は `Date`/`DateTime` 型に変更し、期限切れ判定を型安全に。
- 一覧 API に `limit`/`offset`（または `Query` での上限）を追加。
- テストに「不正な status/priority で 422」「存在しないタスクの更新で 404」「タグ名の大文字小文字統合」などの異常系・境界を追加。

## テストの網羅性

`tests/test_api.py` は CRUD・各種フィルタ・タグ・分析の正常系を概ね押さえており良好です。ただし入力バリデーションの異常系（不正 status/priority、空タイトル）、`update_task`/`delete_tag` の 404、楽観的更新やドラッグ&ドロップ相当の挙動は未カバーです。スキーマに列挙制約を入れた上で異常系テストを追加すべきです。

## 総合評価

**6 / 10**

機能は一通り揃い、フロント込みで完成度は高いものの、CORS 設定の不備・列挙値未検証・内部例外の露出といった看過できない問題が残ります。スキーマ強化と例外処理の見直しで実用水準に到達します。
