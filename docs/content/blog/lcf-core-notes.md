+++
title = "Reimplementing the LCF format in Rust"
description = "Notes on building lcf-core, a pure-Rust reader and writer for the RPG Maker 2000/2003 binary format."
date = 2026-09-03
slug = "lcf-core-notes"
draft = true

[taxonomies]
tags = ["engineering", "ai-assisted"]
+++

<!--
DRAFT OUTLINE - not published until `draft = true` is removed.

This is a skeleton, not a finished post. The section headings are the argument;
fill each one from what you actually hit while building `lcf-core`. Anything
you cannot back from the code or from liblcf should come out rather than get
hand-waved.

Suggested shape:

1. What LCF is
   - The four file types: .ldb (database), .lmt (map tree), .lmu (map), .lsd (save).
   - Where the format documentation came from: EasyRPG's open docs and liblcf.

2. Why reimplement it at all
   - What you wanted that binding to liblcf would not have given you.
   - Be fair to EasyRPG's Editor here; the README already is.

3. The chunk model
   - How records and chunks are structured, and how you represented that in Rust.
   - The typing decisions: where you used enums, where you kept raw bytes.

4. Round-tripping as the correctness test
   - Reading and writing back byte-for-byte is the property that matters.
   - What you tested against, and what that did and did not catch.

5. Where it bit you
   - The cases the reference implementation handles that a naive reader misses.
   - Maniac Patch content passing through as inert data.

6. Writing it with an AI assistant
   - Specific: what it was good at (mechanical field coverage, 153 fields of
     Terms/Vocabulary) versus where it needed hard verification (anything where
     being subtly wrong means corrupting someone's project file).

7. What it is not
   - Not affiliated with EasyRPG, not as tested as their tools, back up your projects.
-->

*Draft in progress.*
