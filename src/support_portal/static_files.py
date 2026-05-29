from pathlib import Path


def setup_static(app, static_dir: str) -> None:
    # CVE-2024-23334: aiohttp < 3.9.2 with follow_symlinks=True skips the
    # filepath.relative_to(directory) boundary check in StaticResource._handle,
    # allowing path traversal via GET /static/../../sensitive/file.
    app.router.add_static("/static/", static_dir, follow_symlinks=True)
