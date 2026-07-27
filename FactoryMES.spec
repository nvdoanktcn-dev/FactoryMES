from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path(SPECPATH).resolve()

hidden_imports = collect_submodules(
    "src"
)

analysis = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (
            str(
                ROOT
                / "config"
                / "app.json"
            ),
            "config",
        ),
        (
            str(
                ROOT
                / "assets"
                / "factorymes_icon.png"
            ),
            "assets",
        ),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "coverage",
        "pytest",
    ],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(
    analysis.pure
)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="FactoryMES",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="assets/factorymes.ico",
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

application = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FactoryMES",
)
