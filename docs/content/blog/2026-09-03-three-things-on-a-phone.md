+++
title = "Three things on a phone"
description = "Three Android apps in a month, and what a phone is actually good for."
date = 2026-09-03
slug = "three-things-on-a-phone"

[taxonomies]
tags = ["engineering", "science"]
+++

Three Android apps this month, all Kotlin and Compose, none of them public yet. They have
less in common than the count suggests.

**A personal finance tracker.** This one is unapologetically for me. Argentine personal
finance has a shape that general-purpose apps do not model: two currencies in daily use, four
simultaneous exchange rates that all mean different things, credit card purchases split into
installments that stretch months ahead, and CEDEARs sitting alongside ordinary holdings. Every
app I tried assumed one currency and one rate. That is the second reason from
[the earlier post](@/blog/2026-09-02-a-log-for-the-tooling.md) — not that nothing exists, but
that the gap between what exists and what I need is wider than the gap between nothing and
what I need.

**A droplet evaporation simulator.** This is the one I actually care about. It integrates the
Abramzon–Sirignano model with an adaptive Dormand–Prince step and a root-find nested inside
each step — the same physics I run on a desktop, in a package that fits in a pocket.

Nothing about the model is new. What is new is where it runs. If you want to see how a droplet
of a given diameter behaves at 30 °C and 40% humidity, the honest answer today is "install
Python, get the dependencies, run the script" — which is a wall for a student, and an
impossible ask for someone merely curious. Putting it on a phone removes the wall entirely.
Type in conditions, get a curve.

The physics lives in its own package with no Android dependencies at all, which keeps it
portable and means the model can be checked without a phone anywhere near it. That separation
was the first thing I did and the thing I would defend hardest.

It is early. There are no tests yet, which for a thing whose entire purpose is producing
correct numbers is the obvious next job — and until that exists, treat anything it prints as
a demonstration rather than a measurement.

**The third one I am not going to describe.** It is an idea I am prototyping toward something
that might become a small venture, and writing about it now would be writing about an
intention rather than a result. When there is something to show, it will be here.

---

The pattern I did not expect: two of these exist because a phone is a *delivery mechanism*,
not because it is a good place to compute. The maths could run anywhere. What the phone
supplies is that it is already in the hand of the person who wants the answer.
