+++
title = "A log for the tooling"
description = "Why I write the code when a tool already exists, and what this log is for."
date = 2026-09-02
slug = "a-log-for-the-tooling"

[taxonomies]
tags = ["engineering", "science"]
+++

For most of what I build, something else already exists that would do the job. That is worth
saying up front, because "I wrote my own" tends to imply "nothing else would do," and that is
rarely the honest reason.

There are three reasons I actually end up writing the code.

## To find out where a tool fails

You can use a model quite happily until it hands you an answer you have no way to check.
Implementing it yourself — the property correlations, the solver, the assumptions the paper
does not restate because everyone in that subfield already knows them — is the fastest way I
know to learn what it does near the edge of its validity.

Running Wilson against Abramzon–Sirignano against the classical D²-law on identical
conditions tells you something that reading all three papers does not. Not because the
papers are wrong, but because the disagreement between them only becomes concrete when the
same integrator, the same properties and the same initial conditions are feeding all three.

## Because the thing I need is too specific

General tools are general, and that is their virtue. But when the measurement is a
particular droplet geometry on a particular image series, or one instrument's undocumented
binary format, the distance between what a tool gives you and what you need can be larger
than the distance between nothing and what you need.

That is roughly where [Menipy](https://github.com/carenaudo/Menipy) came from. A droplet
hanging from a needle has a shape, and that shape encodes a surface tension — but getting
from an image to a number means a contour you trust and a fit whose assumptions you can
state.

## To learn

Sometimes there is no better reason than wanting to know how the thing works, and I would
rather say that than dress it up as necessity. A fair amount of what is on my GitHub is
there because I wanted to find out whether I could.

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
