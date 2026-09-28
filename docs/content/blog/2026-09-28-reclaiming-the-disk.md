+++
title = "Reclaiming the disk"
description = "Two small Rust tools that give disk space back, why the order they delete things in matters more than how fast they find them, and the promise an AI-assisted README made that the code did not keep."
date = 2026-09-28
slug = "reclaiming-the-disk"

[taxonomies]
tags = ["engineering", "ai-assisted"]
+++

Two small tools in the same week, both Rust, both doing the same kind of job: find what is
quietly eating a drive and give the space back.

[cargo-trim](https://github.com/carenaudo/cargo-trim) looks for Cargo `target/` directories.
[uv-migrator](https://github.com/carenaudo/uv-migrator) looks for Python virtual environments
and rebuilds them with [`uv`](https://github.com/astral-sh/uv).

## What the junk looks like

The tables below are illustrative, not a run on my drive. They show the typical sizes of this
kind of junk on a workstation that has been used for a few years of scientific and desktop
work.

Rust build output grows with the dependency tree, not with the size of your own code. A
native GUI pulls in a graphics stack, and every profile and every toolchain upgrade leaves
its own copy:

```text
Project Path                                     Size        Last Active
─────────────────────────────────────────────────────────────────────────
projects/editor/target                          11.8 GB      3 days ago
projects/solvers/pbe-rust/target                 6.9 GB      5 weeks ago
projects/instrument/parser-rs/target             2.1 GB      2 months ago
projects/tools/cli-utility/target              740.0 MB      1 week ago
sandbox/hello_world/target                       6.0 MB      3.1 years ago
─────────────────────────────────────────────────────────────────────────
Total                                           21.5 GB across 5 projects
```

Python environments are the same story in a different shape. Each one is a full private copy
of everything it has installed, and the scientific stack is not small:

```text
Environment                                      Python      Size
─────────────────────────────────────────────────────────────────────────
research/ml-segmentation/.venv   (torch, onnx)   3.11        5.6 GB
research/droplet-models/.venv    (scipy, mpl)    3.12        690 MB
desktop/qt-tool/venv             (PySide6)       3.12        610 MB
teaching/fluids-notebooks/.venv  (jupyter)       3.11        480 MB
scratch/old-experiment/env       (numpy)         3.9         210 MB
─────────────────────────────────────────────────────────────────────────
Total                                                        7.6 GB
```

uv keeps one copy of each package version in a shared cache and links it into every
environment that needs it. So five environments that all use NumPy stop costing five NumPy
installs, and the space that comes back depends on how much the environments overlap.

Nobody decides to spend 30 GB like that. Each build and each environment just leaves its
contents behind. Finding it turned out to be the easy part. The hard part is being sure that
whatever you delete can be got back.

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

The GUI for uv-migrator is `egui`, the same as the RPG Maker editor. It comes out at about
6.6 MB, and the CLI at about 3 MB. For a tool whose whole purpose is recovering disk space,
shipping it inside a bundled browser runtime would have been a bad joke.

## The part that matters is what "deleted" costs

The two tools delete very different kinds of things.

A Cargo `target/` directory is a cache. Delete it and the worst that happens is the next
`cargo build` takes a while. That is why cargo-trim can be fairly relaxed: it shows you a
sorted table, asks `y/N`, and then removes the directories. It will not delete the `target/`
directory containing its own running binary, which is the one self-inflicted wound worth
guarding against explicitly.

A virtual environment looks like a cache too, but often it is not. If the project has a
complete `pyproject.toml` or `requirements.txt`, the environment can be rebuilt from it and
deleting it costs a reinstall. If the project has neither, or has one that stopped being true
the day somebody ran `pip install` by hand, then the environment is the only record of what
the code actually runs against. Delete it and that information is gone.

So the two tools need different levels of care, and the second one needs a great deal more.

## What uv-migrator used to do

Both tools were written in AI-assisted sessions; the `authors` field in both manifests still
names the assistant. Before writing this I went back and read the code against the READMEs.

The uv-migrator README listed "Zero Data Loss" as a principle. The order of operations in
the [first version of `migrator.rs`](https://github.com/carenaudo/uv-migrator/blob/d9e756a557da742bcd1e7708d6443b95920bdcf2/src/migrator.rs)
was:

1. If the project had no `pyproject.toml`, `requirements.txt`, `setup.py` or `uv.lock`,
   write the installed packages into a new `requirements.txt`.
2. Delete the old environment.
3. Create the new one with `uv venv`.
4. Install dependencies into it.

Step 2 came before steps 3 and 4. If either of those failed (a pin with no wheel for the
target Python, a network drop, a package that was installed from a local path), the old
environment was already gone. I built an environment designed to fail that way, with one
package installed from a local folder that no longer existed, and ran the first version on
it. It deleted the environment, failed to install anything into the replacement (not even the
package that was available from the index), and reported the migration as **OK**. The
project's `venv/` had been replaced by an empty `.venv`. And that was not the only problem:

- **The snapshot was conditional.** It was only written when the project had no manifest at
  all. A project with a `requirements.txt` listing half of what was installed got no
  snapshot, and the other half was lost.
- **The snapshot flattened provenance.** A package installed in editable mode, from a git URL
  or from a local path became `name==version`, which may not resolve from an index at all.
- **A failed pinned install fell back to unpinned.** If `uv pip install -r` failed, the
  fallback stripped every version bound, installed the latest of each package, and reported
  success. That is a silent upgrade of every dependency, which is exactly what a pinned
  environment exists to prevent.
- **A partial install counted as success.** If the new environment had a Python binary, the
  migration was marked successful even when dependency installation had failed.
- **The dry run estimated rather than measured.** Its "new size" was the old size multiplied
  by 0.3.

None of this is exotic. It is the ordinary result of writing the happy path first and the
guarantees second. What made it dangerous is that the README described the guarantees as if
they were already there.

## What it does now

The [fix](https://github.com/carenaudo/uv-migrator/commit/0a78e44dba7124dbc203b28406fc97ac757dca1e)
is not complicated. It is just slower, and it needs a little more disk space at the peak:

1. **Always snapshot**, to a sidecar file next to the environment
   (`.venv.uv-migrator-snapshot.txt`), whatever manifests exist. Each line keeps the package's
   source from its `direct_url.json`, so an editable checkout stays `-e`, a git install stays
   pinned to its commit, and a local path stays a local path. `requirements.txt` is never
   touched.
2. **Move the old environment aside** to `.venv.uv-migrator-backup`. Do not delete it.
3. **Build the new environment in its place** from the snapshot, pins intact. There is no
   unpinned fallback any more: if the pins cannot be satisfied, that is a failure.
4. **Verify**: every package in the snapshot must be installed at the same version.
5. **Only then delete the old environment.** If any step fails, remove the half-built one and
   move the original back.

I ran the new version on two test projects. The first had an incomplete `requirements.txt`, an
editable local package and two pinned packages. It migrated, and all of them were installed
at the same versions, with the local package still editable. The second had a package
installed from a local folder that I then deleted, so it could not be reinstalled. That one
failed, as it should, and the original environment was put back unchanged: same files, same
`pyvenv.cfg`, still importable.

The dry run no longer guesses a size. It reports the target Python and how many packages it
would rebuild and verify. The size of each new environment is labelled as apparent, because
uv's hardlinks make a file count in full in every environment that links it. The only honest
measure of what came back is the change in free space on the volume, and that is now the
number the summary puts forward.

cargo-trim has a smaller version of the same gap. It treats a directory named `target` as
Cargo's if it contains a `debug/` or `release/` folder, even without a `Cargo.toml` next to it
or the `CACHEDIR.TAG` Cargo writes. For a directory it is about to delete whole, that
evidence is too weak, and it is the next thing to tighten. But a false positive there costs
a rebuild at worst, not a lost environment.

## What the assistant was and was not good for

As in [the LCF post](@/blog/lcf-core-notes.md), the split is clear. The assistant was quick at
everything a compiler or a run could check: the walker, the parallel sizing, the `egui`
screens, the calls out to `uv`. It was also the one that wrote "Zero Data Loss" into the
README, in the same confident voice as everything else, and nothing ever checked that
sentence.

The fix came out of an AI-assisted session as well. What changed was the order of work. First
the code was read against the README and each gap was written down. Then the code was changed
and run against an environment built to fail, and only after that was the README rewritten
to match what the run showed. The assistant is good at producing the happy path. Designing
the failure path is still on me.

For a tool that only reports, a README that promises more than the code does is
embarrassing. For a tool that deletes, the gap is the whole question. The first thing to
design in a cleanup tool is the sequence that makes sure nothing is lost. The speed of the
scan barely matters beside it.
