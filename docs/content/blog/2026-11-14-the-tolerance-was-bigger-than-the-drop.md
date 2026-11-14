+++
title = "The tolerance was bigger than the drop"
description = "An absolute tolerance of 1e-9 kg, a droplet that weighs 6.5e-11 kg, and the scaling law that caught lifetimes off by up to 30 % before any test did."
date = 2026-11-14
slug = "the-tolerance-was-bigger-than-the-drop"

[taxonomies]
tags = ["science", "engineering", "ai-assisted"]
+++

[Evaporacion.jl](https://github.com/carenaudo/evaporacion) is now public. It is a Julia
package of droplet evaporation models: the classical D² law and its variants with Stefan flow
and convection, Abramzon–Sirignano for drops in flight, and the diffusion-limited modes of a
sessile drop. The first post on this log talked about running Wilson, Abramzon–Sirignano and
the D² law under the same integrator and the same properties; this is that code.

It also came with a bug that this post is about, because the way it was found is more
useful than the fix.

## The setup

An in-flight drop is two ordinary differential equations: its mass `m` and its mean
temperature `T̄`. They are integrated with Tsitouras' adaptive Runge–Kutta method (`Tsit5`),
with a relative tolerance of 1e-6 and an absolute tolerance of 1e-9, and the run stops when
the mass falls to 1e-15 kg.

An adaptive solver accepts a step when its error estimate on each state is below
`atol + rtol·|u|`. The same `atol = 1e-9` went to both states: to the temperature in °C, and to
the mass in kilograms.

Here is what the drops weigh:

| Diameter | Mass |
|---|---|
| 50 µm | 6.5e-11 kg |
| 200 µm | 4.2e-9 kg |
| 1200 µm | 9.0e-7 kg |

For the 1200 µm drop, 1e-9 kg is a thousandth of its mass, which is fine. For the 200 µm drop
it is a quarter of its mass. For the 50 µm drop it is fifteen times the whole drop. On the
mass, the error control was not loose. It was absent.

## How it showed up

Nothing failed. The runs finished, the lifetimes looked plausible, and the tables were full.

What gave it away was physics. The simplest model, the classical D² law held at the wet-bulb
temperature, has a constant evaporation coefficient `K`. Its lifetime is exactly `d0²/K`, so
doubling the diameter must multiply the lifetime by exactly four, whatever the properties.

The comparison table the package's own scripts produced, at 10 °C and 20 % relative humidity:

| d0 | Lifetime in the table | Ratio to the previous size | Should be |
|---|---|---|---|
| 50 µm | 3.46 s | | |
| 200 µm | 78.66 s | 22.7 | 16 |
| 600 µm | 535.65 s | 6.8 | 9 |
| 1200 µm | 2143.87 s | 4.00 | 4 |

The largest drops obey the law and the smaller ones do not. Against the analytic `d0²/K`,
computed with the package's own property correlations, the 200 µm lifetime was 30 % too long
and the 50 µm one 8 % too short. The errors had no consistent sign, which is what an
uncontrolled error looks like: they depend on which steps the solver happened to take.

The Abramzon–Sirignano model was barely affected, by less than 0.2 %. Its temperature equation
is active, and on a temperature of order 10 °C the relative tolerance alone asks for about
1e-5 °C, which kept the steps small enough for the mass to ride along accurately. The isothermal models had nothing holding them back: their
temperature equation is identically zero, so the mass was the only state the solver could
judge error on, and it judged it against 1e-9 kg.

## The fix, and the test that needed fixing too

A scalar `atol` [now applies](https://github.com/carenaudo/evaporacion/blob/main/julia/src/droplet/solver.jl)
to the mass relative to the drop's initial mass, `atol·m0`, and to the temperature as it was.
A caller who wants something else still passes one tolerance per state.

The [regression test](https://github.com/carenaudo/evaporacion/blob/main/julia/test/test_d2_lifetime.jl)
compares the isothermal D² law with its analytic solution at 50, 200 and 1200 µm, to 1e-4.
Its first draft was wrong in a small and instructive way. The solver stops at 1e-15 kg, not
at zero, and for a 50 µm drop the last 1e-15 kg takes 0.06 % of the lifetime. That is more
than the tolerance of the test, so the reference has to be the time to reach 1e-15 kg, not
`d0²/K`. A test that checks to 1e-4 has to be exact about what it is comparing.

After the fix, the 200 µm lifetime is 60.43 s and the 600 µm one 543.87 s, both matching the
analytic values. The convective D² model, isothermal as well, moved by up to 30 %.

## What I take from it

- **An absolute tolerance has units.** 1e-9 means nothing until you say 1e-9 of what. For a
  state that spans seven orders of magnitude between cases, it should be relative to the
  case. This is the same lesson as [the last post](@/blog/2026-10-22-bitwise-then-1e-13.md),
  from the other side: there a tolerance at rounding level made results depend on the CPU;
  here a tolerance larger than the quantity removed the control altogether.
- **A scaling law is a free test.** The D² law says how the answer must scale before you
  compute any answer. Checking that one ratio found what no unit test had, and it cost a
  division.
- **"It runs and the numbers look reasonable" is not a check.** Every number in that table
  looked reasonable. Only one property of them was checkable without running anything, and
  that property was false.

This turned up while reviewing the package's scripts with an AI assistant, against a written
description of the methods they were supposed to implement. Nothing clever was involved: it
was reading every solver call, noticing that one number was doing two jobs in two different
units, and then testing a single consequence of the physics. That is exactly the kind of
tedious, exhaustive reading an assistant is good for, as long as the last step is a check
against something it cannot talk its way around.
