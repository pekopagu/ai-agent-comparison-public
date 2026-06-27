# 実験E（相互コードレビュー） 評価集計表【targets-B】

実験B対象（targets-B/）。targets-Aの集計は experiment-E-review-scores.md を参照。

---

## レビュアー: claude-code（target-2）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 構成 | 主な指摘 |
|---|---|---|---|---|
| target-1 | antigravity-ide | 7 | FastAPI+SQLAlchemy（タグ/分析/カンバン） | status/priorityのバリデーション欠如、**CORS過剰許可（allow_origins=["*"]+allow_credentials=True）**、例外詳細の露出 |
| target-3 | codex-ide | **9** | FastAPI+生sqlite3（シンプル） | LIKEエスケープ、ヘルスでのパス露出（いずれも軽微） |
| target-4 | copilot-agent | 7 | FastAPI+sqlite3クラス | **接続クローズ漏れ（リーク）**、import時副作用 |
| target-5 | codex-cli | 7 | FastAPI+sqlite3関数型 | **接続クローズ漏れ**、静的パスのCWD依存、PUT全項目必須 |
| target-6 | antigravity-cli | 7 | FastAPI+SQLAlchemy（カンバン） | パッケージ化されていないimport構成、DELETE 200、updated_at二重更新 |

平均評価点: 7.4

### 主な指摘内容（横断的な所感）

- target-3が突出: 標準ライブラリのみでCHECK制約+Pydantic多層
  バリデーション、lifespan/app.stateによるDI、異常系テストの網羅。
  スコープは小さいが完成度・堅牢性が最も高い。
- **重大バグ（実害あり）**: target-4/5は`with sqlite3.connect()`が
  接続をcloseしない（commitのみ）リソースリーク。最も実害のある
  バグと明記。
- LIKE検索のワイルドカード未エスケープが4targetに共通
  （SQLインジェクションは全てパラメータ化済みで回避）。
- 機能リッチさ: target-1が最多（タグ・分析・カンバン）だが、
  ORMを使いながらenum/CHECK制約を持たない点で生sqlite系に
  整合性で劣るという皮肉な逆転を指摘。
- セキュリティ: 全フロントがVueテンプレート（v-html不使用）で
  XSSは回避。最も気になるのはtarget-1のCORS設定
  （allow_origins=["*"] + allow_credentials=True）。

### 実験A評価との比較（同一レビュアー・同一target）

| target | 実際のエージェント | 実験A評価 | 実験B評価 |
|---|---|---|---|
| target-1（antigravity-ide） | 7 | 7 |
| target-3（codex-ide） | 9 | **9** |
| target-4（copilot-agent） | 8 | 7 |
| target-5（codex-cli） | 7 | 7 |
| target-6（antigravity-cli） | 6 | 7 |

→ target-3（codex-ide）への評価が実験A・B両方で「9点」と完全一致。
Claude Codeのcodex-ideへの評価基準は実験設計（詳細仕様/自由設計）に
関わらず安定している。

---

## レビュアー: antigravity-cli（target-6）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | **6** | **CORS設定問題（High: allow_origins=["*"]+allow_credentials=True）**、DB commit競合 |
| target-2 | claude-code | 8 | ステータス値の不整合リスク、Windows DB lock |
| target-3 | codex-ide | **8.5** | レースコンディション（status toggle、Medium） |
| target-4 | copilot-agent | 7.5 | **descriptionをnullに更新できない（High）** |
| target-5 | codex-cli | 6.5 | **TaskUpdateの未入力値がデフォルトにフォールバックし既存データを上書き消去（High）** |

平均評価点: 7.3

### ★最重要発見：均質化トラップが実験Bでは再現されていない

target-1（antigravity-ide）への評価:
- 実験A（targets-A）でのAntigravity CLIの評価: **9.0点**（最高評価）
- 実験B（targets-B）でのAntigravity CLIの評価: **6点**（今回の最低評価）

同セッションのClaude Codeの評価（実験B）はtarget-1に7点。
つまり実験Bでは「異系統のClaude Codeより、同系統のAntigravity CLIの
方が低い評価」という、均質化トラップの仮説とは正反対の結果になった。

これは重要な反証データであり、「均質化トラップは常に起きるわけ
ではない」ことを示している。実験Aで観察された「Antigravity系の
同系統高評価」は、もしかすると均質化トラップではなく、
「target-1（antigravity-ide）の実験A実装が実際に高品質だった」
ことの正当な評価だった可能性も再考する必要がある。
実験Bでは設計（自由設計）が異なるため、評価が変わるのは
当然であり、系統的な偏りという解釈は早計だったかもしれない。

### CORS問題の独立した発見（再現性の高い指摘）

Antigravity CLIとClaude Code（同じtarget-1に対して）が、
全く同じセキュリティ問題（allow_origins=["*"] +
allow_credentials=Trueの組み合わせ）を独立に発見した。
異なる系統のエージェントが同じ技術的問題を検出したことで、
この指摘の信頼性は非常に高い。

### 新しい重大バグ：PUT部分更新でのデータ消失パターン

target-5（codex-cli）について、「TaskUpdateスキーマの未入力値が
デフォルト値にフォールバックし、既存のDBフィールドを空データで
上書きする」という重大バグ（High）を発見。これはtarget-3
（codex-ide、実験Aでも指摘された部分更新の不備）やtarget-4
（copilot-agent、description nullの問題）と同種の、
「PUT部分更新の実装パターン」に起因する系統的な弱点として
複数のtargetで繰り返し検出されている。

---

## レビュアー: codex-cli（target-5）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 | テスト実測 |
|---|---|---|---|---|
| target-1 | antigravity-ide | 6 | null許容で500エラーの恐れ（medium）、CORS過剰許可（medium） | 6 passed |
| target-2 | claude-code | 7 | null許容、DB制約なし、テストDB並列衝突リスク | 22 passed |
| target-3 | codex-ide | 8 | null許容、health経由でDBパス露出（low） | 9 passed |
| target-4 | copilot-agent | 7 | **nullを無視して200成功扱い（逆方向の問題、medium）** | 19 passed（--basetemp指定必要） |
| target-6 | antigravity-cli | 5 | null許容、due_dateの不正日付未検証、CWD依存パス | 6 passed |

平均評価点: 6.6

### ★最重要発見：全target共通の「null許容」設計盲点

5つ全てのtargetで、「PUTの部分更新（exclude_unset）」実装において
「未指定フィールド」と「明示的なnull送信」を区別する処理が
欠落していることを発見。

- target-1, 2, 3, 6: 明示的なnullを許容し、DBのNOT NULL制約に
  当たって500系エラーになり得る
- target-4: 逆方向の問題。nullを「未指定」と同じ扱いで無視し、
  200成功を返すため、クライアントのバグを隠してしまう

これは6エージェント全員が「PUTの部分更新」を実装する際に
共通して見落とした設計上の盲点であり、実験Bの自由設計が
生み出した最も重要な横断的発見の一つ。

### CORS問題の3エージェント目の確認

Codex CLIも「CORS が allow_origins=["*"] かつ
allow_credentials=True」をtarget-1に対して指摘（medium）。
Antigravity CLI（High）・Claude Code・Codex CLIの3つの異なる
系統のエージェントが全員同じセキュリティ問題を検出しており、
非常に再現性の高い指摘になった。

### target-4のテスト実行環境問題（新種）

target-4（copilot-agent）について、通常のpytest実行は
「一時ディレクトリ権限」エラーで失敗し、`--basetemp`オプション
指定で19 passedとなることを実測確認。これまでの
ModuleNotFoundError（実験Aのtarget-5/6）とは異なる新種の
実行環境問題。

特徴: 実験A同様、全targetで実際にpytestを実行し実測した上で
レビューしている。Codex CLIの一貫した実証的レビュー手法が
実験Bでも再現された。

---

## レビュアー: codex-ide（target-3）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 7 | CORS問題（medium）、タグ重複未検証、広い例外捕捉 |
| target-2 | claude-code | 8 | 空PUTの仕様曖昧、**「コメント文字化け」指摘（誤検出）** |
| target-4 | copilot-agent | 7 | **descriptionをnullにできない（high）**、「文字化け」指摘（誤検出） |
| target-5 | codex-cli | 7 | **PUTが全置換で部分更新できない（high）** |
| target-6 | antigravity-cli | 6 | **DB URL固定（high）**、due_date検証不足 |

平均評価点: 7.0

### 検証手法の違い（同一エンジンでの変化）

実験A（targets-A）ではCodex IDEも全targetで実際にpytestを実行する
手法だったが、今回（targets-B）は「`python -m compileall -q`で
構文エラーのみ確認、フルのpytest実行はしていません」と明記。
同一エンジンでも実験によって検証の深さが変化した。

### ★誤検出の発見：「コメント文字化け」指摘の検証

Codex IDEはtarget-2（claude-code）・target-4（copilot-agent）の
両方で「コメント・docstringが広範囲に文字化けしており保守性を
落としている」と指摘した。

しかし人間が`Get-Content -Encoding UTF8`で実際のファイルを
確認したところ、**文字化けは存在しなかった**（日本語コメントが
正しく表示された）。これはCodex IDE自身のファイル読み取り時の
エンコーディング処理に問題があった可能性が高く、レビュー結果に
含まれた誤検出（false positive）の具体的な事例となった。

この発見の重要性: 「複数のエージェントが同じ問題を指摘している
場合は信頼性が高い」という原則の裏返しとして、単独のエージェントの
指摘（特に他のレビュアーが言及していない事項）は検証が必要で
あることを示す好例。AIエージェントのレビュー結果を無批判に
信用してはいけないという教訓を、実験全体を通じて最も具体的に
示したデータになった。

### PUTの設計問題（再現性の確認）

target-5（codex-cli）について「TaskUpdateがTaskBaseを継承して
いるため部分更新ではなく全フィールド更新になる（high）」と指摘。
これは実験Aでcodex-ideへの指摘として複数回出ていた問題パターンが、
実験Bでは逆にcodex-cliの実装で発生していることを示す。
「TaskUpdateがTaskBaseを継承する」という実装上の落とし穴は、
実験A・B・複数エージェントで繰り返し検出される系統的な問題。

---

## レビュアー: antigravity-ide（target-1）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-2 | claude-code | 7 | テストDB競合リスク、非標準的な接続管理 |
| target-3 | codex-ide | 6 | NULLでIntegrityError・500エラー |
| target-4 | copilot-agent | 7 | description nullで更新スキップ |
| target-5 | codex-cli | **4** | **PATCHの完全な機能不全＋テストが本番DB破壊（最重大）** |
| target-6 | antigravity-cli | 7 | create_all副作用、静的配信の404処理問題 |

平均評価点: 6.2

### ★【後日訂正】「テストが本番DBを破壊する」指摘は誤検出と判明

target-5（codex-cli）について、当初「テスト用DB切り替えに
importlib.import_moduleを使っているが、Pythonのモジュール
キャッシュにより機能せず、テストが分離されないばかりか
本番DBを破壊する重大なバグの原因となっている」という指摘を
実験Eで最も深刻なバグとして記録していた。

**しかし後日、Claude（第三者検証者）が実際にコードを動かして
検証した結果、この指摘は誤りだったことが判明した。**
`get_db_path()`が呼び出し時に毎回`os.environ.get(...)`を
評価する設計のため、モジュールキャッシュの影響を受けず、
本番DB（テスト実行前に作成したタスクを含む）はpytest実行後も
複数回の検証で一切破壊されなかった。

これはCodex IDEの「コメント文字化け」指摘（targets-B、同じく
誤検出）に続く、実験E全体で2件目に確認されたAIレビューの
誤検出（false positive）の事例である。「単独のレビュアーのみが
指摘した重大な問題は、複数レビュアーの指摘や実際の動作確認で
裏付けない限り、過大評価してはならない」という教訓を補強する
データとなった。

なお、「completedを指定せずにリクエストを送るとデフォルト値
Falseが適用され、タスク状態が強制的に『未完了』に巻き戻される」
という指摘（PUTの全置換問題）は、Codex CLI・Codex IDEも同様に
指摘しており、複数レビュアーが一致する妥当な指摘として残る。

### 均質化トラップの再検証（2例目）

target-6（antigravity-cli、自分と同系統）への評価:
- 実験A（Antigravity IDE自身の評価）: 8点（最高評価）
- 実験B（Antigravity IDE自身の評価）: 7点

他レビュアー（実験B）: Claude Code 7点 / Codex CLI 5点 / Codex IDE 6点

→ 今回の評価（7点）は異系統エージェントとほぼ同じ範囲（5〜7点）に
収まり、実験Aで見られた明確な高評価（8点 vs 異系統5〜6点）は
再現されなかった。これはAntigravity CLI（実験B・target-1）でも
同様の結果が見られたパターンであり、「実験Bでは均質化トラップが
弱まる、または見られない」ことが2つの独立したケースで再現された。

---

## レビュアー: copilot-agent（target-4）

| レビュー対象target | 実際のエージェント | 評価点（1〜10） | 主な指摘 |
|---|---|---|---|
| target-1 | antigravity-ide | 6 | **CORS *+credentials（High）**、status/priority未検証（High） |
| target-2 | claude-code | **9** | 重大問題なし。パラメータ化・Enum・テスト充実 |
| target-3 | codex-ide | **9** | 重大問題なし。CHECK制約・DI・サマリ集計が秀逸 |
| target-5 | codex-cli | 6 | **DB接続リーク（High）**、PUT全置換でデータ消失 |
| target-6 | antigravity-cli | 7 | フラット構成の実行ディレクトリ依存、DELETE 200返却 |

平均評価点: 7.4

### CORS問題：4エージェント目の確認（決定的な信頼性）

target-1（antigravity-ide）のCORS設定問題（allow_origins=["*"]+
allow_credentials=True）を、Antigravity CLI・Claude Code・
Codex CLI・Copilot Agentの4つの異なる系統のエージェントが
全員独立に検出した。これは実験全体で最も再現性の高い指摘であり、
技術的な正確性は確定的と言える。

### target-5（codex-cli）への評価：5エージェント全員が問題を検出

target-5に対する評価:
- Claude Code: 7点 / Codex IDE: 7点 / Antigravity IDE: 4点（最低、
  本番DB破壊バグを発見） / Copilot Agent: 6点（接続リーク、
  PUT全置換でのデータ消失）

5エージェント中5エージェント全員がtarget-5に何らかの重大な
問題（high相当）を発見しており、target-5（codex-cli）の
実験B実装は最も問題の多い成果物として確定的になった。

---

## 被レビュー側の集計（実験B・全6エージェント・最終確定）

| target | 実際のエージェント | Claude Code | Antigravity CLI | Codex CLI | Codex IDE | Antigravity IDE | Copilot Agent | 平均評価 |
|---|---|---|---|---|---|---|---|---|
| target-1 | antigravity-ide | （対象外） | 6 | 6 | 7 | （対象外） | 6 | 6.3 |
| target-2 | claude-code | （対象外） | （対象外） | 7 | 8 | 7 | 9 | 7.8 |
| target-3 | codex-ide | 9 | （対象外） | 8 | （対象外） | 6 | 9 | 8.0 |
| target-4 | copilot-agent | 7 | 7 | 7 | 7 | 7 | （対象外） | 7.0 |
| target-5 | codex-cli | 7 | （対象外） | （対象外） | 7 | 4 | 6 | 6.0 |
| target-6 | antigravity-cli | 7 | （対象外） | 5 | 6 | 7 | 7 | 6.4 |

---

## 実験E（targets-B）総括

### 全エージェント共通の最重要発見：「PUT部分更新のnull処理」設計盲点

6エージェント全員の実験B実装が、「PUTの部分更新時、未指定
フィールドと明示的なnull送信を区別する処理」を欠いていた。
target-1,2,3,6はnullを許容してDB制約違反になり得る、target-4は
逆にnullを無視して成功扱いにしてしまう、target-5はデフォルト値で
既存データを上書きする——というように、表面化の形は違うが
根本原因は共通していた。これは実験Aの仕様書（詳細仕様）には
無かった「部分更新の仕様」を実験Bで各エージェントが自由に
実装した結果、誰も完全には解決できなかった共通の落とし穴。

### 均質化トラップの結論：実験条件依存の現象

実験A（targets-A）では、Antigravity系（CLI⇔IDE）が同系統の
成果物（target-1, target-6）に対し、異系統エージェントより
一貫して2〜3点高い評価を付けるという明確な均質化トラップの
パターンが観察された。

しかし実験B（targets-B）では、同じ組み合わせ（Antigravity CLI→
target-1、Antigravity IDE→target-6）で、この傾向は再現されな
かった。同系統の評価が異系統とほぼ同じ範囲に収まり、むしろ
Antigravity CLIはtarget-1（同系統）に最も厳しい評価（6点）を
付けるケースもあった。

**結論**: 均質化トラップは固定的な現象ではなく、実験条件
（詳細仕様による条件統一か、自由設計による差異化か）に依存して
出現する可能性がある。詳細仕様（実験A）では実装の差異が少なく
「表面的な品質」で判断しやすいため、同系統への評価が甘くなる
余地が大きい。一方、自由設計（実験B）では各エージェントの
実装が大きく異なり、レビュアーが個別の実装内容を深く検証する
必要があるため、系統的な偏りが生じにくいのかもしれない。
この仮説は記事化する際の重要な考察ポイントになる。

### AIレビューの限界：誤検出（false positive）の実例

Codex IDEがtarget-2・target-4に対して指摘した「コメント文字化け」
は、人間が実際にファイルを確認したところ誤りだった。これは
実験全体を通じて、AIによるコードレビューも完璧ではなく、
人間による検証が依然として重要であることを示す具体的な証拠と
なった。

### AIレビューの誤検出（2件目）

Antigravity IDEがtarget-5（codex-cli）に対して指摘した
「テスト用DB切り替えがモジュールキャッシュにより機能せず、
本番DBを破壊する」というバグは、当初実験全体で最も実害が
大きい欠陥として記録されたが、後日Claudeによる実機検証で
誤検出と判明した（get_db_path()が呼び出し時に毎回環境変数を
評価する設計のため、モジュールキャッシュの影響を受けない）。
Codex IDEの「コメント文字化け」指摘と合わせて、実験E全体で
2件目の確定的な誤検出事例となった。
