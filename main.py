#!/usr/bin/env python3
"""Entry point for news-image-20261119 v3 (@kanbara12).

The front page is painted ahead of time by render.py, which composites
thirteen illustrations generated fresh for this build into the 1024x1024
newspaper page and writes entry.png. All this program does is copy that
finished image into the output directory, so it needs nothing but the
standard library and writes the same bytes on every run.
"""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "entry.png", out_dir / "entry.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
