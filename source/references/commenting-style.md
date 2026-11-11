# Comment quality bar

The goal is a disassembly a reader who does not know Z80 assembly can
follow line by line. That means every comment should explain **why**, in
terms of the game's own concepts, not just restate the instruction in
English.

## What "good" looks like

**Bad** (restates the instruction, uses raw addresses, no game concept):

```
9078 CALL $A129    ; call routine
907B JP NZ,$A09C   ; jump if not zero
907E CALL $9C99    ; call routine
9081 SET 5,(IX+$07) ; set bit
```

**Good** (names the game concept the address/register represents, explains
the purpose of the test, and connects consecutive lines into a narrative):

```
9078 CALL $A129    ; Is the target locked, or already open?
907B JP NZ,$A09C      ; If so, say which ("the door is locked."/"already open.")
907E CALL $9C99          ; Dry run? Then stop here: it would work
9081 SET 5,(IX+$07)         ; Open it
```

## Rules that produce this

- **Name variables by what they hold**, not their address: "the target's
  own record", "the current actor", "the room the player is in" - reserve
  the raw `$XXXX` for the first time a variable is introduced (in a data
  table's own description), and use the name everywhere after.
- **Name routines by what they do when a comment calls into one**: "Is the
  target locked, or already open?" rather than "call $A129" or even "call
  the lock-check routine" - say what the *caller* learns from the call, in
  the vocabulary of the game, phrased so the flag test on the next line
  reads naturally as its answer.
- **Group a short run of instructions that do one conceptual step** under a
  single comment on the first line, and leave the rest of that group's
  comments blank, rather than repeating "(continued)" or restating the
  same idea on every line. A reader scanning down the comment column
  should get a coherent narrative, not a wall of near-duplicate phrases.
- **State the polarity of every test explicitly** in terms of what it
  means, not just which flag: "Is it open?" / "No: say so and stop" reads
  correctly regardless of whether the underlying instruction is `JR Z` or
  `JR NZ`; get the actual polarity right by checking the branch target, not
  by assuming from the mnemonic (see `verification.md` - this is exactly
  where mistakes hide).
- **When a routine reuses another's tail** (jumps into the middle of a
  different routine to share code, a common Z80 space-saving trick), say so
  explicitly and explain what parameter substitution makes that reuse work
  ("this reuses the tail of #R$9BCD, which compares against whatever byte
  HL points at, by pointing HL at a different variable than #R$9BCD's own
  caller does").
- **Flag self-modifying code plainly** where you find it (a routine poking
  an opcode byte into another instruction before running it) - it's
  disorienting to a reader otherwise, and it's a distinctive, useful thing
  to know about the codebase as a whole.
- **Distinguish "confirmed by running the game" from "read from the code"**
  in prose descriptions of anything non-obvious, especially bug reports and
  trivia entries. A phrase like "confirmed in the emulator: ..." or "this
  follows from the code; it was not tried in the emulator" costs one clause
  and materially changes how much weight a reader should put on the claim.
- **Write the prose description before the line comments**, and match them
  up afterwards - a routine's paragraph-level description should say what
  it's *for*; the line comments should walk through *how*, in the same
  vocabulary.

## A short worked example: turning a trace into comments

Given this raw disassembly of an unknown routine (a text adventure engine's
"give an item to someone" handler):

```
9308  ld iy,($b5fa)
930c  call $9bcd
930f  ld hl,$ace4
9312  jp nc,$72d4
```

Work out what it does first (read `9bcd`'s own contract: "does the actor
hold object A? returns carry set if so"; read `$ace4` via the message
renderer: "you are not carrying it."), *then* write:

```
9308 LD IY,($B5FA)   ; IY = the instrument's (the receiver's) own record
930C CALL $9BCD          ; Is the actor holding the target?
930F LD HL,$ACE4            ; "you are not carrying it."
9312 JP NC,$72D4               ; If not, say so and stop
```

Notice the third line's comment is the *message text*, not "load message
address" - that's what a reader actually wants to know, and it makes the
fourth line's comment read as a natural continuation.
