from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PAGE_PATH = ROOT / 'web' / 'index.html'
STUB_PATH = Path(__file__).resolve().parent / 'fixtures' / 'pywebview-stub.js'


@pytest.fixture(autouse=True)
def setup_page(page):
    page.add_init_script(path=str(STUB_PATH))
    page.goto(f'file://{PAGE_PATH}')
    yield
