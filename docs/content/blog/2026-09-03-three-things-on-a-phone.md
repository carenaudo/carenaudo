+++
title = "Three things on a phone"
description = "Three Android apps in a month: where data lives, and whether a phone can carry the maths."
date = 2026-09-03
slug = "three-things-on-a-phone"

[taxonomies]
tags = ["engineering", "science", "mobile"]
+++

Three Android apps this month, all Kotlin and Compose, none of them public. They have less in
common than the count suggests.

**A personal finance tracker.** I tried a number of the existing ones first, and none of them
worked the way I wanted — not for lack of features, but over where the data lives. I wanted
it entirely on the device, with nothing sent anywhere, and a plain export to CSV or XLSX any
time I want it back out. A private ledger I look at, not an account that syncs. That is a
preference, not a gap in the market, and it was easier to build than to argue with.

**A droplet evaporation simulator.** This one began as a question about the phone rather than
about the physics: could I get an Abramzon–Sirignano integration running properly on Android
— an adaptive Dormand–Prince step with a root-find nested inside each one? By desktop
standards that is not heavy computation, but it is well past what a spreadsheet does, and I
wanted to know how that class of problem behaves on a handset.

It runs, and it runs fast — on the one phone I have actually tried it on, a Moto Edge 40 Pro.
Whether the numbers are *right* is a separate question, and validating them on the device is
the part I have not solved. Speed was never going to be the hard half.

The other half of it is reach. Type in a diameter, an air temperature and a humidity, get a
curve, without installing a Python environment first. Plenty of tools can integrate this
model; what I did not have was one in my pocket, and neither does a student with a question
and a phone.

The physics lives in its own package with no Android dependencies at all, so the model can be
exercised without a phone anywhere near it. That separation was the first thing I did, the
thing I would defend hardest, and the route by which the numbers eventually get checked.
There are no tests yet; that is the next job, and until there are, treat what it prints as a
demonstration rather than a measurement.

**The third one I am not going to describe.** It is an idea I am prototyping toward something
that might become a small venture, and writing about it now would be writing about an
intention rather than a result. When there is something to show, it will be here.

---

Two of these turned out to be asking different questions. One was about where data sits and
who else gets to see it. The other was about whether the device in your hand can carry the
computation at all — which, this time, it could.
