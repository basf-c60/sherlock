[README-github.md](https://github.com/user-attachments/files/34690104/README-github.md)
# Sherlock (ZX Spectrum, 1984) - annotated disassembly

A complete, cross-referenced, plain-English disassembly of *Sherlock*, the text adventure
published by Melbourne House for the ZX Spectrum in 1984 (developed by Beam Software), in
which you play Sherlock Holmes with Dr Watson and Inspector Lestrade over three days of
Victorian London.

It is written for people who **do not read Z80 assembly**. Every routine and every data
table has a title and a description, and the lines of every routine carry comments that
say *why* the line is there, in the game's own terms ("is the china man's disguise being
worn?", "the actor's own record") rather than restating the instruction or quoting a bare
address. Addresses in the text are links, so you can follow the code the way you would
follow a story.

**Browse it: open [`index.html`](index.html)** (or the published site, if you are reading
this on GitHub Pages).

## What you will find

| Page | What it is |
|---|---|
| [How the engine works](how-it-works.html) | The overview: actors and their scripts, the parser, the message language, the clock, trains and cabs. Start here. |
| [The case](the-case.html) | The story as the program holds it: the evidence flags, who must be cleared, and what Lestrade needs to hear. |
| [Walkthrough: Monday to the win](the-walkthrough.html) | One winning route, all 372 typed lines in 32 stretches, each with the clock, the room, the game's reply and whether the route still wins without that line. |
| [Every ending, played](the-endings-played.html) | The seven endings (one win, six ways to lose) and what you type to reach each. |
| [Map and rooms](map.html) | The room table drawn as a grid: exits, one-way exits, blocked exits and the garden maze. |
| [Pictures](pictures.html) | The 14 room pictures, drawn by running the game's own drawing routine. |
| [The cast and their scripts](cast.html) | Every character's plan script, decoded instruction by instruction, with where each one starts. |
| [Characters and things](things.html) | The object and character records and what the game does with each. |
| [Vocabulary](vocabulary.html) | The dictionary: every word the parser knows and what it means to the program. |
| [Trains and cabs](trains-cabs.html) | The timetables, fares and the cab ride. |
| [State bits](state-bits.html) | What "asleep", "dead" and the other bits in an actor's state mean. |
| [Bugs](reference/bugs.html) | 14 bugs in the original program, each explained. |
| [Trivia by theme](trivia-by-theme.html) | 59 findings, grouped by theme. |
| [Routines and data](asm/) | The disassembly itself: 815 titled blocks, all named and explained, with about 9,200 line comments. |

## Things worth knowing about the game

A few of the things this work turned up, each explained in detail on the pages above:

- **Characters run their own programs.** Every character executes a small plan script each
  turn, in a little language of its own (verbs, "is it this hour?", "is this person in this
  room?", moves), using the same action code the player uses.
- **Messages are programs.** Text is stored as dictionary references and control codes: jump
  offsets, sub-messages, conditions such as "only if it is night", and a choice of
  sentence-ending punctuation. About 210 messages are rendered in full by running the game's
  own message printer.
- **It is a deterministic game with one random seed.** The random numbers step through the
  program's own bytes from a pointer seeded once at the first keypress, so an exact sequence
  of typed lines gives exactly the same game. A failed command costs part of a minute, and
  three failures in a row cost a whole one, which is why the timing of a route matters.
- **It can be won in two ways**, both by typing commands only: alone, and by shadowing
  Lestrade from Scotland Yard. The walkthrough page says which lines are essential and which
  can be dropped.
- **Bugs.** Fourteen are documented, including ones that were found by playing them.

## Repository layout

```
index.html, *.html        the browsable site (generated)
asm/                      one page per routine or data block
reference/                the Bugs and Trivia pages
images/, pictures/, maps/ location pictures, the map and the routine/message/data indexes
source/                   the sources the site is built from (see below)
tools/                    the build, check and analysis scripts
README.md                 this file
```

If you publish with GitHub Pages, note that Pages can serve only the repository root or a
`/docs` folder, so put the contents of the generated site in one of those.

### `source/`

| File | What it is |
|---|---|
| `game.skool` | The complete annotated disassembly in [SkoolKit](https://skoolkit.ca) "skool" format. |
| `game.ctl` | The SkoolKit control file it was generated from. |
| `game.ref` | The extra pages: overview, bugs, trivia, the case, the cast, the walkthrough and the rest. |
| `overlay_*.py`, `build.py` | The annotation scripts. Every description and line comment lives in these; `build.py` combines them into `game.ctl` and `game.ref`. |
| `sitegen.py`, `sherlock.css`, `linkify.py` | The page templates, the stylesheet (light and dark, phone-friendly) and the tool that turns addresses into links. |
| `rooms.py`, `gridmap.py`, `objects.py`, `dictionary.py`, `render_messages.py`, `walkthrough_steps.py` | Helpers that decode the room table, draw the map, list the objects, decode the dictionary, render every message with the game's own text printer, and build the walkthrough page. |
| `messages.json` | Every message in the game, as the game itself prints it. |
| `walkthrough_*.json`, `walkthrough_route_shortened.cmds` | The data behind the walkthrough page. |

## The version disassembled

The tape is the Melbourne House release `Sherlock v2.0`: a short BASIC loader
(`LOAD "" CODE: PRINT USR 32768`), a 256-byte loader stub, a 7,188-byte block at `$840B`,
the loading screen (6,912 bytes) and the main program block `p`, which is **41,600 bytes
loaded at `$5D80`** and runs to the top of memory. The disassembly covers the code and data
in the program block. The tape itself is not included in this repository.

## Checking the work yourself

You need [SkoolKit](https://skoolkit.ca) 10.1 or later (`pip install skoolkit`).

**Reassemble the disassembly and compare it with your own copy of the tape.** The result
should be byte-for-byte identical to the game's program block:

```
skool2bin.py -i source/game.skool rebuilt.bin
cmp rebuilt.bin p.bin && echo IDENTICAL
```

(`p.bin` is the main block taken from your own tape image; it is not distributed here.)

**Regenerate the website from the skool file:**

```
cd source
skool2html.py -d ../html game.skool game.ref
```

**Regenerate `game.skool` from the annotation scripts:** from the top level run
`python3 tools/check.py` (two or three times, until it stops changing things). It rebuilds
`game.ctl`, `game.ref` and `game.skool`, round-trips them through `skool2bin`, and checks
every address quoted in a comment against the real instruction boundaries.

## How it was made, and how far to trust it

Code and data were separated by running the game in a Z80 emulator and recording which
bytes were executed, then working out each table and subsystem by hand. Descriptions were
written from the code first, then checked:

- the whole disassembly reassembles to the original bytes;
- every address quoted in a comment is checked automatically against the real instruction
  boundaries;
- claims about behaviour were tested by running the game with typed commands, not only by
  reading code. The game has been **won from a fresh start with typed commands only (no
  pokes)** by two different routes, and every other ending that can be reached has been
  reached.

Things that were run are marked as such on the Bugs and Trivia pages, along with the ones
that are a careful reading of the code that was not reproduced. Testing also *overturned*
several earlier descriptions, and those were corrected throughout. For example, an early
note claimed the game could not be won; that was wrong and was withdrawn.

Some things are still open, and the pages say so where they matter:

- a handful of message stubs (the two-byte `WHAT` records) and one routine whose purpose is
  not known;
- why most lines in the winning route are needed. Any one of 39 can be left out and the game
  is still won, and the other 333 cannot, but whether each is needed for the story or only
  for the timing of the random numbers cannot be told apart with these checks;
- a few evidence flags and one state bit, listed on the pages that use them.

If you find something that is wrong, please open an issue. A corrected claim is worth more
than a tidy one.

## Credits and notices

- *Sherlock* is © Melbourne House. This project is not affiliated with or endorsed by the
  authors, the publisher or their successors.
- This is a study of how the program works. A disassembly necessarily reproduces the
  program's code and data, so the same rights apply to it as to the original: it is
  published here for research and education, does not include the game tape, and should not
  be treated as a substitute for owning the game.
- The site is generated with [SkoolKit](https://skoolkit.ca) by Richard Dymond.
