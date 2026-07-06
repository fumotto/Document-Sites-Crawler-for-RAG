import functools
import http.server
import socketserver
import threading
from pathlib import Path

from dotenv import load_dotenv
import os

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
PAGE_PATH = ROOT / 'web' / 'index.html'
STUB_PATH = Path(__file__).resolve().parent / 'fixtures' / 'pywebview-stub.js'


@pytest.fixture(scope='session')
def web_server():

    load_dotenv(".env.test")
    TESTSERVER_HOST = os.getenv("TESTSERVER_HOST", "127.0.0.1")
    TESTSERVER_PORT = os.getenv("TESTSERVER_PORT", "8080")

    assert PAGE_PATH.exists(), f'Expected web page at {PAGE_PATH}'
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = socketserver.TCPServer((TESTSERVER_HOST, int(TESTSERVER_PORT)), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{TESTSERVER_HOST}:{TESTSERVER_PORT}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def playwright_instance(web_server):
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="function")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser):
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(autouse=True)
def setup_page(page, web_server):
    page.add_init_script(path=str(STUB_PATH))
    page.goto(f'{web_server}/web/index.html')
    yield
