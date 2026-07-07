# 00_pytestテストケース一覧表（軽量版）

> 原本：`docs/04_単体テスト/pytestテストケース一覧表.md`（約200件、表形式でテストID・観点・優先度・前提条件・確認方法・期待結果・テストメソッド名を保持）。
> 本ファイルは**実装済みテストのID・観点(1行)・優先度・テストメソッド名**のみを抜き出した軽量版。前提条件・確認方法・期待結果の詳細が必要な場合は原本を参照すること。
> `[NEW]` `[FIX]` の接頭辞はレビュー起因の追加・修正であることを示す（原本の表記をそのまま踏襲）。

凡例：優先度は 最高／高／中／低。

---

## 1. site_identifier.py（サイト識別子生成）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| SID-001 | 基本的な小文字化・記号置換 | 最高 | `test_lowercase_and_symbol_replacement` |
| SID-002 | 末尾スラッシュ有無の同一視 | 最高 | `test_trailing_slash_equivalence` |
| SID-003 | 大文字・小文字表記揺れの同一視 | 高 | `test_case_insensitivity` |
| SID-004 | パスなしドメインのみのURL | 最高 | `test_react_dev_example` |
| SID-005 | 空文字列URLでの例外送出 | 高 | `test_empty_url_raises` |
| SID-006 | 記号の連続圧縮（`://`由来） | 中 | `test_repeated_symbols_collapse` |
| SID-007 | パス末尾以外の連続記号 | 中 | `test_double_slash_in_path_collapses` |
| SID-008 | http/httpsの違いがスキーム除去で無視される | 中 | `test_http_and_https_are_equivalent` |
| SID-009 | サブドメイン・ポート番号を含むURL | 中 | `test_subdomain_and_port_are_converted` |

## 2. url_normalizer.py（URL正規化・page_hash算出）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| URLN-001 | スキーム・ホスト名の小文字化 | 最高 | `test_scheme_and_hostname_lowercased` |
| URLN-002 | デフォルトポート除去（https:443） | 高 | `test_default_port_removed_https` |
| URLN-003 | デフォルトポート除去（http:80） | 高 | `test_default_port_removed_http` |
| URLN-004 | 非デフォルトポートは保持 | 中 | `test_non_default_port_preserved` |
| URLN-005 | フラグメント除去 | 高 | `test_fragment_removed` |
| URLN-006 | クエリパラメータの保持 | 高 | `test_query_preserved` |
| URLN-007 | パス省略時のルート補完 | 中 | `test_missing_path_defaults_to_root` |
| [FIX] URLN-008 | 末尾スラッシュ有無はページURLとして区別される（同一視しない） | 高 | `test_trailing_slash_is_not_normalized_away` |
| URLN-009 | page_hashの決定性 | 最高 | `test_page_hash_is_deterministic` |
| URLN-010 | page_hashが異なるURLで異なる値になる | 高 | `test_page_hash_differs_for_different_urls` |

## 3. atomic_io.py（アトミック書き込み）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| AIO-001 | JSON書き込み後にファイルが読み書き可能 | 最高 | `test_atomic_write_json_creates_readable_file` |
| AIO-002 | テキスト書き込み後にファイルが読み書き可能 | 最高 | `test_atomic_write_text_creates_readable_file` |
| AIO-003 | read_jsonで書き込んだ内容を正しく読み戻せる | 最高 | `test_read_json_round_trip` |
| AIO-004 | 既存ファイルへの上書きが成功する | 高 | `test_overwrite_existing_file` |
| AIO-005 | 親ディレクトリが存在しない場合に自動作成される | 高 | `test_parent_directory_auto_created` |
| AIO-006 | 書き込み中に例外発生時、一時ファイルが残らない | 中 | `test_no_tmp_file_left_on_writer_exception` |
| [NEW] AIO-007 | fchmodが例外を送出する環境でも書き込みが継続する | 中 | `test_fchmod_failure_is_swallowed` |

## 4. site_lock.py（サイト単位排他ロック）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| LOCK-001 | ロック取得・解放後にファイルが読み書き可能 | 最高 | `test_site_lock_creates_readable_file` |
| LOCK-002 | 同一ロックファイルへの二重取得で例外送出 | 高 | `test_double_acquire_raises_lock_error` |
| LOCK-003 | ロック解放後は再取得できる | 高 | `test_lock_can_be_reacquired_after_release` |
| LOCK-004 | 例外発生時でもロックが確実に解放される | 中 | `test_lock_released_even_on_exception` |
| [NEW] LOCK-005 | fcntl非対応環境でPIDベースの簡易排他ロックが機能する | 高 | `test_pid_based_fallback_lock_when_fcntl_unavailable` |
| [NEW] LOCK-006 | ロックファイルの親ディレクトリが存在しない場合に自動作成される | 中 | `test_lock_parent_directory_auto_created` |

## 5. logging_setup.py（ログ設定）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| LOG-001 | ログファイル作成後に読み書き可能 | 最高 | `test_setup_logging_creates_readable_file` |
| LOG-002 | ログレベルがルートロガーへ反映される | 高 | `test_log_level_applied_to_root_logger` |
| LOG-003 | text形式のフォーマットで出力される | 中 | `test_text_format_output` |
| LOG-004 | json形式のフォーマットで出力される | 中 | `test_json_format_output_is_parseable` |
| LOG-005 | 既存ハンドラの重複登録防止（再実行時） | 中 | `test_repeated_setup_does_not_accumulate_handlers` |
| [NEW] LOG-006 | RotatingFileHandlerのmaxBytes/backupCountが正しく設定される | 中 | `test_rotating_file_handler_parameters` |

## 6. directory_bootstrap.py（ディレクトリ自動生成）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| DIR-001 | cache/output/archives/logsのみ作成しtestsは作成しない（Issue #5） | 最高 | `test_issue5_tests_dir_not_created` |
| DIR-002 | build_site_contextでサイト単位ディレクトリが生成される | 高 | `test_build_site_context_creates_per_site_directories` |
| DIR-003 | manifest_path_override指定時にmanifestパスが上書きされる | 高 | `test_manifest_path_override_applied` |
| DIR-004 | 既存ディレクトリがある場合でもエラーにならない | 中 | `test_ensure_project_directories_idempotent` |
| [NEW] DIR-005 | build_site_contextが返すSiteContextRecordの各フィールドが期待通り | 高 | `test_site_context_record_fields_match_expected_paths` |

## 7. url_filter.py（INCLUDE/EXCLUDEフィルタ）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| UF-001 | INCLUDE未設定・EXCLUDE未設定で全て許可 | 最高 | `test_no_include_no_exclude_allows_all` |
| [FIX] UF-002 | INCLUDE指定パスに前方一致するURLを許可 | 最高 | `test_include_prefix_match_allows` |
| [FIX] UF-003 | INCLUDE指定パスに前方一致しないURLを除外 | 最高 | `test_include_prefix_mismatch_excludes` |
| UF-004 | EXCLUDE指定パスに前方一致するURLを除外 | 高 | `test_exclude_prefix_match_excludes` |
| UF-005 | INCLUDEとEXCLUDEが競合する場合EXCLUDEが優先される | 高 | `test_exclude_takes_priority_over_include` |
| UF-006 | 複数INCLUDE条件のいずれかに一致すれば許可 | 中 | `test_any_of_multiple_include_patterns_matches` |
| [NEW] UF-007 | 前方一致の仕様上、意図しない部分一致が発生するケース | 中 | `test_prefix_match_causes_unintended_partial_match` |

## 8. duplicate_resolver.py（重複判定）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| DUP-001 | content_sha256重複時、retrieved_atが最新のものが正規扱い | 最高 | `test_newest_retrieved_at_wins` |
| DUP-002 | 重複のないページは全てcanonicalに残る | 最高 | `test_all_unique_pages_remain_canonical` |
| DUP-003 | 除外されたページがexcludedリストに正しく入る | 高 | `test_excluded_pages_contain_older_duplicate_only` |
| DUP-004 | 3件以上が同一sha256の場合、最新1件のみ残り他は全て除外 | 中 | `test_three_or_more_duplicates_only_newest_kept` |
| DUP-005 | 入力が空リストの場合 | 中 | `test_empty_input_returns_empty_result` |
| [NEW] DUP-006 | retrieved_at完全同一の重複は入力順（安定ソート）で先頭が正規扱い | 中 | `test_same_retrieved_at_keeps_first_in_input_order` |

## 9. chunk_builder.py（結合Markdown生成）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| CB-001 | WORD_LIMIT以内の複数ページが1ファイルに結合される | 最高 | `test_pages_within_word_limit_combined_into_one_file` |
| CB-002 | WORD_LIMIT超過時に新しいファイルへ分割される | 最高 | `test_word_limit_exceeded_splits_into_new_file` |
| CB-003 | 1ページが複数ファイルに跨らない | 最高 | `test_single_page_never_spans_multiple_files` |
| CB-004 | 単体でWORD_LIMIT超過ページは単独ファイル化＋警告 | 高 | `test_single_page_exceeding_limit_gets_own_file_with_warning` |
| CB-005 | chunk_recordsがファイル名と正しく対応する | 高 | `test_chunk_records_reference_correct_filenames` |
| CB-006 | 入力が空リストの場合、ファイルが生成されない | 中 | `test_empty_input_produces_no_files` |
| CB-007 | ページ本文がpage_bodiesに存在しない場合の挙動 | 中 | `test_missing_page_body_treated_as_empty_string` |
| [NEW] CB-008 | WORD_LIMIT境界値の挙動（丁度は分割されず、1語超過で分割） | 高 | `test_word_limit_boundary_exact_vs_exceeded` |

## 10. index_builder.py（Index.md生成）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| IDX-001 | titleが存在する場合はtitleが見出しに使われる | 最高 | `test_title_used_as_heading_when_present` |
| IDX-002 | titleがNoneの場合はURLで代替表示（SEQ-11） | 高 | `test_url_used_as_heading_when_title_is_none` |
| [FIX] IDX-003 | 本文が120文字以下ならそのまま概要になる | 中 | `test_summary_under_limit_shown_in_full` |
| [FIX] IDX-004 | 本文が120文字超過時は先頭120文字＋`...`に切り詰め | 中 | `test_summary_over_limit_truncated_with_ellipsis` |
| IDX-005 | 空のページリストでもエラーにならない | 中 | `test_empty_page_list_produces_header_only` |

## 11. page_ordering.py（ページ並び替え）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| ORD-001 | sitemap_order未指定時はURL順にソートされる | 最高 | `test_no_sitemap_order_sorts_by_url` |
| ORD-002 | sitemap_order指定時はsitemap記載順が優先される | 最高 | `test_sitemap_order_takes_priority` |
| ORD-003 | sitemap未記載のページは記載ページの後ろにURL順で並ぶ | 高 | `test_pages_not_in_sitemap_appear_after_sitemap_pages_in_url_order` |
| [NEW] ORD-004 | ソートキー構造：未記載ページは共通インデックス値でソートされる | 中 | `test_sort_key_structure_unlisted_pages_share_common_index` |

## 12. diff_checker.py（差分判定）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| DIFF-001 | MODE=fullの場合は常に無条件取得と判定 | 最高 | `test_mode_full_always_fetches_unconditionally` |
| DIFF-002 | 新規URL（既存レコードなし）は無条件取得と判定 | 最高 | `test_new_url_with_no_existing_record_fetches_unconditionally` |
| DIFF-003 | sitemap lastmodが前回と一致する場合はスキップ判定 | 最高 | `test_matching_sitemap_lastmod_skips_fetch` |
| [FIX] DIFF-004 | lastmod不一致でETag/Last-Modifiedがある場合は条件付き取得 | 高 | `test_etag_present_with_mismatched_sitemap_lastmod_fetches_conditionally` |
| DIFF-005 | ETag/Last-Modified/sitemap lastmod全てない場合は無条件取得 | 高 | `test_no_etag_no_last_modified_no_sitemap_lastmod_fetches_unconditionally` |
| DIFF-006 | content_changed: sha256が異なる場合True | 高 | `test_content_changed_true_when_sha256_differs` |
| DIFF-007 | content_changed: sha256が同一の場合False | 高 | `test_content_changed_false_when_sha256_matches` |
| DIFF-008 | content_changed: existingがNoneの場合True | 中 | `test_content_changed_true_when_existing_is_none` |

## 13. robots_parser.py（robots.txt解析）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| ROB-001 | robots.txt取得成功時、Disallow指定パスが拒否される | 最高 | `test_disallowed_path_is_rejected` |
| ROB-002 | robots.txt取得成功時、Allow指定パスが許可される | 最高 | `test_allowed_path_is_permitted` |
| ROB-003 | robots.txt取得失敗（404等）時は制限なしとして扱う | 高 | `test_robots_fetch_failure_status_treated_as_unrestricted` |
| ROB-004 | robots.txt取得時のネットワーク例外も制限なしとして扱う | 高 | `test_network_exception_treated_as_unrestricted` |
| ROB-005 | robots.txt内のSitemap行が正しく抽出される | 高 | `test_sitemap_line_is_extracted` |
| ROB-006 | 複数Sitemap行がすべて抽出される | 中 | `test_multiple_sitemap_lines_all_extracted` |
| ROB-007 | is_allowedでparser内部エラー時はTrueにフォールバック | 中 | `test_is_allowed_falls_back_to_true_on_internal_error` |
| [NEW] ROB-008 | parse()の戻り値が(RobotFileParser, List[str])のタプルであること | 中 | `test_parse_returns_tuple_of_parser_and_list` |

## 14. sitemap_fetcher.py（sitemap取得）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| SM-001 | urlsetからURL一覧が取得できる | 最高 | `test_urlset_returns_all_urls` |
| SM-002 | lastmod付きURLでlastmodが正しく取得される | 高 | `test_lastmod_extracted_correctly` |
| SM-003 | sitemap index（再帰展開）から子sitemapのURLも取得できる | 最高 | `test_sitemap_index_recursively_expanded` |
| SM-004 | 再帰深度上限に達すると打ち切られる | 中 | `test_recursion_depth_limit_stops_deep_nesting` |
| SM-005 | 同一URLの循環参照で無限ループしない | 高 | `test_self_referencing_sitemap_index_does_not_infinite_loop` |
| SM-006 | sitemap取得失敗（404等）時は空リストを返す | 高 | `test_fetch_failure_returns_empty_list` |
| SM-007 | 不正なXMLの場合は空リストを返す | 中 | `test_malformed_xml_returns_empty_list` |
| SM-008 | robots.txt記載のsitemap URLも統合される | 高 | `test_robots_txt_sitemap_urls_are_merged` |
| SM-009 | 複数sitemapで同一URL重複時は後勝ちで統合される | 中 | `test_duplicate_urls_across_sitemaps_deduplicated` |
| [NEW] SM-010 | ルート要素が想定外XML構造の場合は空リストを返す | 中 | `test_unrecognized_root_element_returns_empty_list` |

## 15. html_fetcher.py（HTML取得）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| HF-001 | 200 OKで正常にHTMLが取得できる | 最高 | `test_200_ok_returns_populated_response` |
| HF-002 | 304 Not Modifiedでtextなしのレスポンスが返る | 最高 | `test_304_not_modified_returns_no_text` |
| HF-003 | 404でNotFoundErrorが送出される | 最高 | `test_404_raises_not_found_error` |
| HF-004 | 429でTooManyRequestsErrorが送出される | 高 | `test_429_raises_too_many_requests_error` |
| HF-005 | 5xxでServerErrorが送出される | 高 | `test_5xx_raises_server_error` |
| HF-006 | タイムアウト時にCrawlTimeoutErrorが送出される | 高 | `test_timeout_raises_crawl_timeout_error` |
| HF-007 | 接続エラー時にNetworkErrorが送出される | 高 | `test_connection_error_raises_network_error` |
| HF-008 | リダイレクトが正しく追跡される（5ホップ以内） | 高 | `test_redirect_followed_within_hop_limit` |
| HF-009 | リダイレクトが5ホップ超過でNetworkError | 中 | `test_exceeding_max_redirect_hops_raises_network_error` |
| HF-010 | ETag/Last-Modifiedを条件付きヘッダーとして送信する | 中 | `test_etag_and_last_modified_sent_as_conditional_headers` |
| HF-011 | 想定外のステータスコードでNetworkError | 低 | `test_unexpected_status_code_raises_network_error` |
| [NEW] HF-012 | リダイレクト応答にLocationヘッダーがない場合は打ち切って続行 | 中 | `test_redirect_without_location_header_breaks_loop_and_returns_response` |
| [NEW] HF-013 | リダイレクト追跡中のタイムアウト/接続エラーも正しく例外送出 | 中 | `test_timeout_during_redirect_follow_raises_crawl_timeout_error` |

## 16. markdown_extractor.py（本文抽出）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| MD-001 | 通常のHTMLからtitle/body_markdownが抽出できる | 最高 | `test_extracts_title_and_body_from_normal_html` |
| MD-002 | コードブロックがMarkdown形式で保持される | 高 | `test_code_block_preserved_in_markdown` |
| MD-003 | 言語(language)が推定できる場合に設定される | 中 | `test_language_is_set_when_detectable` |
| MD-004 | trafilatura未インストール環境でのフォールバック抽出 | 中 | `test_fallback_extraction_used_when_trafilatura_unavailable` |
| MD-005 | 本文が抽出できないHTMLの場合Noneまたは空になる | 中 | `test_empty_body_returns_none_or_empty` |
| [NEW] MD-006 | フォールバック抽出で`<title>`タグがない場合titleがNoneになる | 中 | `test_fallback_extraction_title_none_when_missing` |

## 17. statistics_calculator.py（統計計算）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| STAT-001 | word_count/char_countが正しく計算される | 最高 | `test_word_and_char_count_computed_correctly` |
| STAT-002 | tiktoken利用可能時にtoken_countが算出される | 高 | `test_token_count_uses_tiktoken_when_available` |
| STAT-003 | tiktoken初期化失敗時に文字数ベース推定へフォールバック | 高 | `test_token_count_falls_back_to_char_based_estimate_when_tiktoken_unavailable` |
| [FIX] STAT-004 | 空文字列（フォールバック時）はtoken_count=1になる | 中 | `test_empty_string_fallback_token_count_is_exactly_one` |
| [NEW] STAT-005 | 空文字列（tiktoken利用可能時）はmax(1,...)が適用されない | 低 | `test_empty_string_tiktoken_branch_not_forced_to_one` |
| STAT-006（旧STAT-005） | encode例外発生時フォールバックする | 中 | `test_encode_exception_falls_back_to_estimation` |

## 18. manifest_mapper.py / manifest_repository.py

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| MAN-001 | SUCCESS結果は全フィールドが更新される | 最高 | `test_success_full_update` |
| MAN-002 | NETWORK_ERROR時は前回情報が保持される | 最高 | `test_network_error_preserves_previous_fields` |
| MAN-003 | NOT_MODIFIEDはmanifestへ書き込まれない | 最高 | `test_not_modified_does_not_write` |
| MAN-004 | delete_manyで複数URLが一括削除される | 高 | `test_delete_many` |
| MAN-005 | ファイル未存在時のload()は空dictを返す | 高 | `test_load_returns_empty_dict_when_file_missing` |
| MAN-006 | NOT_FOUND/ROBOTS_DENIED時も前回情報が保持される | 高 | `test_not_found_and_robots_denied_preserve_previous_fields` |
| [FIX] MAN-007 | existing=None時はcrawl_result種別に関わらず全フィールド新規登録 | 中 | `test_no_existing_record_registers_new_record_fully_regardless_of_result` |
| MAN-008 | manifest_record⇔dict往復変換が一致する | 高 | `test_manifest_record_roundtrip_conversion` |
| MAN-009 | delete()で存在しないURLを指定してもエラーにならない | 低 | `test_delete_nonexistent_url_does_not_raise` |
| [NEW] MAN-010 | delete_manyで対象URL全てが未登録ならsave()が呼ばれない | 中 | `test_delete_many_with_no_matching_urls_does_not_save` |

## 19. page_metadata_mapper.py / page_metadata_repository.py

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| PM-001 | save→loadで内容が一致する | 最高 | `test_save_then_load_round_trip` |
| PM-002 | exists()がファイル有無を正しく判定する | 高 | `test_exists_reflects_file_presence` |
| PM-003 | delete()でファイルが削除される | 高 | `test_delete_removes_file` |
| PM-004 | load_all()が全件を(page_hash, record)タプルで返す | 最高 | `test_load_all_returns_all_records_as_tuples` |
| PM-005 | metadata_dir未存在時、load_all()は空リストを返す | 中 | `test_load_all_returns_empty_list_when_directory_missing` |
| PM-006 | dict→PageMetadataでdatetimeが正しくパースされる | 中 | `test_dict_to_page_metadata_parses_datetime_correctly` |

## 20. page_repository.py（本文操作）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| PR-001 | save→load_pageで本文が一致する | 最高 | `test_save_then_load_page_round_trip` |
| PR-002 | 存在しないpage_hashでload_pageがFileNotFoundError | 最高 | `test_load_page_raises_for_missing_hash` |
| PR-003 | exists()がファイル有無を正しく判定する | 高 | `test_exists_reflects_file_presence` |
| PR-004 | delete()でファイルが削除される | 中 | `test_delete_removes_file` |

## 21. chunk_mapper.py / chunk_manifest_repository.py

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| CM-001 | save→loadでChunkRecordリストが一致する | 最高 | `test_save_then_load_round_trip` |
| CM-002 | ファイル未存在時のload()は空リストを返す | 高 | `test_load_returns_empty_list_when_file_missing` |
| CM-003 | chunk_records⇔list往復変換が一致する | 中 | `test_chunk_records_to_list_and_back_round_trip` |
| [NEW] CM-004 | ChunkManifestRepositoryのsave→loadサイクル（Repository層確認） | 高 | `test_chunk_manifest_repository_save_load_cycle_with_multiple_records` |

## 22. config_loader.py（CLI/`.env`設定統合）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| CFG-001 | CLI引数でURL指定時、単一サイト処理として確定 | 最高 | `test_cli_url_confirms_single_site_processing` |
| CFG-002 | CLI引数なし・`.env`にBASE_URLSありで複数サイト処理 | 最高 | `test_no_cli_url_with_base_urls_becomes_multi_site` |
| CFG-003 | URLもBASE_URLSも未指定でConfigError | 最高 | `test_no_url_and_no_base_urls_raises_config_error` |
| CFG-004 | URL未指定で`--manifest`のみ指定でConfigError | 高 | `test_manifest_without_url_raises_config_error` |
| CFG-005 | 複数サイト処理時に`--manifest`指定でConfigError | 高 | `test_manifest_with_base_urls_multi_site_raises_config_error` |
| CFG-006 | MAX_PAGES未設定でConfigError | 最高 | `test_max_pages_missing_raises_config_error` |
| CFG-007 | TIMEOUT_SECONDS未設定でConfigError | 最高 | `test_timeout_seconds_missing_raises_config_error` |
| CFG-008 | MODEが不正値でConfigError | 高 | `test_invalid_mode_raises_config_error` |
| CFG-009 | 不正なURLスキームでConfigError | 高 | `test_invalid_url_scheme_raises_config_error` |
| CFG-010 | MAX_PAGES/TIMEOUT_SECONDSが数値変換不可でConfigError | 高 | `test_max_pages_non_numeric_raises_config_error` |
| CFG-011 | 優先順位：CLI(--log-level) > .env(LOG_LEVEL) | 高 | `test_cli_log_level_overrides_env_log_level` |
| CFG-012 | デフォルト値の適用（未設定時） | 中 | `test_default_values_applied_when_optional_env_missing` |
| CFG-013 | INCLUDE/EXCLUDEのカンマ区切りパース | 中 | `test_include_exclude_csv_parsed_correctly` |
| CFG-014 | 不正なLOG_LEVEL指定でConfigError | 中 | `test_invalid_log_level_raises_config_error` |
| CFG-015 | 不正なLOG_FORMAT指定でConfigError | 低 | `test_invalid_log_format_raises_config_error` |
| [NEW] CFG-016 | CLI引数URL指定時はBASE_URLSより優先される | 高 | `test_cli_url_takes_priority_over_base_urls` |
| [NEW] CFG-017 | WORD_LIMIT/REQUEST_DELAYが数値変換不可でConfigError | 高 | `test_word_limit_or_request_delay_non_numeric_raises_config_error` |

## 23. gui/config_builder.py（GUIフォーム→ConfigRecord変換）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| GCB-001 | 単一URL入力がurlフィールドにマッピングされる | 最高 | `test_single_url_maps_to_url_field` |
| GCB-002 | 複数行URL入力がbase_urlsにマッピングされる | 最高 | `test_multiple_urls_map_to_base_urls` |
| GCB-003 | 空URL入力でConfigError | 最高 | `test_empty_urls_raises_config_error` |
| GCB-004 | 不正なURLスキームでConfigError（単一URL） | 高 | `test_invalid_url_scheme_raises_config_error` |
| GCB-005 | 不正なmode値でConfigError | 高 | `test_invalid_mode_raises_config_error` |
| GCB-006 | include/exclude CSVパース | 高 | `test_include_exclude_csv_parsing` |
| GCB-007 | GUIではmanifest_path_overrideが常にNoneになる | 中 | `test_manifest_override_always_none_for_gui` |
| GCB-008 | 数値項目が数値変換できない場合ConfigError | 高 | `test_non_numeric_word_limit_raises_config_error` |
| GCB-009 | 不正なlog_level値でConfigError | 中 | `test_invalid_log_level_raises_config_error` |
| [NEW] GCB-010 | 複数行URLのうち1行でも不正スキームがあればConfigError | 高 | `test_one_invalid_url_among_multiple_lines_raises_config_error` |

## 24. gui/settings_store.py（設定永続化）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| SS-001 | save_settings→load_settingsで値が復元される | 最高 | `test_save_then_load_round_trips_values` |
| SS-002 | settings.json未存在時はDEFAULT_SETTINGSが返る | 高 | `test_missing_settings_file_returns_defaults` |
| SS-003 | 不正なJSON（破損ファイル）時はデフォルトへフォールバック | 中 | `test_corrupt_json_falls_back_to_defaults` |
| SS-004 | 部分的な設定のみ保存時、不足キーはデフォルト補完される | 中 | `test_partial_settings_are_merged_with_defaults` |

## 25. gui/execution_worker.py（非同期実行管理）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| EW-001 | 初期状態はidleである | 最高 | `test_initial_state_is_idle` |
| EW-002 | 不正フォームでstart時ConfigErrorによりfailedへ遷移 | 最高 | `test_invalid_form_transitions_to_failed_without_thread` |
| EW-003 | 実行中に再度startすると二重実行が無視される | 最高 | `test_double_start_is_ignored_while_running` |
| EW-004 | 実行開始時にログレベルがルートロガーへ反映される（Issue #4） | 最高 | `test_issue4_log_level_applied_on_start` |
| EW-005 | 実行完了後、state=completedかつresult_summaryが設定される | 高 | `test_execution_completes_with_result_summary` |
| EW-006 | Orchestrator実行中に予期しない例外が発生した場合failedになる | 高 | `test_unexpected_exception_during_run_transitions_to_failed` |
| [NEW] EW-007 | get_state_snapshot()が独立コピーを返す | 高 | `test_get_state_snapshot_returns_independent_copy` |

## 26. gui/js_api.py（JS公開API）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| JSAPI-001 | get_status(since_index)が差分ログのみ返す | 最高 | `test_js_api_get_status_returns_diff_only` |
| JSAPI-002 | 実行中にstart_executionを呼ぶとalready_runningが返る | 最高 | `test_js_api_already_running_response` |
| JSAPI-003 | load_settingsがsettings_storeの値を返す | 高 | `test_load_settings_returns_settings_store_value` |
| JSAPI-004 | get_app_infoがapp_name/versionを返す | 中 | `test_get_app_info_returns_app_name_and_version` |
| JSAPI-005 | open_log_folderが例外時にerrorステータスを返す | 低 | `test_open_log_folder_returns_error_status_on_exception` |
| [NEW] JSAPI-006 | start_execution呼び出し時にsave_settingsが呼び出される（IMPL-4） | 中 | `test_start_execution_saves_settings` |

## 27. url_filter.py + crawler_service.py（Issue #6: 暗黙INCLUDE）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| ISS6-001 | INCLUDE未設定時、対象URLのパスが暗黙INCLUDEとして適用される | 最高 | `test_issue6_implicit_include_from_path` |
| ISS6-002 | INCLUDE明示指定時は暗黙スコープより優先される | 最高 | `test_issue6_explicit_include_still_takes_priority` |
| ISS6-003 | 対象URLがドメインルートの場合は暗黙INCLUDEが適用されない | 高 | `test_issue6_domain_root_url_has_no_implicit_include` |

## 28. crawler_service.py（サイト単位クロール統括）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| CS-001 | sitemap利用時に記載URL全件がクロールされる | 最高 | `test_sitemap_all_entries_crawled` |
| CS-002 | sitemap不在時にフォールバッククロールへ移行する | 最高 | `test_no_sitemap_falls_back_to_link_crawling` |
| CS-003 | robots.txtでDisallowされたURLはROBOTS_DENIEDとして記録される | 高 | `test_robots_disallowed_url_recorded_and_not_crawled` |
| CS-004 | 全ページがクロール失敗した場合はfatal_error=Trueになる | 高 | `test_all_pages_failing_marks_fatal_error` |
| CS-005 | 1件もURLが発見できない場合はfatal_error=Trueになる | 高 | `test_no_urls_discovered_marks_fatal_error` |
| CS-006 | MAX_PAGES超過時（sitemap利用）は警告ログのみで全件処理 | 中 | `test_max_pages_exceeded_via_sitemap_still_processes_all` |
| CS-007 | MAX_PAGES到達時（フォールバック）はクロールが打ち切られる | 高 | `test_max_pages_reached_truncates_fallback_crawl` |
| CS-008 | discovery_complete=Falseの場合、削除ページ判定がスキップされる | 高 | `test_discovery_incomplete_skips_deletion_guard` |
| CS-009 | 探索完了時、未発見URLがmanifestから削除される | 高 | `test_discovery_complete_deletes_undiscovered_url` |
| CS-010 | 200 OK取得時に3つのRepositoryへ正しく保存される | 最高 | `test_200_ok_saved_to_all_three_repositories` |
| CS-011 | 304 Not Modified時はmanifest書き込みが行われない | 高 | `test_304_not_modified_does_not_update_manifest` |
| CS-012 | sitemap lastmod一致時はHTTPリクエスト自体が省略される | 中 | `test_sitemap_lastmod_match_skips_http_fetch_entirely` |
| [NEW] CS-013 | _crawl_oneがSKIP判定時`(None, [])`を返し結果に追加されない | 高 | `test_crawl_one_skip_by_sitemap_lastmod_returns_none_and_no_result` |
| [NEW] CS-014 | フォールバッククロールで同一ドメイン外リンクはキューに追加されない | 中 | `test_fallback_crawl_ignores_external_domain_links` |
| [NEW] CS-015 | _apply_deletion_guardがフィルタ範囲内かつ未発見URLのみ削除する | 高 | `test_deletion_guard_respects_current_include_exclude_filter` |

## 29. builder_service.py（ビルド処理統括）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| BS-001 | metadataが1件もない場合、警告付き空結果が返る（エラーにしない） | 最高 | `test_no_metadata_returns_empty_result_without_fatal_error` |
| BS-002 | 正常系：全metadataからdocs_XXX.md等が生成される | 最高 | `test_full_build_generates_expected_output_files` |
| BS-003 | 本文ファイルが見つからない場合BuilderErrorが送出される（要件15節） | 最高 | `test_missing_page_body_raises_builder_error` |
| BS-004 | 重複ページがtotal_pages_includedから除外される | 高 | `test_duplicate_pages_excluded_from_total_count` |
| BS-005 | ページ順序がsitemap順（指定時）で出力される | 中 | `test_page_order_follows_sitemap_order_when_given` |

## 30. orchestrator.py（全体オーケストレーション・終了コード判定）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| ORC-001 | 全サイト成功時、終了コード0が返る | 最高 | `test_all_sites_succeed_returns_exit_success` |
| ORC-002 | 1サイト以上致命的失敗時、終了コード2が返る | 最高 | `test_one_site_fatal_returns_exit_partial_failure` |
| ORC-003 | site_resultsが空の場合、終了コード1が返る | 高 | `test_empty_site_results_returns_exit_fatal` |
| ORC-004 | ロック取得失敗時、当該サイトのみfatal扱いで他は継続する | 高 | `test_lock_failure_marks_site_fatal_but_continues_other_sites` |
| [FIX] ORC-005 | クロール致命的失敗でもキャッシュがあればビルド・アーカイブは実行（SEQ-6） | 高 | `test_crawl_fatal_but_cache_exists_still_runs_build_and_archive` |
| ORC-006 | ビルド結果0件の場合はアーカイブが実行されない | 中 | `test_zero_pages_built_skips_archive` |
| ORC-007 | BuilderError送出時、has_fatal_error=Trueの結果が返る | 高 | `test_builder_error_results_in_fatal_build_result` |
| ORC-008 | 単一URL/複数base_urls指定でそれぞれ正しく処理対象が決定される | 高 | `test_single_url_and_multi_base_urls_target_correct_sites` |

## 31. archive_service.py（ZIPアーカイブ生成）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| ARC-001 | output配下のファイルがZIPに正しく格納される | 最高 | `test_output_files_included_in_zip` |
| ARC-002 | ファイル名に命名規則が使われる | 高 | `test_archive_filename_matches_naming_convention` |
| ARC-003 | 連続archive呼び出しで既存ZIPを上書きしない | 中 | `test_repeated_archive_calls_produce_distinct_files` |
| ARC-004 | output_dirが空の場合でも例外にならない | 中 | `test_empty_output_dir_produces_empty_zip_without_error` |

## 32. exceptions/errors.py（例外とCrawlResultの対応）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| [FIX] ERR-001 | 各Crawl系例外（6種）が正しくマッピングされている | 高 | `test_all_six_crawl_exceptions_mapped_to_expected_crawl_results` |
| [NEW] ERR-002 | RobotsDeniedErrorが"ROBOTS_DENIED"にマッピングされている | 中 | `test_robots_denied_error_maps_to_robots_denied_value` |

## 33. gui/log_buffer.py（InMemoryLogHandler）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| [NEW] LB-001 | emit()でログが蓄積され、get_lines_sinceで差分取得できる | 最高 | `test_emit_accumulates_and_get_lines_since_returns_all` |
| [NEW] LB-002 | get_lines_since(index)で指定index以降の差分のみ返る | 高 | `test_get_lines_since_returns_only_new_entries` |
| [NEW] LB-003 | max_linesを超えるログは古いものから破棄される | 中 | `test_ring_buffer_discards_oldest_entries_beyond_max_lines` |
| [NEW] LB-004 | clear()でバッファ・インデックスがリセットされる | 中 | `test_clear_resets_buffer_and_index` |
| [NEW] LB-005 | フォーマット例外発生時はgetMessage()にフォールバックする | 低 | `test_format_exception_falls_back_to_get_message` |

## 34. gui/user_paths.py（データ保存先パス解決）

| ID | 観点 | 優先度 | テストメソッド名 |
|---|---|---|---|
| [NEW] UP-001 | get_app_data_root()が期待パスを返しディレクトリが作成される | 高 | `test_get_app_data_root_creates_expected_directory` |
| [NEW] UP-002 | get_settings_path()がapp_data_root配下のsettings.jsonを返す | 中 | `test_get_settings_path_is_under_app_data_root` |
| [NEW] UP-003 | 各get_*_root()が対応ディレクトリを作成して返す | 高 | `test_get_cache_output_archives_logs_roots_are_created` |
| [NEW] UP-004 | get_log_file_path()が期待パスを返す | 中 | `test_get_log_file_path_is_under_logs_root` |

---

## 集計（優先度別・原本と同一）

| 優先度 | 件数（目安） |
|---|---|
| 最高 | 約49件 |
| 高 | 約82件 |
| 中 | 約63件 |
| 低 | 約6件 |
| **合計** | **約200件** |

---

## 補足

- `desktop_main.py`（PyWebView起動そのもの）・`web/index.html`・`web/js/main.js`はブラウザ/OS依存が強く単体テスト対象外（結合・E2Eテストの対象として別途検討）。
- CI（`.github/workflows/*.yml`）・Dockerfile・インストーラ関連（`installer.iss`等）は単体テスト対象外。
- 前提条件・確認方法・期待結果の詳細、レビュー対応サマリー（FIX/NEWの経緯）は原本 `docs/04_単体テスト/pytestテストケース一覧表.md` を参照。
