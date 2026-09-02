+++
title = "Reimplementing the LCF format in Rust"
description = "Notes on lcf-core: what the RPG Maker 2000/2003 binary format is, why writing it is harder than reading it, and the false completeness claim an AI assistant left in my own repository."
date = 2026-09-02T14:00:00Z
slug = "lcf-core-notes"

[taxonomies]
tags = ["engineering", "ai-assisted"]
+++

This one started with a build failure, not an ambition.

[easy-rpg-REditor](https://github.com/carenaudo/easy-rpg-REditor) needed to read RPG Maker
2000/2003 project files, and the reference implementation for that format is
[`liblcf`](https://github.com/EasyRPG/liblcf) — a mature C++ library maintained by the
EasyRPG project. The obvious move is to bind to it. I spent a while fighting vcpkg and ICU
trying to get it linking statically under MSVC, and at some point the question stopped being
"how do I get this to build" and became "what would it take not to need it."

That is the second reason from [the previous post](@/blog/2026-09-02-a-log-for-the-tooling.md):
the tool exists and is good, but the shape I needed it in — no C++ toolchain, no vcpkg, no
static-linking ritual for anyone who clones the repo — was specific enough that removing the
dependency was cheaper than carrying it.

## What LCF actually is

Four binary files, all the same format underneath:

| File | Holds |
|---|---|
| `.ldb` | The database — actors, items, skills, enemies, troops, chipsets, terms |
| `.lmt` | The map tree |
| `.lmu` | A single map |
| `.lsd` | A save file |

The encoding is pleasantly simple. Every field on disk is:

```text
[chunk_id: varint][length: varint][payload]
```

The varint is the usual 7-bits-per-byte scheme with the top bit as a continuation flag. A
struct's reader is a loop over chunks: if the id maps to a field it knows, decode the payload
by that field's declared type; if it does not, seek forward by `length` and carry on.

That last clause is the single most useful property of the format. **Unknown chunks are
skippable**, which means a reader that only understands a third of the fields still reads the
other two thirds correctly rather than desynchronising and producing garbage. It is what
makes an incremental port possible at all: you can hand-write three structs, test them
against real files, and know that the fields you have not gotten to yet are being stepped
over cleanly rather than silently corrupting their neighbours.

## The easy part and the hard part

Reading is the easy part. The varint decoder and chunk loop are perhaps an afternoon, and
the writer's varint encoder is a trivial mirror of the reader's.

The hard part is deciding *what to write at all*.

The rule LCF uses is that a field's chunk is emitted only if either the field is explicitly
marked as persist-if-default, or its current value differs from its declared default. Fields
sitting at their default are simply omitted from the file. This is what keeps output
byte-compatible with what RPG Maker's own editor produces — and it means every single field
needs to know its own default before you can write it back.

In liblcf's schema, 348 of 1,044 fields carry the persist-if-default flag. The rest are
governed by a default comparison. Three things make that worse than it sounds:

1. **Defaults are not always constants.** Some are version-conditional. `Actor.final_level`
   has a default of `50|99` — 50 under RPG Maker 2000, 99 under 2003 — resolved against the
   engine version recorded in the file itself. A port that hard-codes either number produces
   files that are subtly wrong on the other engine.
2. **Strings have to survive the round trip.** Text is stored in the project's own 8-bit
   encoding — Shift-JIS for a Japanese project, Windows-1252 for a Western one — so the write
   path has to *encode* back into it, not just decode out of it. [`encoding_rs`](https://docs.rs/encoding_rs)
   handles this well: it is bidirectional, it is what Firefox uses, and it needs no C
   toolchain, which was the whole point.
3. **Array order and index semantics have to be exact.** This is the one that actually
   frightens me. A read bug shows wrong data in the editor — visible, annoying, harmless. An
   off-by-one in an array index produces a file that RPG Maker loads *happily*, with the
   wrong event sitting on the wrong map slot. The failure is silent and it is in the user's
   project, not in my program.

## Why the schema had to generate the code

Seventy structs. Roughly 1,200 fields. Seventy-three enums.

Hand-transcribing default values, persistence flags and version conditions across 1,200
fields is not engineering, it is dictation — and the error rate on dictation is not zero. It
is also exactly the work that liblcf's own `generator/csv/*.csv` schema already exists to
make mechanical. That schema is the same source of truth liblcf's C++ is generated from, and
it has been validated against real RPG Maker output for years.

So `lcf-core` is generated from those CSVs by `lcf-codegen`, a standalone Rust crate in the
same repository. Not liblcf's Python and Jinja2 pipeline — reimplementing the consumer in
Rust keeps the build self-contained, so a contributor needs `cargo` and nothing else.

The payoff is where correctness is bounded. Consuming the schema means the question is "did
I translate the schema correctly," which is one problem, rather than "did I transcribe 1,200
fields correctly," which is 1,200 problems.

## The sequencing that mattered

The tempting move is to build the code generator first, since it is obviously the interesting
part.

That is a trap, and it is worth naming: **codegen built on unvalidated primitives compounds
one bug across all seventy structs simultaneously, instead of catching it on one.** A varint
off-by-one or a wrong default-comparison rule, discovered after generation, is seventy
identical bugs and a regenerate-and-pray cycle.

So the order was: hand-write the reader and writer primitives and two or three real structs,
get round-trip byte-identity tests passing on actual game files, and only then point a
generator at the pattern those structs proved.

## Round-tripping is the only test that counts

The test is unglamorous and it is the whole safety net:

1. Read a real `.ldb` / `.lmt` / `.lmu` / `.lsd` with the Rust reader.
2. Write it straight back out, unmodified.
3. Byte-diff the output against the original.

Any difference has to be *explainable*, not merely small. Where it currently stands:

```text
test test_ldb_roundtrip_2000 ... ok    (8 actors, 14 chipsets, 132 skills,
                                        86 items, 81 enemies, 86 troops)
test test_lmt_roundtrip_2000 ... ok    (81 maps)
test test_lmt_roundtrip_2003 ... ok    (22 maps)
test test_lmu_roundtrip_all_maps_2000 ... ok  (80 maps)
test test_lmu_roundtrip_all_maps_2003 ... ok  (20 maps)
test test_lsd_save_roundtrip ... ok
```

Which is a real result and a narrow one. It says the format machinery survives contact with
the projects I have. It does not say it survives the enormous variety of real RPG Maker games
that exist, and I would not claim otherwise.

`lcf-core` is alpha. That is not modesty, it is the status.

## The false claim in my own repository

Which brings me to the part of this worth writing down.

There is a document in this repository that opens by announcing complete **100% API-level
feature parity** with C++ `liblcf`.

That claim is false. Nobody enumerated liblcf's API and checked it off. What actually
happened is that eight round-trip tests passed, and somewhere between that result and the
document, it became a completeness claim about the entire library.

I did not write that sentence, and that is exactly the point. It was produced in the middle
of an AI-assisted session, in the confident register these tools default to, and then it sat
in my repository — in my voice, under my name — looking like a fact I had established.
Months later it is indistinguishable from something I verified, because nothing about it
looks uncertain.

This is the failure mode I would flag to anyone working this way. The assistant does not
hedge unless you make it. It will summarise "the tests I was told to run passed" as "100%
parity achieved," because that is the shape of the sentence that usually follows in the
text it learned from. The generated code was checked by a test suite. The generated *prose
about* the code was checked by nobody.

Documentation written this way inherits the cadence of a finished result without inheriting
the work that would justify it — and unlike a code bug, no test ever fails to tell you.

## What the assistant was and was not good for

With that caveat sitting in front, the split was sharper here than on most work.

It was genuinely good at the mechanical surface: 153 fields of terms and vocabulary, seventy
struct definitions, the enum translations. Wide, repetitive, well-specified work where the
schema says exactly what the answer is.

It was not something I would trust unverified anywhere near the write path, and I did not.
The round-trip byte-diff is not a formality there; it is the thing standing between a
plausible-looking implementation and a corrupted project file. Plausible is precisely what a
language model is good at producing, and plausible is not the bar when the failure mode is
damaging someone's game.

So: fastest exactly where a schema or a test can check its work, most dangerous exactly where
neither can — and prose is the place where neither can.

## What this is not

It is not finished, and it is not a replacement for anything. `lcf-core` is alpha: round-trip
tested against a handful of real and synthetic projects, not against the variety of games
that actually exist.

It is also not affiliated with, endorsed by, or supported by EasyRPG. Their open
documentation of the format and their `liblcf` source are the reason any of this was
possible, and their own [Editor](https://github.com/EasyRPG/Editor) is the mature,
well-tested tool. If you have a project you care about, use theirs — and either way, keep
backups.
