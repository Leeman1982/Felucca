#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Leo Kuroshita (@kurogedelic), Hügelton Instruments
"""The one-file updater (NightShift; after the Carpenter84 Updater of xtro's SMK-37 port): one .html that holds the
firmware package and installs it on an FM-1 from Chrome or Edge (Web MIDI), or puts the official V15 back. No Python,
no server: double-click it.

  web/make_updater.py build/felucca.fwsc OUT.html [--name NightShift] [--version v1.5-NS1]

It fills the same page the site's installer uses (web/index_pkg.html): the modules inline, the package as base64 with
its size (the page checks it and the package's identity before writing). The package must be one made by
tools/fm1pkg_make.py (identity FM-1_9xx, Felucca's own loader: no vendor files are patched in).
"""
import argparse
import base64
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_site  # noqa: E402

REPO = "https://github.com/Leeman1982/Felucca"


def swap(page, old, new):
    if page.count(old) != 1:
        raise SystemExit(f"index_pkg.html: {old!r} must appear exactly once; update make_updater.py")
    return page.replace(old, new)


def make(pkg, out, name="NightShift", version=None):
    raw = Path(pkg).read_bytes()
    product = make_site.product_of(raw)
    if not re.fullmatch(r"FM-1_9\d\d", product):
        raise SystemExit(f"{pkg}: identity {product!r} is not a Felucca package (FM-1_9xx)")
    if b"FELUCCA-LOADER-1" not in raw:
        raise SystemExit(f"{pkg}: no Felucca loader in it (a package patched from an official one carries vendor files)")
    html = (HERE / "index_pkg.html").read_text(encoding="utf-8")
    lib = "\n".join(make_site.strip_module((HERE / f).read_text(encoding="utf-8"))
                    for f in ("fm1pkg.js", "fm1ota.js", "fm1backup.js"))
    meta = {"version": version or "", "product": product, "size": len(raw), "data": base64.b64encode(raw).decode()}
    html = swap(html, "/*LIB*/", lib)
    html = swap(html, "/*META*/", json.dumps(meta))
    html = swap(html, "<title>Felucca</title>", f"<title>{name} updater</title>")
    html = swap(html, "<h1>Felucca</h1>", f"<h1>{name} <span class=\"small\">for the FM-1</span></h1>")
    html = swap(html, "say(`Felucca ${meta.version}`);", f"say(`{name} ${{meta.version}}`);")
    html = swap(html, '  <p><a href="../editor/" style="color:inherit" data-t="editor"></a></p>\n', "")
    html = swap(html, '<p class="small" data-t="beta"></p>',
                '<p class="small" data-t="beta"></p>\n  <p class="small"><b>' + name + ' has not been run on a real FM-1 yet.</b> '
                'It is Felucca 1.5 with eight tracks and a few Open Samples sounds. Installing is at your own risk; '
                '"Return to official V15" below takes you back. Your Felucca projects load (tracks 5-8 start empty); '
                'the 4-track backup of this build does not cover tracks 5-8.</p>')
    for rel in ("../../firmware/LICENSING.md", "../../firmware/LICENSE", "../../firmware/LICENSES/"):
        html = html.replace(f'href="{rel}"', f'href="{REPO}/blob/main/' + rel.replace("../../firmware/", "") + '"')
    html = swap(html, "Samples: Versilian Studios VSCO-2 Community Edition and VCSL (CC0 1.0).",
                "Samples: Versilian Studios VSCO-2 Community Edition and VCSL (CC0 1.0); NightShift's 101 BASS, 4P BASS, "
                "JUNO STR and LINN: Open Samples by Jeffrey Brice and contributors (Open Samples Permissive Use Public "
                "License: free to use, not to be resold as a sample product, no AI training).")
    html = html.replace("https://github.com/hugelton/Felucca", REPO)
    Path(out).write_text(html, encoding="utf-8")
    return product, len(html)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("package")
    ap.add_argument("out")
    ap.add_argument("--name", default="NightShift")
    ap.add_argument("--version", default="")
    a = ap.parse_args(argv)
    product, n = make(a.package, a.out, a.name, a.version)
    print(f"updater  {a.out}  {n} B, installs {product}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
