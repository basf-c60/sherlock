# Harness notes (Phase 1)

## Why a custom hook, not raw port emulation

Grepping the whole 41,600-byte "p" block for `IN A,($FE)` (`DB FE`) and
`IN A,(C)` (`ED 40/48/50/58/60/68/78`) with port $FE found **zero**
matches. This game does not poll the keyboard port directly at all.

Instead it relies on a real Spectrum's ROM interrupt handler to scan the
keyboard into the standard system variables (FLAGS $5C3B, LAST-K $5C08),
and has its own routine, GET-KEY at $C41F, that does `EI; HALT; DI` to
let exactly one such interrupt happen, then reads those variables. Found
by grepping for literal little-endian references to $5C3B and $5C08 and
finding a tight, sensible cluster of both within a few bytes of each
other (see the disassembly in overlay_01_boot.py's $C41F block).

Since this sandbox has no real 48K ROM loaded, there is no interrupt
handler to actually populate those system variables. Rather than try to
emulate that whole path, `scripts/harness.py` sets a breakpoint directly
on GET-KEY's entry ($C41F) and simulates its entire contract in Python,
then jumps straight back to the caller - exactly the "hook the read-key
routine as a breakpoint" approach `emulator-harness.md` describes, just
applied at a CALL/RET boundary instead of a polling loop.

## Two real bugs, caught only by running it

**Bug 1: wrong entry address.** The first attempt used $C426 as GET-KEY's
entry (misreading the disassembly - $C426 is `LD IY,$5C3A`, a few bytes
*into* the routine, not its start). The real entry, confirmed by
grepping for `CALL $c41f` and finding three genuine `CD 1F C4` call
sites, is $C41F (the `PUSH IY` that begins the register-save sequence).
Using the wrong address meant we intercepted execution *after* the
routine's own prologue had already run, so our "pop the return address
off the stack" logic popped a value that was never a return address,
and the game reliably wandered off into unmapped memory a few
instructions later. Caught by single-stepping and noticing PC end up
executing zeroed/unmapped memory - not by re-reading the disassembly
more carefully.

**Bug 2: missing flags.** After fixing the entry address, the game still
misbehaved: it would spin printing nothing but space characters forever.
Bypassing GET-KEY skips its real final instruction (`XOR A` for "no key",
`SET 7,A` for "key available") - which sets CPU flags the *caller*
almost certainly branches on immediately after the `CALL`. Our bypass
set the `A` register correctly but left `F` untouched from whatever ran
*before* the call, so the caller's very next conditional jump could go
the wrong way. Fixed by computing the flags a plain `OR A` on the
returned value would produce (exactly matches `XOR A`'s flags for the
A=0 case, and is the standard assumption for the A=ascii|$80 case) and
setting `self.m.f` explicitly before returning. This exact class of bug
- "the bypass returns the right value but not the right side effects" -
is precisely why `verification.md` says to test the actual behaviour
rather than trust a plausible-looking shortcut.

**Bug 3 (harness-only, not a game bug): forgetting to step over a
breakpoint.** Adding a second breakpoint at PLOT-CHAR ($C388, see below)
to capture printed text, the very first attempt just read `A` at the
breakpoint and moved on - without calling `step_over_breakpoint()`.
Per this emulator's own documented breakpoint semantics ("a breakpoint
fires on the attempt to execute the marked instruction, before it makes
any progress"), simply calling `run()` again re-traps on the *same*
instruction with no progress at all. The symptom looked identical to a
real infinite loop (billions of T-states, output frozen on repeated
space characters) until a single-tick trace showed PC genuinely stuck
at one address forever - a good example of `verification.md`'s
"distinguish test-harness artefacts from real bugs" advice applying to
harness *construction*, not just to interpreting a finished run.

## PLOT-CHAR ($C388) as a message-rendering hook

Found by write-marking the display file (`mark_addrs` + `WRITE_MARK`)
during a scripted run and histogramming which PC was live at each write.
Two huge, uniform-sized clusters (6144 and 767/768 writes) were an
obvious CLS. A later run (after feeding a few ENTERs) showed four
dominant call-sites in the tens of thousands, all inside one small
region ($C280-$C3E3); disassembling it found PLOT-CHAR at $C388, which
computes its source glyph address as `A*8 + $3C00` - exactly the real
ROM font table layout (space, code 32, maps to $3D00). That confirms A
holds a literal ASCII code at the moment this runs, regardless of
whether real glyph pixels are available to draw (they aren't, since
there's no ROM loaded here - printed characters render as blank space on
our simulated screen, but the *character codes* going through this
routine are exactly what a real player would see printed).

Hooking this (read A, `step_over_breakpoint()`, continue) reliably
recovers legible text, confirmed against the real, known opening scene
of *Sherlock Holmes: Riddle of the Crown Jewels* - e.g. Watson's line
"Good morning Holmes." and the sitting-room description - which is
strong independent confirmation this hook is capturing the real thing
and not an artefact.

## Known current limitation: SAVE/LOAD

Sending the `SAVE` command reliably wedges the harness: the real game
calls into the ROM's tape-save routine ($04C2, confirmed as a genuine,
repeated CALL target - see the raw CALL-target frequency scan in this
project's exploration notes), which we don't hook, so execution runs
into unmapped/zeroed memory and never returns. Once this happens the
rest of that playthrough is unusable and must be restarted from a fresh
`Game()` instance. Exploring SAVE/LOAD properly would need a third hook,
on $04C2 (and probably $0556, the load routine), simulating "instant
success" the same way GET-KEY is bypassed. Not yet implemented.

## Coverage-tracking caveat

`Game(track_pc_coverage=True)` marks the "p" block's own address range
for read-tracking and records every address read - which includes data
operand reads, not just instruction fetches (the underlying emulator API
has no distinct "this was an opcode fetch" signal). This means some
addresses in the resulting map are pure data that happened to be read
by nearby code (e.g. a byte of message text the printer walked past),
not real instruction boundaries. `sna2ctl.py`'s own algorithm is
tolerant of this (it decodes one instruction from each marked address
and merges contiguous runs; spurious single entries show up as tiny,
awkward "code" blocks rather than corrupting the whole disassembly), but
this is exactly the "never trust the automatic split as final" caveat
`SKILL.md` warns about, and it applies with extra force here.

One more caveat specific to this hooking style: because GET-KEY is
bypassed via a direct PC redirect rather than executed and
`step_over_breakpoint()`-stepped, its own bytes never pass through the
tracked read callback and don't appear in the coverage map on their own
- they were added back into the map by hand once independently
confirmed by disassembly (see `build.py`'s use of `coverage_combined`).

## A real bug in build.py, caught by the round-trip check doing its job

Adding the confirmed $E03A overlay entry produced a skool file that
failed to round-trip (`skool2bin.py` warned about an instruction
overlap, and the rebuilt binary genuinely differed from the original).
Cause: the baseline `sna2ctl.py` guess had independently placed a data-
block boundary at $E03D, which sits in the middle of a real 3-byte
`LD A,($A036)` instruction starting at $E03B (now confirmed real).
`build.py`'s merge logic only forced boundaries at the overlay's own
declared addresses; it had no way to know a *stale* baseline boundary
a few bytes further in was now wrong, so both boundaries ended up in
the merged ctl, and `sna2skool.py` produced instructions that
overlapped on disk.

Fixed by having `build.py` remove any baseline boundary that falls
strictly between two consecutive addresses in a block's own confirmed
comment keys (which are, by construction, real instruction starts -
this project's own address cross-checker already guarantees that).
This is exactly the kind of mistake the round-trip check exists to
catch: it's cheap, it runs after every batch of changes, and it caught
a real, binary-breaking bug the moment it was introduced rather than
letting it sit unnoticed in a growing control file.

## Session 2026-11-05: pictures, teleporting, and walking every exit

**Pictures are skipped.** Entering some rooms (the entrance hallway,
room 6, is the first one you reach) draws a location picture: $A277
calls the picture interpreter at $F3C2, which plots through the 48K
ROM (PIXEL-ADD at $22AA, called from $F5FE). The harness has no ROM, so
the call ran off into empty memory and wrecked the game state (the
player's location ended up as 23). `harness.py` now sets a breakpoint
at $F3C2 (`PICTURE_ENTRY`) and returns straight to the caller
(`Game._skip_picture`, counted in `Game.pictures`); `tools/play.py` and
`render_messages.py` do the same. The picture code only draws, so
nothing the game does afterwards depends on it. Confirmed: the walk
your room -> hall -> entrance hallway -> Baker Street -> back now runs
cleanly, with "[picture skipped]" on the two rooms that have one.

**Teleporting the player** means setting three things, not two: the
player's location ($8CC9), the displayed room ($A00A), and the
last-room-entered pair $DD01 (room) / $DCFF (record address). The move
action writes $DD01/$DCFF for *any* actor that moves, and after the
boot sequence they hold room 16 (platform one, Aldergate station),
because someone moved there during the first turns (the file has 0).
Without them, the next description started "You are at platform one
of Aldergate station" before the real room.

**`tools/walkall.py`** uses that to try every exit in the room table:
206 exits, 194 move the player where the table says; the other 12 are
refused exactly as $DCD2/$DD35 predict, and the 5 of those with a real
destination let the player through once the player's size (+2) is
poked from 96 down to 8. Results: `source/exits_checked.json`.

## 2026-11-07: why a key sometimes disappears after WAIT UNTIL

While the player is waiting until a time (plan verb 50), the main loop
polls the keyboard once a minute ($A07F) so that ENTER can cut the wait
short. The harness answers that poll from its queue like any other key
read, so the first character of the next command can be consumed there.
That is very probably the old "W eaten, I DO NOT KNOW THE WORD 'AIT'"
oddity, read from the code and not re-tested. Queue the next
command only after the wait has ended, or expect to lose one character.
With an empty queue the harness answers "no key", which also drives the
input time-out ($A536): the player WAITs after 3,000 empty polls.

## 2026-11-07 (evening): pictures can be drawn after all

The harness skips $F3C2 because the game image has no ROM. SkoolKit ships
the 48K ROM (`skoolkit/resources/48.rom`); `tools/draw_pictures.py` loads
it at $0000, calls $F3C2 directly with HL = a picture and a sentinel
return address, and saves the screen. Every picture returns within a
fraction of a second of host time. Note for z80.Z80Machine: give run()
a generous total budget - the fills are slow in emulated time.

## 2026-11-07 (evening): teleporting leaves carried things behind

Moving the player by poking memory (the room at $8CC9, $A00A, $DCFF-
$DD01) does not update the room (+15) of anything the player carries.
Code that asks "is it here?" ($C821) then thinks a carried lamp is still
in the old room - the first darkness test failed that way. Walk the
player when carried things matter (tools/experiments/dark_test.py).

## Playing the game by typed commands (8 November, night)

- `tools/experiments/replay_log.py CMDFILE [N]` replays a list of typed
  commands from a fresh boot; `tools/experiments/replay_verbose.py CMDFILE
  OUT` does the same and writes every reply (truncated, the last few in
  full) plus the clock and room after each command. A line
  `(until TEXT) CMD` repeats CMD until TEXT appears in the reply, **at most
  80 times**: a wait that needs more (a long ride, WAIT = 5 minutes each)
  must be split over two lines, and TEXT must be a single word that the
  80-column wrap cannot split.
- The game is deterministic, so the same command file always ends in the
  same state; 444 lines take under a minute to replay on an idle machine
  (the first replay took sixteen minutes only because another job ran
  alongside it).
- Never run a blind wait loop after telling a cabbie where to go until
  the cab has actually moved (see the Bugs page, 'A failed SAY TO leaves
  its quotation behind').
- A winning command file is easy to spoil when stitched together out of
  snapshot logs: a log that was cloned from a snapshot also carries the
  commands of the branch it was cloned from, including dead ends (one
  such stretch ended in Phipps's 9:50am shot and had to be cut out).

## Shortening a command file (minimize_cmds.py)

`tools/experiments/minimize_cmds.py IN OUT` removes lines whose reply was an
error and plain LOOK/INVENTORY lines, keeping each removal only if the
whole file still wins. The check must be the winning *text*: the same room
and clock (Victoria platform one, 6:43pm) also come with the death ending
when Lestrade is left behind, and a first version that checked only room and
time produced a 370-line file that lost. Every minute counts in this route
(one line fewer or more can put Lestrade and the player in the same cab or
on the wrong train), so a candidate removal is never safe without a replay.
