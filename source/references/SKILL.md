---
name: zx-spectrum-disassembly
description: Build a complete, human-readable, purpose-level annotated disassembly of a ZX Spectrum game from a TZX or TAP tape image, using SkoolKit and a scripted Z80 emulator. Use this whenever the user provides a .tzx, .tsp, or .tap file (or asks about one) and wants to understand, document, modify, patch, or find bugs in the game's machine code - even if they only ask a narrow question like "what does this routine do" or "can I patch X", since answering well requires the same disassembly infrastructure this skill builds. Also use it if the user asks to "reverse engineer", "decompile", or "make a skool file for" an old 8-bit game, or wants a browsable HTML disassembly, a map of the game's locations, bug list, or trivia page for a Spectrum title.
---

# ZX Spectrum game disassembly

This skill turns a ZX Spectrum tape image into a complete, cross-referenced,
purpose-level annotated disassembly: a browsable SkoolKit HTML site where
every routine and every data table is named and explained in plain English,
every line of every routine has a comment that says *why* it does what it
does (not just what the instruction is), and every non-trivial claim has
been checked by actually running the game rather than only reading the code.

This was built and refined over a long, iterative session disassembling
*The Hobbit* (1982, Melbourne House). That game is used throughout as a
worked example, but nothing here is specific to it - the same approach
applies to any Spectrum game with an interesting engine (adventures,
simulations, arcade games with data-driven levels, and so on).

**The single most important lesson from that session:** confident-sounding
descriptions written from reading code alone are wrong more often than you'd
expect, in ways that are individually small but collectively matter a lot.
Over the course of one game, mistakes were found in a load-bearing register
convention, a swap-direction in a helper routine, a room-number check, and
even a claim repeated confidently across several files for many sessions
before it was tested and found false. Every one of those was caught by
*running the game*, not by reading more carefully. Build the ability to run
the game early, and use it constantly. See `references/verification.md`.

## Prerequisites

Check these are available before starting; install what's missing:

```bash
pip install skoolkit --break-system-packages   # sna2skool.py, skool2html.py, skool2bin.py, skool2asm.py
pip install z80 --break-system-packages        # a Python Z80 emulator, used for the test harness
apt-get install -y z80dasm graphviz            # a throwaway disassembler for quick look-ups; graphviz for maps
```

`skoolkit` is the backbone: it turns an annotated control file into a
browsable HTML site and back into a binary again (which is how you prove
you haven't changed the facts). The `z80` package is what lets you *run*
the game headlessly to check what you think you've understood. Neither
tool understands anything about the specific game - all of the actual
reverse-engineering is manual, assisted by scripts you write as you go.

## The workflow, phase by phase

Work through these roughly in order, but expect to loop back: understanding
the object format, say, will change how you read the room format, which
will send you back to re-check an early assumption about the parser.

### Phase 0 - Get the file open

Parse the tape container and pull out the loader and the main code block(s).
See `references/tape-formats.md` for TZX and TAP block layouts, how to find
the BASIC loader, and how to work out the load address and entry point
(usually a `RANDOMIZE USR n` at the end of the loader, or a checksum-verified
header block naming it).

Write out the extracted code block(s) as raw binary files you can feed to
everything else. Keep the *original* tape file untouched; all rebuilding
happens by patching a copy of the binary and re-inserting it with a
recalculated checksum (see `scripts/tzx_tools.py`).

### Phase 1 - Separate code from data

A raw binary mixes code, tables, and text with no markers. Disassembling
data as code (or vice versa) as a starting point wastes time and misleads.

The fastest reliable way to bootstrap the split: **run the game** while
recording every address the processor actually executes, then feed that
execution map to `sna2ctl.py` to generate a first-pass control file.

1. Build a minimal Z80-emulator harness (`references/emulator-harness.md`)
   that can load the binary at its real address, feed it synthetic
   keypresses, and capture printed output.
2. Play it for a while with *random* input: movement in all directions,
   every verb in an approximate vocabulary crossed with every noun you can
   guess, teleporting the player around every location number, and so on.
   Record every program-counter value visited into a bitmap the length of
   memory.
3. `sna2ctl.py -h -o <load address> -m <map file> <binary>` turns that into
   a `.ctl` file marking `c` (code) and `b` (data) regions.
4. From here on, you *overlay* corrections onto this control file by hand as
   you learn more - see Phase 3. Never trust the automatic split as final;
   it only knows what got exercised during your random play, and anything
   untouched defaults to "data" even if it's really an unreached routine.

### Phase 2 - First disassembly and site

```bash
sna2skool.py -H -o <load address> -c game.ctl game.bin > game.skool
skool2html.py -H -d html game.skool
```

This alone gives you a clickable disassembly with addresses as labels and
no explanations - not yet useful to a reader, but the scaffolding everything
else hangs off. Confirm early that this round-trips:

```bash
skool2bin.py -i game.skool /tmp/check.bin
cmp /tmp/check.bin game.bin && echo IDENTICAL
```

Run this check after *every* significant change from now on. It costs
seconds and catches control-file mistakes (a block boundary in the wrong
place, an address typo) immediately, before they compound.

### Phase 3 - Annotate iteratively, in Python, not by hand-editing the .ctl

Do not edit the `.ctl` or `.skool` files directly. Instead, write small
Python modules ("overlay" scripts) that build up a dictionary of
descriptions, keyed by address, and a `build.py` that combines them into
the control file before each `sna2skool.py` run. This is what makes the
whole thing maintainable over hundreds of routines and lets you correct an
earlier mistake in one place rather than by hand-editing generated output.

See `scripts/build_skeleton.py` for the pattern: a shared `A` dict of
per-address records (title, prose description, register doc, line-by-line
comments, sub-block breakdown for data), a `blk()` helper to populate it,
a `C()` helper to add line comments to an existing block, and a `build.py`
that walks the dict and emits `.ctl` directives.

Work in this order, because each layer makes the next one legible:

1. **Read the very first few hundred bytes of execution** (the entry point
   found in Phase 0) by hand. This is usually setup: clear the screen,
   seed a random number generator, set up variables, jump into a main loop.
   Identify the main loop early; almost everything else is reached from it.
2. **Find the vocabulary/dictionary**, if it's a text game. Look near the
   very start of the code block; text adventures usually store their word
   list before the routines. Work out the letter-packing scheme (5-bit
   letters, ASCII, tokenised) and the end-of-word marker by finding a
   handful of recognisable words (verbs like TAKE, GO, LOOK) and diffing
   the bytes. See `references/discovery.md` for the general technique:
   cross-reference a table's *entries* against where they're pointed to
   from code, and let a small handful of anchor facts (a known word, a
   known starting room) triangulate the rest of the format.
3. **Find the "world model" data**: whatever structure represents objects,
   rooms, or game entities. Look for a table of pointers (an index) feeding
   into fixed-size or tagged-variable-size records. Confirm the record
   layout by finding one field you're confident about (e.g. this song's
   room number matches where the game visibly starts) and using it as an
   anchor to work out the others by comparing several records side by side.
4. **Find the command parser and the action dispatch table.** Nearly every
   text/adventure engine has a table of "verb (+ preposition) -> handler"
   entries. Find it by locating the routine that reads player input and
   tracing where it goes after tokenising a line.
5. **Find the message/text printer.** Almost never plain ASCII - look for
   a small interpreter with control codes, word-abbreviation tables, and
   articles/suffixes handled separately from the word list (this saves
   space on 48K machines). Once you find it, **use it to render every
   message yourself** rather than hand-decoding bytes - see
   `references/message-rendering.md`. This was the single biggest quality
   jump in the Hobbit disassembly: every message comment went from an
   approximate hand-transcription to the exact text the game itself would
   print, args and all, by calling the interpreter in the emulator with
   placeholder objects.
6. **Work outward from there**: turn processing, timers/scheduled events,
   independent-actor/NPC behaviour, save/load, and so on. Each of these is
   usually a fairly self-contained subsystem once the core data model is
   understood.

At every step, write the description as prose *first* ("what is this for
and how does it work"), then go back and add line-by-line comments once
you're confident. See `references/commenting-style.md` for the standard
this should meet and worked before/after examples.

### Phase 4 - Verify relentlessly

This is not a final phase - do it continuously, but it's worth stating as
its own discipline because it's the thing most tempting to skip.

Read `references/verification.md` in full before writing anything you'd
call a "bug" or an authoritative claim about behaviour. In short:

- **Run it, don't just read it**, for anything conditional, anything
  involving a flag's polarity, and anything you'd call surprising.
- **Trace data cross-references explicitly** (grep the binary for a
  routine's address as raw bytes) rather than assuming a nearby table entry
  is the trigger for it. Two real errors in the worked example came from
  assuming proximity implied causation.
- **Script an automated address-cross-check**: every address named in a
  line comment should be a genuine instruction boundary inside that routine
  (see `scripts/verify_addresses.py`). This catches transcription slips at
  zero cost, every single build.
- **Re-run the round-trip check** after every batch of changes.
- **When you find one wrong claim, grep for it everywhere else** - a wrong
  assumption made once is often repeated in a summary page, a table, and a
  trivia note, and all of them need fixing together.
- Keep a **Bugs** page and a **Trivia** page (see Phase 5) and be honest
  about which claims were emulator-verified and which are "a careful
  reading of the code" - say so in each entry.

### Phase 5 - Supplementary pages

Once the core is solid, these make the site far more useful and often
surface further bugs while you build them:

- **A map.** If the game has locations with exits, extract them
  programmatically and render with Graphviz (`scripts/build_map.py`):
  nodes for each location, edges for exits, distinguishing lit/dark,
  one-way links, and links that pass through a lockable object.
- **A characters/objects/pictures reference table**, generated from the
  data itself (not retyped by hand) so it can never drift out of sync.
- **A "how it works" overview page**, written or rewritten *last*, once
  you actually understand the whole engine - an early draft written before
  you understood the system will read as vague or subtly wrong.
- **Bugs and Trivia pages**, filled in as you go (Phase 4).

### Phase 6 - Package it up

Ship a zip containing the generated HTML site *and* every script and
overlay module used to build it (`source/` folder inside the zip). This
makes the result reproducible and correctable - if you or the user finds
one more mistake next week, rebuilding is one command, not starting over.

## When the user asks a narrow question instead of "disassemble this"

If they ask something like "what does routine X do" or "can you patch Y",
and no disassembly infrastructure exists yet for this game, still build the
scaffolding (Phases 0-2 at minimum, plus enough of Phase 3 to answer the
specific question) rather than reading the raw bytes ad hoc - it's barely
more work up front and means the answer is checked, not guessed, and the
next question is fast to answer too.

If the user asks for a patch or a bugfix, prefer the "no patches" default
of the earlier long session **unless they explicitly ask for a changed
tape** - many people disassembling a game want to understand and document
it, not distribute a modified copy. If they do want a patch, verify it in
the emulator (does the picture/behaviour match before and after, byte for
byte where it should) before handing over a rebuilt tape, and recompute the
tape's checksums.

## Reference files

- `references/tape-formats.md` - TZX/TAP block layouts, loader identification
- `references/emulator-harness.md` - building a scriptable Z80 test rig
- `references/discovery.md` - general technique for reverse-engineering an
  unknown table/record format from cross-references and anchor facts
- `references/message-rendering.md` - rendering text via the game's own
  printer instead of hand-decoding
- `references/commenting-style.md` - the comment-quality bar, with examples
- `references/verification.md` - the verification checklist and case
  studies of real mistakes this caught
- `scripts/build_skeleton.py` - the overlay/build.py pattern
- `scripts/verify_addresses.py` - automated address cross-checker
- `scripts/build_map.py` - Graphviz map generator template
- `scripts/tzx_tools.py` - TZX/TAP block extraction and checksum recompute
