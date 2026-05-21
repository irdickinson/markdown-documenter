# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # markdown extensions
        'markdown.extensions.extra',
        'markdown.extensions.nl2br',
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
        'markdown.extensions.abbr',
        'markdown.extensions.footnotes',
        'markdown.extensions.md_in_html',
        # trafilatura dependencies
        'trafilatura',
        'trafilatura.core',
        'trafilatura.settings',
        'trafilatura.utils',
        'lxml',
        'lxml.etree',
        'lxml._elementpath',
        'certifi',
        'charset_normalizer',
        'urllib3',
        'urllib3.util',
        # yt-dlp
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.extractor._extractors',
        # youtube-transcript-api
        'youtube_transcript_api',
        'youtube_transcript_api._api',
        # ollama
        'ollama',
        'httpx',
    ],
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
    name='MarkdownDocumenter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MarkdownDocumenter',
)
