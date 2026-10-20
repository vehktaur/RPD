#!/usr/bin/env python3
"""
fix_bib.py -- repair a Mendeley BibTeX export so LaTeX can use it.

Run this after every re-export from Mendeley:

    python tools/fix_bib.py references.bib

Mendeley has three habits that quietly break a bibliography:

  1. It reuses citation keys. Five different 2026 papers by an author named
     Zhang all come out as "Zhang2026". BibTeX keeps the first and DISCARDS
     the rest with only a "Repeated entry" line buried in the .blg log.
  2. It emits entries with no key at all -- "@techReport{," -- for records
     imported by dragging in a PDF, where it never found author or year.
     These collide with each other and all but one is dropped.
  3. It leaves LaTeX special characters (& _ # %) unescaped in titles and
     author fields, which makes pdflatex fail once the entry is cited.

This script fixes all three, and keeps assigned keys STABLE across
re-exports by remembering them in tools/bibkeys.json. That matters: once
your chapters contain \cite{Zhang2026c}, a fresh export that renumbers the
suffixes would silently point that citation at a different paper.

It rewrites the file in place after saving a .bak copy, and prints a report
of anything whose metadata is still wrong and needs fixing in Mendeley.
"""

import json
import os
import re
import shutil
import sys

SPECIALS = set("&_#%")
SKIP_ESCAPE = {"abstract"}
KEYMAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bibkeys.json")


def escape_specials(value: str) -> str:
    """Backslash-escape LaTeX specials, leaving existing escapes and $math$ alone."""
    out, i = [], 0
    while i < len(value):
        ch = value[i]
        if ch == "\\":
            out.append(value[i:i + 2])
            i += 2
            continue
        if ch == "$":
            close = value.find("$", i + 1)
            if close != -1:
                out.append(value[i:close + 1])
                i = close + 1
                continue
        out.append("\\" + ch if ch in SPECIALS else ch)
        i += 1
    return "".join(out)


def split_entries(text: str):
    return re.split(r"(?=^@\w+\{)", text, flags=re.M)


def field(entry: str, name: str) -> str:
    m = re.search(r"\n\s*" + name + r"\s*=\s*\{(.*?)\},?\s*\n", entry, re.S)
    return m.group(1).strip() if m else ""


def title_signature(entry: str) -> str:
    """Stable identity for an entry, used to keep its key across re-exports."""
    return re.sub(r"[^a-z0-9]", "", field(entry, "title").lower())[:80]


def escape_entry(entry: str) -> tuple[str, int]:
    pattern = re.compile(r"(\n[ \t]*)([A-Za-z]+)([ \t]*=[ \t]*)\{")
    parts, pos, changed = [], 0, 0
    while True:
        m = pattern.search(entry, pos)
        if not m:
            break
        parts.append(entry[pos:m.end()])
        depth, i = 1, m.end()
        while i < len(entry) and depth:
            if entry[i] == "\\":
                i += 2
                continue
            depth += (entry[i] == "{") - (entry[i] == "}")
            i += 1
        value = entry[m.end():i - 1]
        if m.group(2).lower() in SKIP_ESCAPE:
            parts.append(value + "}")
        else:
            fixed = escape_specials(value)
            changed += fixed != value
            parts.append(fixed + "}")
        pos = i
    parts.append(entry[pos:])
    return "".join(parts), changed


def derive_key(entry: str) -> str:
    authors = field(entry, "author")
    surname = "Anon"
    if authors:
        first = authors.split(" and ")[0].strip()
        surname = first.split(",")[0] if "," in first else first.split()[-1]
        surname = re.sub(r"[^A-Za-z]", "", surname) or "Anon"
    year = re.search(r"\n\s*year\s*=\s*\{?(\d{4})", entry)
    return f"{surname}{year.group(1) if year else 'nd'}"


def audit(key: str, entry: str) -> list[str]:
    problems = []
    title, author, year = field(entry, "title"), field(entry, "author"), field(entry, "year")
    if not author:
        problems.append("no author")
    if not year:
        problems.append("no year")
    if not title:
        problems.append("no title")
    elif len(title) < 20:
        problems.append("title looks truncated")
    elif title.count("-") > 4 or title.lower().endswith((".pdf", "-co")):
        problems.append("filename in title field")
    if title and not field(entry, "doi") and not field(entry, "url"):
        problems.append("no DOI or URL")
    return problems


def main(path: str) -> int:
    text = open(path, encoding="utf-8", errors="ignore").read()
    remembered = json.load(open(KEYMAP)) if os.path.exists(KEYMAP) else {}

    entries = split_entries(text)
    taken, escaped, keyed, problems = set(), 0, 0, []
    occurrence = {}          # signature -> how many times seen in this run
    out = []

    for entry in entries:
        m = re.match(r"^(@\w+\{)([^,]*),", entry)
        if not m:
            out.append(entry)
            continue

        current = m.group(2).strip()
        sig = title_signature(entry)

        # Mendeley can hold the same paper twice. Index each occurrence so the
        # second copy gets its own stable key rather than colliding.
        n = occurrence.get(sig, 0)
        occurrence[sig] = n + 1
        memo = f"{sig}#{n}" if sig else None

        if memo and memo in remembered and remembered[memo] not in taken:
            key = remembered[memo]                       # stable across exports
        elif current and current not in taken:
            key = current                                # Mendeley's key is fine
        else:
            base = derive_key(entry)
            key, i = base, 0
            while key in taken:
                key = base + chr(ord("a") + i)
                i += 1

        if key != current:
            entry = re.sub(r"^(@\w+\{)[^,]*,", r"\1" + key + ",", entry, count=1)
            keyed += 1
        taken.add(key)
        if memo:
            remembered[memo] = key

        entry, n_esc = escape_entry(entry)
        escaped += n_esc

        found = audit(key, entry)
        if found:
            problems.append((key, found, field(entry, "title")[:58]))
        out.append(entry)

    shutil.copyfile(path, path + ".bak")
    open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    json.dump(remembered, open(KEYMAP, "w"), indent=1, sort_keys=True)

    total = sum(1 for e in entries if re.match(r"^@\w+\{", e))
    print(f"{path}: {total} entries, {len(taken)} unique keys")
    print(f"  keys assigned or disambiguated : {keyed}")
    print(f"  fields escaped                 : {escaped}")
    print(f"  keys remembered for next export: {len(remembered)}")
    print(f"  backup written                 : {os.path.basename(path)}.bak")

    if len(taken) != total:
        print("\n  WARNING: key count does not match entry count.")

    if problems:
        print(f"\n{len(problems)} entries still have bad metadata. "
              f"Fix these in Mendeley, not here:\n")
        for key, found, title in problems:
            print(f"  {key:20s} [{', '.join(found)}]")
            print(f"  {'':20s} {title}")
    else:
        print("\nNo metadata problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "references.bib"))
