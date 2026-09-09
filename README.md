# Research Proposal — LaTeX

RPD proposal for Universiti Teknologi PETRONAS, built to match
`RPD Proposal Template Oct 2020.docx`.

## Build

```
latexmk -pdf main.tex
```

Output lands in `build/main.pdf`. In VS Code, install the **LaTeX Workshop**
extension and press `Ctrl+Alt+B`; `.vscode/settings.json` is already wired up.

You need a TeX distribution on Windows — **MiKTeX** is the easy option, since
it fetches missing packages on demand.

## Layout

| File | What it holds |
|---|---|
| `main.tex` | Document root. Nothing but structure. |
| `metadata.tex` | **Edit here** for title, name, ID, dates, programme. |
| `preamble.tex` | Formatting. Matches the Word template. |
| `frontmatter/cover.tex` | Cover page layout. |
| `chapters/*.tex` | One file per chapter. Guidance is in the comments. |
| `references.bib` | Bibliography. Export over it from Zotero/Mendeley. |

## Formatting decisions

- Letter paper, 1 in margins, Times (via `mathptmx`), 12 pt — from the template.
- **1.5 line spacing.** The bare template is single-spaced; UTP submissions are
  normally 1.5. Switch in `preamble.tex` if your supervisor prefers otherwise.
- Sections are numbered (1.1, 1.2, ...). The template leaves Chapter 1's
  subsections unnumbered but numbers Chapter 3's — an inconsistency in the
  template, not a rule.
- Chapter 4 is "REFERENCES" as a numbered chapter, per the template. The
  bibliography prints without its own heading to make that work.
- Citations are numeric, in order of appearance (`unsrtnat`). For author–year,
  swap to `plainnat` and drop the `[numbers]` option in `preamble.tex`.

## Before submitting

Search the source for `\note` — every placeholder uses it, and they render in
red so nothing gets missed. Delete the `placeholder2026` entry from
`references.bib` and the `\nocite` line in `chapters/04_references.tex` once
the real library is imported.
