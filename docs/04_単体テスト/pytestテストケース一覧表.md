# 単体テスト（pytest）テストケース一覧表

## 凡例
- **テスト優先度**：最高／高／中／低（本文冒頭の基準に準拠）
- **テストメソッド名**：既存テストファイル（`tests/*.py`）から特定できたもののみ記入。未作成は空欄。

---

## 1. `site_identifier.py`（サイト識別子生成）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| SID-001 | 基本的な小文字化・記号置換 | 最高 | なし | `https://supabase.com/docs/` を渡す | `supabase_com_docs` が返る | `test_lowercase_and_symbol_replacement` |
| SID-002 | 末尾スラッシュ有無の同一視 | 最高 | なし | 末尾スラッシュあり／なしの2URLを渡す | 両者が同一の識別子になる | `test_trailing_slash_equivalence` |
| SID-003 | 大文字・小文字表記揺れの同一視 | 高 | なし | ホスト名・パスに大文字を含むURLと小文字URLを渡す | 両者が同一の識別子になる | `test_case_insensitivity` |
| SID-004 | パスなしドメインのみのURL | 最高 | なし | `https://react.dev` を渡す | `react_dev` が返る | `test_react_dev_example` |
| SID-005 | 空文字列URLでの例外送出 | 高 | なし | 空文字列を渡す | `ValueError` が送出される | `test_empty_url_raises` |
| SID-006 | 記号の連続圧縮（`://`由来） | 中 | なし | クエリ・ポート等で `_` が連続しうるURLを渡す | `_` が1文字に圧縮される | |
| SID-007 | パス末尾以外の連続記号（例：`//`を含むパス） | 中 | なし | `https://example.com/a//b` のようなURLを渡す | `_` が連続せず1文字に圧縮される | |
| SID-008 | httpとhttpsの違いがスキーム除去で無視される | 中 | なし | `http://example.com/x` と `https://example.com/x` を渡す | 両者が同一識別子になる | |
| SID-009 | サブドメイン・ポート番号を含むURL | 中 | なし | `https://docs.example.com:8080/a` を渡す | ポート番号・ドット等が `_` に変換される | |

---

## 2. `url_normalizer.py`（URL正規化・page_hash算出）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| URLN-001 | スキーム・ホスト名の小文字化 | 最高 | なし | `HTTPS://Example.COM/Path` を渡す | scheme/hostnameのみ小文字化されpathは保持される | |
| URLN-002 | デフォルトポート除去（https:443） | 高 | なし | `https://example.com:443/a` を渡す | ポート番号が除去される | |
| URLN-003 | デフォルトポート除去（http:80） | 高 | なし | `http://example.com:80/a` を渡す | ポート番号が除去される | |
| URLN-004 | 非デフォルトポートは保持 | 中 | なし | `https://example.com:8443/a` を渡す | ポート番号が保持される | |
| URLN-005 | フラグメント除去 | 高 | なし | `https://example.com/a#section1` を渡す | `#section1` が除去される | |
| URLN-006 | クエリパラメータの保持 | 高 | なし | `https://example.com/a?tab=2` を渡す | クエリがそのまま保持される | |
| URLN-007 | パス省略時のルート補完 | 中 | なし | `https://example.com` を渡す | パスが `/` として補完される | |
| URLN-008 | 末尾スラッシュ有無は正規化しない | 高 | なし | `https://example.com/a/` と `https://example.com/a` を渡す | 正規化結果が異なる（同一視しない） | |
| URLN-009 | page_hashの決定性（同一入力で同一ハッシュ） | 最高 | なし | 同一正規化URLで2回`compute_page_hash`を呼ぶ | 同じSHA-256値が返る | |
| URLN-010 | page_hashが異なるURLで異なる値になる | 高 | なし | 異なる正規化URLで`compute_page_hash`を呼ぶ | 異なるSHA-256値が返る | |

---

## 3. `atomic_io.py`（アトミック書き込み）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| AIO-001 | JSON書き込み後にファイルが読み書き可能 | 最高 | tmp_path | `atomic_write_json`で書き込み | ファイルが存在しread/write権限を持つ | `test_atomic_write_json_creates_readable_file` |
| AIO-002 | テキスト書き込み後にファイルが読み書き可能 | 最高 | tmp_path | `atomic_write_text`で書き込み | ファイルが存在しread/write権限を持つ | `test_atomic_write_text_creates_readable_file` |
| AIO-003 | `read_json`で書き込んだ内容を正しく読み戻せる | 最高 | tmp_path | `atomic_write_json`→`read_json` | 元のdictと一致する内容が返る | |
| AIO-004 | 既存ファイルへの上書きが成功する | 高 | 既存ファイルがある状態 | 同一パスに2回`atomic_write_json` | 2回目の内容で上書きされる | |
| AIO-005 | 親ディレクトリが存在しない場合に自動作成される | 高 | 親ディレクトリ未作成のパス | `atomic_write_json`で書き込み | 親ディレクトリが自動作成されファイルが生成される | |
| AIO-006 | 書き込み中に例外発生時、一時ファイルが残らない | 中 | writerが例外を送出するようモック | `_atomic_write`を例外送出writerで呼ぶ | 例外が伝播し `.tmp` ファイルが残らない | |

---

## 4. `site_lock.py`（サイト単位排他ロック）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| LOCK-001 | ロック取得・解放後にファイルが読み書き可能 | 最高 | tmp_path | `site_lock`のwithブロックを実行 | ファイルが存在しread/write権限を持つ | `test_site_lock_creates_readable_file` |
| LOCK-002 | 同一ロックファイルへの二重取得で例外送出 | 高 | fcntl利用可能環境 | 1つ目のロック取得中に2つ目を取得しようとする | `LockAcquisitionError`が送出される | |
| LOCK-003 | ロック解放後は再取得できる | 高 | fcntl利用可能環境 | 1回目のwithブロック終了後、2回目のブロックに入る | 例外なく2回目のロックが取得できる | |
| LOCK-004 | 例外発生時でもロックが確実に解放される | 中 | withブロック内で例外送出 | ブロック内で例外を送出させる | finally節でロックが解放され、以降再取得可能 | |

---

## 5. `logging_setup.py`（ログ設定）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| LOG-001 | ログファイル作成後に読み書き可能 | 最高 | tmp_path | `setup_logging("INFO","text",path)` | ファイルが存在しread/write権限を持つ | `test_setup_logging_creates_readable_file` |
| LOG-002 | ログレベルがルートロガーへ反映される | 高 | なし | `setup_logging("ERROR",...)` | `logging.getLogger().level`がERRORになる | |
| LOG-003 | text形式のフォーマットで出力される | 中 | なし | text形式でログ出力しファイル内容を確認 | 指定フォーマットの文字列が出力される | |
| LOG-004 | json形式のフォーマットで出力される | 中 | なし | json形式でログ出力しファイル内容を確認 | 各行がパース可能なJSONになっている | |
| LOG-005 | 既存ハンドラの重複登録防止（再実行時） | 中 | 既に`setup_logging`済み | 同一プロセスで2回`setup_logging`を呼ぶ | ハンドラ数が増え続けない | |

---

## 6. `directory_bootstrap.py`（ディレクトリ自動生成）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| DIR-001 | cache/output/archives/logsのみ作成しtestsは作成しない（Issue #5） | 最高 | tmp_path | `ensure_project_directories(tmp_path)` | 作成物が`{cache,output,archives,logs}`のみ、`tests`が含まれない | `test_issue5_tests_dir_not_created` |
| DIR-002 | `build_site_context`でサイト単位ディレクトリが生成される | 高 | tmp_path, ConfigRecord | `build_site_context`を呼ぶ | `cache/{id}/pages`,`cache/{id}/metadata`,`output/{id}`,`archives/{id}`が生成される | |
| DIR-003 | `manifest_path_override`指定時にmanifestパスが上書きされる | 高 | override付きConfigRecord | `build_site_context`を呼ぶ | `manifest_path`がoverride値になる | |
| DIR-004 | 既存ディレクトリがある場合でもエラーにならない | 中 | 事前にディレクトリ作成済み | 2回`ensure_project_directories`を呼ぶ | 例外が発生しない | |

---

## 7. `url_filter.py`（INCLUDE/EXCLUDEフィルタ）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| UF-001 | INCLUDE未設定・EXCLUDE未設定で全て許可 | 最高 | include=[], exclude=[] | 任意URLで`is_included` | `True`が返る | |
| UF-002 | INCLUDE指定パスに一致するURLを許可 | 最高 | include=["/docs"] | `/docs/guide`のURLで判定 | `True`が返る | |
| UF-003 | INCLUDE指定パスに一致しないURLを除外 | 最高 | include=["/docs"] | `/blog/x`のURLで判定 | `False`が返る | |
| UF-004 | EXCLUDE指定パスに一致するURLを除外 | 高 | exclude=["/blog"] | `/blog/x`のURLで判定 | `False`が返る | |
| UF-005 | INCLUDEとEXCLUDEが競合する場合EXCLUDEが優先される | 高 | include=["/docs"], exclude=["/docs/internal"] | `/docs/internal/x`で判定 | `False`が返る（EXCLUDE優先） | |
| UF-006 | 複数INCLUDE条件のいずれかに一致すれば許可 | 中 | include=["/docs","/guides"] | `/guides/x`で判定 | `True`が返る | |

---

## 8. `duplicate_resolver.py`（重複判定）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| DUP-001 | content_sha256重複時、retrieved_atが最新のものが正規扱い | 最高 | 同一sha256の複数metadata | `resolve`を呼ぶ | 最新retrieved_atのページのみcanonicalに残る | `test_newest_retrieved_at_wins` |
| DUP-002 | 重複のないページは全てcanonicalに残る | 最高 | 各ページが異なるsha256 | `resolve`を呼ぶ | 全ページがcanonicalに含まれる | |
| DUP-003 | 除外されたページがexcludedリストに正しく入る | 高 | 重複ありのデータ | `resolve`を呼ぶ | excludedにretrieved_atが古い方のみ含まれる | 部分的に`test_newest_retrieved_at_wins`でカバー |
| DUP-004 | 3件以上が同一sha256の場合、最新1件のみ残り他は全て除外 | 中 | 同一sha256の3件以上 | `resolve`を呼ぶ | canonicalに1件、excludedに残り全件 | |
| DUP-005 | 入力が空リストの場合 | 中 | 空リスト | `resolve([])`を呼ぶ | canonical/excluded共に空リストが返る | |

---

## 9. `chunk_builder.py`（結合Markdown生成）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| CB-001 | WORD_LIMIT以内の複数ページが1ファイルに結合される | 最高 | word_limit十分大きい | 複数ページを渡す | 1つの`docs_001.md`に全ページが結合される | |
| CB-002 | WORD_LIMIT超過時に新しいファイルへ分割される | 最高 | 複数ページ合計がword_limitを超える | ページを渡す | 2つ以上の`docs_XXX.md`に分割される | |
| CB-003 | 1ページが複数ファイルに跨らない | 最高 | 分割が発生する構成 | 分割結果を検証 | 各ページは単一ファイルにのみ含まれる | |
| CB-004 | 単体でWORD_LIMITを超えるページは単独ファイル化＋警告 | 高 | 1ページのword_countがword_limit超過 | ページを渡す | 単独ファイルとして出力され`warnings`にメッセージが入る | |
| CB-005 | chunk_recordsがファイル名と正しく対応する | 高 | 複数ページ・複数ファイル | 結果の`chunk_records`を検証 | 各`ChunkRecord.file`が実際の格納先ファイル名と一致する | |
| CB-006 | 入力が空リストの場合、ファイルが生成されない | 中 | 空のordered_pages | `build_chunks([], {}, limit)` | filesもchunk_recordsも空 | |
| CB-007 | ページ本文がpage_bodiesに存在しない場合の挙動 | 中 | page_bodiesに該当page_hashなし | 該当ページを渡す | 空文字列として扱われエラーにならない（現仕様の確認） | |

---

## 10. `index_builder.py`（Index.md生成）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| IDX-001 | titleが存在する場合はtitleが見出しに使われる | 最高 | title設定済みrecord | `build_index`を呼ぶ | 見出しにtitleが出力される | |
| IDX-002 | titleがNoneの場合はURLで代替表示される（SEQ-11） | 高 | title=Noneのrecord | `build_index`を呼ぶ | 見出しにURLが出力される | |
| IDX-003 | 本文がSUMMARY_CHAR_LIMIT以下ならそのまま概要になる | 中 | 短い本文 | `build_index`を呼ぶ | Summary行が本文全体と一致 | |
| IDX-004 | 本文がSUMMARY_CHAR_LIMIT超過時は省略記号付きで切り詰め | 中 | 長い本文 | `build_index`を呼ぶ | Summaryが120文字＋`...`で切られる | |
| IDX-005 | 空のページリストでもエラーにならない | 中 | 空リスト | `build_index([], {}, "site")` | 例外なくヘッダのみのMarkdownが返る | |

---

## 11. `page_ordering.py`（ページ並び替え）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ORD-001 | sitemap_order未指定時はURL順にソートされる | 最高 | sitemap_order=None | `order_pages`を呼ぶ | URL文字列の昇順で並ぶ | |
| ORD-002 | sitemap_order指定時はsitemap記載順が優先される | 最高 | sitemap_orderあり | `order_pages`を呼ぶ | sitemap記載順に並ぶ | |
| ORD-003 | sitemap未記載のページはsitemap記載ページの後ろに、URL順で並ぶ | 高 | 一部ページのみsitemap記載 | `order_pages`を呼ぶ | 未記載ページが末尾にURL順で並ぶ | |

---

## 12. `diff_checker.py`（差分判定）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| DIFF-001 | MODE=fullの場合は常に無条件取得と判定される | 最高 | config.mode="full" | `decide`を呼ぶ | `FETCH_UNCONDITIONAL`が返る | |
| DIFF-002 | 新規URL（既存レコードなし）は無条件取得と判定される | 最高 | existing=None | `decide`を呼ぶ | `FETCH_UNCONDITIONAL`が返る | |
| DIFF-003 | sitemap lastmodが前回と一致する場合はスキップ判定 | 最高 | existing.sitemap_lastmod == sitemap_lastmod | `decide`を呼ぶ | `SKIP_BY_SITEMAP_LASTMOD`が返る | |
| DIFF-004 | ETagまたはLast-Modifiedがある場合は条件付き取得と判定 | 高 | existing.etag設定済み、lastmod不一致 | `decide`を呼ぶ | `FETCH_CONDITIONAL`が返る | |
| DIFF-005 | ETag/Last-Modifiedもsitemap lastmodもない場合は無条件取得 | 高 | existingあるがetag/last_modified/lastmod全てNone | `decide`を呼ぶ | `FETCH_UNCONDITIONAL`が返る | |
| DIFF-006 | content_changed: sha256が異なる場合True | 高 | 異なるsha256 | `content_changed`を呼ぶ | `True`が返る | |
| DIFF-007 | content_changed: sha256が同一の場合False | 高 | 同一sha256 | `content_changed`を呼ぶ | `False`が返る | |
| DIFF-008 | content_changed: existingがNoneの場合True | 中 | existing=None | `content_changed`を呼ぶ | `True`が返る | |

---

## 13. `robots_parser.py`（robots.txt解析）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ROB-001 | robots.txtが200で取得でき、Disallow指定パスが拒否される | 最高 | httpx.Client.getをモック | `parse`後`is_allowed`を確認 | Disallow対象URLで`False` | |
| ROB-002 | robots.txtが200で取得でき、Allow指定パスが許可される | 最高 | httpx.Client.getをモック | `parse`後`is_allowed`を確認 | Allow対象URLで`True` | |
| ROB-003 | robots.txt取得失敗（404等）時は制限なしとして扱う | 高 | status_code=404を返すモック | `parse`後`is_allowed`を確認 | 任意URLで`True`（制限なし） | |
| ROB-004 | robots.txt取得時にネットワーク例外が発生しても制限なしとして扱う | 高 | RequestExceptionを送出するモック | `parse`を呼ぶ | 例外を吸収し空のparserを返す | |
| ROB-005 | robots.txt内のSitemap行が正しく抽出される | 高 | Sitemap行を含むrobots.txt | `parse`を呼ぶ | `sitemap_urls`に記載URLが含まれる | |
| ROB-006 | 複数Sitemap行がすべて抽出される | 中 | 複数Sitemap行を含むrobots.txt | `parse`を呼ぶ | 全てのURLが`sitemap_urls`に含まれる | |
| ROB-007 | is_allowedでparser内部エラー時はTrueにフォールバック | 中 | can_fetchが例外を送出 | `RobotsParser.is_allowed`を呼ぶ | `True`が返る（安全側フォールバック） | |

---

## 14. `sitemap_fetcher.py`（sitemap取得）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| SM-001 | 通常のsitemap.xml（urlset）からURL一覧が取得できる | 最高 | urlsetのXMLを返すモック | `fetch`を呼ぶ | 記載された全URLがSitemapEntryとして返る | |
| SM-002 | lastmod付きURLでlastmodが正しく取得される | 高 | lastmod付きurlset | `fetch`を呼ぶ | 各エントリの`lastmod`が正しい値になる | |
| SM-003 | sitemap index（再帰展開）から子sitemapのURLも取得できる | 最高 | sitemapindexを返すモック | `fetch`を呼ぶ | 子sitemap内のURLも結果に含まれる | |
| SM-004 | 再帰深度上限（MAX_SITEMAP_DEPTH）に達すると打ち切られる | 中 | 深いネストのsitemapindex | `fetch`を呼ぶ | 上限を超えた階層のURLは含まれない | |
| SM-005 | 同一URLの循環参照で無限ループしない | 高 | 自己参照するsitemapindex | `fetch`を呼ぶ | 無限ループせず処理が終了する | |
| SM-006 | sitemap取得失敗（404等）時は空リストを返す | 高 | status_code=404 | `fetch`を呼ぶ | 空の結果が返る | |
| SM-007 | sitemap.xmlが不正なXMLの場合は空リストを返す | 中 | 不正なXMLを返すモック | `fetch`を呼ぶ | 例外にならず空リストが返る | |
| SM-008 | robots.txt記載のsitemap URLも統合される | 高 | extra_sitemap_urls指定 | `fetch`を呼ぶ | robots.txt由来URLと既定パスの両方が統合される | |
| SM-009 | 複数sitemapで同一URLが重複する場合は後勝ちで統合される | 中 | 同一URLが複数sitemapに存在 | `fetch`を呼ぶ | 重複が除去され1件になる | |

---

## 15. `html_fetcher.py`（HTML取得）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| HF-001 | 200 OKで正常にHTMLが取得できる | 最高 | status_code=200のモック | `fetch`を呼ぶ | `HttpResponse`にtext/etag/last_modifiedが入る | |
| HF-002 | 304 Not Modifiedでtextなしのレスポンスが返る | 最高 | status_code=304のモック | `fetch`を呼ぶ | `status_code=304`, `text=None`が返る | |
| HF-003 | 404でNotFoundErrorが送出される | 最高 | status_code=404のモック | `fetch`を呼ぶ | `NotFoundError`が送出される | |
| HF-004 | 429でTooManyRequestsErrorが送出される | 高 | status_code=429のモック | `fetch`を呼ぶ | `TooManyRequestsError`が送出される | |
| HF-005 | 5xxでServerErrorが送出される | 高 | status_code=500のモック | `fetch`を呼ぶ | `ServerError`が送出される | |
| HF-006 | タイムアウト時にCrawlTimeoutErrorが送出される | 高 | `httpx.TimeoutException`を送出するモック | `fetch`を呼ぶ | `CrawlTimeoutError`が送出される | |
| HF-007 | 接続エラー時にNetworkErrorが送出される | 高 | `httpx.RequestError`を送出するモック | `fetch`を呼ぶ | `NetworkError`が送出される | |
| HF-008 | リダイレクトが正しく追跡される（5ホップ以内） | 高 | 302を3回返した後200を返すモック | `fetch`を呼ぶ | 最終的に200のレスポンスが返る | |
| HF-009 | リダイレクトが5ホップを超えるとNetworkErrorが送出される | 中 | 6回以上302を返すモック | `fetch`を呼ぶ | `NetworkError`が送出される | |
| HF-010 | ETag/Last-ModifiedをIf-None-Match/If-Modified-Sinceとして送信する | 中 | etag/last_modified引数指定 | リクエストヘッダーを検証 | 該当ヘッダーが正しくセットされる | |
| HF-011 | 想定外のステータスコード（3xx以外の非2xx等）でNetworkError | 低 | 想定外status_codeのモック | `fetch`を呼ぶ | `NetworkError`が送出される | |

---

## 16. `markdown_extractor.py`（本文抽出）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| MD-001 | 通常のHTMLからtitle/body_markdownが抽出できる | 最高 | 通常HTML | `extract`を呼ぶ | title・body_markdownが空でない | |
| MD-002 | コードブロックがMarkdown形式で保持される | 高 | `<pre><code>`を含むHTML | `extract`を呼ぶ | 出力Markdownにコードブロック記法が含まれる | |
| MD-003 | 言語(language)が推定できる場合に設定される | 中 | 言語判定可能なHTML | `extract`を呼ぶ | `language`が推定値になる | |
| MD-004 | trafilatura未インストール環境でのフォールバック抽出 | 中 | `_TRAFILATURA_AVAILABLE=False`相当 | フォールバック関数を直接呼ぶ | title/body_markdownが簡易抽出される | |
| MD-005 | 本文が抽出できないHTMLの場合Noneまたは空になる | 中 | 空のbody | `extract`を呼ぶ | `body_markdown`がNoneまたは空文字 | |

---

## 17. `statistics_calculator.py`（統計計算）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| STAT-001 | word_count/char_countが正しく計算される | 最高 | 既知のテキスト | `calculate`を呼ぶ | 期待通りのword_count/char_countが返る | |
| STAT-002 | tiktoken利用可能時にtoken_countが算出される | 高 | tiktoken初期化成功環境 | `calculate`を呼ぶ | token_countが文字数ベース推定と異なる妥当な値になる | |
| STAT-003 | tiktoken初期化失敗時に文字数ベース推定へフォールバック | 高 | `_TRAFILATURA...`ではなく`_TIKTOKEN_AVAILABLE=False`相当 | `_estimate_token_count`を呼ぶ | `char_count // 4`相当の推定値が返る | |
| STAT-004 | 空文字列に対する計算 | 中 | 空文字列 | `calculate("")`を呼ぶ | word_count=0, char_count=0, token_count>=1 | |
| STAT-005 | encode実行時に例外が発生した場合フォールバックする | 中 | encodeが例外を送出するモック | `calculate`を呼ぶ | 例外にならず推定値が返る | |

---

## 18. `manifest_mapper.py` / `manifest_repository.py`（manifest.json操作）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| MAN-001 | SUCCESS結果は全フィールドが更新される | 最高 | 既存レコードあり | `merge_update`(SUCCESS)を呼ぶ | 全フィールドが新しい値で上書きされる | `test_success_full_update` |
| MAN-002 | NETWORK_ERROR時は前回情報が保持される | 最高 | 既存SUCCESSレコードあり | `merge_update`(NETWORK_ERROR)を呼ぶ | etag等は保持されlast_crawled/crawl_resultのみ更新 | `test_network_error_preserves_previous_fields` |
| MAN-003 | NOT_MODIFIEDはmanifestへ書き込まれない | 最高 | なし | `merge_update`(NOT_MODIFIED)を呼ぶ | ファイルに当該URLが記録されない | `test_not_modified_does_not_write` |
| MAN-004 | delete_manyで複数URLが一括削除される | 高 | 複数URL登録済み | `delete_many`を呼ぶ | 指定URLのみ削除され他は残る | `test_delete_many` |
| MAN-005 | ファイル未存在時のload()は空dictを返す | 高 | manifest.json未作成 | `load()`を呼ぶ | 空dictが返る | |
| MAN-006 | NOT_FOUND/ROBOTS_DENIED時も前回情報が保持される | 高 | 既存SUCCESSレコードあり | `merge_update`(NOT_FOUND)を呼ぶ | etag等保持、crawl_resultのみ更新 | |
| MAN-007 | 新規URL（existing=None）でNETWORK_ERROR系が来た場合は新規登録される | 中 | 既存レコードなし | `merge_update`(NETWORK_ERROR, existing=None)を呼ぶ | 新規レコードとして登録される | |
| MAN-008 | manifest_record_to_dict/dict_to_manifest_recordの往復変換が一致する | 高 | ManifestRecordインスタンス | dict変換→dict逆変換 | 元のレコードと一致する | |
| MAN-009 | delete()で存在しないURLを指定してもエラーにならない | 低 | 未登録URL | `delete`を呼ぶ | 例外なく処理が終わる | |

---

## 19. `page_metadata_mapper.py` / `page_metadata_repository.py`（metadata操作）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| PM-001 | save→loadで内容が一致する | 最高 | tmp_path | `save`後`load` | 元のPageMetadataRecordと一致する | |
| PM-002 | exists()がファイル有無を正しく判定する | 高 | 一部のみ保存済み | `exists`を呼ぶ | 保存済みは`True`、未保存は`False` | |
| PM-003 | delete()でファイルが削除される | 高 | 保存済みファイルあり | `delete`後`exists` | `False`が返る | |
| PM-004 | load_all()が全件を(page_hash, record)のタプルで返す | 最高 | 複数ファイル保存済み | `load_all`を呼ぶ | 全件が正しく返る | |
| PM-005 | metadata_dirが存在しない場合load_all()は空リストを返す | 中 | ディレクトリ未作成 | `load_all`を呼ぶ | 空リストが返る | |
| PM-006 | dict_to_page_metadataでdatetimeが正しくパースされる | 中 | ISO8601文字列 | 変換関数を呼ぶ | `retrieved_at`がdatetime型になる | |

---

## 20. `page_repository.py`（本文操作）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| PR-001 | save→load_pageで本文が一致する | 最高 | tmp_path | `save`後`load_page` | 元のMarkdown文字列と一致する | |
| PR-002 | 存在しないpage_hashに対しload_pageでFileNotFoundError | 最高 | 未保存page_hash | `load_page`を呼ぶ | `FileNotFoundError`が送出される | |
| PR-003 | exists()がファイル有無を正しく判定する | 高 | 一部のみ保存済み | `exists`を呼ぶ | 保存済みは`True`、未保存は`False` | |
| PR-004 | delete()でファイルが削除される | 中 | 保存済みファイルあり | `delete`後`exists` | `False`が返る | |

---

## 21. `chunk_mapper.py` / `chunk_manifest_repository.py`

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| CM-001 | save→loadでChunkRecordリストが一致する | 最高 | tmp_path | `save`後`load` | 元のリストと一致する | |
| CM-002 | ファイル未存在時のload()は空リストを返す | 高 | chunk_manifest.json未作成 | `load()`を呼ぶ | 空リストが返る | |
| CM-003 | chunk_records_to_list/list_to_chunk_recordsの往復変換が一致する | 中 | ChunkRecordリスト | 変換の往復 | 元のリストと一致する | |

---

## 22. `config_loader.py`（CLI/`.env`設定統合）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| CFG-001 | CLI引数でURLを指定した場合、単一サイト処理として確定する | 最高 | argv=["https://a.com"] | `load_config`を呼ぶ | `url`が設定され`base_urls=[]` | |
| CFG-002 | CLI引数なし・`.env`にBASE_URLSありで複数サイト処理となる | 最高 | env["BASE_URLS"]設定 | `load_config`を呼ぶ | `base_urls`にリストが入り`url=None` | |
| CFG-003 | URLもBASE_URLSも未指定でConfigError | 最高 | argv=[], env={}（必須項目のみ設定） | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-004 | URL未指定で`--manifest`のみ指定でConfigError | 高 | argv=["--manifest","x.json"] | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-005 | 複数サイト処理時（url省略）に`--manifest`を指定するとConfigError | 高 | argv=[], BASE_URLSあり, --manifest指定 | `load_config`を呼ぶ | `ConfigError`が送出される（07仕様5節） | |
| CFG-006 | MAX_PAGES未設定でConfigError | 最高 | env未設定 | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-007 | TIMEOUT_SECONDS未設定でConfigError | 最高 | env未設定 | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-008 | MODEが不正値でConfigError | 高 | env["MODE"]="invalid" | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-009 | 不正なURLスキーム（http/https以外）でConfigError | 高 | argv=["ftp://x.com"] | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-010 | MAX_PAGES/TIMEOUT_SECONDSが数値変換不可でConfigError | 高 | env["MAX_PAGES"]="abc" | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-011 | 優先順位: CLI引数(--log-level) > .env(LOG_LEVEL) | 高 | 両方指定 | `load_config`を呼ぶ | CLI引数の値が採用される | |
| CFG-012 | デフォルト値の適用（WORD_LIMIT/REQUEST_DELAY等未設定時） | 中 | 該当envキー未設定 | `load_config`を呼ぶ | デフォルト値（450000, 0.5等）が設定される | |
| CFG-013 | INCLUDE/EXCLUDEのカンマ区切りパースが正しく行われる | 中 | env["INCLUDE"]="/a, /b" | `load_config`を呼ぶ | `["/a","/b"]`が設定される | |
| CFG-014 | 不正なLOG_LEVEL指定でConfigError | 中 | env["LOG_LEVEL"]="TRACE" | `load_config`を呼ぶ | `ConfigError`が送出される | |
| CFG-015 | 不正なLOG_FORMAT指定でConfigError | 低 | env["LOG_FORMAT"]="xml" | `load_config`を呼ぶ | `ConfigError`が送出される | |

---

## 23. `gui/config_builder.py`（GUIフォーム→ConfigRecord変換）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| GCB-001 | 単一URL入力がurlフィールドにマッピングされる | 最高 | urls_text="https://example.com" | `build_config_from_form`を呼ぶ | `url`設定、`base_urls=[]` | `test_single_url_maps_to_url_field` |
| GCB-002 | 複数行URL入力がbase_urlsにマッピングされる | 最高 | 複数行urls_text | `build_config_from_form`を呼ぶ | `url=None`、`base_urls`にリスト | `test_multiple_urls_map_to_base_urls` |
| GCB-003 | 空URL入力でConfigError | 最高 | urls_text="   \n  " | `build_config_from_form`を呼ぶ | `ConfigError`が送出される | `test_empty_urls_raises_config_error` |
| GCB-004 | 不正なURLスキームでConfigError | 高 | urls_text="ftp://example.com" | `build_config_from_form`を呼ぶ | `ConfigError`が送出される | `test_invalid_url_scheme_raises_config_error` |
| GCB-005 | 不正なmode値でConfigError | 高 | mode="bogus" | `build_config_from_form`を呼ぶ | `ConfigError`が送出される | `test_invalid_mode_raises_config_error` |
| GCB-006 | include/exclude CSVパース | 高 | include="/docs, /guides", exclude="/blog" | `build_config_from_form`を呼ぶ | 期待通りのリストになる | `test_include_exclude_csv_parsing` |
| GCB-007 | GUIではmanifest_path_overrideが常にNoneになる | 中 | 通常フォーム | `build_config_from_form`を呼ぶ | `manifest_path_override is None` | `test_manifest_override_always_none_for_gui` |
| GCB-008 | 数値項目が数値変換できない場合ConfigError | 高 | word_limit="abc" | `build_config_from_form`を呼ぶ | `ConfigError`が送出される | |
| GCB-009 | 不正なlog_level値でConfigError | 中 | log_level="TRACE" | `build_config_from_form`を呼ぶ | `ConfigError`が送出される | |

---

## 24. `gui/settings_store.py`（設定永続化）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| SS-001 | save_settings→load_settingsで値が復元される | 最高 | tmp path | `save_settings`後`load_settings` | 保存した値が復元される | |
| SS-002 | settings.json未存在時はDEFAULT_SETTINGSが返る | 高 | ファイル未作成 | `load_settings`を呼ぶ | デフォルト値の辞書が返る | |
| SS-003 | 不正なJSON（破損ファイル）時はデフォルトへフォールバック | 中 | 壊れたJSONファイル | `load_settings`を呼ぶ | 例外にならずデフォルト値が返る | |
| SS-004 | 部分的な設定のみ保存されている場合、不足キーはデフォルト補完される | 中 | 一部キーのみのJSON | `load_settings`を呼ぶ | 全キーが存在しデフォルトで補完される | |

---

## 25. `gui/execution_worker.py`（非同期実行管理）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| EW-001 | 初期状態はidleである | 最高 | インスタンス生成直後 | `get_state_snapshot`を確認 | `state=idle`, `is_running=False` | `test_initial_state_is_idle` |
| EW-002 | 不正フォームでstartするとConfigErrorによりfailedへ遷移 | 最高 | urls_text="" | `start`を呼ぶ | `state=failed`, `error_message`あり、スレッドは起動しない | `test_invalid_form_transitions_to_failed_without_thread` |
| EW-003 | 実行中に再度startすると二重実行が無視される | 最高 | 実行中状態 | 実行中に`start`を再度呼ぶ | 状態が変化せず`is_running`のまま | `test_double_start_is_ignored_while_running` |
| EW-004 | 実行開始時にログレベルがルートロガーへ反映される（Issue #4） | 最高 | log_level="ERROR"を含むフォーム | `start`後ロガー状態を確認 | `logging.getLogger().level == ERROR` | `test_issue4_log_level_applied_on_start` |
| EW-005 | 実行完了後、state=completedかつresult_summaryが設定される | 高 | 正常完了するモック構成 | `_run`実行後の状態確認 | `state=completed`, `result_summary`が`BuildResultRecord`要約になる | |
| EW-006 | Orchestrator実行中に予期しない例外が発生した場合failedになる | 高 | Orchestrator.runが例外送出 | `_run`を呼ぶ | `state=failed`, `error_message`にメッセージが入る | |

---

## 26. `gui/js_api.py`（JS公開API）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| JSAPI-001 | get_status(since_index)が差分ログのみ返す | 最高 | ログ2件出力済み | `get_status(-1)`→`get_status(last_index)` | 1回目は全件、2回目は差分のみ返る | `test_js_api_get_status_returns_diff_only` |
| JSAPI-002 | 実行中にstart_executionを呼ぶとalready_runningが返る | 最高 | 実行中状態 | `start_execution`を2回呼ぶ | 1回目`started`、2回目`already_running` | `test_js_api_already_running_response` |
| JSAPI-003 | load_settingsがsettings_storeの値を返す | 高 | settings.json保存済み | `load_settings`を呼ぶ | 保存済み設定が返る | |
| JSAPI-004 | get_app_infoがapp_name/versionを返す | 中 | なし | `get_app_info`を呼ぶ | `app_version`モジュールの値が返る | |
| JSAPI-005 | open_log_folderが例外時にerrorステータスを返す | 低 | subprocess.runが例外送出 | `open_log_folder`を呼ぶ | `{"status":"error", ...}`が返る（例外がAPI外へ漏れない） | |

---

## 27. `url_filter.py` + `crawler_service.py`（Issue #6: 暗黙INCLUDE）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ISS6-001 | INCLUDE未設定時、対象URLのパスが暗黙のINCLUDEとして適用される | 最高 | INCLUDE未設定、対象URLがパスを含む | `process_site`を呼ぶ | 対象パス以外（`/blog/`等）はクロール対象外になる | `test_issue6_implicit_include_from_path` |
| ISS6-002 | INCLUDE明示指定時は明示指定が暗黙スコープより優先される | 最高 | INCLUDE=["/blog"]、対象URLは別パス | `process_site`を呼ぶ | 明示指定パスのみがクロール対象になる | `test_issue6_explicit_include_still_takes_priority` |
| ISS6-003 | 対象URLがドメインルートの場合は暗黙INCLUDEが適用されない | 高 | 対象URL=`https://example.com`（パスなし） | `_resolve_effective_include`を呼ぶ | 空リストが返る（制限なし） | |

---

## 28. `crawler_service.py`（サイト単位クロール統括）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| CS-001 | sitemap利用時に記載URL全件がクロールされる | 最高 | sitemap.xmlあり | `process_site`を呼ぶ | sitemap記載の全URLに対しクロール結果が生成される | 部分的に`test_issue6_implicit_include_from_path`でカバー |
| CS-002 | sitemap不在時にフォールバッククロールへ移行する | 最高 | sitemap.xml/robots.txt Sitemap記載なし | `process_site`を呼ぶ | 同一ドメイン内リンクを辿ってクロールされる | |
| CS-003 | robots.txtでDisallowされたURLはROBOTS_DENIEDとして記録されクロールされない | 高 | robots.txt Disallow設定 | `process_site`を呼ぶ | 該当URLがCrawlResult.ROBOTS_DENIEDでmanifest記録、本文取得なし | |
| CS-004 | 全ページがクロール失敗した場合はfatal_error=Trueになる | 高 | 全ページが404を返す | `process_site`を呼ぶ | `fatal_error=True` | |
| CS-005 | 1件もURLが発見できない場合はfatal_error=Trueになる | 高 | sitemapもフォールバックも空 | `process_site`を呼ぶ | `fatal_error=True` | |
| CS-006 | MAX_PAGES超過時（sitemap利用）は警告ログのみで全件処理される | 中 | sitemap件数 > max_pages | `process_site`を呼ぶ | 全件がクロールされ、打ち切られない | |
| CS-007 | MAX_PAGES到達時（フォールバック）はクロールが打ち切られる | 高 | フォールバッククロールでmax_pages到達 | `process_site`を呼ぶ | `discovery_complete=False`でクロール打ち切り | |
| CS-008 | discovery_complete=Falseの場合、削除ページ判定がスキップされる | 高 | フォールバック打ち切り発生 | `process_site`を呼ぶ | manifestに存在する未発見URLが削除されない | |
| CS-009 | 探索完了時、manifestに存在するが今回発見されなかったURLが削除される | 高 | 前回manifestに余分なURLあり、discovery_complete=True | `process_site`を呼ぶ | 該当URLがmanifestから削除される | |
| CS-010 | 200 OK取得時にpage_repo/metadata_repo/manifest_repoへ正しく保存される | 最高 | 正常な200レスポンス | `process_site`を呼ぶ | 3つのRepositoryそれぞれに整合するデータが保存される | |
| CS-011 | 304 Not Modified時はmanifest書き込みが行われない | 高 | 前回ETag一致で304応答 | `process_site`を呼ぶ | manifestの該当URLが更新されない | |
| CS-012 | sitemap lastmod一致時はHTTPリクエスト自体が省略される | 中 | 前回sitemap_lastmodと今回一致 | `process_site`を呼ぶ | HTMLフェッチが呼び出されない | |

---

## 29. `builder_service.py`（ビルド処理統括）

| テストID | 観点 | 優先度 | 最高 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|---|
| BS-001 | metadataが1件もない場合、警告付きの空結果が返る（エラーにしない） | 最高 | metadata_dirが空 | `build`を呼ぶ | `total_pages_included=0`, `has_fatal_error=False`, warningあり | |
| BS-002 | 正常系: 全metadataからdocs_XXX.md/chunk_manifest.json/Index.mdが生成される | 最高 | metadata・pages本文が複数件存在 | `build`を呼ぶ | 出力ファイルが期待通り生成されBuildResultRecordが正しい | |
| BS-003 | 本文ファイルが見つからない場合BuilderErrorが送出される（要件15節） | 最高 | metadataはあるがpages本文が欠損 | `build`を呼ぶ | `BuilderError`が送出される | |
| BS-004 | 重複ページがtotal_pages_includedから除外される | 高 | 重複content_sha256のmetadata | `build`を呼ぶ | `duplicate_excluded_count`が正しくカウントされる | |
| BS-005 | ページ順序がsitemap順（指定時）で出力される | 中 | sitemap_order指定 | `build`を呼ぶ | docs_XXX.mdの内容順がsitemap順になる | |

---

## 30. `orchestrator.py`（全体オーケストレーション・終了コード判定）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ORC-001 | 全サイト成功時、終了コード0（EXIT_SUCCESS）が返る | 最高 | 全site_resultがhas_fatal_error=False | `run`を呼ぶ | `exit_code==0` | |
| ORC-002 | 1サイト以上が致命的失敗の場合、終了コード2（PARTIAL_FAILURE）が返る | 最高 | 一部site_resultがhas_fatal_error=True | `run`を呼ぶ | `exit_code==2` | |
| ORC-003 | site_resultsが空の場合、終了コード1（EXIT_FATAL）が返る | 高 | 対象URLなし相当 | `_determine_exit_code([])`を呼ぶ | `exit_code==1` | |
| ORC-004 | ロック取得失敗時、当該サイトがhas_fatal_error=Trueとして記録され他サイト処理は続行する | 高 | 2サイト中1つがLockAcquisitionError | `run`を呼ぶ | 失敗サイトはfatal、もう一方は正常に処理される | |
| ORC-005 | クロールが致命的失敗でもキャッシュが存在すればビルド・アーカイブは実行される（SEQ-6） | 高 | crawl_fatal=True、既存キャッシュあり | `_process_one_site`を呼ぶ | build/archiveが呼び出され結果が返る | |
| ORC-006 | ビルド結果0件の場合はアーカイブが実行されない | 中 | build_result.total_pages_included=0 | `_process_one_site`を呼ぶ | `archive_path=None`でarchive未呼び出し | |
| ORC-007 | BuilderErrorが送出された場合、has_fatal_error=Trueの結果が返る | 高 | build()がBuilderErrorを送出 | `_process_one_site`を呼ぶ | `has_fatal_error=True`のBuildResultRecordが返る | |
| ORC-008 | 単一URL指定時と複数base_urls指定時でそれぞれ正しく処理対象が決定される | 高 | url指定 / base_urls指定の2パターン | `run`を呼ぶ | それぞれ対応するサイトのみが処理される | |

---

## 31. `archive_service.py`（ZIPアーカイブ生成）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ARC-001 | output配下のファイルがZIPに正しく格納される | 最高 | output_dirに複数ファイルあり | `archive`を呼ぶ | 生成ZIP内に全ファイルが含まれる | |
| ARC-002 | ファイル名にsite_identifier_YYYYMMDD_HHMMSS.zip形式が使われる | 高 | なし | `archive`を呼ぶ | 命名規則に一致するファイル名が返る | |
| ARC-003 | 同一秒内で2回アーカイブしても既存ZIPを上書きしない仕様の確認 | 中 | 連続archive呼び出し（別タイムスタンプ） | 2回`archive`を呼ぶ | 2つの異なるファイルが生成される | |
| ARC-004 | output_dirが空の場合でも例外にならない | 中 | output_dirが空 | `archive`を呼ぶ | 空のZIPが生成され例外なし | |

---

## 32. `exceptions/errors.py`（例外とCrawlResultの対応）

| テストID | 観点 | 優先度 | 前提条件 | 確認方法 | 期待結果 | テストメソッド名 |
|---|---|---|---|---|---|---|
| ERR-001 | 各Crawl系例外がCRAWL_EXCEPTION_TO_RESULT_VALUEで正しくマッピングされている | 高 | なし | 辞書の内容を検証 | 6種の例外が対応するCrawlResult文字列にマッピングされている | |

---

## テストケース集計（優先度別）

| 優先度 | 件数（目安） |
|---|---|
| 最高 | 約48件 |
| 高 | 約68件 |
| 中 | 約48件 |
| 低 | 約4件 |

---

### 補足
- 「最高」「高」の項目は、正常系の主要分岐（sitemap有無、200/304/404/429/5xx、MODE=incremental/full、単一/複数サイト等）を可能な限り網羅する形で洗い出しています。
- 「中」「低」は代表例のみを列挙しており、網羅性は重視していません。
- `desktop_main.py`（PyWebView起動そのもの）・`web/index.html`・`web/js/main.js`はブラウザ/OS依存が強く、本表では単体テスト対象から除外しています（結合・E2Eテストの対象として別途検討推奨）。
- CI（`.github/workflows/*.yml`）・Dockerfile・インストーラ関連（`installer.iss`等）は単体テスト対象外です。
