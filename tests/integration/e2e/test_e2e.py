from playwright.sync_api import Page


def test_input_screen_visible(page: Page):
    # TestID: E2E-001
    assert page.locator('#app-title').inner_text() == 'Document Sites Crawler for RAG'
    assert page.locator('#urls_text').is_visible()
    assert page.locator('#btn-start').is_visible()
    assert page.locator('label', has_text='モード').is_visible()


def test_execution_flow_shows_running(page: Page):
    # TestID: E2E-002
    page.fill('#urls_text', 'https://example.com/docs')
    page.click('#btn-start')
    assert page.locator('#screen-running').is_visible()
    assert 'サイト処理中' in page.locator('#progress-text').inner_text()


def test_input_validation_requires_url(page: Page):
    # TestID: E2E-003
    page.click("#btn-start")
    assert page.locator("#input-error").is_visible()
    assert "対象URL" in page.locator("#input-error").inner_text()


def test_invalid_url_format_shows_error(page: Page):
    # TestID: E2E-004
    page.fill("#urls_text", "ftp://example.com")
    page.click("#btn-start")
    assert page.locator("#input-error").is_visible()
    assert "URLの形式" in page.locator("#input-error").inner_text()


def test_multiple_urls_trigger_multi_site_progress(page: Page):
    # TestID: E2E-005
    page.evaluate("""
      () => {
        window.pywebview.api.start_execution = async function(form) {
          window.__last_form = form;
          return { status: 'started' };
        };
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          return {
            state: 'running',
            log_lines: ['working'],
            last_index: calls,
            sites_done: Math.min(calls, 2),
            sites_total: 2,
            result_summary: null,
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs\nhttps://example.org/blog")
    page.click("#btn-start")
    assert page.locator("#screen-running").is_visible()
    assert "2" in page.locator("#progress-text").inner_text()


def test_mode_selection_is_sent_to_api(page: Page):
    # TestID: E2E-006
    page.evaluate("""
      () => {
        window.__captured_form = null;
        window.pywebview.api.start_execution = async function(form) {
          window.__captured_form = form;
          return { status: 'started' };
        };
      }
    """)
    page.locator('input[name="mode"][value="full"]').check()
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    captured = page.evaluate("() => window.__captured_form")
    assert captured["mode"] == "full"


def test_advanced_settings_toggle(page: Page):
    # TestID: E2E-007
    page.locator("summary").click()
    assert page.locator("#word_limit").is_visible()
    assert page.locator("#request_delay").is_visible()


def test_advanced_setting_values_are_sent(page: Page):
    # TestID: E2E-008
    page.evaluate("""
      () => {
        window.__captured_form = null;
        window.pywebview.api.start_execution = async function(form) {
          window.__captured_form = form;
          return { status: 'started' };
        };
      }
    """)
    page.locator("summary").click()
    page.fill("#word_limit", "123456")
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    captured = page.evaluate("() => window.__captured_form")
    assert captured["word_limit"] == 123456


def test_saved_settings_are_restored(page: Page):
    # TestID: E2E-009
    assert page.locator("#urls_text").input_value() == ""
    assert page.locator("#word_limit").input_value() == "450000"


def test_log_lines_are_appended_via_polling(page: Page):
    # TestID: E2E-010
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          const states = [
            { state: 'running', log_lines: ['Start'], last_index: 0, sites_done: 0, sites_total: 1, result_summary: null },
            { state: 'running', log_lines: ['Continue'], last_index: 1, sites_done: 1, sites_total: 1, result_summary: null },
          ];
          return states[Math.min(calls - 1, states.length - 1)];
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert "Start" in page.locator("#log-panel").text_content()
    assert "Continue" in page.locator("#log-panel").text_content()


def test_progress_text_updates_during_polling(page: Page):
    # TestID: E2E-011
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          return {
            state: 'running',
            log_lines: ['tick'],
            last_index: calls,
            sites_done: calls,
            sites_total: 3,
            result_summary: null,
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert "サイト処理中: 2 / 3" in page.locator("#progress-text").text_content()


def test_completed_screen_shows_result_summary(page: Page):
    # TestID: E2E-012
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls < 3) {
            return { state: 'running', log_lines: ['working'], last_index: calls, sites_done: 1, sites_total: 1, result_summary: null };
          }
          return {
            state: 'completed',
            log_lines: ['finished'],
            last_index: calls,
            sites_done: 1,
            sites_total: 1,
            result_summary: [{ site_identifier: 'example.com', has_fatal_error: false, total_pages_included: 3, duplicate_excluded_count: 1, chunk_file_count: 2, warnings: [] }],
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(4000)
    assert page.locator("#screen-completed").is_visible()
    assert "example.com" in page.locator("#result-summary").text_content()


def test_completed_screen_shows_site_stats(page: Page):
    # TestID: E2E-013
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls < 2) {
            return { state: 'running', log_lines: [], last_index: 0, sites_done: 1, sites_total: 1, result_summary: null };
          }
          return {
            state: 'completed',
            log_lines: ['done'],
            last_index: 1,
            sites_done: 1,
            sites_total: 1,
            result_summary: [{ site_identifier: 'example.com', has_fatal_error: false, total_pages_included: 3, duplicate_excluded_count: 1, chunk_file_count: 2, warnings: [] }],
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(4000)
    assert (
        "完了: 3ページ / 重複除外 1件 / チャンク 2件"
        in page.locator("#result-summary").text_content()
    )


def test_warning_list_is_rendered(page: Page):
    # TestID: E2E-014
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls < 2) {
            return { state: 'running', log_lines: [], last_index: 0, sites_done: 1, sites_total: 1, result_summary: null };
          }
          return {
            state: 'completed',
            log_lines: ['done'],
            last_index: 1,
            sites_done: 1,
            sites_total: 1,
            result_summary: [{ site_identifier: 'example.com', has_fatal_error: false, total_pages_included: 1, duplicate_excluded_count: 0, chunk_file_count: 1, warnings: ['warning 1'] }],
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert "warning 1" in page.locator("#result-summary").text_content()


def test_restart_button_returns_to_input_form(page: Page):
    # TestID: E2E-015
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls < 2) {
            return { state: 'running', log_lines: [], last_index: 0, sites_done: 1, sites_total: 1, result_summary: null };
          }
          return { state: 'completed', log_lines: ['done'], last_index: 1, sites_done: 1, sites_total: 1, result_summary: [] };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    page.click("#btn-restart")
    assert page.locator("#screen-input").is_visible()


def test_start_button_is_disabled_while_running(page: Page):
    # TestID: E2E-016
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    assert page.locator("#btn-start").is_disabled()


def test_failed_state_shows_error_screen(page: Page):
    # TestID: E2E-017
    page.evaluate("""
      () => {
        window.pywebview.api.get_status = async function() {
          return { state: 'failed', log_lines: ['failed'], last_index: 1, sites_done: 0, sites_total: 1, result_summary: null, error_message: 'Boom' };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert page.locator("#screen-error").is_visible()
    assert "Boom" in page.locator("#error-message").text_content()


def test_error_screen_opens_log_folder(page: Page):
    # TestID: E2E-018
    page.evaluate("""
      () => {
        window.__opened = false;
        window.pywebview.api.get_status = async function() {
          return { state: 'failed', log_lines: [], last_index: 1, sites_done: 0, sites_total: 1, result_summary: null, error_message: 'Boom' };
        };
        window.pywebview.api.open_log_folder = async function() {
          window.__opened = true;
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    page.click("#btn-open-log")
    opened = page.evaluate("() => window.__opened")
    assert opened is True


def test_error_screen_back_button_returns_to_input(page: Page):
    # TestID: E2E-019
    page.evaluate("""
      () => {
        window.pywebview.api.get_status = async function() {
          return { state: 'failed', log_lines: [], last_index: 1, sites_done: 0, sites_total: 1, result_summary: null, error_message: 'Boom' };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    page.click("#btn-back-from-error")
    assert page.locator("#screen-input").is_visible()


def test_partial_failure_shows_fatal_result_card(page: Page):
    # TestID: E2E-021
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls < 2) {
            return { state: 'running', log_lines: [], last_index: 0, sites_done: 1, sites_total: 1, result_summary: null };
          }
          return {
            state: 'completed',
            log_lines: ['done'],
            last_index: 1,
            sites_done: 1,
            sites_total: 1,
            result_summary: [{ site_identifier: 'example.com', has_fatal_error: true, total_pages_included: 0, duplicate_excluded_count: 0, chunk_file_count: 0, warnings: [] }],
          };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert page.locator(".site-summary-card.fatal").is_visible()
    assert page.locator(".status-fatal").is_visible()


def test_status_error_recovers_on_next_poll(page: Page):
    # TestID: E2E-022
    page.evaluate("""
      () => {
        let calls = 0;
        window.pywebview.api.get_status = async function() {
          calls += 1;
          if (calls === 1) {
            throw new Error('temporary failure');
          }
          return { state: 'completed', log_lines: ['done'], last_index: 1, sites_done: 1, sites_total: 1, result_summary: [] };
        };
      }
    """)
    page.fill("#urls_text", "https://example.com/docs")
    page.click("#btn-start")
    page.wait_for_timeout(2500)
    assert page.locator("#screen-completed").is_visible()
