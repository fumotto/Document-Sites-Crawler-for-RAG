# CHANGELOG

## v1.0.2（未リリース）

### 変更

　アプリアイコンを更新

### Bug Fixes

- **#4 画面の詳細設定の「ログレベル」が効かない**
  `ExecutionWorker.start()` がフォーム入力の `log_level` を `ConfigRecord` に格納するのみで、実行時のルートロガーへ反映していなかった。デスクトップアプリ起動時に `setup_logging(log_level="INFO", ...)` を一度呼ぶだけで、以降「実行」ボタンを押すたびにログレベルを更新する処理が欠落していた。
  → `ExecutionWorker.start()` 内で `logging.getLogger().setLevel(config.log_level)` を明示的に呼ぶよう修正（`src/app/gui/execution_worker.py`）。

- **#5 画面で実行した際にテストフォルダも作成されてしまう**
  `ensure_project_directories()` が `cache/` `output/` `archives/` `logs/` に加えて `tests/` まで無条件で作成していた。CLI/Docker版ではプロジェクトルート直下に無害な空フォルダが増えるだけだったため気づきにくかったが、GUI版では実行のたびに `%USERPROFILE%\DocumentSitesCrawlerForRAG\` 配下にも無関係な `tests/` が作られてしまっていた。
  → `tests` をディレクトリ作成対象から削除（`src/app/utils/directory_bootstrap.py`）。`tests/` はソースリポジトリ側でバージョン管理されるべきものであり、実行時に自動生成する必要はないと判断した。

### Enhancements

- **#6 ドメイン内すべて取得して来ようとしている？**
  sitemap利用時のクロールは常にドメインルートの `sitemap.xml` を参照する仕様のため、`INCLUDE` が未設定のまま `https://example.com/docs/guides` のようにパスを含むURLを指定しても、`/blog/` 等ドメイン全体が取得対象になっていた。
  → `INCLUDE` が未設定の場合、指定URLのパス部分を暗黙のINCLUDEとして自動適用するよう変更（`CrawlerService._resolve_effective_include()`、`src/app/crawler/crawler_service.py`）。`INCLUDE` を明示的に指定した場合は常にその指定を優先するため、既存のCLI利用者の挙動は変わらない。
  削除ページ判定（`_apply_deletion_guard`）の比較範囲も同じスコープに統一した。

### Documentation

- `docs/NotebookLM_Document_Crawler_要件定義書.md` 11節、`docs/07_CLI仕様.md` 3節、`docs/06_処理シーケンス.md` 設計方針に、上記INCLUDE自動スコープの補足を追記。

---

## v1.0.1

初回のデスクトップアプリ配布版。
