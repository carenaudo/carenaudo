+++
title = "A log for the tooling"
description = "Why a chemical engineer ends up writing a Rust CLI, and what this log is for."
date = 2026-09-02
slug = "a-log-for-the-tooling"

[taxonomies]
tags = ["engineering", "science"]
+++

Most of what I build exists because a measurement needed making and the software to make it
either did not exist, cost too much, or could not be inspected.

That is the honest through-line. A droplet hanging from a needle has a shape, and that shape
encodes a surface tension — so you need contour extraction and a geometry fit, which becomes
[Menipy](https://github.com/carenaudo/Menipy). The same droplet falling through air loses
mass and cools, and the literature offers you several formulations that disagree — so you
need an ODE integrator and a way to compare Wilson against Abramzon–Sirignano against the
classical D²-law on identical conditions. Scale that up to an agricultural sprayer and the
question becomes where the droplets land and how much never arrives at all.

None of that is a software project when it starts. It becomes one at the point you notice
you have re-derived the same property correlation in three notebooks and they no longer
agree.

## What ends up here

Four things, roughly:

- **Scientific computing.** The physics and the numerics: evaporation models, population
  balance methods, shape metrics. What the equations actually do when you integrate them.
- **Engineering.** Parsing binary instrument formats, porting Python to Rust and keeping the
  two at parity, building desktop UIs with `egui` and Qt, and the unglamorous business of
  packaging something a colleague can install.
- **AI-assisted development.** I build a good deal of this by pair-programming with an AI
  assistant, including an entire file-format-accurate desktop editor. I would rather write
  about where that works and where it quietly does not than pretend either extreme.
- **Teaching.** I teach undergraduate fluid mechanics and particulate solids processing.
  Reproducibility is a grading criterion, which turns out to be a good forcing function for
  my own code too.

## The rule

Anything I claim here about a model should be traceable to the paper it came from, and
anything I claim about code should be reproducible from a repository. Where a result is
preliminary I will say so. Where I got something wrong, the correction goes in the same
place as the mistake.

Notes as I go, then. Longer than a commit message, shorter than a paper.
