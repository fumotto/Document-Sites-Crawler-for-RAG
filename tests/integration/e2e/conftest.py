import functools
import http.server
import socketserver
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PAGE_PATH = ROOT / 'web' / 'index.html'
STUB_PATH = Path(__file__).resolve().parent / 'fixtures' / 'pywebview-stub.js'


@pytest.fixture(scope='session')
def web_server():
    assert PAGE_PATH.exists(), f'Expected web page at {PAGE_PATH}'
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = socketserver.TCPServer(('127.0.0.1', 0), handler)
    port = server.server_address[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{port}'
    server.shutdown()
    server.server_close()


@pytest.fixture(autouse=True)
def setup_page(page, web_server):
    page.add_init_script(path=str(STUB_PATH))
    page.goto(f'{web_server}/web/index.html')
    yield
