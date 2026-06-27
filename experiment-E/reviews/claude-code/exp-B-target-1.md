# コードレビュー: target-1

対象: `targets-B/target-1/task-app/`
構成: FastAPI + SQLAlchemy(ORM) / Vue3(CDN) / SQLite
特徴: タグ(多対多)・分析(analytics)・カンバン(ドラッグ&ドロップ)まで実装した最もリッチな構成。

---

## 1. 問題点

### High

なし（致命的な不具合は確認されず）。

### Medium

- **status / priority のサーバー側バリデーションが無い**
  `schemas.TaskBase.status` / `priority` は `str = Field(..., max_length=50)` のみで、許可値（`todo|in_progress|done`、`low|medium|high`）を制約していない。API 経由で `status="garbage"` のような不正値が保存でき、`get_analytics` / カンバン表示の前提が崩れる。フロントは選択肢を絞っているが API は無防備。
  → `Literal[...]` か `Enum` で制約すべき。target-3/4/5/6 では制約しているのと比べ明確に弱い。

- **CORS 設定が不適切（`allow_origins=["*"]` かつ `allow_credentials=True`）** (`main.py:21-27`)
  この組み合わせは仕様上不正で、Starlette は資格情報付きリクエストに対してリクエスト元 Origin を反射する挙動になり、実質「全オリジンから資格情報付きで許可」になる。本アプリは同一オリジン配信のため CORS 自体不要であり、この広すぎる許可は将来認証を入れた際の事故源。

- **例外詳細をクライアントに露出** (`main.py:43,50,80,87,103`)
  `except Exception as e: raise HTTPException(..., detail=str(e))` で内部例外文字列をそのまま返している。スタック内部情報・SQL エラーが漏れうる。汎用 500/400 に丸めるべき。

### Low

- **`due_date` の形式未検証**
  `due_date: Optional[str] = None` で形式チェックが無い。`get_analytics` の overdue 判定は文字列比較（`due_date < today_str`）に依存しており、`YYYY-MM-DD` 以外が入ると判定が壊れる。
- **タグ生成のたびに commit** (`crud.py:21-37`)
  `get_or_create_tags_by_name` がタグ1件ごとに `commit/refresh`。複数タグ作成や、ほぼ同時の同名タグ作成で UNIQUE 制約違反の競合（TOCTOU）が起こりうる。`flush` でまとめ、`IntegrityError` を握る方が堅牢。
- **analytics が COUNT を 6 回発行** (`crud.py:142-156`)
  `GROUP BY status` 等で 1〜2 クエリに集約可能。データ規模が小さいため実害は軽微。
- **ソートが `created_at desc` 固定**
  コメントで due_date ソートに触れているが未実装。plan の「ソート機能(低)」は未達。

---

## 2. 改善提案

- `status`/`priority` を `Enum`/`Literal` 化し、DB にも `CHECK` 制約を付与（target-3/5 を踏襲）。
- CORS ミドルウェアは削除（同一オリジン配信）、または開発時のみ限定オリジンを許可。
- 例外ハンドラは `logging` で記録し、レスポンスは固定メッセージに。
- `due_date` に `field_validator` を追加して `date.fromisoformat` で検証。
- タグ取得・分析クエリを集約してラウンドトリップ削減。
- テストに異常系（不正 status/priority、404 update、未指定フィールド維持）を追加。

---

## 3. テスト網羅性

`tests/test_api.py` は CRUD・各フィルタ・タグ・分析の正常系を一通り押さえており良好。`StaticPool` を使った in-memory 設定も正しい。ただし**異常系がほぼ無い**（422 バリデーション、404、空タイトル等）。update での「未指定フィールド維持」は検証しているのは良い。

---

## 4. 総合評価

**7 / 10**

機能の網羅性（タグ・分析・カンバン）は5ターゲット中最も高く、コード構成（crud/models/schemas/database 分離）も明快で可読性が高い。一方で **status/priority のバリデーション欠如**と **CORS/例外露出**というセキュリティ・データ整合性の弱点があり、ORM 採用にもかかわらず制約面で raw-sqlite 系（target-3/5）に劣る。異常系テストの薄さも減点要因。
