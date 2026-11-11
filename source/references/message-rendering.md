# Rendering messages via the game's own interpreter

Most Spectrum text adventures don't store messages as plain ASCII - space
is far too tight on 48K. Expect a small bytecode: dictionary word
references, one-byte abbreviations for very common words, literal
characters for punctuation, and control codes for things like "print the
current actor's name", "his/her", "is/are", pluralisation, jumps, and
sub-message calls. Once you've identified this interpreter (Phase 3, step 5
in SKILL.md), the single best return on effort in the whole project is:
**don't hand-decode messages by reading the bytecode. Call the
interpreter itself, in the emulator, and capture what it actually prints.**

Hand-decoding is slow, error-prone (you will misjudge a control code's
effect at some point), and - critically - misses anything the interpreter
does dynamically (suffix endings on verbs depending on subject, articles
chosen by flag bits on the referenced word, capitalisation rules). Calling
the real interpreter gets all of that for free and exactly matches what a
player would see.

## The approach

1. Find the interpreter's entry point (call it with `HL` = message address).
2. Find where it reads its *parameters* - most messages take one or more
   "fill in the blank" values (the current actor, a target object, a word
   the player typed) via specific fixed memory locations, or via the stack
   just before the call. Set these up with clearly-fake but valid dummy
   values before calling.
3. Fabricate two or three dummy dictionary words (e.g. "THING", "WORD",
   "OTHER") in any unused byte range near the end of the dictionary, so
   parameter substitutions produce a legible - if generic - placeholder,
   rather than garbage or a crash from an unencoded value.
4. Hook the interpreter's low-level *print-a-character* routine (the same
   breakpoint from the harness) to capture output, run the interpreter over
   every message address you can find, and store the results (e.g. as a
   `{address: text}` JSON file) for every later annotation pass to draw on.

```python
def render_message(game, addr, actor=0, target=DUMMY1, instrument=DUMMY2):
    game.m.memory[ACTOR_VAR]      = actor
    game.m.memory[TARGET_VAR]     = target
    game.m.memory[INSTRUMENT_VAR] = instrument
    # ... any other parameters this engine's printer expects ...
    game.m.pc = INTERPRETER_ENTRY
    game.m.hl = addr
    game.m.sp = SCRATCH_STACK
    game.out = []
    for _ in range(20000):
        game.m.ticks_to_stop = 1
        game.m.run()
        if game.m.pc == game.print_bp:
            game.out.append(chr(game.m.a)); game.m.step_over_breakpoint()
        elif game.m.pc == RETURN_MARKER:
            break
    return ''.join(game.out)
```

5. **Find every message address**, not just the ones you happen to notice
   while reading code: scan every place a routine loads `HL` (or an
   equivalent) with a constant address inside the text-data region just
   before calling the interpreter, plus every pointer inside object/room
   "own description" fields, help-text tables, and so on. Render every one
   you find; the exercise itself often reveals messages nothing in the
   *reachable* game logic points to (see "unused content" below).

6. **Feed the rendered texts back into your annotations automatically**
   rather than pasting them in by hand: have your line-comment generator
   look up an address in the rendered-message dictionary and use the exact
   text (truncated for length) whenever a routine references it, so
   comments never drift out of sync with a later re-render.

## Bonus discoveries this tends to produce

Rendering *everything* rather than only what you already suspect is
interesting has a habit of turning up:

- **Unused/unreferenced content** - a fuller description for a location
  that the room-description code never actually points to, because the
  room uses its plain name instead. Worth a line in a Trivia page.
- **Shared substrings between two ostensibly different messages** where
  one message's tail is reused as another's, saving space - useful to note
  when explaining a data region's layout, since it means the boundary
  between "message A" and "message B" isn't where you'd naively assume.
- **The exact wording** for every failure case a parser/action-resolution
  system can produce ("I don't see that", "you can't do that", "which one
  do you mean?") - useful both for documentation and for writing test
  assertions later (matching on exact game text is far more precise than
  matching on category).

## Caution

Treat any parameter substitution you didn't explicitly account for as a
potential source of nonsense output (an unencoded dictionary reference will
often print as a stray printable character or a decoding glitch, not throw
an error) - if a rendered message looks garbled, check whether it needs a
parameter you haven't supplied yet, rather than assuming the message itself
is corrupt data.
