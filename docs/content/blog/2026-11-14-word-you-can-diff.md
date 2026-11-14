+++
title = "Word you can diff"
description = "Quire-Tex: a Word-style editor whose file is LaTeX, and the property test that keeps it honest."
date = 2026-11-14T18:00:00Z
slug = "word-you-can-diff"

[taxonomies]
tags = ["engineering", "ai-assisted"]
+++

Most of what I write ends up in one of two places. Many journals and co-authors want Word: a
template, tracked changes, comments in the margin. I want LaTeX: equations, references that
never go stale, a bibliography database, and plain text I can keep in Git.

Quire-Tex is an attempt to stop choosing. It is a visual editor that looks and works like
Word, built on [WordCraft](https://github.com/storytold/wordcraft), an open-source Word-style
editor in Rust. The difference is the file underneath. Quire-Tex reads and writes LaTeX, and
compiles it with TeX Live.

## The file is the TeX

Bold writes `\textbf`, Heading 1 writes `\section`, a table becomes a `tabular`, a citation a
`\cite` from your `.bib`. References, citations and captions are rendered on the page from the
last compile. Anything the editor does not understand yet, such as TikZ or a custom macro, is
kept as TeX and hidden unless you ask to see it.

Review works the same way. Comments become `todonotes`, tracked changes become the `changes`
package, and the thread details Word keeps (dates, initials, replies) go in a small file beside
the `.tex`. A co-author can review in a Word-like window, and the result is still a LaTeX
project that diffs line by line.

## Nothing is lost

The rule that makes this usable on real projects is the same one as in
[the LCF post](@/blog/lcf-core-notes.md): whatever you did not edit is written back byte for
byte. Opening and saving a paper must not reformat it.

A property test enforces that. It generates random strings of TeX's awkward characters
(backslashes, braces, `%`, `~`, blank lines), reads each one in, writes it out and requires the
same bytes back. It found a case nobody would have written by hand: `"~\n\n~"`.

The editor stored the source of each untouched paragraph under a fingerprint of its content.
Two identical paragraphs shared one entry, so the second one's trailing whitespace was written
for both, and a repeated paragraph followed by an environment got merged into its neighbour on
save. Each repeat now keeps its own source, and the shrunk case is checked in so it runs before
any new ones.

## Where it is

This is about a week of work, pair-programmed with an AI assistant, on top of a project that
did the hard part. Text, headings, lists, tables, figures, footnotes, citations, multi-file
projects and the bibliography work. A PDF pane with SyncTeX, and ribbon buttons for
everything Word offers, do not exist yet.

It is not public yet.
