# Verification discipline

Confident, careful-sounding prose written from reading disassembled code
alone is wrong more often than intuition suggests, in ways spell-checking
or re-reading will not catch. This file is a checklist, and a set of real
case studies (generalised from a full disassembly project) of the specific
*kinds* of mistakes that got caught only by testing. Read it before you
write anything you'd call authoritative, and re-read it if a reviewer asks
you to "check and revise" - that request should trigger everything below,
not just a re-read of your own prose.

## The checklist

**1. Cross-check every address cited in a comment against real code.**
Write this once and run it after every batch of edits - it's cheap and it
catches transcription slips (wrong hex digit, copy-paste from the wrong
routine) at zero ongoing cost:

```python
# For every (routine_address -> {line_address: comment}) mapping you keep,
# confirm every line_address is a genuine instruction boundary inside
# that routine's real disassembly, not a typo or an address from a
# different routine.
def check_addresses(comments_by_routine, real_instruction_addrs):
    bad = []
    for routine, lines in comments_by_routine.items():
        valid = real_instruction_addrs.get(routine)
        if valid is None:
            bad.append((routine, 'NO SUCH ROUTINE')); continue
        for addr in lines:
            if addr not in valid:
                bad.append((routine, addr))
    return bad
```

**2. Reassemble and diff against the original binary after every change.**
SkoolKit's `skool2bin.py` (or an equivalent for your toolchain) turns the
annotated disassembly back into a raw binary. If it doesn't match the
original byte-for-byte, something about a block boundary or a data
directive is wrong - find it before doing anything else.

**3. For anything conditional, don't infer the polarity - test it.**
Z80's flag conventions are a classic trap: a routine's own author might
document "returns Z if found", but the *actual* code might set Z when the
search reaches a sentinel value (i.e. Z means *not* found). Reading the
code carefully can still get this backwards, because it's easy to trace
the "found" branch and stop, without separately confirming what happens on
the "not found" branch. **Call the routine twice, once with an input you
know exists and once with one you know doesn't, and read the flags back.**
This single technique caught a genuinely load-bearing, previously-wrong
convention that had been stated (incorrectly) in several places for many
sessions before it was tested.

**4. Trace data cross-references explicitly; don't assume from proximity.**
When you conclude "table entry X is what triggers routine Y", *prove it*
by searching the binary for routine Y's address as raw bytes and looking at
exactly what precedes each hit (see `discovery.md`). Two separate,
previously-uncaught errors in one project came from assuming a routine was
triggered by "opening" something, because a room-entry-style hook seemed
like the obvious mechanism - when the actual reference, found only by
grepping for the address, showed it was chained to a completely different
action (throwing something through an opening, not opening it). The
narrative built on the wrong assumption was coherent, plausible, and wrong.

**5. Re-derive register/variable roles from a fresh trace; don't trust
your own memory of "which way round" from a previous read.** A routine
that temporarily swaps two roles (e.g. "target" and "instrument") to reuse
one code path for two command phrasings is an easy place to get a
direction backwards - `B` holds the *old* instrument becoming the *new*
target, not the other way round, say. Redo the register trace by hand
line-by-line rather than pattern-matching on "this looks like the routine
I remember", and check the result against the emulator if there's any
doubt.

**6. Test the actual reachability of anything you're about to call a bug.**
Finding a suspicious instruction (a jump into what turns out to be data, a
comparison that can never succeed) is only half the job. Check the game's
own data (a map of locations and exits, a table of which actions are
possible) to see whether a player could actually trigger the path in normal
play, and say so explicitly either way ("reachable: standing in room X or Y
and typing Z" vs "this follows from the code; I have not found a way to
reach it in normal play").

**7. When you find one wrong claim, search for it everywhere else.**
A wrong assumption is rarely written down exactly once - it tends to get
copied into a routine's own description, a summary table, and a "trivia"
page, phrased slightly differently each time. Grep broadly for the wrong
noun/room/mechanism name across every file before considering the
correction complete.

**8. Distrust "both X and Y work" claims about flexible input parsing
until you've actually typed both.** Natural-language parsers in these
games are usually far less flexible than a quick read of the matching code
suggests - a "the words can be crossed over" code path found while reading
an action-resolution routine does not necessarily mean *arbitrary* word
reordering works; it may only cover one narrow, specific case that ordinary
play never exercises the other way. Test several phrasings, including
ones that keep the verb in its expected position and ones that don't,
before asserting general flexibility.

**9. Distinguish test-harness artefacts from real bugs.** If output looks
truncated, wrong, or a call never returns, check first whether your
emulator harness ran out of patience (step budget too low, especially for
anything that prints a lot of text or contains a real pause-for-a-keypress
loop) before concluding the game itself is broken. Increase the budget by
an order of magnitude and retry before writing up a "bug" based on a
harness timeout.

**10. Say which things are verified and which are not.** Not everything
can be tested (game logic ten moves deep into a specific, hard-to-reach
state; timing-sensitive races). That's fine - just say so plainly in the
write-up rather than letting careful prose imply a confidence level you
don't actually have. A short, explicit "checked in the emulator" list
alongside a longer "read from the code" body of documentation is more
useful to a reader than uniform confident phrasing throughout.

## When asked to "check and revise" previous work

Treat this as a full pass, not a skim:

1. Run the automated address cross-checker (item 1) across *everything*,
   not just what's new.
2. Reassemble and diff (item 2).
3. Grep your own prose for hedge words and generalising claims ("both...
   work", "either order", "always", "never") and empirically retest a
   sample of them, prioritising anything that would be embarrassing if
   wrong (a headline "this is how you win" or "this is the bug" claim).
4. For every "trigger" or "handler" claim you can, re-derive it from a data
   cross-reference (item 4) rather than trusting the earlier prose.
5. Fix root causes in *every* file that repeats a wrong claim (item 7), not
   just the most recent one.
6. Report back honestly: what you re-checked, what you found wrong, what
   you fixed, and what you tested but is now more confidently correct.
   A revision pass that finds nothing wrong at all, on a large enough body
   of claims, should itself be treated with some suspicion - go back and
   test harder, especially anything phrased with unusual confidence.
