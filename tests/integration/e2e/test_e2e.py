from playwright.sync_api import Page


def test_input_screen_visible(page: Page):
    assert page.locator('#app-title').inner_text() == 'Document Sites Crawler for RAG'
    assert page.locator('#urls_text').is_visible()
    assert page.locator('#btn-start').is_visible()
    assert page.locator('label', has_text='モード').is_visible()


def test_execution_flow_shows_running(page: Page):
    page.fill('#urls_text', 'https://example.com/docs')
    page.click('#btn-start')
    assert page.locator('#screen-running').is_visible()
    assert 'サイト処理中' in page.locator('#progress-text').inner_text()


def test_error_screen_controls_visible(page: Page):
    page.evaluate("() => { document.getElementById('screen-error').hidden = false; }")
    assert page.locator('#btn-open-log').is_visible()
    assert page.locator('#btn-back-from-error').is_visible()
