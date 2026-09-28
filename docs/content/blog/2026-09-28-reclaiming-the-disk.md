+++
title = "Reclaiming the disk"
description = "Two small Rust tools that give disk space back, and why the order they delete things in matters more than how fast they find them."
date = 2026-09-28
slug = "reclaiming-the-disk"

[taxonomies]
tags = ["engineering"]
+++

Two small tools in the same week, both Rust, both doing the same kind of job: find what is
quietly eating a drive and give the space back.

[cargo-trim](https://github.com/carenaudo/cargo-trim) looks for Cargo `target/` directories.
[uv-migrator](https://github.com/carenaudo/uv-migrator) looks for Python virtual environments
and rebuilds them with [`uv`](https://github.com/astral-sh/uv). Pointed at my projects folder,
cargo-trim found 21.44 GB across five build directories, one of them last touched more than
three years ago. Nobody decides to spend 21 GB like that. Each build
just leaves its output behind.

Finding the waste turned out to be the easy part. The hard part is being sure that what you
delete can be got back.

## Finding is a directory walk

Both tools are, underneath, the same loop: walk the tree with
[`walkdir`](https://docs.rs/walkdir), recognise a directory by what is inside it, add up its
size, and stop descending once you have a match. The size and age calculations for
cargo-trim run in parallel with [`rayon`](https://docs.rs/rayon), which is most of why it
feels instant on a large drive.

The one design choice that matters here is what the walk refuses to skip. A general-purpose
cleaner tends to stop at the first project marker it recognises, which is reasonable until
your Rust solver lives three levels down inside a Python project. cargo-trim does not stop at
project boundaries. It skips `.git`, `.venv` and `node_modules` by name, because nothing it is
looking for lives in those, and it walks everything else.

The GUI for uv-migrator is `egui`, the same as the RPG Maker editor. It comes out at
about 6.6 MB, and the CLI at about 3 MB. For a tool whose whole purpose is recovering disk
space, shipping it inside a bundled browser runtime would have been a bad joke.

## The part that matters is what "deleted" costs

The two tools delete very different kinds of things.

A Cargo `target/` directory is a cache. Delete it and the worst that happens is the next
`cargo build` takes a while. That is why cargo-trim can be fairly relaxed: it shows you a
sorted table (path, size, how long since anything in it changed), asks `y/N`, and then removes
the directories. It will not delete the `target/` directory containing its own running
binary, which is the one self-inflicted wound worth guarding against explicitly.

A virtual environment looks like a cache too, but often it is not. If the project has a
complete `pyproject.toml` or `requirements.txt`, the environment can be rebuilt from it and
deleting it costs a reinstall. If the project has neither, or has one that stopped being true
the day somebody ran `pip install` by hand, then the environment is the only record of what
the code actually runs against. Delete it and that information is gone.

So the two tools need different levels of care, and the second one needs a great deal more.

## What the code actually does

I went back and read both tools against their own READMEs before writing this. Most of it
holds up. Some of it does not, and it is better to say so here than for someone to find out
the hard way.

**cargo-trim.** It decides a directory named `target` belongs to Cargo if any of three things
is true: it contains a `CACHEDIR.TAG` file, its parent contains a `Cargo.toml`, or it contains
a `.rustc_info.json`, a `debug/` or a `release/`. The first two are sound. The third is loose:
any build system that writes `target/release/` will match, and the name match ignores case, so
`Target/` qualifies too. For a directory the tool is about to delete in full, "contains a
folder called `release`" is not strong enough evidence. The fix is to require the Cargo
evidence and treat the rest as a hint.

Two smaller things. The `--keep-bin` mode only knows the `debug` and `release` profiles, so a
target built for a specific triple or a custom profile gets nothing trimmed. And the sizes in
the table are apparent sizes, the sum of file lengths, not what the filesystem actually
allocates. They are close enough for deciding what to delete, but they are not a precise
measure.

**uv-migrator.** This is the one I am less comfortable with. Its README lists "Zero Data Loss"
as a principle. The order of operations in
[`migrator.rs`](https://github.com/carenaudo/uv-migrator/blob/d9e756a557da742bcd1e7708d6443b95920bdcf2/src/migrator.rs)
is:

1. If the project has no `pyproject.toml`, `requirements.txt`, `setup.py` or `uv.lock`,
   write the installed packages out of `.dist-info` metadata into a new `requirements.txt`.
2. Delete the old environment.
3. Create the new one with `uv venv`.
4. Install dependencies into it.

Step 2 comes before steps 3 and 4. If either of those fails (a pin that has no wheel for the
target Python, a network drop, a package that was installed from a local path), the old
environment is already gone. And that is not the only problem:

- **The snapshot is conditional.** It is only written when the project has no manifest at
  all. A project with a `requirements.txt` that lists half of what is installed gets no
  snapshot, and the other half is lost.
- **The snapshot flattens provenance.** A package installed in editable mode, from a git URL
  or from a local wheel becomes `name==version`, which may not resolve from an index at all.
- **A failed pinned install falls back to unpinned.** If `uv pip install -r` fails, the
  fallback strips every version bound and installs the latest of each package. It then reports
  success. That is a silent upgrade of every dependency, which is exactly what a pinned
  environment exists to prevent.
- **A partial install counts as success.** If the new environment exists and has a Python
  binary, the migration is marked successful even when dependency installation failed. It
  carries a warning, but it still counts as a success.
- **The dry run estimates rather than measures.** Its "new size" is the old size multiplied
  by 0.3. That is a placeholder, not a prediction, and it should not be shown as a figure for
  space saved.

None of this is exotic. It is the ordinary result of writing the happy path first and the
guarantees second. But the README describes the guarantees as if they were already there.

## What it should do instead

The safe order is not complicated. It is just slower, and it needs a little more disk space
at the peak:

1. **Always snapshot**, to a sidecar file next to the environment rather than into
   `requirements.txt`, regardless of what manifests exist. Record the install source where
   `direct_url.json` has one, not just the version.
2. **Build the new environment beside the old one**, not in its place.
3. **Install and verify.** Compare what ended up installed against the snapshot, name for
   name and version for version. Any difference is a failure unless the user asked for an
   upgrade.
4. **Only then swap**, and only then delete the old environment.
5. **Measure what was actually reclaimed** as the change in free space on the volume. uv
   saves space by linking packages from a shared cache, so adding up file sizes inside each
   new environment counts the linked files in full and misses the cache entirely. Free space
   before and after is the only honest figure, and the tool already reads it.

cargo-trim can stay as it is apart from the stricter recognition rule, because a `target/`
directory costs nothing but time to rebuild.

Until uv-migrator does the above, the honest usage note is: run it with `--dry-run`, and only
migrate environments you could rebuild from their manifest anyway.

## The same lesson again

This is the lesson from [the LCF post](@/blog/lcf-core-notes.md) in a different place. The code
did roughly what it looked like it did. The README described something stronger: "Zero Data
Loss", "Safe Dry-Run Mode", a space gauge. Nothing ever checks a README, so nothing ever
failed to tell me the gap was there.

For a tool that only reports, that kind of gap is embarrassing. For a tool that deletes, it is
the whole question. The first thing to design in a cleanup tool is the sequence that ensures
nothing is lost. The speed of the scan barely matters beside it.

Both repositories will get the fixes described here. When they land, the READMEs will say what
the code does, and this post will link to the commits.
