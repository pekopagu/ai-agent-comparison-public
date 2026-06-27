# 実験B 共通テスト結果レポート

実施者: Claude（第三者検証者、方法B = サンドボックス内で完結実行）
実施日: 2026-06-21
実施方法: 6エージェント分のtask-app/フォルダをアップロードし、Claudeの
サンドボックス環境内でFastAPI/uvicorn/pytestを実行。サーバー起動・
テスト実行・結果記録まで全て完結させた（人間のPC操作は不要）。

---

## 背景・実施方針

実験Bは各エージェントがAPIパス・データモデルを自由設計したため、
実験Aのような単一の統一テストは適用できない。事前調査の結果、
6エージェントは以下の2グループに分かれることを確認した。

- **グループA（status3値モデル）**: Claude Code, Antigravity CLI, Antigravity IDE
- **グループB（completed2値モデル）**: Codex CLI, Codex IDE, Copilot Agent

各グループに対し、観点を統一した共通テスト（test_common_group_a.py /
test_common_group_b.py）を新規作成し、レスポンス構造の差異
（配列 vs ラッパー構造、環境変数名の違い等）を吸収するアダプタ層を
実装した上で実行した。

---

## 事前調査で判明した構造差異

| エージェント | APIパス | 一覧の構造 | DBパス切替方式 |
|---|---|---|---|
| Claude Code | /api/tasks | 配列 | 環境変数 TASKS_DB_PATH |
| Antigravity CLI | /api/tasks | 配列 | 環境変数 TASKS_DB_PATH |
| Antigravity IDE | /api/tasks | 配列 | SQLAlchemy create_all（テスト用engine差し替え） |
| Codex CLI | /api/tasks | 配列 | 環境変数 TASK_DB_PATH |
| Codex IDE | /api/tasks | **{items, total, active, completed}** | app.state.database_path |
| Copilot Agent | /api/tasks | 配列 | app.dependency_overrides（DIオーバーライド） |

全6エージェントが`/api/tasks`に収束した点は、仕様書に
プレフィックスの指定がなかったにもかかわらず一致した、興味深い
発見である（実験Aでは単に`/tasks`だった）。

---

## グループA（status3値モデル）結果

| エージェント | 結果 | 詳細 |
|---|---|---|
| Claude Code | **11 passed** | 修正なしで全合格 |
| Antigravity CLI | **11 passed** | 修正なしで全合格 |
| Antigravity IDE | **10 passed, 1 xfailed** | 不正priority値のバリデーション漏れ（新発見） |

### Antigravity IDEの新発見：priority/statusのバリデーション欠落

```python
# schemas.py（実際のコード）
status: str = Field("todo", max_length=50)
priority: str = Field("medium", max_length=50)
```

`status`/`priority`が単純な`str`型（Enum/Literal/pattern制約なし）
のため、`priority="invalid_value"`のような不正な値でも201で
タスクが作成されてしまう。実験Eの6エージェント×複数回のレビュー
でもこの観点は指摘されていなかった、共通テストならではの新発見。

---

## グループB（completed2値モデル）結果

| エージェント | 結果 | 詳細 |
|---|---|---|
| Codex CLI | **13 passed, 1 failed, 2 skipped** | **PUT部分更新の重大バグを実証** |
| Codex IDE | **16 passed** | 修正なしで全合格 |
| Copilot Agent | **16 passed** | 修正なしで全合格 |

### Codex CLIの重大バグ（実証）：PUT部分更新が機能しない

```python
# schemas.py（実際のコード）
class TaskUpdate(TaskBase):
    completed: bool = False
```

`TaskUpdate`が`TaskBase`をそのまま継承しているため、`title`が
暗黙的に必須化されている。`{"priority": "high"}`のようにtitleを
含まない部分更新を送ると、以下のエラーで422が返る。

```json
{"detail":[{"type":"missing","loc":["body","title"],
"msg":"Field required","input":{"priority":"high"}}]}
```

これは実験Eで複数のレビュアー（Antigravity IDE等）が指摘していた
問題であり、今回の共通テストで実機検証により確定的に実証された。

---

## 実験Eの指摘内容との対比（検証結果）

| 実験Eでの指摘 | 対象 | 今回の検証結果 |
|---|---|---|
| PUT部分更新が機能しない | Codex CLI | **実証された（実在するバグ）** |
| テストが本番DBを破壊する | Codex CLI | **誤検出と判明（再現せず）** |
| completedを指定しない更新でFalseに巻き戻る | 各種 | 今回のテストでは再現せず（3エージェントとも正常） |
| priority/statusのバリデーション漏れ | - | **新たに発見（Antigravity IDE）** |

実験Eのレビューは「概ね妥当だが、一部に誤検出が含まれる」ことが、
共通テストによる実機検証で改めて確認された。これは実験全体を通じて
最も重要な教訓のひとつであり、「AIによるコードレビュー（静的・
動的問わず）は、複数の手法で裏付けを取らない限り、過信してはならない」
ことを示す具体的な事例となった。

---

## 実施環境・手法上の特記事項

- 環境構築: pypi.org経由でfastapi/uvicorn/sqlalchemy/pydantic/
  pytest/playwright等をインストール。deb.nodesource.comへのアクセスは
  ブロックされていたため、Playwrightのシステム依存パッケージは
  一部インストールできなかったが、Chromiumブラウザ自体は動作した。
- サーバー実行方式: bash_toolの各呼び出しが独立したシェルセッションに
  なるため、サーバーのバックグラウンド起動と操作を同一コマンド内で
  完結させる必要があった（`(uvicorn ... &); sleep 2; curl ...; pkill ...`）。
- TestClientベースのテストでは、`with TestClient(app) as client`
  （lifespan発火）が必須なエージェントと、環境変数のみで足りる
  エージェントが混在していたため、エージェントごとの個別対応が必要
  だった。
- 各エージェントのDBパス切替方式が3パターン（環境変数、
  app.state、dependency_overrides）に分かれており、共通テストの
  アダプタ層で吸収する必要があった。これも実験Bの自由設計性を
  反映するデータと言える。

---

## 結論

実験Bの共通テストは、人間のPC操作を介さずClaudeのサンドボックス内で
完結して実施できた（方法B）。これにより、実験Aで必要だった
「main.py共有→分析→テスト作成→PowerShellで実行→結果共有」という
何度もの往復が不要になり、効率が大幅に向上した。

一方で、各エージェントの自由設計（DBパス切替方式・レスポンス構造の
差異）に対応するための個別調整は、実験Aの比ではない手間を要した。
これは「実験Bは自由設計のため、共通テストの適用に無理がある」という
当初の懸念が、実際に手を動かしてみて裏付けられた結果でもある。

最終的に、Codex CLIの重大バグ（PUT部分更新）の実証、Antigravity IDE
のバリデーション漏れの新発見、そしてAntigravity IDE自身のレビュー
（テストが本番DBを破壊する）の誤検出判明という、3つの価値ある
発見が得られた。
