# コードレビュー結果: exp-B-target-6

## 1. バグ・潜在的な不具合
### インポート時の本番DB強制初期化によるテスト実行時の副作用 (重大度: medium)
`main.py` のモジュールトップレベル（ルートスコープ）で `models.Base.metadata.create_all(bind=engine)` を実行しています。
このため、テストコード `test_main.py` の冒頭で `from main import app` を実行してインポートしただけで、本番用データベース接続設定が走り、テスト実行マシンのカレントディレクトリに本番用DBである空の `tasks.db` ファイルが自動生成されてしまいます。
テストの実行がローカルのファイルシステムに対して意図しない副作用を与えるため、インフラ管理やクリーンなビルド環境の観点から望ましくない設計です。

---

## 2. セキュリティ上の問題
特になし。
SQLAlchemy (ORM) を適切に使用しており、SQLインジェクション脆弱性は排除されています。

---

## 3. パフォーマンス上の問題
### contains による部分一致検索 (重大度: low)
`main.py` の一覧取得で `contains(q)`（SQLの `LIKE '%q%'`）を使用しています。SQLiteでは前方一致以外のLIKE検索においてインデックスを利用できずフルスキャンになるため、タスク件数が増えた場合の検索処理でパフォーマンスが低下します。

---

## 4. コードの可読性・保守性
### 静的ファイルをルート（`/`）にマウントしていることによるパスの競合リスク (重大度: medium)
`main.py` にて `app.mount("/", StaticFiles(directory="static", html=True), name="static")` と、ルートパスに直接静的ファイルをマウントしています。
APIとして定義されていない任意のパス（例: `/invalid-api-path`）にアクセスした際、FastAPIは適切な404エラーを返す代わりに、静的ファイルディレクトリ（`static`）の中に一致するファイルがないか探索しに行きます。
これはAPIとしてのエラーハンドリングを阻害する原因になり、また将来的にAPIパスと静的ファイル名が競合した場合に予期しない挙動（ファイルが優先される等）を招くリスクがあります。

---

## 5. ベストプラクティスへの準拠
### `delete_task` エンドポイントが `200 OK` を返している (重大度: low)
削除処理（`DELETE`）が成功した際、レスポンスとして `{"status": "success", "message": "..."}` というJSONボディとステータス `200` を返しています。
REST APIの標準的なベストプラクティスとしては、リソースが正常に削除された場合は `204 No Content` を返却し、レスポンスボディは空にするのが一般的であり、他のターゲットの実装と比べても一貫性を欠いています。

### 静的ファイルディレクトリの相対パス依存 (重大度: medium)
静的ファイル管理（`os.path.exists("static")` およびマウント）で、カレントディレクトリからの相対パス `"static"` を利用しています。
アプリケーションを起動する場所（カレントディレクトリ）が異なると、想定外の場所に `static` フォルダが作成されたり、静的ファイルが配信できなくなったりします。

---

## 6. テストの網羅性
### テスト分離は適切に行われている (重大度: なし)
`test_main.py` では SQLAlchemy のトランザクション機能（`db.begin()` からのロールバック）と `app.dependency_overrides` を組み合わせてインメモリDB (`sqlite:///:memory:`) 上でテストを実行しています。
テスト間の隔離は非常に高いクオリティで実現されており、テスト実行の堅牢性は十分に確保されています。

---

## 改善提案

### 1. テーブル作成処理の `lifespan` への移動
モジュールのインポート時にテーブルが強制的に作られないよう、FastAPI の `lifespan` イベントを使ってアプリケーション起動時にテーブルが初期化されるように変更します。

```python
# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリケーション起動時にテーブル作成を実行
    models.Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Task Manager API", lifespan=lifespan)
```

### 2. 静的ファイルの配信方法の見直しと絶対パス化
静的ファイルディレクトリへのパスを `Path(__file__).resolve().parent / "static"` のように絶対パス化し、さらにルートへの直接マウントを避けて以下のように記述します。

```python
# main.py
from fastapi.responses import FileResponse
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent / "static"

@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")

# 静的アセット (CSS/JS) は /static 配下で配信
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

### 3. `delete_task` のステータスコードを 204 に変更

---

## 総合評価
**7 / 10 点**

### 評価理由
SQLAlchemy (ORM) が適切に設計されており、コードの構成や読みやすさは非常に洗練されています。また、テストコードにおける「インメモリDBへの差し替え」と「トランザクションロールバック」の組み合わせは非常に完成度が高く、テストは安全に実行できます。一方で、インポート時に本番DBを強制生成してしまうこと、静的ファイルのルートマウントによるAPIルートとのパス競合リスク、相対パス依存など、インフラやデプロイ時の堅牢性・仕様の一貫性の面でいくつかの改善点が見られます。
