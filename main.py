#!/usr/bin/env python3
"""THE TUESDAY SIGNAL — MakeFun entry carrier for Akun 18
(@latuconshinaprilly3480), NI24 Wave 1 (news-image-20261124).

Stdlib-only carrier: verifies the PNG signature, reads the IHDR
dimensions and REFUSES to ship an image that breaks the 1024x1024
server gate, copies entry.png byte-for-byte into MAKEFUN_OUTPUT_DIR
(fallback /output), then verifies the copy is byte-identical.
Deterministic: the same input bytes always produce the same output.
"""
import hashlib
import os
import shutil
import struct
import sys

CONCEPT = "THE TUESDAY SIGNAL — Tuesday 24 November 2026 in one image"
ACCOUNT = "@latuconshinaprilly3480"
ACCOUNT_LABEL = "Akun 18"
BOUNTY = "news-image-20261124"
STORIES = 44  # 15 cards + 29 briefs, 7 regions
MAX_SIDE = 1024  # server gate: dimensions must stay within 1x1..1024x1024
MAX_BYTES = 1048576  # server gate: at most 1 MiB

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY = os.path.join(HERE, "entry.png")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_dimensions(path):
    with open(path, "rb") as f:
        head = f.read(33)
    if len(head) < 33 or head[:8] != PNG_SIG:
        raise ValueError("entry.png: bad PNG signature")
    if head[12:16] != b"IHDR":
        raise ValueError("entry.png: first chunk is not IHDR")
    return struct.unpack(">II", head[16:24])


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.isfile(ENTRY):
        print("entry.png missing next to main.py", file=sys.stderr)
        return 1
    w, h = png_dimensions(ENTRY)
    if w > MAX_SIDE or h > MAX_SIDE:
        print("entry.png is %dx%d, over the 1024x1024 gate" % (w, h),
              file=sys.stderr)
        return 1
    size = os.path.getsize(ENTRY)
    if size > MAX_BYTES:
        print("entry.png is %d bytes, over the 1 MiB gate" % size,
              file=sys.stderr)
        return 1
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, "entry.png")
    shutil.copyfile(ENTRY, dest)
    if sha256_of(ENTRY) != sha256_of(dest):
        print("copy is not byte-identical", file=sys.stderr)
        return 1
    print("OK %s %dx%d %d bytes sha256=%s"
          % (CONCEPT, w, h, size, sha256_of(dest)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
