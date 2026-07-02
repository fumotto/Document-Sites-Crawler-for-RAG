# Document Sites Crawler for RAG 要件定義書 v2

## 1. 概要

Webサイト上のドキュメントを収集・整形し、NotebookLMへアップロードしやすいMarkdownファイル群を生成するツールを作成する。

本ツールはSupabase Docsに限らず、React、Next.js、Cloudflare、Stripe、AWSなど、一般的なドキュメントサイト全般で利用できる汎用ツールとする。

実行環境はDocker Composeを前提とし、Windows環境でも `docker compose up` のみで実行できることを目標とする。

---

## 2. 実行環境

- Docker Composeのみで実行可能
- Windows環境に対応
- `docker compose up` だけで実行できる
- Pythonベースで実装する

---

## 3. 対象URL（単一サイト指定）

CLI引数（`docker compose run` の引数）でURLを指定できる。

```
docker compose run crawler https://react.dev
```

**`BASE_URL`（単数）は .env では使用しない。** CLIから単一サイトを指定する場合の値として扱う。

> v1からの変更点：v1では `.env` の `BASE_URL` をデフォルト値として利用する想定だったが、v2では `.env` 側はBASE_URLS（複数）のみを正とする。単一サイト指定はCLI引数経由のみとする。

---

## 4. 複数サイト対応（.env BASE_URLS）

`.env` の `BASE_URLS` で複数URLを指定可能。

```
BASE_URLS=
https://supabase.com/docs/
https://react.dev/
https://nextjs.org/docs
```

サイトごとに独立して処理を行う（cache / output / archives もサイト単位で分離。詳細は各節を参照）。

---

## 5. URL指定の優先順位

| 状況 | 挙動 |
|---|---|
| CLI引数でURLが指定された場合 | `.env` の `BASE_URLS` は**スキップ**し、単一サイトの処理のみを行う |
| CLI引数の指定がない場合 | `.env` の `BASE_URLS` を読み込み、複数サイトを順次処理する |

優先順位：**CLI引数 > .env（BASE_URLS）**

---

## 6. ページ探索

探索優先順位

1. sitemap.xml
2. sitemap index
3. robots.txt に記載された Sitemap
4. 同一ドメインクロール（フォールバック）

サイトマップが利用できる場合は優先して利用する。存在しない場合のみクロールへフォールバックする。

---

## 7. クロール無限ループ対策

同一ドメインクロール（フォールバック探索）時、無限ループを防止するため以下を実施する。

### URL正規化

訪問済み判定の前に、以下のルールでURLを正規化する。

- フラグメント（`#`以降）を除去
- 末尾スラッシュの有無を統一する（末尾スラッシュなしに統一）
- スキーム・ホスト名を小文字化する
- 既知のトラッキングパラメータ（`utm_*` 等）を除去する
- 上記以外のクエリパラメータは保持する（ページネーションやタブ切り替え等、意味を持つ場合があるため）

### 訪問済みURL管理

- 正規化後のURLを「訪問済みURLセット」で管理し、リクエスト開始時点でセットへ登録することで、並行処理時の二重リクエストを防止する。

### リダイレクト対策

- リダイレクトの最大ホップ数を **5回** とする。
- 上限を超えた場合は当該URLをスキップし、ログに記録する。

---

## 8. 同一ドメインクロールの上限（MAX_PAGES）

`.env`

```
MAX_PAGES=1000
```

- デフォルト値は `.env` に必ず記載すること。**未定義の場合はエラーとする。**
- sitemapが利用できる場合：sitemap上の総URL数が事前に判明するため、クロール開始前に `MAX_PAGES` を超過するかどうかを判定し、超過する場合は警告ログを出力する。
- sitemapが利用できずクロールへフォールバックする場合：リンクをたどりながらでないと総ページ数が判明しないため、事前判定はできない。`MAX_PAGES` に到達した時点でクロールを打ち切る（ソフトリミット）。
- しきい値超過時の挙動：**それまでに取得済みの成果物は保持したままクロールのみを打ち切る**（ジョブ全体はエラー終了させない）。

---

## 9. HTML取得

取得対象

- 同一ドメイン
- 指定URL配下

robots.txtを遵守し、不要なURLは除外可能とする（[11. URLフィルタ](#11-urlフィルタ) 参照）。

---

## 10. SPA非対応

本ツールは静的HTMLまたはSSR/SSGによって生成されたHTMLを対象とする。

**JavaScriptの実行を前提とするSPA（クライアントサイドレンダリングのみでコンテンツが描画されるサイト）は対象外とする。**

- ヘッドレスブラウザによるレンダリングは行わない。
- SPA向けの自動検知ロジックは実装しない（仕様として明記するのみ）。

---

## 11. URLフィルタ

`.env`

```
INCLUDE=/docs/
EXCLUDE=
/blog/
/pricing/
/legal/
```

INCLUDE・EXCLUDEの両方を指定可能。

> **補足（v1.0.1 Issue #6対応）**：`INCLUDE`が指定されない場合、対象URLのパス部分（ドメインルートを除く）を暗黙のINCLUDEとして自動適用する。sitemap利用時のクロールはドメインルートの`sitemap.xml`を参照する仕様上、`INCLUDE`未設定のままだと指定パス外のページ（例：`/blog/`）まで取得対象になってしまう不具合があったための修正である。詳細は「07_CLI仕様」3節を参照。

---

## 12. 本文抽出

HTMLから以下を除去する。

- ナビゲーション
- サイドバー
- フッター
- パンくずリスト
- コメント
- その他本文以外

ライブラリ：`trafilatura`

Markdownへ変換する。

---

## 13. コードブロック保持

コードブロックはMarkdown形式で保持する。

例

````
```ts
const client = createClient(...)
```
````

---

## 14. NotebookLM向けフォーマット

各ページは以下の形式で出力する。

```
==================================================
TITLE:
Authentication
URL:
https://...
UPDATED:
2026-06-30T12:00:00Z
==================================================
本文
```

---

## 15. キャッシュ構造とビルドの分離

HTMLのダウンロード・パースと、Markdown結合（ビルド）の処理を分離する。

### 処理フロー

1. **ダウンロード・パース工程**：差分（新規・更新）が検出されたページのみ、HTMLを取得し本文抽出・Markdown変換を行う。
2. 変換済みのMarkdown本文を**キャッシュへ実体ファイルとして保存**する（メタデータのみではなく本文そのものを保持する）。

   ```
   cache/{site}/pages/{hash}.md
   ```

3. **ビルド工程（結合）**：上記1・2を経ずに、**キャッシュに存在する全ページのMarkdown本文を毎回読み込み**、結合Markdown（`docs_XXX.md`）を作り直す。差分更新でも `incremental` / `full` どちらのモードでも、結合自体は常に「キャッシュ全件」から再構築する。

### エラーハンドリング

- ビルド工程で、manifestに記録されているページに対応するキャッシュ上のMarkdown本文ファイルが見つからない場合は、**エラーとして処理を中断する**（サイレントにスキップしない）。

---

## 16. Markdown結合（ビルド処理）

全ページ（キャッシュ全件）を結合し、

```
docs_001.md
docs_002.md
docs_003.md
...
```

として出力する。

ページの割り当ては [17. 分割条件](#17-分割条件) に従う。

---

## 17. 分割条件

`.env`

```
WORD_LIMIT=450000
```

NotebookLM上限（500,000 words）を超えないよう、安全マージンを持たせる。

### ページ単位での分割

- **1ページの本文が複数の `docs_XXX.md` に跨って分割されることはない。** ページ単位で `docs_XXX.md` に詰めていく。
- 1ページ単体の語数が `WORD_LIMIT` を超える場合、そのページのみで1つの `docs_XXX.md` を生成する（`WORD_LIMIT` を超過したファイルとなる）。この場合、警告ログを出力する。

---

## 18. 重複除去

### 対象

- 重複判定の対象は、**HTTPステータスコードが 200 OK で取得できたページのみ**とする。
- `304 Not Modified`（前回200で取得済み・今回未変更）で返ってきたページは、重複判定の対象に**含めない**（既に重複チェック済みの内容のため）。

### 判定方法

- URL
- 本文SHA256

本文SHA256が一致するページは重複とみなす。

### 重複時の扱い

- 重複と判定された場合、**後から見つかったURLを優先**して残す。
- 重複と判定された（後から見つかった方ではない）ページは、`manifest.json` 上には**記録として残す**が、結合Markdown（`docs_XXX.md`）の出力対象からは**除外**する。

### 再結合トリガー

- 差分更新によって新たに重複が検出された場合、該当ページは次回のビルド（結合）処理時に自動的に結合Markdownから取り除かれる。すなわち、重複除去の判定結果が変化した場合、結合Markdownの再生成（[15. キャッシュ構造とビルドの分離](#15-キャッシュ構造とビルドの分離) の方式により、ビルドは常にキャッシュ全件から再構築されるため）が自動的なトリガーとなる。

---

## 19. 差分更新モード

`.env`

```
MODE=incremental
```

または

```
MODE=full
```

デフォルト：`incremental`

- **incremental**：更新されたページのみ取得。
- **full**：すべて再取得し、成果物を作り直す。

---

## 20. 差分判定の優先順位

差分判定は以下の優先順位で行う。

1. **sitemapのlastmod**：sitemapに `lastmod` が記載されているURLは、これを一次フィルタとして利用する。前回取得時の記録と比較し、更新がなければHTTPリクエスト自体を省略する。
2. **HTTP条件付きリクエスト**：`If-Modified-Since` / `If-None-Match` を利用し、`304 Not Modified` を優先する。
3. **SHA256比較**：上記が利用できない場合、または明示的な確認が必要な場合に本文SHA256を比較する。

### フォールバック条件

- sitemapに `lastmod` の記載がないURL
- 同一ドメインクロール（フォールバック探索）で発見されたURL（sitemapに掲載されていないページ）

これらについては、引き続き「HTTP条件付きリクエスト → SHA256比較」の判定にフォールバックする。

---

## 21. manifest管理

キャッシュ：`cache/{site}/manifest.json`

管理内容

- URL
- ETag
- Last-Modified
- sitemap lastmod
- SHA256
- ダウンロード日時
- 出力先ファイル（`docs_XXX.md`）
- 重複フラグ（重複としてマークされているか）

---

## 22. manifest保存先・マルチサイト対応

### マルチサイト対応

manifestは**サイトごとにファイルを分離**する。

```
cache/
  supabase/
    manifest.json
  react/
    manifest.json
  next/
    manifest.json
```

### CLI引数による変更

```
docker compose run crawler --manifest ./manifest-prod.json
```

- `--manifest` オプションは**単一サイト処理を前提**とする。
- **複数サイト処理時（`.env` の `BASE_URLS` による処理時）に `--manifest` オプションが指定された場合はエラーとする。**
- 単一サイト処理（CLI引数でURL指定時）であれば、CLI指定のmanifestパスを優先する。

---

## 23. 削除ページ対応

差分更新時に以下を判定する。

- 新規
- 更新
- 削除

削除されたページはmanifestから除去する。

---

## 24. ログ

```
logs/
  crawler.log
```

出力内容

- Downloaded
- Updated
- Skipped
- Deleted
- Duplicate（重複除外）
- Error
- Warning（ページ単体がWORD_LIMIT超過、MAX_PAGES超過、リダイレクト上限到達 等）

---

## 25. アクセス速度制御・エラーハンドリング・リトライ

### アクセス速度制御（Rate Limit）

`.env`

```
REQUEST_DELAY=0.5
```

ページ取得ごとに待機時間を設ける。

目的

- サーバーへの負荷軽減
- アクセス制限回避
- 429エラー防止

### リトライ方針

- **リトライは行わない。** タイムアウト・5xx・接続エラーが発生したページは、その場でスキップしログに記録する（再試行しない）。
- エラー発生時は、次のリクエストへ進む前に **0〜5秒のランダムな待機時間** を追加する（バックオフ）。

### 429（Too Many Requests）への対応

- 429が返却された場合も**例外なくスキップ**し、リトライは行わない。
- レスポンスに `Retry-After` ヘッダーが含まれる場合は、**次のリクエストまでその秒数分だけ余分に待機する**（指定ページ自体は再試行しない）。
- `Retry-After` ヘッダーが無い場合は、通常の `REQUEST_DELAY` ＋ ランダムバックオフ（0〜5秒）に従う。

---

## 26. タイムアウト

`.env`

```
TIMEOUT_SECONDS=30
```

- HTTPリクエストのタイムアウト秒数を設定する。
- デフォルト値は `.env` に必ず記載すること。**未定義の場合はエラーとする。**

---

## 27. User-Agent

`.env`

```
USER_AGENT=NotebookLM-Crawler/1.0
```

HTTPアクセス時のUser-Agentを変更可能。

目的

- 適切なクローラー識別
- サーバーログ上で識別しやすくする

---

## 28. 出力ディレクトリ

サイトごとに分離。

```
output/
  supabase/
  react/
  next/
```

---

## 29. NotebookLM用インデックス生成

各サイトについて `Index.md` を生成する。

内容

- ページタイトル一覧

例

```text
# Supabase Docs

- Introduction
- Authentication
- Database
- Storage
- Edge Functions
```

目的：NotebookLMがサイト全体の構造を把握しやすくする。

## 30. ページ統計

各ページについて記録する。

- Word数
- 文字数
- 推定Token数

### 推定Token数の算出方法

- **tiktoken による実測**を採用する。
- 注記：NotebookLM自体はGemini系モデルを利用しているため、tiktoken（OpenAI用エンコーダ）による値は厳密なトークン数とは一致しない。あくまで**目安**として扱う旨を成果物または仕様書に明記する。

NotebookLM以外のRAGでも利用可能にする。

---

## 31. チャンクマニフェスト

`chunk_manifest.json` を生成する。

内容

```
docs_001.md
- Authentication
- Database
- Storage
```

どのMarkdownにどのページが格納されたかを追跡できるようにする。

> 重複として除外されたページ（[18. 重複除去](#18-重複除去) 参照）は、`chunk_manifest.json` および結合Markdownには含めない。

---

## 32. ZIPアーカイブ生成

生成後、自動でZIP化する。

命名例

```
supabase_docs_20260630_213045.zip
react_docs_20260630_213045.zip
```

常にユニークなファイル名とする。上書きしない。

---

## 33. アーカイブ保存

```
archives/
  supabase/
  react/
  next/
```

履歴として保存する。一方 `output/` には最新成果物のみ配置する。

---

## 34. 生成メタデータ

各Markdownの先頭に生成情報を付与する。

例

```
Generated by : Document Sites Crawler for RAG v1.0
Generated At : 2026-06-30T21:30:45+09:00
Source : https://supabase.com/docs/
Mode : incremental
```

後から成果物のみを見ても生成条件が分かるようにする。

---

## 35. CLI仕様

### 単一サイト処理

```bash
docker compose run crawler https://react.dev
```

### manifest指定

```bash
docker compose run crawler https://react.dev --manifest ./manifest.json
```

### .envによる複数サイト処理

```bash
docker compose up
```

### エラーとなる例

- URL未指定で `--manifest` のみ指定
- 複数サイト処理時に `--manifest` を指定

## 36. 設定方法

### `.env` で設定可能な項目

| 変数名 | 説明 | デフォルト | 未定義時 |
|---|---|---|---|
| `BASE_URLS` | 複数サイトURL（改行区切り） | なし | CLI引数指定があればスキップ |
| `MODE` | `incremental` / `full` | `incremental` | デフォルト適用 |
| `WORD_LIMIT` | 結合Markdown1ファイルあたりの語数上限 | `450000` | デフォルト適用 |
| `REQUEST_DELAY` | リクエスト間の待機秒数 | `0.5` | デフォルト適用 |
| `USER_AGENT` | HTTPアクセス時のUser-Agent | `NotebookLM-Crawler/1.0` | デフォルト適用 |
| `INCLUDE` | 取得対象パス | なし | デフォルト適用（制限なし） |
| `EXCLUDE` | 除外対象パス | なし | デフォルト適用（制限なし） |
| `MAX_PAGES` | 同一ドメインクロール時の最大ページ数 | `1000` | **エラー** |
| `TIMEOUT_SECONDS` | HTTPタイムアウト秒数 | `30` | **エラー** |

> `BASE_URL`（単数）は `.env` では使用しない。CLI引数（`docker compose run crawler <URL>`）でのみ単一サイトを指定する。

### CLIから変更可能な項目

- URL（単一サイト指定。指定時は `BASE_URLS` の処理をスキップ）
- manifest保存先（`--manifest`。複数サイト処理時はエラー）

CLI指定が常に優先される。

---

## 37. 中断・再実行可能性（Resume）

本ツールはレジューム可能である。

- 差分取得・パース済みのページは `cache/` に保持されるため、処理途中で異常終了しても再実行時に再利用する。
- `incremental` モードでは、正常に保存済みのキャッシュは再取得しない。
- ビルド（結合）工程はキャッシュ全件から毎回再構築するため、途中停止後も整合性を保った成果物を生成できる。

## 38. 設計方針

- NotebookLMへの投入品質を最優先
- ドキュメントサイトに依存しない汎用設計（ただしSPAは対象外）
- 差分更新を高速化（ダウンロード・パースは差分のみ／結合は常に全件再構築）
- サーバーへの負荷を最小限にする
- NotebookLMだけでなくRAG用途にも流用可能
- Docker Composeのみで簡単に実行できること
