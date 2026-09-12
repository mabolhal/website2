#!/usr/bin/env python3
# render.py — build index.html from template.html + config.json
#
# Usage:
#     python render.py [config.json] [template.html] [index.html]
#
# Defaults: config.json, template.html, index.html in the current directory.
# Stdlib only — no dependencies.
import json
import re
import sys
from html import escape
from pathlib import Path


def e(text):
    """HTML-escape a config string."""
    return escape(str(text), quote=True)


def build_nav(cfg):
    person = cfg["person"]
    logo = f'<a class="logo" href="#">{e(person["logo"])}<span>/</span>{e(person["logoYear"])}</a>'
    # nav entries: (section key in config, label, anchor) — only if section exists
    entries = [
        ("systems", "SYSTEMS", "#systems"),
        ("approach", "APPROACH", "#approach"),
        ("stack", "STACK", "#stack"),
        ("about", "ABOUT", "#about"),
    ]
    links = "".join(
        f'<a href="{anchor}">{label}</a>'
        for key, label, anchor in entries
        if key in cfg.get("sections", {})
    )
    return f"{logo}\n<nav>{links}</nav>"


def build_hero(cfg):
    p, hero = cfg["person"], cfg["hero"]
    tagline = e(p["tagline"])
    for connector in (" that ", " into "):
        if connector in tagline:
            lead_first, lead_emphasis = tagline.split(connector, 1)
            lead = f'{lead_first}<br><strong>{connector.strip()} {lead_emphasis}</strong>'
            break
    else:
        lead = tagline
    return f"""<div class="eyebrow"><span class="pulse"></span> {e(hero["eyebrow"])}</div>
<h1>{e(hero["heading"])}<br><em>{e(hero["subheading"])}</em></h1>
<div class="hero-bottom">
  <p class="lead">{lead}</p>
  <div class="hero-meta">
    <span>{e(p["location"])}</span>
    <span>01</span>
  </div>
</div>
<a class="scroll" href="#systems">{e(hero["scrollText"])}</a>"""


def build_systems(cfg):
    items = cfg["sections"]["systems"]["items"]
    rows = []
    for i, s in enumerate(items, 1):
        chips = "".join(f'<span class="chip">{e(c)}</span>' for c in s.get("chips", []))
        link = (
            f' <a class="sys-link" href="{e(s["link"])}" target="_blank" '
            f'rel="noopener noreferrer" aria-label="Open {e(s["name"])}" '
            f'onclick="event.stopPropagation()">↗</a>'
            if s.get("link") else ""
        )
        rows.append(f"""  <div class="sys">
    <div class="sys-head">
      <span class="idx">{i:02d}</span>
      <h3>{e(s["name"])}{link}</h3>
      <span class="tag">{e(s["tag"])}</span>
      <span class="plus">+</span>
    </div>
    <div class="sys-body">
      <div class="sys-body-in">
        <p style="color:var(--ink)">{e(s["description"])}</p>
        <p>{e(s["detail"])}</p>
        <div class="chips">{chips}</div>
      </div>
    </div>
  </div>""")
    return '<div id="systems-list">\n' + "\n".join(rows) + "\n</div>"


def build_approach(cfg):
    steps = cfg["sections"]["approach"]["steps"]
    cells = "\n".join(f"""  <div>
    <small>{e(st["number"])}</small>
    <strong>{e(st["title"])}</strong>
    <p>{e(st["description"])}</p>
  </div>""" for st in steps)
    return '<div class="process">\n' + cells + "\n</div>"


def build_stack(cfg):
    skills = cfg["sections"]["stack"]["skills"]
    groups = []
    for category in dict.fromkeys(sk["category"] for sk in skills):
        items = "".join(
            f'<span>{e(sk["name"])}</span>'
            for sk in skills
            if sk["category"] == category
        )
        groups.append(f'''  <div class="skill-group">
    <div class="skill-category">{e(category)}</div>
    {items}
  </div>''')
    return '<div id="skill-grid" class="skill-grid">\n' + "\n".join(groups) + "\n</div>"


def build_about(cfg):
    """Grid ONLY (heading + bio). The .timeline wrapper lives in the template."""
    a = cfg["sections"]["about"]
    bio = "\n".join(f"    <p>{e(b)}</p>" for b in a["bio"])
    return f"""<div class="about-grid">
  <h2>{e(a["heading"])}<br><em>{e(a["subheading"])}</em></h2>
  <div>
{bio}
  </div>
</div>"""


def build_timeline(cfg):
    """Year spans + separators ONLY. The .timeline wrapper lives in the template."""
    entries = cfg["sections"]["about"]["timeline"]
    parts = []
    for t in entries:
        parts.append(f'<span data-detail="{e(t["detail"])}">{e(t["year"])}</span>')
        parts.append("<i></i>")
    parts.pop()  # drop trailing separator
    return "".join(parts)


def build_contact(cfg):
    p, c = cfg["person"], cfg["sections"]["contact"]
    return f"""<div class="eyebrow">{e(c["eyebrow"])}</div>
<h2>{e(c["heading"])}<br><em>{e(c["subheading"])}</em></h2>
<div class="contact-row">
  <a href="mailto:{e(p["email"])}">{e(c["buttonText"])}</a>
  <span>{e(p["name"]).upper()}</span>
</div>"""


def build_footer(cfg):
    p, hero = cfg["person"], cfg["hero"]
    return (f'<span>{e(p["logo"])}/{e(p["logoYear"])}</span>\n'
            f'<span>{e(hero["eyebrow"])}</span>\n'
            f'<span>{e(p["footer"])}</span>')


def build_replacements(cfg):
    p, hero, secs = cfg["person"], cfg["hero"], cfg["sections"]
    repl = {
        "{{title}}": f'{e(p["name"])} — {e(p["title"])}',
        "{{nav}}": build_nav(cfg),
        "{{hero}}": build_hero(cfg),
        "{{systems}}": build_systems(cfg),
        "{{approach}}": build_approach(cfg),
        "{{stack}}": build_stack(cfg),
        "{{about}}": build_about(cfg),
        "{{timeline}}": build_timeline(cfg),
        "{{contact}}": build_contact(cfg),
        "{{footer}}": build_footer(cfg),
    }
    # dotted section-head placeholders, e.g. {{sections.systems.title}}
    for sec_key, sec in secs.items():
        if isinstance(sec, dict) and "title" in sec:
            repl[f"{{{{sections.{sec_key}.title}}}}"] = e(sec["title"])
        if isinstance(sec, dict) and "subtitle" in sec:
            repl[f"{{{{sections.{sec_key}.subtitle}}}}"] = e(sec["subtitle"])
    return repl


def render(config_path, template_path, output_path):
    cfg = json.loads(Path(config_path).read_text(encoding="utf-8"))
    out = Path(template_path).read_text(encoding="utf-8")

    for key, value in build_replacements(cfg).items():
        out = out.replace(key, value)

    leftover = sorted(set(re.findall(r"\{\{[^}]+\}\}", out)))
    if leftover:
        raise SystemExit(f"Error: unfilled placeholders remain: {leftover}")

    Path(output_path).write_text(out, encoding="utf-8")
    print(f"Rendered {output_path} ({len(out)} bytes)")


if __name__ == "__main__":
    args = sys.argv[1:]
    render(*(args + ["config.json", "template.html", "index.html"][len(args):]))