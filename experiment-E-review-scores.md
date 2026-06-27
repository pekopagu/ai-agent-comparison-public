# 実験E（相互コードレビュー） 評価集計表【完了・6エージェント全データ】

実験A対象（targets-A/）

## レビュアー: Antigravity CLI（target-6）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | high件数 | medium件数 | low件数 |
|---|---|---|---|---|---|
| target-1 | antigravity-ide | 9.0 | 0 | 1 | 0 |
| target-2 | claude-code | 7.0 | 1 | 0 | 0 |
| target-3 | codex-ide | 7.5 | 1 | 1 | 0 |
| target-4 | copilot-agent | 6.5 | 1 | 1 | 0 |
| target-5 | codex-cli | 5.5 | 2 | 1 | 0 |

平均評価点: 7.1

### 主な指摘内容
- target-1（antigravity-ide）: TaskUpdateのtitleがnull許容で500エラーの恐れ（medium）
- target-2（claude-code）: フィルタ時のサマリー集計バグ（high）、テストDB速度低下
- target-3（codex-ide）: 同様の集計バグ（high）、TaskUpdateの全項目必須化（medium）
- target-4（copilot-agent）: 同様の集計バグ（high）、空白のみtitleの許容（medium）
- target-5（codex-cli）: 接続プーリング不使用（high）、SQL動的組み立て（high）、性能面の課題（medium）

---

## レビュアー: claude-code（target-2）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 7 | UI完成度は高いが統計の二重リクエスト、コメント残骸 |
| target-3 | codex-ide | 9 | 型安全・DRY・インデックス・UTC対応で最も配慮が行き届く |
| target-4 | copilot-agent | 8 | テスト網羅性が群を抜くが、sort/order検証が非慣用的 |
| target-5 | codex-cli | 7 | 生sqlite3・CHECK制約は良いが、init二重呼び出し |
| target-6 | antigravity-cli | 6 | 動作するがエラー処理・レスポンスの一貫性に粗さ |

平均評価点: 7.4

### 主な指摘内容
- セキュリティ: XSS/SQLインジェクションともに致命的な脆弱性なし
- 共通の弱点: titleの空白のみ許容、フィルタ後リスト基準のサマリー集計ズレ、datetime.now()のナイーブなローカル時刻

---

## レビュアー: codex-cli（target-5）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 7 | ページングなし・create_all依存・DB URL固定 |
| target-2 | claude-code | 8 | 同種の構造的指摘のみ、最も軽微 |
| target-3 | codex-ide | 6 | **PUT部分更新が機能しない（実測確認・high）** |
| target-4 | copilot-agent | 8 | 同種の構造的指摘、デフォルトソート順の不一致 |
| target-6 | antigravity-cli | 5 | **pytest収集エラー（実測確認・high）、sort/order検証漏れ** |

平均評価点: 6.8

### 主な指摘内容
- target-3（codex-ide）: TaskUpdateがTaskBaseを継承しtitleが必須。実際にPUT呼び出して422を確認。既存テストでは検出できていない。
- target-6（antigravity-cli）: pytestがModuleNotFoundErrorで収集エラー（PYTHONPATH=.補完で6 passed）。

特徴: 全targetで実際にpytestを実行し、実測した上でレビュー。

---

## レビュアー: codex-ide（target-3）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 7 | 空白タイトル許容・ページングなし |
| target-2 | claude-code | 8 | テストDBがファイルベース（「インメモリ」とのコメントと矛盾） |
| target-4 | copilot-agent | 7 | デフォルトソート順の不一致（API vs UI初期値） |
| target-5 | codex-cli | 6 | **テスト収集エラー（実測確認・high）** |
| target-6 | antigravity-cli | 5 | **テスト収集エラー（実測確認・high）** |

平均評価点: 6.6

### 主な指摘内容
- target-5: pytest -q testsがModuleNotFoundErrorで収集失敗（Codex CLIの指摘と一致）
- target-6: 同様にテスト収集エラー、sort/orderの黙殺フォールバックも指摘

特徴: Codex CLIとほぼ同じレビュー手法（実際にpytest実行）。

---

## レビュアー: antigravity-ide（target-1）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-2 | claude-code | 7 | タイムゾーン依存・CORSハードコード・サマリーバグ |
| target-3 | codex-ide | 8 | SQLAlchemy 2.0準拠は優秀、部分更新不備・サマリーバグ |
| target-4 | copilot-agent | 7 | 空白タイトル許容・タイムゾーン依存・サマリーバグ |
| target-5 | codex-cli | 6 | **SQLインジェクション脆弱性リスク（High）**、接続管理問題 |
| target-6 | antigravity-cli | **8** | UI完成度最高評価、空白タイトル・PUTセマンティクス違反 |

平均評価点: 7.2

### 主な指摘内容
- target-5: ORDER BY句への直接変数バインドを「SQLインジェクション脆弱性リスク（High）」と断定
- target-6（自分と同系統）: UIデザイン完成度を「最も高い」と明記、8点

特徴: UI/UXの完成度を重視する評価軸が一貫（Antigravity CLIと同様）。

---

## レビュアー: copilot-agent（target-4）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 7 | NULL制御は丁寧だが二重フェッチ・空白タイトル許容 |
| target-2 | claude-code | 8 | バランス良好、テストコメントと実装の矛盾 |
| target-3 | codex-ide | 8 | 技術的完成度最良、PUT全置換でデータ消失懸念 |
| target-5 | codex-cli | 7 | SQLi耐性は堅実、接続生成の非効率 |
| target-6 | antigravity-cli | 6 | **sortの黙殺フォールバック（high）、最も改善余地大** |

平均評価点: 7.2

### 主な指摘内容
- 共通の弱点: due_dateソート時のNULL順序が全target未制御
- target-3: 技術的完成度は最良だが、PUTが全置換で部分更新時にデータ消失の懸念
- target-2: テストが「インメモリ」と記載しつつ実体はファイルDB（Codex IDEと同様の発見）
- target-6: 不正sortのサイレントフォールバック（high）、依存バージョン未固定

---

## 被レビュー側の集計（全6エージェント・最終確定）

| target | 実際のエージェント | Antigravity CLI | Claude Code | Codex CLI | Codex IDE | Antigravity IDE | Copilot Agent | 平均評価 |
|---|---|---|---|---|---|---|---|---|
| target-1 | antigravity-ide | 9.0 | 7 | 7 | 7 | （対象外） | 7 | 7.4 |
| target-2 | claude-code | 7.0 | （対象外） | 8 | 8 | 7 | 8 | 7.6 |
| target-3 | codex-ide | 7.5 | 9 | 6 | （対象外） | 8 | 8 | 7.7 |
| target-4 | copilot-agent | 6.5 | 8 | 8 | 7 | 7 | （対象外） | 7.3 |
| target-5 | codex-cli | 5.5 | 7 | （対象外） | 6 | 6 | 7 | 6.3 |
| target-6 | antigravity-cli | （対象外） | 6 | 5 | 5 | 8 | 6 | 6.0 |

---

## 検証事項（均質化トラップ）— 最終結論

### target-1（antigravity-ide）への評価
- Antigravity CLI（同系統）: **9.0点**
- Claude Code / Codex CLI / Codex IDE / Copilot Agent（異系統4者）: **全員7点で完全一致**

### target-6（antigravity-cli）への評価
- Antigravity IDE（同系統）: **8点**
- Claude Code: 6点 / Codex CLI: 5点 / Codex IDE: 5点 / Copilot Agent: 6点
（異系統4者は5〜6点の狭い範囲に収束）

### 最終結論

2つの独立したtarget（target-1, target-6）の両方で、異系統4エージェントが
ほぼ完全に一致する評価（target-1は4者全員7点、target-6は4者が5〜6点）を
付ける中、同系統のレビュアー（Antigravity CLI⇔Antigravity IDE）のみ
一貫して2〜3点高い評価を付けている。これは偶然の一致とは考えにくい
再現性のあるパターンであり、「同系統ベンダーの成果物への評価が
甘くなる」均質化トラップの存在を強く裏付けるデータと言える。

他の系統間（Codex⇔Claude⇔Copilot）では、target-2, 3, 4, 5への評価が
レビュアーの系統に関わらず比較的分散しており、Antigravity系のような
明確な偏りパターンは見られなかった。これはAntigravity系（Google/Gemini）
に特有の現象である可能性があり、記事化する際の重要な考察ポイントになる。

---

## Codex系エンジンの評価一貫性（均質化トラップとは別の現象）

target-5（codex-cli）・target-6（antigravity-cli）のテスト収集エラーを、
Codex CLI・Codex IDEの両方が独立して実測確認し、最終的な評価点も
非常に近い値になった（target-6: 両者ともに5点）。

これは「同系統への高評価」（均質化トラップ）とは異なる現象で、
「同一エンジンが一貫した評価基準・検証手法（実際にpytestを実行する）を
持つ」ことを示すデータである。均質化トラップとエンジンの一貫性は
別の現象として区別して記事化する必要がある。

---

## 全レビュアー共通で検出されたバグ（横断的発見）

### フィルタ適用時のサマリー集計バグ

target-2, 3, 4, 6 について、6エージェント中複数のレビュアーが独立に
「フィルタ適用後のリストを基準にサマリー統計を計算しているため、
全体件数の表示がフィルタの影響を受けてズレる」バグを検出した。

検出したレビュアー: Antigravity CLI, Claude Code, Codex CLI,
Codex IDE, Antigravity IDE（5/6エージェント）

→ 実装時の動作確認では発見されなかった潜在バグ。実験Aの仕様書に
「サマリー表示」の集計仕様が明記されていなかったため、各エージェントが
同じ実装パターンを選んだ結果と考えられる。

### target-5/6のテスト収集エラー

target-5（codex-cli）・target-6（antigravity-cli）の自作テストが、
標準的な実行方法（`pytest -q tests`）ではModuleNotFoundErrorで
収集失敗することを、Codex CLI・Codex IDEの両方が実測で確認した。

→ Codex系エンジンが実際にpytestを実行して検証する手法を一貫して
採用していたことで発見された問題。他系統（Antigravity, Claude,
Copilot）のレビューでは指摘されていない（静的レビュー中心のため）。

### target-3（codex-ide）のPUT部分更新バグ

Codex CLI・Copilot Agentの両方が、TaskUpdateの設計に起因する
PUT更新の問題（部分更新ができない、または全置換でデータ消失の懸念）
を指摘した。Claude Codeはこの問題に気づかず最高評価（9点）を
付けており、評価手法（静的読解 vs 動的検証）の違いが評価結果に
明確に影響した事例。
