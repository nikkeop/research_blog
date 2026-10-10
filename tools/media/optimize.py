#!/usr/bin/env python3
"""Make web-sized copies of photos for the media bucket (Cloudflare R2).

For every image it writes two files, keeping the relative path:

    <out>/<path>/<name>.<ext>        longest edge at most 2000 px  (lightbox, hero)
    <out>/<path>/<name>.w800.<ext>   800 px wide                   (cards, in-text)

That pair is what `layouts/_partials/media.html` expects for a bucket key
when `params.media.thumbnails` is on in hugo.yaml.

The copies are rotated upright and stripped of EXIF metadata, which removes the
GPS position phones write into every photo. The colour profile is kept.

Usage:
    python3 tools/media/optimize.py SOURCE OUT [--prefix trips/2025-alps]

SOURCE is a directory of images or a .tar archive (such as the WordPress media
export). --prefix is put in front of every relative path, so the result can be
uploaded to the bucket root as-is.

Needs Pillow (`pip install pillow`).
"""
import argparse
import io
import os
import re
import sys
import tarfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path, PurePosixPath

from PIL import Image, ImageOps

FULL = 2000
THUMB = 800
QUALITY = 82
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def safe_relpath(name):
    """A member path that stays inside OUT, or None."""
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or not p.name:
        return None
    return p


def save(img, path, fmt):
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if img.info.get("icc_profile"):
        kwargs["icc_profile"] = img.info["icc_profile"]
    if fmt == "JPEG":
        img = img.convert("RGB") if img.mode not in ("RGB", "L") else img
        kwargs.update(quality=QUALITY, optimize=True, progressive=True)
    elif fmt == "PNG":
        kwargs.update(optimize=True)
    elif fmt == "WEBP":
        kwargs.update(quality=QUALITY)
    img.save(path, fmt, **kwargs)


def process(job):
    try:
        return convert(*job)
    except Exception as exc:  # one broken file should not stop the batch
        return PurePosixPath(job[0]), f"error: {exc}"


def convert(rel, data, out, overwrite):
    rel = PurePosixPath(rel)
    target = Path(out, *rel.parts)
    thumb = target.with_name(f"{target.stem}.w{THUMB}{target.suffix}")
    if not overwrite and target.exists() and thumb.exists():
        return rel, "skipped"
    with Image.open(io.BytesIO(data)) as src:
        fmt = src.format
        icc = src.info.get("icc_profile")
        img = ImageOps.exif_transpose(src)
        img.info = {"icc_profile": icc} if icc else {}
        full = img.copy()
        full.thumbnail((FULL, FULL), Image.LANCZOS)
        full.info = img.info
        save(full, target, fmt)
        small = img.copy()
        if small.width > THUMB:
            small = small.resize((THUMB, round(small.height * THUMB / small.width)), Image.LANCZOS)
        small.info = img.info
        save(small, thumb, fmt)
    return rel, "ok"


def jobs(source, out, prefix, overwrite):
    prefix = PurePosixPath(prefix) if prefix else PurePosixPath()
    if source.is_file() and tarfile.is_tarfile(source):
        with tarfile.open(source) as tar:
            for member in tar:
                rel = safe_relpath(member.name)
                if not member.isfile() or rel is None or rel.suffix.lower() not in EXTENSIONS:
                    continue
                if re.search(r"\.w\d+$", rel.stem):
                    continue
                yield str(prefix / rel), tar.extractfile(member).read(), out, overwrite
    else:
        for path in sorted(source.rglob("*")):
            if path.is_file() and path.suffix.lower() in EXTENSIONS and not re.search(r"\.w\d+$", path.stem):
                rel = PurePosixPath(path.relative_to(source).as_posix())
                yield str(prefix / rel), path.read_bytes(), out, overwrite


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--prefix", default="", help="bucket path to put in front, e.g. trips/import")
    ap.add_argument("--overwrite", action="store_true", help="redo files that already exist")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    done = failed = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for rel, status in pool.map(process, jobs(args.source, args.out, args.prefix, args.overwrite), chunksize=4):
            done += 1
            if status.startswith("error"):
                failed += 1
                print(f"{rel}: {status}", file=sys.stderr)
            if done % 50 == 0:
                print(f"{done} images …", file=sys.stderr)
    print(f"{done - failed} of {done} images written to {args.out}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
