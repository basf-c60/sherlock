# World-model notes (Phase 3, partial)

## The actor table at $9860 - confirmed by cross-reference

`discovery.md` step 5 warns not to trust a table's meaning from
proximity alone, but to confirm by finding *every* real reference to it
and checking they make sense together. Done here:

Four genuine `CALL`s to $CC0E exist in the whole block ($CC3D, $DDA3,
$E03E, $E300 - confirmed via a literal-bytes search for `CD 0E CC`, not
guessed from context). $CC0E itself is:

```
LD DE,$0008
LD IY,$9860
loop:
  LD A,(IY+0)
  CP C            ; C holds the actor id being searched for
  JR Z, found
  CP $FF          ; end-of-table sentinel
  JR Z, not_found
  ADD IY,DE       ; next record (8 bytes along)
  JR loop
```

This is a plain **"find the actor whose id is C" linear search** over a
sentinel-terminated array of 8-byte records starting at $9860 - textbook
"generic N-byte table, sentinel-terminated" per `discovery.md`, and now
independently confirmed (not just inferred from the boot-sequence code
that first led here, which only ever walked the table without an
explicit search key).

The boot-sequence code (see `overlay_01_boot.py`, $A040) separately
confirmed: field `+0` is the id/sentinel byte, and fields `+6`/`+7` hold
a 16-bit value that gets set from a stored value at $9FDD when a
specific actor (id $32) is present and the player pressed ENTER at a
particular boot prompt. $B0AC (one of the other real users of $9860,
found while cross-referencing) does something structurally identical:
`LD IX,$9860; LD (IX+6),L; LD (IX+7),H` after computing a value in HL -
strong confirmation fields +6/+7 are a genuine, reused per-actor 16-bit
value (a position? a target room? not yet determined which), set by
more than one place in the code using the same offsets.

**Not yet determined**: what fields +1 through +5 hold, how many
records exist in total, or what the 16-bit value at +6/+7 actually
represents (a location is the obvious guess for an adventure game's
character table, but not confirmed - the boot-sequence code sets it from
a saved value at $9FDD without printing or otherwise revealing its
meaning in anything tested so far).

## A per-room "action list" work area at $9806? (leads, not confirmed)

Diffing the whole "p" block's writable memory before and after walking
from the sitting room into the closet (`NORTH`, after opening the plain
door) showed 175 changed bytes. Most interesting: a block starting at
$9806 that is **all zero in the static tape image** (confirmed - dumped
the raw file bytes there, all `$00`) but gets filled with structured-
looking data at runtime:

```
0a 13 98 27 4b f2 15 03 01 ff
0a 1d 98 26 32 f2 1a 04 01 ff
0a 2c 98 25 3b f2 1e 04 01 ff
...
```

Read as little-endian words, several of these contain values in the
$98xx range (plausibly more pointers into the same page as the actor
table) and the $F2xx range (plausibly code addresses - $F2xx is inside
this project's loaded "p" block, so a value there could genuinely be a
handler routine's address, matching discovery.md's "object's own list
of action handlers" pattern), each entry apparently ending in an `$FF`
byte in the same position - consistent with, but **not confirmed as**,
a sentinel-terminated list of the kind `discovery.md` describes for a
room or object's own action handlers.

**Not yet done**: found no literal `LD DE,$9806` (or `LD HL,$9806`)
anywhere in the block, so the destination address for whatever writes
this data is computed at runtime rather than being a fixed immediate -
this needs a write-watch (`mark_addrs` + `WRITE_MARK`, exactly as used
successfully elsewhere in this project - see `harness_notes.md`) on the
$9800-$9860 range specifically during a room transition, to catch the
*copying* code in the act rather than just its result. Flagged here as
the concrete next step rather than guessed at further.

## Follow-up: the write-watch was done - extends (and complicates) the picture

Ran the suggested write-watch during a real `NORTH` movement. The real
writers are small accessor routines around $CEA0-$CEDE and
$D020-$D059, not one bulk copy - e.g. $D02F-$D044 sets `(IX+3)`,
`(IX+4)`, `(IX+6)` or `(IY+3)`, `(IY+4)`, `(IY+5)` depending on which
branch runs, and $CEAF/$CEB2 sets `(IY+1)`, `(IY+2)`. Put together with
the boot-code-confirmed `(IX+6)/(IX+7)` and the id at `+0`, that
accounts for bytes 0 through 7 of the record - the full 8 bytes $CC0E's
search step already confirmed as the record size - but **the exact
meaning of fields +1/+2, +3/+4, and +5 is not established**, only that
they're genuinely read and written as part of moving between rooms.

Also found, one level further in: $D045 reads the very *first* actor
record's id byte (`LD A,($9860)` - record 0, presumably the player) and
calls $D495 with it, which itself calls $D237 and then, if a type check
passes (`CP (IX+0)` against 1), reads **`(IX+$0F)`** - offset 15, past
the end of an 8-byte actor record. That means $D237 resolves the id into
a pointer into a **different, larger-record table** - very plausibly
the room table itself (a room record with at least 16 bytes would fit
`discovery.md`'s "fixed header + variable trailing data" pattern much
better than the compact 8-byte actor record). This was the most
promising lead in this project - chased it properly below.

## Follow-up: chased the $D237/$D495 lead - confirmed empirically

Disassembled $D237 and its own helper $D34E. The full chain turns out
to be:

```
$D045: LD A,($9860)     ; the FIRST actor record's own id byte
       CALL $D495
       LD ($A009),A     ; stash the result
$D495: CP $FF; RET Z             ; invalid id -> $FF
       CALL $D237                ; resolve id -> a record pointer (in IX)
       LD A,$01; CP (IX+0)       ; that record's own type tag must be 1
       LD A,$FF; RET NZ          ; if not, fail
       LD A,(IX+$0F); RET        ; else: return byte at offset +15
$D237: LD IX,$8B6F               ; base of a 3-byte-record index table
       CALL $D34E                ; find the record whose id matches A
       ... (register-juggling that nets IX = that record's own stored
            16-bit pointer, i.e. one level of indirection)
$D34E: EXX; LD E,3                ; 3-byte records, sentinel-search
       ... walks from $8B6F: id byte, then a 16-bit pointer, $FF = end
```

**Confirmed empirically**, not just by reading: called $D495 directly
(isolated, via the `call_routine` pattern from `emulator-harness.md`)
with A=0 while the player was in the sitting room - got back `$08`.
Moved the player north into the small closet in the real, running game,
called it again - got back `$09`. Moved back south - got `$08` again.
**This is confirmed to be "get the current room number of actor A".**

Went further: called `$D237` directly for ids 0-3 and dumped the full
records it resolves to. All four are 17 bytes, all start with the type
tag `$01`, and are laid out **back-to-back** (0x8cba, 0x8ccb, 0x8cdc,
0x8ced - each exactly 17 bytes after the last, confirming the record
size independently of the earlier 8-byte *index* table's stride).
Offset +15 is confirmed as the room number for all four (id 0 and id 3
both read $08 - very plausibly Holmes and Watson, both starting in the
sitting room together, matching the real opening scene where Watson
sits right there in his own armchair; id 2 reads $0A, a room not yet
visited but presumably a real one elsewhere in the game; id 1 reads
$00, and unlike the other three its offset +7/+8 field also doesn't
look like a valid pointer into loaded memory - id 1 may be an unused or
differently-shaped record, not confirmed either way).

**Not yet determined**: what offsets +1 through +6, +9/+10, and +16 of
this 17-byte record hold. Offset +7/+8 looks like a pointer (falls
inside the loaded "p" block for ids 0, 2, 3) but attempting to read it
as message/name text didn't produce anything ASCII-recognisable -
either it points at something else (a sub-record, not text), or
whatever it points at needs its own expansion step first (plausible,
given the dictionary's own words need expansion too - see
`dictionary_notes.md`). Flagged as a lead, not a conclusion.

## Follow-up: found (and ruled out) a real message-printing loop

While hunting for how room descriptions get from storage to screen,
found a second, completely different, genuinely real routine: a loop at
$C1CB that reads a byte, masks off bit 7, prints it via a gated entry
point at $C1FD, and stops when it hits a byte that **had** bit 7 set
(i.e., messages as **plain ASCII, terminated by setting the top bit of
the last character** - no bytecode at all, for whatever uses this).
Confirmed as real code by finding all 4 of its genuine callers (literal
`CALL $C1CB` bytes at $C070, $C09C, $C0EA, $C1C0).

**Ruled out** as the room-description path specifically: breakpointed
$C1CB directly during a real `LOOK` command and got **zero hits** -
whatever prints room text doesn't go through this loop. Also tried
breakpointing $C1FD (the gated print-entry this loop calls) and its
own only found caller ($D944) turned out to call it a mere 4 times
with no visible output - consistent with $C1FD's very first check
(`LD A,($5C3C); AND A; JR NZ,...; RET`) reading a flag that's never
zero in this project's unbooted-ROM sandbox, so this whole gated path
silently no-ops here regardless of what it's really for (a "printer
echo" toggle is a reasonable guess, given $5C3C sits in what would be
Spectrum ROM system-variable territory on real hardware - not
confirmed).

Also tried breakpointing $C2BA (the CR-handling print wrapper
`overlay_01_boot.py` already documents from earlier in this project)
directly during a real `LOOK`, hoping to catch its caller via the
return address on the stack the same way - this got zero hits too, and
suspiciously also suppressed the PLOT-CHAR hits that reliably fire in
every other test in this project. Something about that specific
breakpoint address interacts badly with this test (or $C2BA's
`overlay_01_boot.py` description may need re-checking - the block was
originally identified from a disassembly window that turned out to
have an alignment problem elsewhere in this project, see
`harness_notes.md`'s GET-KEY mix-up for a similar mistake). **Not
resolved. Flagged rather than left silently unstated.** The reliable,
still-standing fact is simply that PLOT-CHAR ($C388) itself is
definitely used for room text (confirmed many times over in this
project); exactly what calls it for room text specifically remains
open.

**RESOLVED further down this file** ("the room-text print path is
resolved - and a false alarm explained"): this zero-hit result was a
bug in that specific test, not a real property of $C2BA. Re-run
cleanly, the same breakpoint produces 170 real hits during a single
`LOOK`. Left in place here, rather than deleted, as the record of what
was tried and why it looked - wrongly - like a dead end at the time.

**Concrete next step for anyone continuing this**: rather than guessing
which wrapper matters and breakpointing that, breakpoint PLOT-CHAR
($C388) itself (already known-reliable) during a `LOOK` command and read
the *whole call stack*, not just the immediate return address - peek at
several words up the stack from SP, since the true "print this room's
text" driver is probably 2-3 call-levels above PLOT-CHAR's immediate
caller, not the immediate caller itself.

## Follow-up: did the whole-call-stack trace - narrowed further, still open

Fixed a real bug in the first attempt at this (the test loop broke out
the instant the typed command's input queue drained, before the room
text - which prints *after* input is consumed - had a chance to appear
at all; needed the same idle-detection loop `Game.run()` already uses).
With that fixed, sampled the full stack (12 words up from SP) at
several consecutive PLOT-CHAR hits partway into a real `LOOK` response.

The stack was **identical across five consecutive space characters**,
which is itself useful confirmation: whatever's several frames up isn't
changing per-character, so it's a genuine outer "print this whole
message" frame, not part of the tight inner glyph-plotting loop.
Disassembled the most promising stable address ($A2A8, a return address
into a small "print N blank lines" utility, $A296) and traced one level
further to $A9B7 - which turned out to be a **shared, flag-gated
low-level output primitive**: if a mode flag at $A027 is set, it
appends the character into a growing buffer at a position tracked at
$A9B5 (handling space/CR/quote/backspace specially) instead of drawing
it - this is genuinely the same buffer-building mechanism used earlier
in this project while tracing dictionary word comparison (`$5C0B`, see
`dictionary_notes.md`); if the flag is clear, it presumably falls
through to real screen output elsewhere (unexplored, past this
disassembly's window).

So: **not the room-text driver itself**, but a real, useful
clarification - $A9B7 is one shared low-level primitive doing double
duty for both keyboard-echo buffering and general character output,
gated by the same $A027 flag documented in `dictionary_notes.md` and
seen earlier controlling PR-CHAR-MAIN's behaviour too. The actual
"here is a whole room description, print it" driver is still higher up
the call stack than this - the $DC7D/$DC84/$CB37 addresses seen in the
same stack dumps are the next honest lead (not yet examined).

## Follow-up: found the main per-turn dispatch and room-change logic

Chased $CB37 next and it paid off - found a genuine **computed-jump
action dispatcher**:

```
$CB2C: LD IX,($CB28)   ; save/restore IX and IY around the jump -
       LD IY,($CB2A)   ; whatever gets dispatched to is trusted to
       CALL $CB40       ; clobber them, apparently
       LD ($CB28),IX
       LD ($CB2A),IY
       RET
$CB40: JP (HL)          ; the actual computed jump - HL must be set by
                         ; the (one, confirmed real) caller before this
```

Its one real caller ($CA64, confirmed the same way as everywhere else
in this project - grepping for the literal `CD 2C CB` bytes) sits in
what looks like the main per-turn command-execution routine:

```
$CA64: ... (set up default position variables at $9FD7/$9FD8,
            falling back to $A034/$A035 if unset/$FF)
       CALL $CB2C           ; dispatch to whatever handles the parsed
                             ; action - this is presumably where a
                             ; verb's own handler routine runs
       CALL $CA7F           ; then check: has the player's room changed?
       [if $A00C is still 0] CALL $CAAF
```

$CA7F is a clean, small, self-contained check: get actor 0's (the
player's) current room via the now-confirmed $D237/$D495 chain, and
compare it against $A009 (the value $D045 stashes there earlier, in
`overlay_01_boot.py`'s neighbourhood) - i.e. **"is the room now
different from what we last recorded"**.

$CAAF, called when that's true, does several further comparisons (the
player's room against a *different* cached byte at $C491; another
actor's room, read via `$A036`, against the player's; and, in one
branch, walks a sentinel/count-terminated array of the same 17-byte
entity records - counted by `(IX+0)` as a loop counter this time,
rather than searched by id - looking for one whose room, offset +15
again, matches the player's current room). That last part in
particular looks like exactly the mechanism that would answer "what
else is in this room with the player" for a room description's "you
can see..." line - **a real, promising lead, not yet fully confirmed**.

**Not yet determined**: the exact contents of `$C491` (a second,
different "last known room" byte, distinct from `$A009`); what `$68ED`
(a fixed dictionary-region address used as a parameter to a call in
this same neighbourhood, `$CBC2`) is for; and whether the "walk by
count, match on room" logic in `$CAAF` really is the room-contents
lister. All flagged as leads for continuation, not claimed as
confirmed.

This is, however, the clearest picture yet of the game's actual turn
cycle: **parse a command -> dispatch to its handler via a computed
jump -> check whether the player's room changed as a result -> if so,
run follow-up logic that appears to involve room contents.** That's a
genuinely major structural finding for continuing this disassembly,
even though the exact dispatch table (what fills HL before `$CB2C` is
called) and the room-description text itself remain open.

## Follow-up: found the actual verb dispatch table

Traced back from $CB2C's one caller far enough to find where a verb
number actually turns into a handler address. At $C960:

```
LD A,(IX+1)      ; a verb number, 1-based (IX points at some
                 ; per-command working record, not yet fully typed)
LD E,A; LD D,0
LD HL,$AA71      ; the table's base
DEC DE
ADD HL,DE
ADD HL,DE        ; HL = $AA71 + (verb_number - 1) * 2
LD E,(HL); INC HL; LD D,(HL); EX DE,HL   ; HL = the table's stored value
```

**Confirmed real**, not just plausible-looking: dumped the first 20
entries of the table at $AA71 and every single one falls inside the
loaded "p" block's address range (mostly clustered in two bands, $9Axx
and $Exxx - suggestive of two different *kinds* of verb, see below).
Checked the bytes at verb 1's target ($9A99) and they disassemble as
real, sensible code (`CALL $9AA3`, `JP Z,$DC15`, ...) - this is
genuinely executable, not misread data.

Checked a couple of the $Exxx-band entries too (verb 3's target,
$E1A3; verb 4's, $E022) and they do *not* look like plain code in the
same way - more small values and what look like more addresses close
together, suggestive of some kind of compact per-verb record rather
than straight executable code. **Not resolved** - plausible guesses
(a message-id + fallback-handler pair; a small further dispatch
structure) are just guesses at this point, not confirmed.

**What this means for the project so far**: verbs in this range that
land in the $9Axx band (at least verb 1) get real custom handler code;
whatever lands in the $Exxx band is some other, more compact
structure. This is very likely the boundary discovery.md predicts
between "verbs with genuinely special logic" (movement, taking,
looking) and "verbs that just print a canned response" (most of them) -
matching how few *routines* a typical text adventure needs versus how
many *verbs* the vocabulary recognises.

**Concrete next step**: disassemble verb 1's handler at $9A99 properly
(a real, confirmed, in-range routine - a solid, tractable next target),
and separately, try to work out which verb NUMBER corresponds to which
typed WORD - this project has confirmed the dictionary's per-letter
index table (`dictionary_notes.md`) but hasn't yet connected a
dictionary entry to the small integer "verb number" this table is
indexed by. That link (a dictionary entry -> verb number mapping) is
probably the single most valuable next thing to find, since it would
finally connect the vocabulary side of this project to the action side.

## Follow-up: the "verb number" isn't a verb number - corrected

Went looking for that link empirically: breakpointed $C960 during real
play and logged (IX+1) - what I'd been calling "the verb number" - for
several different typed commands, using a fresh game instance per
command so nothing from an earlier command's state could leak in.

The result **falsified the simple "typed verb -> number" hypothesis**,
and it's worth recording exactly how, since this is precisely the kind
of confident-sounding-but-wrong reading `verification.md` warns about:

```
LOOK:            index 11, IX=$8F08  (twice)
INVENTORY:       index 11, IX=$8F08  (twice)
TAKE LAMP:       index 11, IX=$8F08  (twice)
OPEN PLAIN DOOR: index  6, IX=$90E5  (three times), THEN
                 index 11, IX=$8F08  (twice)
XYZZY / FOOBAR / (empty line): no hits at all
```

Three genuinely different, successfully-executed verbs (LOOK,
INVENTORY, TAKE) all produced the *exact same* index and the *exact
same* IX. That rules out "index = which verb was typed" - if it did,
these three would differ. What's consistent instead: **the same
check runs after every successfully-parsed command**, and it does
*not* run when the typed command was rejected outright (XYZZY,
FOOBAR, a bare Enter all produced zero hits). OPEN additionally
triggers a *different* index/IX pair, three times, *before* that
shared one - plausibly while resolving "which door" (three candidate
matches tried, given the real game's own "WHICH DOOR?" disambiguation
prompt seen earlier in this project when the noun is ambiguous).

**Current best reading** (a genuine improvement, not yet fully
confirmed): IX doesn't point at "the verb" at all - it points at
*whichever record is currently being tested*, and the number at
offset +1 of that record is a **per-record "primary action" field**,
looked up in the shared $AA71 table to find out what that action
actually does. $8F08 looks like it might be a fixed, generic "end of
a successful turn" record (checked after everything), while $90E5 is
plausibly the plain door object's own record, checked specifically
while OPEN resolves which door is meant. This matches
`discovery.md`'s "an action-number byte immediately precedes this
address, so this is one entry in an object's own list of action
handlers" pattern far better than a flat global verb table would -
just requiring the correction that the table is shared and reusable
across many different *kinds* of record, not solely indexed by "the
verb the player typed."

**Not yet confirmed**: what $8F08 and $90E5 actually are (record type,
full field layout), and therefore what "the single most valuable next
link" really looks like now - it's likely "which object/record does
the parser resolve a typed noun to" rather than "which number does a
typed verb map to", which is a more promising and probably easier
question to chase (three real, distinct IX values are already in hand
to dump and compare, the same way the actor records were successfully
characterised earlier in this project).

## Follow-up: dumped both records - looks like per-object action lists

```
$8F08: 1f 0b 0d 08 0c 0c 19 08 18 0c ff 01 1e 10 40 80 c0 00 68 01
$90E5: 24 06 0e 07 ff 04 ff ff ff 00 80 00 6e 22 16 06 00 00 00 00
```

Offset +1 matches the logged index exactly for both (11 = $0B for
$8F08, 6 = $06 for $90E5 - a good sanity check that the earlier
breakpoint logging was reading the right bytes). Field +0 differs
between them ($1F vs $24) and doesn't match the actor record's
consistent type-tag pattern, so **these are a different table
entirely from the 17-byte actor/entity records** - not yet named or
sized with confidence.

$90E5's tail is dominated by repeated $FF bytes (offsets +4, +6, +7,
+8), with real-looking values in between (+5 = $04) - a strong match
for `discovery.md`'s "object's own list of action handlers,
terminated by sentinel" pattern: read as a short list of action
numbers to try in turn, $FF marking "no more". $8F08's equivalent
region (+4 onward) has no $FF at all in the same span, consistent
with it being a longer, "generic/always-applicable" list rather than
one specific object's short list - fitting the "checked after every
successful command" behaviour observed. **Plausible, not confirmed** -
offered as the next concrete lead rather than settled fact.

## Follow-up: found where IY itself comes from - a real, static table

Pushed one level further up: $C960 turned out to be called from deep
inside $C9C0, which pops an IY value that its own caller pushes before
jumping in (a "push a parameter, then JP" idiom, not a real CALL/RET
pair - which is exactly why grepping for `CALL $C9C0` earlier found
nothing; it isn't called that way at all).

Breakpointed $C9C0's entry directly (peeking at the stack rather than
disturbing it) across five different real commands, each from a fresh
game instance. The results were extremely clean: **every command
started with the identical five IY values, in the identical order**
(`$D715, $D769, $D77E, $D7D9, $D7FA`), before diverging at a
command-specific point, and (for LOOK/INVENTORY/TAKE/OPEN, though
notably not NORTH) converging again onto a long, identical shared
tail afterwards.

That fixed opening sequence turned out to be real, static data, not a
coincidence of a dynamic walk: searching the file for the literal bytes
of the first value (`$D715`) found exactly one occurrence, at $9929,
sitting inside a clean 5-byte record: `$99 $13 <addr low> <addr high>
<flag>`. Dumping five records forward from there reproduces all five of
the confirmed IY values exactly, in exactly the observed order:

```
$9927: 99 13 15 D7 23   -> $D715, flag $23
$992C: 99 13 69 D7 23   -> $D769, flag $23
$9931: 99 13 7E D7 23   -> $D77E, flag $23
$9936: 99 13 D9 D7 2D   -> $D7D9, flag $2D
$993B: 99 13 FA D7 37   -> $D7FA, flag $37
$9940: (data no longer fits this 5-byte shape)
```

> **CORRECTED 2026-11-07.** These are not 5-byte records. The bytes
> from $9921 are the player's plan script (actor 0's script position in
> the actor table at $9860), and the right alignment is one instruction
> per RUN: `13 15 D7 23 99` = RUN $D715, failure address $9923. So the
> "$99" is the high byte of the previous instruction's failure address
> and the "flag" is the low byte of this one's. The five IY values are
> the RUN targets, which is why they appeared in that order on every
> command. See overlay_08_plans.py and the "plan scripts" Trivia entry.

**Confirmed**: this is a genuine, fixed, 5-entry table of "always
checked, every single turn" records, each shaped `$99, $13, <a 16-bit
address>, <a flag byte>` - the constant `$99 $13` header and varying
trailing flag ($23 for the first three, $2D and $37 for the last two)
are both real, verified against the file's own bytes, not inferred
from behaviour alone. The data stops fitting this exact shape
immediately after the fifth entry, so this table is short and
self-contained - it is *not* a long list that the rest of the observed
sequence (the shared tail, or the command-specific divergent entry)
continues into; those come from somewhere else, not yet found.

**Not yet determined**: what these five particular checks are for
(candidate guesses - a scheduled Watson remark, the game clock
advancing, a random event, a game-over condition check - are just
guesses), what the flag byte means (the $23/$23/$23/$2D/$37 pattern
splits 3-vs-2, which is suggestive but unexplained), and where the
*rest* of the sequence seen at runtime (the command-specific entry and
the long shared tail) is actually stored, since it isn't a simple
continuation of this same table.

## Follow-up: the "boot sequence" is also the per-turn NPC-processing loop

Chased the stable stack addresses one more level up and found something
that requires a real correction to earlier work in this project, not
just a new fact: the actor-table walk documented in
`overlay_01_boot.py` as part of the game's one-time boot sequence
($A040 onward: "walks a sentinel-terminated table of 8-byte records at
$9860...") is **also genuinely re-entered on every single turn**, not
boot-only as originally described.

**Why this is confirmed, not just suspected**: this project's own
harness reaches its first idle ("waiting for a keypress") state only
~40 slices after boot - which necessarily means any one-time boot
processing, including this actor walk, has already finished by then.
Sending a real `LOOK` command afterwards and breakpointing deep inside
the walk (at $C9C0, several calls down) produced dozens of hits, with
a stack trace showing the walk stepping through the *same* $9860 table
records (addresses $9860, $9868, ... - the confirmed 8-byte stride)
all over again. That can only mean the command re-triggered the same
code, not that boot was somehow still running minutes of emulated time
later.

Traced the actual mechanism one level further: `$A0B0` (inside the
walk, immediately following `LD A,(IY+0)` - this record's id) calls
`$CC78`, a genuine, real subroutine:

```
$CC78: CALL $CC5A       ; (a shared tail also reachable via $CC37 below)
       LD IY,($9FDB)    ; reload this actor's own resolved record
       CALL $D008
       LD L,(IY+1); LD H,(IY+2)   ; read a handler address out of it
       ... (continues past this disassembly window)
```

and `$CC5A`'s own entry (`$CC37`, confirmed the real target of the
call at `$CC5A`) does, in order: clear a flag ($CC0B), resolve the
current actor's id to its full record via the already-confirmed
$CC0E, stash that record pointer at $9FDB and its id at $A036, call
$B91F (not yet examined), then call the already-confirmed $CC29 (get
this actor's room, via $D495) and $D045 (get the *player's*
room, actor 0, also via $D495) - building exactly the kind of
"compare this actor's room against the player's" context `$CAAF`
(documented earlier in this file) also uses.

**What this adds up to, confirmed by this chain of genuine, cross-
referenced routines**: for every actor in the $9860 table, once per
turn, the game resolves that actor's full state record, compares its
room against the player's, and reads a handler address out of the
record's own fields (+1/+2) to find out what - if anything - that
actor does this turn. This is a real, coherent "NPC behaviour" system,
not a boot-only curiosity, and the connection back to the whole
$C960/$C9C0/$AA71 apparatus documented above is now much clearer: that
apparatus is very likely how each actor's *own* handler decides what
action to take, not solely how the player's typed verb gets resolved.

**Not yet confirmed**: the exact mechanism by which the main per-turn
loop re-enters this walk (no static `CALL` to any address inside it
was found by grepping literal bytes, consistent with this project's
recurring pattern of computed jumps rather than plain calls - see the
dispatch mechanism documented earlier in this file); what $B91F,
$C821, and $D008 do; and the precise field layout of the per-actor
state record beyond the two fields (+1/+2, a handler address) newly
confirmed here.

**This is a real correction, not just an addition**: `overlay_01_boot.py`'s
description of the $A040 entry point should be read as accurate only
for its very first several instructions (the one-time DI / stack
reset / RNG seed / New-vs-Continue prompt, which genuinely cannot make
sense to repeat every turn) - the actor-table walk further down in the
same routine is shared, reentrant code, not boot-only. The overlay
comments themselves have been left as originally written for now
(they were not factually wrong about *that* walk happening at boot -
it does - only incomplete about it also happening elsewhere), with
this note as the correction of record; a future pass should split
$A040 into its true one-time-only prologue and a separately-named,
properly cross-referenced shared actor-processing routine.

## Follow-up: the room-text print path is resolved - and a false alarm explained

Earlier in this project (see the "found (and ruled out) a real message-
printing loop" section above), breakpointing $C2BA directly during a
real `LOOK` command produced zero hits, which was written up honestly
as unresolved and slightly suspicious. Chasing a completely different
thread (the shared echo/print primitive $A9B7's `$A027`-gated branch)
led to `$AA11`'s `JP $C1E1` and `$AA41`'s `CALL $C1E1` - both real,
confirmed call targets landing exactly on a byte boundary that matches,
instruction for instruction, what this project's very first pass at
this routine had already described under the address $C1FD (a
misaligned disassembly window at the time, flagged honestly as
uncertain rather than asserted). **The original description of that
routine's logic was correct all along; only the exact starting
address was off, by an amount consistent with the window simply
starting a few bytes into the routine rather than at its true entry.**

With the correct entry address in hand, re-ran the exact same $C2BA
breakpoint test from earlier in this project - and this time it
produced **170 real hits** during a single `LOOK` command, with a
dominant, real caller (`$A9FD`, returning to `$AA00`, 133 of the 170
hits). **The earlier zero-hit result was a bug in that test, not a
finding about the game** - almost certainly the same class of mistake
already documented in `harness_notes.md` (a stray or mishandled
breakpoint interaction), not a real property of $C2BA. Recorded here
explicitly so a future reader who finds the old "ruled out" language
doesn't treat it as still standing - it doesn't.

**Confirmed print pipeline for ordinary game text**, assembled from
everything now verified across this project:

```
$C1E1  gatekeeper: checks $5C3C, then $A027 -> either falls through
       to $C2BA directly, or (when $A027 is set) into a case-folding
       and quote-tracking region around $AA12-$AA50
$AA12+ case-folding/quote logic -> eventually calls back into $C2BA
$C2BA  handles CR specially (paging, see overlay_01_boot.py),
       otherwise calls PLOT-CHAR
$C388  PLOT-CHAR: draws the glyph (confirmed since early in this
       project as the hook that recovers real game text)
```

**Not fully traced**: the exact nested call graph between $AA12 and
$C2BA has several small, mutually-referencing routines ($AA14, $AA41's
own call back into $C1E1, etc.) that weren't stepped through
individually - the architecture above is confirmed by real breakpoint
evidence at both ends ($C1E1/$A9B7's entry conditions, and $C2BA's 170
real hits with a real caller), not by tracing every intermediate
instruction. That's a reasonable place to stop for this pass; the
remaining detail would mostly refine exactly *how* case-folding and
quote-tracking work, not *whether* this is the real print path, which
is now solidly established.

## Follow-up: $B91F is intro/setup-only, not part of the per-turn loop

> **CORRECTED 2026-11-07: wrong.** Re-tested with every breakpoint
> stepped over: $B91F runs once per actor whose turn comes up, every
> turn (LOOK 19 hits, WAIT 67, TAKE LAMP 18; 0 only for a command that
> takes no time). It looks for an order or remark waiting for that
> actor on the list at $9FEE. The "scripted" id order below is just the
> actor table's order. The section is kept as it was written.

Went back to properly verify $B91F (read last round but explicitly left
unconfirmed). Breakpointed it across boot and the opening intro
sequence separately: **zero hits during boot itself**, then **25 hits**
during the four ENTERs that step through the opening cutscene text,
with `$A036` (the id it searches for, in the confirmed-real table this
project has been calling the "3-byte index" style search since $CC0E)
taking this exact sequence of values:

```
0, 2, 3, 4, 5, 6, 104, 7, 8, 9, 10, 11, 12, 13, 31, 34, 36, 37, 38, 39,
40, 41, 42, 43, 0
```

That is not a simple linear walk (it jumps from 6 to 104 and back, then
later jumps from 13 to 31 and skips 32/33/35) - it looks like a
**scripted list of specific ids being validated or placed** as part of
the opening sequence (very plausibly "make sure these specific objects
start in their specific rooms"), not a generic per-actor search that
would run every turn. Confirmed separately: breakpointing $B91F during
an ordinary `LOOK` command, well after the intro has finished,
produced **zero hits** - so whatever this is, it only runs once, during
setup.

This corrects last round's framing of $B91F as "on the newly-traced
NPC-dispatch path" - it shares a search mechanism with that path
(and is genuinely called from $CC37, which is genuinely part of that
path), but its own role is intro-specific object/room placement, not
an ongoing per-turn check. The $9FF0 table it searches is confirmed to
start out essentially all zero in the static file and become populated
with real, non-zero data (including what looks like a genuine record
pointer, ending `...8C BA` - matching this project's earlier-confirmed
id-0 record address, $8CBA) only after this sequence runs - consistent
with it being where those scripted placements get recorded.

**Not yet confirmed**: what the specific ids in that sequence
correspond to (room numbers? object numbers? a mix?), or the precise
record layout $9FF0 holds once populated.

## Follow-up: $C821 is a noun/actor resolution test, with a real ID catalog

Found $C863 (called twice inside $C821) does something worth
recording on its own: it resolves an id via $D237, then in $C86E walks
a **chain** - `(IX+1)` holds the *next* id to follow (not a memory
address; another id, resolved the same way), continuing while bits 5
or 3 of the new record's own `(IX+5)` are set, stopping when `(IX+1)`
is $FF or bit 7 of `(IX+5)` is clear. Read as "find this object's
ultimate container, walking up through however many levels of nesting,
honouring per-level flags" - exactly the "is this object inside
something else" mechanism a text adventure needs (container is inside
a room; item is inside a container; item is carried by an actor),
though the exact meaning of the bit-5/bit-3/bit-7 flags isn't nailed
down yet.

$C821 itself is called from 12 real, confirmed sites - among them
$CC67, which is inside the already-documented $CC64 (compares the
player's resolved room-via-container against the current NPC's, then
sets the print-gate flag $5C3C accordingly) - strong, independent
confirmation this really is a "same room / visible" test, not a guess.

Bred an actual **id catalog** by breakpointing $C821 during several
real, known commands (present objects produce many hits including a
repeated, stable id; absent objects produce only a handful of zeros
before giving up):

```
TAKE LAMP / EXAMINE LAMP  -> id 22 (repeated heavily)
TAKE PIPE (not present)   -> no stable id, gives up after 5 hits
EXAMINE ARMCHAIR          -> ids 23, 24 (two armchairs in the room -
                             "your armchair" and "watsons armchair",
                             matching the room text exactly)
TALK TO WATSON            -> id 3, and id 25
EXAMINE SOFA              -> ids 60, 71 (lower confidence - SOFA isn't
                             actually examinable per earlier testing,
                             "YOU CANNOT EXAMINE THE SOFA", so these
                             may be something else, e.g. a rejected
                             candidate or a message id, not a settled
                             object id)
TAKE MONEY (not present)  -> ids 27, 28, 32, 35, repeating - lower
                             confidence for the same reason as SOFA
```

**id 3 = Watson is a genuine cross-confirmation, not a first sighting**:
several rounds ago, this project independently found (by calling the
confirmed $D237/$D495 room-accessor directly) that actor id 3's room
matches actor id 0's (the player's) - both room $08, the sitting room -
and guessed, from context, that id 3 was "very plausibly Holmes and
Watson, both starting in the sitting room together". This round's
`TALK TO WATSON` test landing on id 3 through a completely different
code path (noun resolution rather than the room accessor) makes that
guess a properly confirmed fact rather than a plausible guess.

**Not yet confirmed**: ids for SOFA and MONEY are lower-confidence,
since both objects are known (from earlier gameplay testing) to not
actually be interactable in the expected way, so the ids seen may be
intermediate/rejected candidates rather than settled results. The LAMP,
ARMCHAIR, and WATSON ids are higher-confidence, since those commands
all succeeded and produced a small, stable, repeated id rather than a
handful of ids that never repeat.

## Follow-up: unifying several previously-separate threads into one system

Chased the "what actually loads HL before $CB2C's dispatch" question
(the concrete next step identified after last round's $E003 correction
- see `dictionary_notes.md`) and it ties together three separate
findings from earlier rounds into one coherent picture.

Breakpointing $CB2C directly during a real `TAKE LAMP` shows its one
real caller is $CA64 (return address $CA67, matching `CALL $CB2C`'s
own length), confirmed 22 times for that single command. Breakpointing
$CA64 itself shows *its* one real caller is $C99C, with **IY taking
exactly the same sequence this project found months (in session terms)
earlier while investigating $C9C0**: the fixed 5-entry static table at
$9927 first ($D715, $D769, $D77E, $D7D9, $D7FA), then a command-
specific entry, then a long shared tail. For `TAKE LAMP`, that
command-specific entry is `$DCC1` - **exactly the id this project's
"real object/actor id catalog" round found weeks earlier for `TAKE
LAMP`** (recorded there as one of the ids seen while confirming $C821
as a visibility test).

**This means $C9C0, $CA64, and $CB2C are not three separate mechanisms
- they are one unified per-candidate loop**: for each candidate record
in turn (5 fixed universal checks, then whatever the parser resolved
this command to, then a long shared tail of further candidates), the
loop calls $CA64 (with IY pointing at that candidate), which sets up
some room-comparison state and calls $CB2C, which jumps through a
handler address read from *that candidate's own record* (the
`(IY+2)/(IY+3)` pattern this project found still earlier, at $C9E3).
"Try this candidate's own handler, whatever it is" - run once per
candidate, for every command, not a special path just for the
player's own verb.

**This also means $AA71/$C960 - the table this project spent two
rounds on, first as "the verb table", then corrected to "not simply
verb number", then (wrongly) claimed and un-claimed as TAKE's handler
- is confirmed to be a genuinely separate system from this dispatch
loop.** The unified loop's dispatch address comes from each
candidate's own stored record fields, not from $AA71 at all. What
$AA71 actually is remains open, but the search space is now much
better bounded: it is not the per-turn action dispatcher, since that
mechanism is now fully traced and doesn't touch it.

**Not yet confirmed**: what determines the length and contents of the
"long shared tail" after the command-specific entry (is it a fixed
list, like the 5-entry table, or built dynamically per room?), and
what $AA71 is used for instead, now that "the verb dispatch table" is
ruled out for it.

## Follow-up: found what $AA71 is actually for - a shared action library

Went back to the open question directly: is $C960 (the $AA71 lookup)
ever reached at all during real play? Breakpointed it across boot, the
intro, and ten different real commands. It fires for some commands
(`INVENTORY`, `DROP LAMP`, `OPEN PLAIN DOOR`) and not others (`LOOK`,
`TAKE LAMP`, `NORTH`, `SOUTH`, `EXAMINE ARMCHAIR`, `TALK TO WATSON`) -
genuinely selective, not dead code and not universal.

Logging the actual index looked up (`(IX+1)`) for each hit shows
something the earlier "per-candidate walk" model didn't capture: two
consecutive `INVENTORY` hits came from `$8F08` and `$8F0C` - four bytes
apart, both inside the *same* record this project dumped much earlier
(`1F 0B 0D 08 0C 0C 19 08 18 0C FF 01...`). Read as 4-byte groups, the
second byte of each group is exactly the index looked up: group 0
(`0B`=11) matches the first hit, group 1 (`0C`=12) matches the second.
**So a single candidate record can carry several small "try this
generic action" entries, tried in turn - $CA64/$C9C0's per-candidate
walk doesn't stop at one $AA71 lookup per candidate, it can make
several.**

`OPEN PLAIN DOOR` reliably produces index 6 - the exact table entry
($DE9D) this project found and then explicitly *un*-confirmed as
"verb 6" two rounds ago, on the grounds that it was an isolated
coincidence with no supporting pattern from other commands. **This
time it's different: this is a real, repeated, breakpoint-confirmed
hit during actual OPEN processing, not a static address coincidence.**
Disassembling $DE9D properly this time (correctly aligned, past a
couple of header-looking bytes) shows genuinely coherent code:

```
$DEA4: LD IX,($A013)
       SET 5,(IX+5)     ; <- sets bit 5 of the confirmed record's field +5
       OR 1; RET
...
$DEB6: LD IX,($A013)
       RES 5,(IX+5)     ; <- clears the same bit
       OR 1; RET
```

**This is a shared OPEN/CLOSE implementation** - one pair of generic
routines that any object's own small action-list can reference (via
the 4-byte sub-entries above), rather than every openable object
needing its own custom handler. It also gives real meaning to a flag
this project found gating the containment-chain walk ($C86E, several
rounds ago) but never explained: **bit 5 of field +5 is "is this thing
currently open"** - which is exactly the condition you'd want to gate
"can you see/reach what's inside this container" on. Two previously
separate, unexplained findings from different rounds turn out to be
the same flag.

A third chunk in the same disassembled region ($DECB-$DED8) touches
field +$0F (the confirmed room-number field) and field +1, copying in
a value from $A035 (a "default target position" variable seen
elsewhere) - plausibly a generic "move this into/onto something"
handler, not yet confirmed as thoroughly as the open/close pair.

**Corrected understanding of $AA71**: not a verb-number table in the
naive sense (that hypothesis was tested and failed two rounds ago),
and not the main per-turn dispatcher (that's $CB2C, fully traced last
round) - it is a **library of shared, generic action implementations**
(open, close, and likely others), referenced by small index values
that individual objects' own compact action-lists point into. Most
commands don't touch it at all because most objects have their own
direct handler (via the `(IY+2)/(IY+3)` pointer, dispatched straight
through $CB2C); $AA71 is specifically for behaviour that's the *same*
across many different objects, so it's implemented once and shared.

**Not yet confirmed**: the third ($DECB) chunk's exact purpose, entry
1's ($9A99) real role now that "TAKE" is confirmed not to reach it,
and how an object's own action-list decides whether to use its own
custom handler or fall through to a shared $AA71 entry.

## Follow-up: mapped several more $AA71 entries - a real action library

Broadened the same test (breakpoint $C960, log the index, try many
commands) across sixteen more commands. Several more indices came back
with clean, repeatable, real hits:

```
index 8  ('GET OUT'):     $E432
index 9  ('SIT'):         $E40A
index 11 (INVENTORY, WAIT, STAND UP): $E2C7
index 12 (INVENTORY, SEARCH SOFA):    $E3EA
```

Disassembling each (past a small header of the same kind entries 1 and
6 had) confirms a real, coherent pattern:

**Index 9 (SIT)**: `LD IY,($A017); LD A,($A034); LD (IY+1),A` - takes
the cached full record for the current actor and sets *its own* field
+1 (the same field the containment-chain walker, $C86E, follows as
"what contains me") to the target furniture's id. Sitting in something
is implemented as "you are now contained by it" - the exact same
mechanism as an item being inside a box, reused for a person sitting in
a chair.

**Index 8 (GET OUT)**: `LD IY,($A013); LD A,(IY+1); LD IY,($A017); LD
(IY+1),A` - reads the *target* furniture's own field +1 (i.e. whatever
contains the furniture - the room it's in) and copies that into the
current actor's field +1. Getting out of a chair is "you are now
contained by whatever contains the chair" - the natural inverse of
SIT, built from the same containment field.

**Index 11 (a shared generic fallback, used by three very different
commands)**: does a small self-modifying-code trick (stores a computed
byte into the address immediately before its own code, `$E2C6` - flagged
explicitly per this project's own commenting standard, since it's
exactly the kind of thing that's confusing to a reader unless called
out), then loads a *fixed* address, `$F2B6`, into DE and calls a tail
routine that swaps the current actor/target ids into the position
variables ($A034/$A035) before printing. Read as: **a generic "swap in
the current actor/target and print a stock message" handler** - which
would explain why `WAIT` (which just prints "You wait." verbatim),
`INVENTORY`, and `STAND UP` (when not sitting, presumably falling
through after a more specific check fails) all reach the same code:
none of them need custom logic beyond "print this canned response".

**Not yet confirmed**: index 12's exact behaviour (seen with `INVENTORY`
and `SEARCH SOFA` together - plausibly a second, related generic
response, not yet disassembled in full), what the self-modified byte at
$E2C6 is actually used for afterwards, and what $CBA7 and $DD0E (called
from several of these entries) do.

**Updated picture of $AA71 as a whole**: entries found so far - 1
(unconfirmed reachability), 6 (open/close), 8 (get out), 9 (sit), 11
(generic message fallback), 12 (unconfirmed detail) - are consistent
with a genuine, coherent **shared action library**: a modest set of
common behaviours (successfully verified now for at least four
distinct ones) that many different objects and commands reference
rather than reimplementing, exactly the kind of space-saving reuse
`discovery.md` predicts for this style of engine, now demonstrated
with real, repeatable evidence rather than a single coincidence.

## Follow-up: $CBA7, a shared guard-check called from both SIT and GET OUT

Both $E40A (SIT) and $E432 (GET OUT) call $CBA7 first. Disassembled it:

```
$CBA7: LD A,($B934)
       BIT 6,A
       RET Z              ; bit clear: no problem, continue normally
       POP HL             ; bit set: discard the return address...
       XOR A
       LD ($A027),A
       LD HL,$681A         ; ...print this fixed message...
       CALL $A59F
       JP $DC15             ; ...and jump to the shared failure point
```

Read as a shared **pre-condition guard**: check a flag at $B934 (bit 6)
before letting SIT or GET OUT proceed, and if it's set, print a fixed
message and bail out via the same shared failure point ($DC15) this
project has seen several other entries use. $B934 is the same byte
this project's $B91F investigation found being set from a caller's A
register a few rounds ago (`LD ($B935),A` nearby, `LD (B934)` here) -
not yet tied together into a full account of what condition this flag
tracks, but confirmed as a real, shared guard rather than a one-off.

**Not yet confirmed**: what sets bit 6 of $B934, and therefore what
specific condition blocks sitting/getting out (a reasonable guess -
already carrying/holding something incompatible, or already engaged in
a different action - is just a guess, not tested).

## Follow-up: $D008 is part of an already-known accessor family

Finally examined $D008 (called from the confirmed per-actor dispatch
bridge, $CC78). It turns out to belong to the same small utility
block this project already documented (`overlay_01_boot.py`'s $D045,
"get the player's room") - $D008 through $D04E is one compact set of
get/set accessors for an entity record's fields +3/+4 (a 16-bit value)
and +6 (a byte), all built on the same comparison primitive ($CFB6),
with several genuine external entry points into the middle of the same
block ($D008, $D026, $D03B, $D045 are all real, separately-reached
addresses, not one linear routine with internal fallthrough by
accident).

```
$D008: read record IY's fields +4/+5, compare via $CFB6 against
       record IY's own +3; if equal, cache record IX's +3/+4/+6
       into $9FD6/$9FD7
$D026: the inverse - compare a cached value against $9FD7, and if
       different, write it back into record IX's own +3/+4/+6
$D03B: a plain setter - write A/HL straight into record IY's +3/+4/+5
$D045: (already confirmed) get the player's room via $9860/$D495
```

Read together: a small "cache and conditionally sync" mechanism for
whatever fields +3/+4/+6 hold on an entity record (still not
confirmed what they represent, beyond the room-number field being a
different one, +$0F). Not a new structural discovery on its own, but
it closes out the last previously-unexamined routine on the per-actor
NPC-dispatch path this project traced several rounds ago.

## Session 2026-11-05

The verb and action system, the dictionary, the things and the rooms
are now decoded from their data by `dictionary.py`, `objects.py` and
`rooms.py`, each following the code that reads the format, and are
written up block by block in `overlay_04_actions.py` and
`overlay_06_rooms.py`. Corrections to earlier entries are marked
CORRECTED in the overlays (and in the README's 2026-11-05 section).
The key results:

- Containment is one field: +1 of a thing's record is what it is in or
  held by. TAKE sets target.+1 = actor; SIT/GET INTO sets actor.+1 =
  chair; GET OUT sets actor.+1 = chair.+1.
- Size (+2) is three things depending on what the thing is: its bulk,
  how much a container holds (fit check $DEE4), and for a passage how
  big an actor may be to get through ($DD35). The player and Watson are
  96, so a passage of 69 (a police man) or 85 (the hidden door to the
  opium den) stops them.
- A room's exits are (direction, thing in the way, destination).
  Destination 0 is scenery: $D448 skips it, so the description
  mentions it ("To the east there is a deep stream") but it's never a
  visible or usable exit.
- Door things are shared between buildings and so is their open state
  (bug: one front door for three houses).


## 2026-11-07: the plan-script language

The actor table at $9860 (8-byte records: +0 id, +1/+2 script position,
+3 plan verb, +4/+5 plan direct/indirect object) gives each of 24
actors a script. $CC78 runs one instruction per actor per turn. Opcode
in the low nibble of the first byte; bit 7 = success address follows,
bit 4 = failure address follows, bit 5 = erase after success (no script
uses it), bit 6 = busy (refuse the player's requests). Opcodes:
1 DO verb, 2 DO verb dobj iobj, 3 RUN record, 4 ASK person TO verb dobj
iobj, 5 SAY TO person message, 6 PRINT message, 7 RUN record dobj iobj,
8 SIGNAL actor, 9 AWAIT actor, A RETURN FAIL, B RETURN OK, C unused
(would hang), D/F PASS, E GOTO. Argument bytes $FA-$FD are the plan's
verb, the actor itself, and the plan's indirect and direct objects.
Success ends the actor's turn; failure tries the next instruction at
once, up to ten times. Checks-only action records (flags bit 7) are
sub-scripts, entered with a call frame ($CF80) and left with RETURN.
Verbs 128-140 ($9FAB) are only for scripts. Tools: tools/plan.py,
tools/allplans.py. Verified by a 106-turn fetch trace (every fetched
address decoded).
