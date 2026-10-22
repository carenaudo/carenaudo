+++
title = "Bitwise, then 1e-13"
description = "A regression gate that demanded bit-for-bit agreement, three ways it failed on another machine, and why the last one, a difference of 3.6e-14, was worth fixing rather than tolerating."
date = 2026-10-22
slug = "bitwise-then-1e-13"

[taxonomies]
tags = ["science", "engineering", "ai-assisted"]
+++

The drop-shape analysis pipeline I have been building in Julia takes a photograph of a pendant
or sessile drop, finds its contour, and fits the Young–Laplace equation to it. Before
restructuring the code into packages, I froze its outputs: every number, string and flag the
pipeline writes for 26 real images and 14 older contours, 54,254 values in all. Any change that
is not supposed to move a result is checked against those files.

The rule was strict. Numbers must agree to a relative 1e-10, which on the machine that froze
them means bit for bit. Strings, flags and counts must match exactly. The refactor and a pass
of the code formatter both came back with zero differences, which is exactly what a gate like
that is for.

Then it ran somewhere else.

## Another CPU

On a GitHub runner, the same code on the same images moved 586 of the 54,254 values by more
than 1e-10. The largest moved by about 6e-5 relative. Nothing was wrong. The repository's
notes put it down to SIMD width and the maths library, and an iterative fit carries any
difference in the last bits into the fitted parameters.

So the gate has two settings. On the freezing machine the default stays at 1e-10. Across
machines CI uses a relative 1e-4, while strings, flags and counts still have to match exactly.
The second half of that rule turned out to be the important one.

Even at 1e-4, nine values still failed. All of them were differences of nearly equal numbers:
the spread of the fitted radius across a set of candidate profiles, the same spread for the
Bond number, and a signed sum of residuals. For a quantity like that, a relative tolerance has
no meaning. The spread is close to zero, so a tiny absolute change, the largest was 9.6e-6
pixels, becomes a large relative one. The comparison script's summary made the same mistake
in its own report, quoting a relative change of about 1e290 for a value that had moved from
zero to almost zero.

Those three keys now get absolute tolerances (in pixels for the radius spread and the
residuals), and the summary skips changes below the absolute floor. A tolerance has units, and for a difference of two nearly equal numbers
the relative one is the wrong unit.

## A test at rounding level that makes a decision

The second failure was more interesting, because it was not a number drifting but a decision
flipping.

For sessile drops the pipeline also fits a plain spherical cap, and a stability test decides
between the cap and the full Young–Laplace profile. That test refits the cap with part of the
arc left out and checks whether the fit converges. The fit reported convergence when a step
fell below 1e-10 of the parameters, which is floating-point noise. Near the optimum, whether a
step got that small depended on the CPU. On one image, one trial converged on one machine and
not on the other, and the model choice changed with it.

This is exactly what "strings and flags must match exactly" is there to catch. A difference
in the last bits is harmless while it stays a number. Once it decides a branch, it is a
different result.

The fix judges convergence in the units of the problem: a step that moves the circle by less
than a thousandth of the edge uncertainty, 1.5e-4 pixels by default, counts as converged. A
new test perturbs the input at the 1e-12 level and checks that the outcome does not change.
In the two reference pipelines, two images now take the spherical cap; neither reported a
surface tension before or after. The published configuration did not change at all at 1e-10.

## 3.6e-14

The third failure was the smallest and the one I learned most from.

The pipeline can evaluate the Young–Laplace profile in two ways, and which one it uses is set
per analysis, so analyses using different ones can run side by side on different threads. A
test checks exactly that: run four analyses at once, alternating the two profile models, and
require each result to equal the sequential result for its model, bit for bit. On the GitHub
runner it failed by 3.6e-14.

The cause was a cache. Solving the profile ODE is the expensive step, so solutions were cached
by Bond number and mode. But a solution integrated over a longer arc was allowed to serve a
request for a shorter one. An adaptive solver's steps depend on how far it is asked to go,
and so does the grid built on them. So the profile for a given Bond number depended on which
earlier analysis had first asked for it. The result depended on what happened to be in the
cache, at the 1e-13 level.

The first fix kept the cache as it was and loosened the test. Each concurrent result had to
agree with its own model's sequential value to 1e-12, and be closer to it than to the other
model's. The two models differ by about 6e-10 on that image, so the test would still catch
the bug it was written for, one model leaking into another analysis. It was a reasonable,
defensible change, and it was committed.

Twenty minutes later it was replaced. A tolerance described the symptom; it did not remove
the cause. And the cause was not specific to threads. A single-threaded batch could produce
slightly different numbers for the same image depending on which images came before it.
"This result is a function of its inputs" is a yes-or-no property, and 1e-12 meant no.

So every cached profile is now integrated to the same fixed length, the longest any caller
ever requests, and shorter requests evaluate that same solution. A profile is then a function
of its Bond number and mode alone. The test went back to bit-for-bit equality, and passes.
The frozen outputs had to be refrozen once, because the fixed length differs from whatever
length each image used to get. The largest change was 4e-7 relative in one Bond number, with
no string, flag or count affected.

## What I take from it

- **Put tolerances in the problem's units.** Pixels, or a fraction of the edge uncertainty,
  mean something. 1e-10 of the parameters, at rounding level, measures the floating-point
  format rather than the drop.
- **Relative tolerances fail on differences.** Anything computed as a spread, a residual sum
  or a difference of nearly equal numbers needs an absolute one.
- **Keep the discrete outputs exact.** Most cross-machine drift is harmless. The dangerous
  kind is the drift that changes a branch, and you only see it if model choices and flags
  have to match exactly.
- **When a test fails by 1e-14, ask why the answer is not zero before asking how much to
  allow.** Sometimes the honest answer is floating-point noise across CPUs, and a tolerance
  is right. Sometimes it is hidden state, and a tolerance would have hidden it for good.

I teach with reproducibility as a grading criterion. This was the same lesson at a finer
scale, applied to my own code.

The work was done pair-programming with an AI assistant, and the commit history keeps both
fixes for the last one: the tolerance first, then the root cause. The first commit was not
wrong. It just stopped short, and what made it obvious was asking why the difference was not
zero. That question is the same with an assistant or without one, and having it written into
the commit history is what keeps it honest.
