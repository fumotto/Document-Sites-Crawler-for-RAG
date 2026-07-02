# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller ビルド定義（08_デスクトップアプリ化要件定義書.md 11節）。

RISK-2対応:
    trafilatura / tiktoken は、依存パッケージの動的インポート（プラグイン機構・
    パッケージ内データファイル）をPyInstallerの静的解析だけでは検出しきれない
    ことが知られている。本specでは `collect_all` / 明示的な hiddenimports で
    可能な限り対策しているが、実際にWindows環境でビルドして動作確認するまで
    確実性は低い（08_デスクトップアプリ化要件定義書.md RISK-2）。
    ビルド後、以下を必ず実機確認すること：
      - tiktoken.get_encoding("cl100k_base") がオフラインでも例外にならず、
        フォールバック推定に切り替わること（RISK-1対応済みだが再確認）
      - trafilatura.extract() が正常にMarkdownを返すこと
"""
from PyInstaller.utils.hooks import collect_all

block_cipher = None

datas = [("web", "web")]
binaries = []
hiddenimports = [
    # tiktoken: プラグイン登録が pkgutil.iter_modules ベースのため、
    # PyInstallerの静的解析だけでは見つからないことがある既知の問題への対策。
    "tiktoken_ext",
    "tiktoken_ext.openai_public",
]

for pkg in ("trafilatura", "tiktoken", "dateparser", "lxml", "bs4"):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

a = Analysis(
    ["src/app/gui/desktop_main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocumentSitesCrawlerForRAG",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # --noconsole 相当（07節: コマンドプロンプトを表示しない）
    version="version_info.txt",
    icon="web/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DocumentSitesCrawlerForRAG",
)
