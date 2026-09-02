#!/usr/bin/env python3
"""Regenerate the profile character sheet and the latest-posts block.

Aggregates language statistics across every repository the token can see -
public and private - and emits *only totals*. No name, description or URL of a
private repository appears in this file, in the SVGs, in the README, or on
stdout while running in CI: this repository is public, and so are its Actions
logs.

Repositories are classified by a `track-*` topic set on the repository itself,
which is why no mapping table lives here. To add a repository to a track, add
the corresponding topic to it on GitHub.

Standard library only, so CI needs no `pip install`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.github.com"
USER = "carenaudo"
ROOT = Path(__file__).resolve().parents[2]
FEED_URL = "https://carenaudo.github.io/carenaudo/atom.xml"
LOCAL_FEED = ROOT / "docs" / "public" / "atom.xml"
IN_CI = bool(os.environ.get("CI"))

# Topic -> (label on the sheet, bar colour). A repository carrying one of these
# topics counts toward that track; one carrying none is a hard error, because a
# silent drop would make the bars quietly wrong.
TRACKS = {
    "track-research": ("Particle & Droplet Science", "#6bd968"),
    "track-gamedev": ("Game Systems", "#6aa9ff"),
    "track-teaching": ("Teaching", "#f2c14e"),
    "track-systems": ("Developer Tooling", "#e0736d"),
}

SKIP = {"carenaudo"}          # this repository holds no project code
SKIP_OWNERS = {"community"}   # repositories owned by others we merely belong to

# Jupyter Notebook byte counts are inflated by the base64 image outputs
# embedded in .ipynb JSON, so notebooks are excluded from the proficiency bar
# rather than competing with hand-written source.
NOTEBOOK_LANG = "Jupyter Notebook"

LANG_COLORS = {
    "Python": "#3572a5", "Rust": "#dea584", "Julia": "#a270ba",
    "HTML": "#e34c26", "TypeScript": "#3178c6", "Fortran": "#4d41b1",
    "Svelte": "#ff3e00", "C++": "#f34b7d", "CSS": "#563d7c",
    "JavaScript": "#f1e05a", "Shell": "#89e051", "TeX": "#3d6117",
    "Batchfile": "#c1f12e", "Makefile": "#427819", "C": "#555555",
}
FALLBACK_COLOR = "#8b949e"

THEMES = {
    "dark": {
        "win_top": "#16233d", "win_bottom": "#0b1424", "edge": "#4d7bb5",
        "inner": "#2b426b", "text": "#e8eef7", "dim": "#93a6c4",
        "accent": "#f0c05a", "rail": "#26334d",
    },
    "light": {
        "win_top": "#f4f7fd", "win_bottom": "#e0e8f5", "edge": "#5b7fb0",
        "inner": "#b4c5e0", "text": "#16233d", "dim": "#4f6180",
        "accent": "#8a5d0a", "rail": "#ccd7ea",
    },
}

SEGMENTS = 20
MONO = ("ui-monospace,'SFMono-Regular','SF Mono',Menlo,Consolas,"
        "'DejaVu Sans Mono',monospace")


# --------------------------------------------------------------------------
# GitHub API
# --------------------------------------------------------------------------

def token():
    for var in ("PROFILE_STATS_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    return None


def api(path, tok):
    url = path if path.startswith("http") else API + path
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "carenaudo-profile-generator",
    }
    if tok:
        headers["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp), resp.headers.get("Link", "")


def all_repos(tok):
    """Return (repos, saw_private); falls back to the public listing."""
    if not tok:
        data, _ = api("/users/{}/repos?per_page=100".format(USER), None)
        return data, False

    repos = []
    page = 1
    while True:
        data, link = api(
            "/user/repos?per_page=100&affiliation=owner,organization_member"
            "&page={}".format(page), tok)
        repos.extend(data)
        if 'rel="next"' not in link:
            break
        page += 1
    return repos, any(r.get("private") for r in repos)


# --------------------------------------------------------------------------
# Aggregation
# --------------------------------------------------------------------------

def collect(tok):
    repos, saw_private = all_repos(tok)
    langs = Counter()
    tracks = Counter()
    untagged = []
    counted = 0

    for repo in repos:
        if repo.get("fork") or repo["name"] in SKIP:
            continue
        if repo["owner"]["login"] in SKIP_OWNERS:
            continue

        # sorted() keeps the choice deterministic if a repository ever carries
        # two track topics.
        found = sorted(set(repo.get("topics") or []) & set(TRACKS))
        if not found:
            untagged.append(repo["full_name"])
            continue

        try:
            repo_langs, _ = api(repo["languages_url"], tok)
        except urllib.error.HTTPError:
            repo_langs = {}
        langs.update(repo_langs)
        tracks[found[0]] += sum(repo_langs.values())
        counted += 1

    if untagged:
        sys.stderr.write(
            "ERROR: {} repository/repositories carry no track-* topic. Add one "
            "of {} to each on GitHub.\n".format(
                len(untagged), ", ".join(sorted(TRACKS))))
        if IN_CI:
            sys.stderr.write("Names withheld: this job's logs are public. "
                             "Run the script locally to see them.\n")
        else:
            for full in untagged:
                sys.stderr.write("  - {}\n".format(full))
        sys.exit(1)

    profile, _ = api("/users/{}".format(USER), tok)
    created = datetime.strptime(profile["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    return {
        "level": (now - created).days // 365,
        "langs": langs,
        "tracks": tracks,
        "repos_counted": counted,
        "saw_private": saw_private,
    }


def shares(counter):
    total = sum(counter.values()) or 1
    return sorted(((k, 100.0 * v / total) for k, v in counter.items()),
                  key=lambda kv: kv[1], reverse=True)


# --------------------------------------------------------------------------
# SVG
# --------------------------------------------------------------------------

def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(stats, theme):
    c = THEMES[theme]
    track_rows = shares(stats["tracks"])
    code_langs = Counter({k: v for k, v in stats["langs"].items()
                          if k != NOTEBOOK_LANG})
    lang_rows = shares(code_langs)[:6]
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Ids are namespaced per theme so both sheets can be inlined into a single
    # document - a preview page, say - without the first one's defs winning.
    grad = "win-" + theme
    clip = "barclip-" + theme

    o = []
    add = o.append
    add('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="500" '
        'viewBox="0 0 900 500" role="img" '
        'aria-label="Character sheet for C. Renaudo">')
    add('<defs><linearGradient id="{}" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="{}"/>'
        '<stop offset="1" stop-color="{}"/></linearGradient>'
        '<clipPath id="{}"><rect x="44" y="386" width="812" height="18" '
        'rx="4"/></clipPath></defs>'.format(
            grad, c["win_top"], c["win_bottom"], clip))

    # Window frame: heavy outer edge plus an inner hairline - the RPG Maker
    # message-box look.
    add('<rect x="6" y="6" width="888" height="488" rx="10" fill="url(#{})" '
        'stroke="{}" stroke-width="3"/>'.format(grad, c["edge"]))
    add('<rect x="15" y="15" width="870" height="470" rx="6" fill="none" '
        'stroke="{}" stroke-width="1.5"/>'.format(c["inner"]))
    add('<g font-family="{}">'.format(MONO))

    # Title block
    add('<text x="44" y="72" font-size="31" font-weight="700" fill="{}" '
        'letter-spacing="1.5">C. RENAUDO</text>'.format(c["text"]))
    add('<text x="856" y="72" font-size="27" font-weight="700" fill="{}" '
        'text-anchor="end">Lv.{}</text>'.format(c["accent"], stats["level"]))
    add('<text x="45" y="99" font-size="15" fill="{}">PhD Chemical '
        'Engineering &#183; Research Toolsmith</text>'.format(c["dim"]))
    add('<text x="45" y="121" font-size="13" fill="{}">Assistant Researcher, '
        'PLAPIQUI (UNS&#8211;CONICET) &#183; Teaching Assistant, UNS'
        '</text>'.format(c["dim"]))
    add('<line x1="44" y1="140" x2="856" y2="140" stroke="{}" '
        'stroke-width="1"/>'.format(c["inner"]))

    # Skill trees
    add('<text x="44" y="167" font-size="12" font-weight="700" fill="{}" '
        'letter-spacing="2.5">SKILL TREES</text>'.format(c["accent"]))
    y = 196
    for key, pct in track_rows:
        label, color = TRACKS[key]
        add('<text x="44" y="{}" font-size="14" fill="{}">{}</text>'.format(
            y + 4, c["text"], esc(label)))
        filled = int(round(pct / 100.0 * SEGMENTS))
        if pct > 0:
            # A non-zero track must light at least one segment, or a small
            # share renders as an empty bar and reads as broken.
            filled = max(filled, 1)
        for i in range(SEGMENTS):
            add('<rect x="{}" y="{}" width="21" height="15" rx="2" '
                'fill="{}"/>'.format(330 + i * 26, y - 10,
                                     color if i < filled else c["rail"]))
        add('<text x="856" y="{}" font-size="14" font-weight="700" fill="{}" '
            'text-anchor="end">{:.0f}%</text>'.format(y + 4, c["text"], pct))
        y += 34

    add('<line x1="44" y1="332" x2="856" y2="332" stroke="{}" '
        'stroke-width="1"/>'.format(c["inner"]))

    # Proficiencies: one stacked bar plus a fixed-column legend.
    add('<text x="44" y="362" font-size="12" font-weight="700" fill="{}" '
        'letter-spacing="2.5">PROFICIENCIES</text>'.format(c["accent"]))
    x = 44.0
    add('<g clip-path="url(#{})">'.format(clip))
    for name, pct in lang_rows:
        w = 812.0 * pct / 100.0
        add('<rect x="{:.1f}" y="386" width="{:.1f}" height="18" '
            'fill="{}"/>'.format(x, w + 1.0,
                                 LANG_COLORS.get(name, FALLBACK_COLOR)))
        x += w
    add('</g>')
    add('<rect x="44" y="386" width="812" height="18" rx="4" fill="none" '
        'stroke="{}" stroke-width="1"/>'.format(c["inner"]))

    for i, (name, pct) in enumerate(lang_rows):
        lx = 46 + i * 136
        add('<circle cx="{}" cy="430" r="5" fill="{}"/>'.format(
            lx + 5, LANG_COLORS.get(name, FALLBACK_COLOR)))
        add('<text x="{}" y="435" font-size="13" fill="{}">{} {:.0f}%</text>'
            .format(lx + 17, c["text"], esc(name), pct))

    add('<text x="44" y="466" font-size="11" fill="{}">aggregated across {} '
        'public and private repositories &#183; updated {}</text>'.format(
            c["dim"], stats["repos_counted"], updated))
    add('</g></svg>')
    return "\n".join(o) + "\n"


# --------------------------------------------------------------------------
# Latest posts
# --------------------------------------------------------------------------

START = "<!-- POSTS:START -->"
END = "<!-- POSTS:END -->"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def latest_posts(limit=3):
    if LOCAL_FEED.exists():
        raw = LOCAL_FEED.read_bytes()
    else:
        try:
            req = urllib.request.Request(
                FEED_URL, headers={"User-Agent": "carenaudo-profile-generator"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read()
        except Exception:
            return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    out = []
    for entry in root.findall("atom:entry", NS)[:limit]:
        title = (entry.findtext("atom:title", "", NS) or "").strip()
        link_el = entry.find("atom:link", NS)
        href = link_el.get("href", "") if link_el is not None else ""
        date = (entry.findtext("atom:published", "", NS) or "")[:10]
        if title and href:
            out.append((title, href, date))
    return out


def update_readme(readme):
    posts = latest_posts()
    if not posts:
        return False
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        return False
    lines = ["- **[{}]({})** &middot; {}".format(t, h, d) for t, h, d in posts]
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    block = START + "\n" + "\n".join(lines) + "\n" + END
    readme.write_text(head + block + tail, encoding="utf-8")
    return True


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-posts", action="store_true",
                        help="do not touch the README posts block")
    parser.add_argument("--allow-partial", action="store_true",
                        help="write the sheet even when the token cannot see "
                             "private repositories (totals will be wrong)")
    args = parser.parse_args()

    tok = token()
    if not tok:
        sys.stderr.write(
            "WARNING: no token found (PROFILE_STATS_TOKEN / GH_TOKEN / "
            "GITHUB_TOKEN); falling back to public repositories only, so the "
            "totals will be wrong.\n")

    stats = collect(tok)

    # Refuse to overwrite a correct sheet with a degraded one. In CI the
    # default GITHUB_TOKEN sees only this repository, which would otherwise
    # silently produce a near-empty sheet and commit it. A red run is far
    # better than a profile quietly showing the wrong numbers.
    if not args.allow_partial and (stats["repos_counted"] == 0
                                   or not stats["saw_private"]):
        sys.stderr.write(
            "ERROR: this token sees {} repository/repositories and no private "
            "ones, so the totals would be wrong and are not being written. "
            "Set the PROFILE_STATS_TOKEN secret to a fine-grained PAT with "
            "read-only repository metadata access, or pass --allow-partial to "
            "write anyway.\n".format(stats["repos_counted"]))
        return 1

    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    for theme in ("dark", "light"):
        path = assets / "character-sheet-{}.svg".format(theme)
        path.write_text(build_svg(stats, theme), encoding="utf-8")
        print("wrote {}".format(path.relative_to(ROOT).as_posix()))

    if not args.skip_posts:
        if update_readme(ROOT / "README.md"):
            print("updated README posts block")
        else:
            print("no feed entries yet; README posts block left as is")

    # Aggregates only - safe for a public CI log.
    print("level Lv.{} from {} repositories".format(
        stats["level"], stats["repos_counted"]))
    for key, pct in shares(stats["tracks"]):
        print("  {:28} {:5.1f}%".format(TRACKS[key][0], pct))
    return 0


if __name__ == "__main__":
    sys.exit(main())
