+++
title = "Projects"
description = "Public repositories, and the research they come out of."
+++

## Public

### [easy-rpg-REditor](https://github.com/carenaudo/easy-rpg-REditor) · Rust

An unofficial map and database editor for RPG Maker 2000/2003, built on `lcf-core` — a
pure-Rust reimplementation of the LCF binary format (`.ldb`, `.lmt`, `.lmu`, `.lsd`). Tile
painting, event editing, a resource manager, MIDI synthesis via `rustysynth`, 8 UI
languages, 12 themes.

Not affiliated with or endorsed by [EasyRPG](https://easyrpg.org/), whose open documentation
of the format and `liblcf` reference implementation made it possible. Their
[Editor](https://github.com/EasyRPG/Editor) is the mature, well-tested one; use it for real
projects.

### [Menipy](https://github.com/carenaudo/Menipy) · Python

Droplet and meniscus shape analysis from images — pendant and sessile drop. A PySide6 GUI
plus a headless CLI, modelled as explicit pipelines: load, preprocess, segment, extract
contours, fit geometry, measure, validate, report. Alpha, and not a replacement for a
validated measurement tool.

### [uv-migrator](https://github.com/carenaudo/uv-migrator) · Rust

Migrates Python virtual environments to [`uv`](https://github.com/astral-sh/uv) and reclaims
the disk they were wasting. Snapshots installed packages from `.dist-info` metadata before
touching anything, never modifies system or base Conda installations, and honours
`.uv-migrator-ignore` patterns. A 3 MB CLI and a 6.6 MB native GUI — no Electron.

### [cargo-trim](https://github.com/carenaudo/cargo-trim) · Rust

Finds every nested Cargo `target/` directory on a drive with a parallel filesystem walk —
including the ones nested under non-Rust projects that other tools stop recursing into — and
shows sizes and last-active dates in a sorted table before deleting anything.

### [egui-shadcn](https://github.com/carenaudo/egui-shadcn) · Rust

shadcn-styled components for `egui`. A fork of
[pjankiewicz/egui-shadcn](https://github.com/pjankiewicz/egui-shadcn) that I contribute back to.

## Research code

Most of the research software is not public yet — some of it belongs to work still under
review. What it covers is described on the [about page](@/about.md): droplet evaporation
modelling, spray drift, population balance methods, particle size distribution
instrumentation, and grain morphometry.
