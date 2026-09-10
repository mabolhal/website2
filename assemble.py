#!/usr/bin/env python3
# assemble.py — stitch partials/*.html into a single template.html
#
# This lets you develop the site as small components (header, footer,
# each section, each script) instead of one giant HTML file. It knows
# nothing about your content (that's config.json's job via generate.py)
# — it only resolves {{@include:path}} markers, relative to the
# partials/ directory, recursively.
#
# Usage:
#     python assemble.py [partials_dir] [output_template]
#
# Defaults: partials/, template.html
import re
import sys
from pathlib import Path

INCLUDE_RE = re.compile(r"\{\{@include:([^}]+)\}\}")


def resolve(path: Path, root: Path, seen: tuple) -> str:
    if path in seen:
        chain = " -> ".join(str(p) for p in seen + (path,))
        raise SystemExit(f"Error: circular include: {chain}")
    text = path.read_text(encoding="utf-8")

    def replace(m):
        included = (root / m.group(1)).resolve()
        if not included.is_file():
            raise SystemExit(f"Error: {path} includes missing file {m.group(1)}")
        return resolve(included, root, seen + (path,))

    return INCLUDE_RE.sub(replace, text)


def assemble(partials_dir, output_path):
    root = Path(partials_dir)
    base = root / "base.html"
    if not base.is_file():
        raise SystemExit(f"Error: {base} not found")
    out = resolve(base, root, ())
    Path(output_path).write_text(out, encoding="utf-8")
    print(f"Assembled {output_path} ({len(out)} bytes) from {root}/")


if __name__ == "__main__":
    args = sys.argv[1:]
    assemble(*(args + ["partials", "template.html"][len(args):]))
