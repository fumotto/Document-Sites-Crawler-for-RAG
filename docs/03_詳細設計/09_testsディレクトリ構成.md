# 09_testsディレクトリ構成

## 0. 本書の位置づけ

- 本書は、単体テスト（pytest）に加えて結合テスト（Docker Composeコマンドからの起動テスト、Playwright E2Eテスト）を追加するにあたり、`tests/` ディレクトリを再設計した結果を定義する。
- 単体テストは既存の `tests/*.py` を `tests/unit/` へ移動する。結合テストは新設の `tests/integration/` 配下に、区分ごとにサブディレクトリを分けて配置する。
- CI（`.github/workflows/*`）・Dockerfile・インストーラ関連（`main.spec` / `installer.iss` 等）は本書のスコープ外とする。

---

## 1. 全体方針

- **単体テストと結合テストを明確に分離する。** 単体テストは外部プロセス（Docker・ブラウザ）を起動せず、pytestのみで完結させる。結合テストはシナリオ単位でDocker Compose起動・Playwright起動を伴う。
- **結合テスト用のダミーWebサーバ（`testserver/`）を、区分A（Docker Compose起動テスト）・区分B（Playwright E2Eテスト）の両方から参照可能な共用リソースとして独立させる。** ただし現時点の方針（下記2.3参照）では、区分Bは `pywebview.api` をJSスタブ化してUIロジックのみを検証するため、`testserver/` への実アクセスは発生しない。将来的に実結合（Python側を薄いHTTP APIでラップしてE2Eから実クロールを検証する構成）へ拡張する場合に備え、共用可能な位置に配置しておく。
- **本番用の `docker-compose.yml` は変更しない。** テスト専用の compose 定義・`.env` はすべて `tests/integration/docker/` 配下に置く。

---

## 2. ディレクトリ構成

```
tests/
├── unit/                              # 単体テスト（既存 tests/*.py を移動）
│   ├── __init__.py
│   ├── test_atomic_io.py
│   ├── test_site_identifier.py
│   ├── test_manifest_repository.py
│   ├── test_duplicate_resolver.py
│   ├── test_gui_config_builder.py
│   ├── test_gui_execution_worker.py
│   ├── test_issue_fixes.py
│   └── ...（新規追加分もここに配置）
│
└── integration/
    ├── docker/                        # 区分A: Docker Composeコマンドからの起動テスト
    │   ├── conftest.py                # docker compose up/down、後片付け等のpytest fixture
    │   ├── docker-compose.test.yml    # テスト専用compose定義（本番compose.ymlは変更しない）
    │   ├── .env.test                  # テスト用.env（testserverのURL・MAX_PAGES等）
    │   └── test_docker_scenarios.py   # pytest + subprocessでdocker composeを操作するテスト本体
    │
    ├── e2e/                           # 区分B: PlaywrightによるE2Eテスト
    │   ├── playwright.config.ts
    │   ├── package.json
    │   ├── tests/
    │   │   ├── input-screen.spec.ts
    │   │   ├── execution-flow.spec.ts
    │   │   └── error-screen.spec.ts
    │   └── fixtures/
    │       └── pywebview-stub.ts      # window.pywebview.api の全メソッドをJSでモックする状態機械
    │
    └── testserver/                    # A・B共用：クロール対象のダミーサイト（Node製）
        ├── package.json
        ├── server.js                  # Node製モックHTTPサーバ本体
        ├── fixtures/
        │   ├── sitemap.xml
        │   ├── sitemap-index.xml
        │   ├── robots.txt
        │   └── pages/
        │       ├── docs-guides.html
        │       ├── blog-post1.html
        │       └── ...
        └── scenarios/                 # シナリオ別の応答定義（切り替え可能）
            ├── happy-path.js
            ├── with-duplicates.js
            ├── with-robots-deny.js
            └── error-responses.js
```

---

## 3. 各ディレクトリの責務

### 3.1 `tests/unit/`

- 既存の `tests/*.py`（`test_atomic_io.py` 等）をそのまま移動する。
- 外部プロセス（Docker・ブラウザ）を起動しない、pytest単体で完結するテストのみを配置する。
- 本再設計に伴うコード側の変更は移動のみとし、テスト内容・インポートパス（`sys.path.insert` によるプロジェクトルート参照等）は変更しない。

### 3.2 `tests/integration/docker/`

- Docker Composeコマンドからの起動テスト（シナリオテスト）を配置する。
- `docker-compose.test.yml` は本番用 `docker-compose.yml` をベースに、以下を追加・変更したテスト専用定義とする。
  - `testserver` サービスを追加し、`tests/integration/testserver/` をビルドコンテキストとして起動する。
  - クローラーコンテナから `testserver` サービス名で名前解決できるよう、同一ネットワークに配置する。
  - ボリュームマウント先はテスト用の一時ディレクトリ（例：`.test-workspace/` 等、`.gitignore` 対象）を使用し、本番の `cache/` `output/` `archives/` `logs/` を汚染しない。
- `.env.test` にはテスト実行に必要な最小限の環境変数（`MAX_PAGES` / `TIMEOUT_SECONDS` 等の必須項目、および `testserver` の到達URLに関する情報）を定義する。
- `test_docker_scenarios.py` は pytest から `subprocess` 経由で `docker compose -f docker-compose.test.yml run/up` 等を実行し、終了コード・生成ファイル・ログ内容を検証する。
- `conftest.py` には、各テストケース実行前後で `testserver` のシナリオ切り替え、テスト用ワークスペースのクリーンアップ等を行う fixture を定義する。

### 3.3 `tests/integration/e2e/`

- Playwright（TypeScript）によるE2Eテストを配置する。
- `playwright.config.ts` の `webServer` 機能を用いて、`tests/integration/testserver/server.js` を直接Node起動する（区分A同様、共用の `testserver/` を利用可能な状態にしておく）。ただし現行方針では、区分Bのテスト自体は `pywebview-stub.ts` によるJSスタブを通じてUIロジックのみを検証するため、`testserver` への実アクセスは発生しない。
- `fixtures/pywebview-stub.ts` は、`window.pywebview.api` の以下のメソッドをシナリオごとの固定応答・簡易状態機械として提供する。
  - `get_app_info`
  - `load_settings`
  - `start_execution`
  - `get_status`（ポーリング回数に応じて `state` / `log_lines` / `sites_done` / `result_summary` を段階的に変化させる）
  - `open_log_folder`
- Playwrightの `addInitScript`（または同等の仕組み）で `web/index.html` を開く前にスタブを注入し、実際のPython/PyWebView/クロール処理には一切依存しない構成とする。
- `tests/` 配下は画面・シナリオ単位でファイルを分割する（`input-screen.spec.ts` / `execution-flow.spec.ts` / `error-screen.spec.ts`）。

### 3.4 `tests/integration/testserver/`

- クロール対象となるダミーサイトをNodeで実装する。
- `fixtures/` に、sitemap.xml・sitemap index・robots.txt・各種ページHTML等の静的フィクスチャを配置する。
- `scenarios/` に、正常系（`happy-path`）・重複ページ（`with-duplicates`）・robots.txt拒否（`with-robots-deny`）・エラー応答（`error-responses`：404/429/5xx/タイムアウト等）といったシナリオ別の応答ロジックを配置する。
- シナリオの切り替えは、テストコードから制御しやすいよう管理エンドポイント（例：`POST /__scenario__` でシナリオ名を指定）を用意することを推奨する。これにより「1回目実行時は404を返し、2回目実行前にシナリオを切り替える」といった差分更新系のテストケース（例：ページ削除、内容変更後の再クロール）に対応できる。

---

## 4. 対象外としたテストケースとその理由

以下のテストケースは、テストコードの安定性を優先し、Playwright E2Eテストの対象から除外する方針を採用した。

| テストID | 内容 | 除外理由 |
|---|---|---|
| DC-024 | 中断（プロセスkill）後に再実行するとレジュームされる（Resume） | プロセスkillのタイミング制御が難しく、自動化した場合にテストの再現性・安定性を損ないやすい。手動テストでの確認に留める。 |
| E2E-020 | 実行中にウィンドウを閉じようとすると確認ダイアログが表示される | `desktop_main.py` の `window.events.closing` に依存するPyWebView固有の機能であり、JSスタブ方式のブラウザE2Eでは正しく再現できない。実機能の確認は手動テストに委ねる。 |

上記2件は「シナリオテストケース一覧表_手動.md」に手動確認項目として記載する。

---

## 5. 移行手順の概要

1. 既存の `tests/*.py`（`test_atomic_io.py` / `test_site_identifier.py` / `test_manifest_repository.py` / `test_duplicate_resolver.py` / `test_gui_config_builder.py` / `test_gui_execution_worker.py` / `test_issue_fixes.py` / `__init__.py`）を `tests/unit/` へ移動する。
2. `tests/integration/docker/`・`tests/integration/e2e/`・`tests/integration/testserver/` を新設し、それぞれの雛形ファイル（`conftest.py` / `playwright.config.ts` / `server.js` 等）を配置する。
3. `.github/workflows/ci.yml` の `pytest tests/ -v` 実行範囲は、本書のスコープ外（CI関連）のため本書では変更を定めない。単体テストのみをCIで回す場合は `pytest tests/unit/ -v` への変更が別途必要になる点に留意する。
4. `.gitignore` に、結合テスト実行時に生成される一時ワークスペース（例：`tests/integration/docker/.test-workspace/`）を追加する。

---

## 6. 今後の課題

- 現時点でPlaywright E2Eテストは `pywebview.api` をJSスタブ化する方式を採用しているため、実際のPython側実装（`ExecutionWorker` / `JsApi` 等）とE2Eテストの間に乖離が生じるリスクがある。UI仕様変更時はスタブ側の同期を忘れずに行う必要がある。
- 将来的に実結合（Python側を薄いHTTP APIでラップし、実クロールまで検証するE2E）を追加する場合、`tests/integration/testserver/` はそのまま再利用可能な位置づけとしている。
- `tests/integration/docker/` のテスト用ワークスペースのクリーンアップ方式（テスト失敗時に一時ファイルが残留しないための仕組み）は、`conftest.py` の実装時に詳細化する必要がある。
