# Dictionary/vocabulary notes (Phase 3, partial)

## What's solidly verified

**The per-letter index table lives at $5D80** - i.e. right at the very
start of the "p" block, which `sna2ctl.py`'s automatic execution trace
had guessed was *code* (it isn't reachable from any keypress-driven
playthrough, so it never got marked, and its raw bytes disassemble as
nonsense - `NOP`, garbage `LD` instructions, a stray `DEFB $DD` - exactly
the "garbage from decoding data as code" smell `discovery.md` warns
about). This is corrected in `game.ctl`/`game.skool` were we had time to
splice it in; **treat the very start of the block as data, not code,
generally**, until the whole extent of this table is properly bounded
and marked.

Found by tracing the real tokenizer (starts around $D9C5, called while
parsing typed input): the very first thing it does with the current
word's first letter is

```
LD A,(HL)      ; first letter of the word, plain ASCII (e.g. 'n' = $6E)
AND $1F        ; low 5 bits: for any letter, this gives 1-26 (A=1..Z=26)
                ; directly from ASCII, no separate pack/unpack needed
RLCA           ; x2 (each table entry is a 2-byte pointer)
LD L,A
LD H,$00
LD BC,$5D80    ; the table's base
ADD HL,BC
LD E,(HL)
INC HL
LD D,(HL)      ; DE = a 16-bit value, 0 if this letter has no entries
```

Confirmed by decoding all 26 letters' entries this way and finding they
are **clean and monotonically increasing** (`a` -> offset $0001, `b` ->
$00A7, ... `z` -> $09F5), exactly what you'd expect from an
alphabetically-organised dictionary where each letter's words are stored
contiguously. This alone is strong confirmation the table location and
formula are both right, independent of fully cracking the entry format
below.

The offsets are relative to a second base, **$5DBF** (confirmed by the
`LD HL,$5DBF; ADD HL,DE` immediately following, in three separate places
in the tokenizer/comparison code) - so a letter's first word record sits
at `$5DBF + offset`.

**A stemming/suffix table lives at $A85C**, 16 entries x 4 bytes,
selected by the low nibble of a word-record's first byte (`AND $0F`;
value `$0F` means "no suffix"; otherwise `RLCA;RLCA` (x4) indexes into
this table). The first 9 entries spell out real English inflections,
confirmed just by looking at the bytes as ASCII - no interpretation
needed:

```
0: "S"        3: "\x08IES"   6: "ED"
1: "ES"       4: "D"         7: "\x08ING"
2: "IES"      5: "ING"       8: "LY"
```

The `\x08` (backspace) entries are a neat trick: "\x08ING" means "delete
the stem's last letter, then append ING" - i.e. how a stem like `hop`
(silent-e or consonant-doubling aside) or `mov` becomes `moving` rather
than `moveing`. This table almost certainly serves **both** the parser
(matching a typed inflected form like "examining" against a stored stem
"examine") **and** the message printer (grammatically correct verb
endings in printed text, e.g. "Watson takes the pipe" vs "you take the
pipe") - `message-rendering.md` specifically calls out dynamic suffix
handling as something worth watching for, and this looks like exactly
that mechanism, shared by both directions.

Entries 9-15 of that table do **not** look like plain text (`^#~#`,
mostly high-bit-set garbage) - either the meaningful range really is
only 0-8 and 9-15 are something else entirely (a different table
happening to sit right after, or non-suffix flag combinations that are
rare enough this project didn't happen to trigger them), or there's a
wrinkle in the indexing not yet accounted for. **Not resolved** - stated
here rather than glossed over.

## What's not yet resolved

**SUPERSEDED - see "MAJOR CORRECTION" below.** Everything in this
section turned out to be caused by bugs in the tests used to check it,
not by a real architectural difference. Left in place as the record of
what was tried and why it looked, at the time, like a real dead end.

Tried to call the game's own word-expansion routine directly (found at
$A94D, which chains $A95B - copy literal/synonym-flagged letters into a
scratch buffer at $5C42 - then $A92F - append the suffix from the table
above) to reconstruct spelled-out dictionary words programmatically,
the same way `message-rendering.md` recommends for message text. This
did **not** produce clean results: most calls returned an empty string,
and a few produced text-looking-but-wrong fragments. Likely causes,
untested:

- The routine may need additional registers/state set up by its real
  caller that a raw "jump straight to $A94D" call skips (unlike GET-KEY,
  which turned out to be safely callable in isolation, this one may not
  be).
- The per-letter table's entries may not be a simple flat list of N
  words terminated by a zero word - watched real gameplay (typing
  "TAKE" and breakpointing the comparison routine at $DA7D) and got
  **zero hits at all**, and a write-watch on the $5C42 scratch buffer
  during the same real parse also saw **zero writes** - meaning the
  code path actually used to recognise "TAKE" during real play is
  *not* the one traced statically here. There is more than one
  word-lookup mechanism in this engine, or the one traced is used for
  something else (abbreviation/synonym resolution specifically, rather
  than the everyday case), and the everyday path hasn't been found yet.

**Next step for anyone continuing this**: repeat the "breakpoint the
comparison, log what actually gets hit" approach that worked well
elsewhere in this project (see `harness_notes.md`), but starting from
the *tokenizer's entry point* ($D9C5) itself while parsing a real
command, rather than assuming which downstream routine matters and
breakpointing that. Log every CALL target visited between $D9C5 being
entered and the tokenizer returning a word-class byte - that will show
the *real* control-flow graph for word lookup, rather than the
plausible-but-apparently-wrong one written up above for the synonym/
abbreviation-comparison machinery.

## MAJOR CORRECTION: the original dictionary-matching hypothesis was right

Did exactly the suggested next step - and it reversed the "ruled out"
conclusion above. That earlier test had the *same* bug this project
has now hit more than once: forgetting to `step_over_breakpoint()` on
the entry breakpoint itself before single-stepping onward, which
leaves the emulator stuck re-trapping on the same instruction forever
without executing anything. Once fixed, single-stepping from $D9C5
while typing `TAKE` produces exactly the call sequence this project
originally read statically and then wrongly abandoned:

```
$D9D4 -> CALL $DAC6   (special-character check)
$D9D9 -> CALL $DA34   (the confirmed per-letter dictionary index lookup)
$D9F5 -> CALL $A94D   (word expansion - stem + suffix)
  $A950 -> CALL $A95B
  $A97C -> CALL $A990  (x4)
  $A954 -> CALL $A92F  (append the suffix)
$D9FF -> CALL $DA7D   (the comparison routine)
```

...repeating for each candidate word under the same first letter.
Breakpointing $DA7D directly (this time with the bug fixed) and
logging both buffers on each hit, while typing `TAKE`, gives:

```
candidate @ $6646: typed="ake"  expanded="able"   (mismatch: k vs b)
candidate @ $664A: typed="ake"  expanded="akeS"   (prefix match!)
candidate @ $664E: typed="ake"  expanded="alkS"   (mismatch: k vs l)
```

`typed` is "ake", not "take" - exactly as expected, since the per-letter
index lookup ($DA34, confirmed since early in this project) has
already narrowed the search to 't'-words using the first letter, so
only the *remaining* letters need comparing. The dictionary's own
stored data expands to "able", "akeS", "alkS" for three neighbouring
't'-words - almost certainly TABLE, TAKES, and TALKS - confirming, with
real bytes rather than a plausible story, that:

- the dictionary really does store **stems, not whole words** (a `t`
  is implicit from the index lookup; what's left, "ake", is stored and
  expanded, not "take" in full)
- the **suffix-expansion mechanism genuinely works** ($A94D and its
  sub-calls correctly reconstruct "akeS" from a stem plus a suffix
  table entry) - the earlier standalone test of this same routine
  (see the very first section of this file) that produced empty or
  garbled strings was calling it in isolation without the setup its
  real caller provides, not a sign the routine itself is broken
- "ake" against "akeS" is exactly the **abbreviation/prefix matching**
  this project's very first reading of $DA7D predicted (comparing only
  up to the shorter length) - confirmed with real data, not asserted
  from reading the comparison loop alone

**This reverses the "not resolved" framing earlier in this file.** The
original, very first pass at this dictionary (the per-letter index
table, the suffix table, the $DA7D comparison and synonym-chain logic)
was correct. What was actually wrong was the *test* used at the time to
check it, not the architecture itself - a useful reminder, in the same
spirit as the harness bugs documented in `harness_notes.md`, that a
disconfirming result deserves the same scrutiny as a confirming one
before being written up as settled.

**Still open**: exactly which candidate wins (does the "akeS" match
get accepted, and does the game then correctly land on "TAKE" as the
recognised verb, stripping the trailing "S" it doesn't need?), and how
a verb id/number - the kind this project separately found feeding the
$AA71 table - gets produced from a successful dictionary match. That
connection (dictionary entry -> verb number) is the one piece of the
"single most valuable link" this project has been chasing all session
that is *still* not directly observed, even now.

## Follow-up: the dictionary-to-verb-number link is confirmed - TAKE is verb 5

Traced the tokenizer's return value all the way to its caller ($D6CE,
which does `LD HL,$5B00; CALL $D9C5; CP $D0; JP Z,...; CP $C0; JR
NZ,-10` - i.e. call the tokenizer, and retry if the class byte isn't a
recognised noun ($D0) or verb ($C0)). Typing `TAKE` alone and tracing
through this retry loop directly, three calls happen in sequence
before it succeeds:

```
call 1: returns D=$30, E=$05
call 2: returns D=$B0, E=$05
call 3: returns D=$C0, E=$05   <- accepted (matches the caller's CP $C0)
```

**E stays fixed at 5 across all three calls** - only D (the
class byte) changes. Read as: the tokenizer resolves "TAKE" to word
index 5 immediately, but offers it under a *sequence* of possible
classes (an unexplained $30, then $B0 - the punctuation-class value
this project found much earlier - then $C0, verb) until the caller's
own `CP` tests accept one. **Confirmed real, not just plausible**: the
$AA71 table's entry #5 (`$AA71 + (5-1)*2`) resolves to $E003, and
disassembling it (from a couple of bytes in, past what looks like the
same kind of small header verb 1's entry had) shows genuinely coherent
"take an object" logic:

```
$E008: CALL $E03A      ; (with A=0 first, A=1 on a second path)
$E00B: LD IX,($A013)
$E00F: LD (IX+1),0
$E013: LD A,($A00A)
$E016: LD (IX+$0F),A   ; ($0F is the confirmed room-number field!)
$E019: OR 1; RET
```

and `$E03A` itself:

```
$E03A: LD C,A                    ; C = 0 or 1, from the caller
       LD A,($A036)              ; A036 = the target object's id
       CALL $CC0E                ; find its record (confirmed primitive)
       LD (IY+0),C               ; overwrite field +0 with 0 or 1
       LD IY,($A017)
       LD A,C
       CALL $D237                ; re-resolve via the confirmed chain
       LD ($A017),IX
```

Read together: taking an object finds its compact record (via the
already-confirmed $CC0E), marks it (field +0 becomes 0 or 1 - very
plausibly "held by the player" vs some other state, not yet certain
which), and updates the object's *full* state record's room field
(offset +$0F, the same room-number field this project confirmed for
actors) to the player's current room (`$A00A`) - i.e. "this object is
now wherever I am", exactly what taking something should do.

**This confirms**: TAKE is verb #5 in the $AA71 table, the dictionary-
match-to-verb-number link is real (word index 5, carried in E, is
what the $AA71 table is indexed by - not literally "verb number" in
the sense of a single global mapping, but the specific per-class word
index the tokenizer returns), and the verb's handler code performs
sensible, coherent object-taking logic using entirely already-confirmed
building blocks from elsewhere in this project. This is about as solid
a capstone as a single session's testing can give without also
independently confirming what field +0 being 0 vs 1 means (a "held by
player" vs "held by someone else" guess, not yet tested).

**Not yet confirmed**: what the $30/$B0 class-attempt sequence
before $C0 actually represents (candidate classes tried in a fixed
order? something about "TAKE" specifically having multiple possible
parses?), and what field +0 being set to 0 vs 1 precisely means.

## MAJOR CORRECTION: $E003 is never actually reached - the above was wrong

Went to verify the "0 vs 1" question from the previous section by
breakpointing $E003 directly during a real, successful `TAKE LAMP`.
**Zero hits.** Tried again with a much larger patience budget, with
bare `TAKE` (the exact command the previous section's trace used),
and with several other candidate addresses at once - all zero hits at
$E003, every time. Confirmed the test methodology itself was sound by
checking real output was captured correctly alongside it (`You take
the oil lamp.` - the command genuinely succeeds) and that a real,
alternative dispatch point ($CB2C, the computed-jump mechanism this
project found several rounds earlier) *does* fire, 22 times, for the
exact same command.

**This means the previous section's central claim - "TAKE is verb #5,
traced from typed input to handler" - does not hold up.** What was
actually confirmed there: the tokenizer genuinely resolves "TAKE" to
class $C0 (verb) and word-index 5 (real, re-verified, still stands).
What was **not** actually confirmed, despite being written as if it
was: that word-index 5 is used to look up $AA71's table, or that
$AA71's entry 5 ($E003) is ever executed. That step was inferred from
"the table entry's address happens to contain code that reads like
sensible TAKE logic" - a coincidence of plausible-looking bytes, not
a traced execution path. This is exactly the mistake `verification.md`
warns about most: a coherent, satisfying story that was never actually
run.

**What real testing shows instead**: the actual per-turn dispatch for
a full command (verb + noun both resolved) goes entirely through the
already-confirmed $CB2C/$CB40 computed-jump mechanism, landing on a
long sequence of addresses mostly in the $Dxxx-$Fxxx range (`$D6CE`
itself among them - the very noun/verb classification loop being
called *as one of the dispatch targets*, suggesting parsing and
per-candidate action-checking are unified into one generic "try this"
loop, not separate phases) - none of which is $E003, and none of
which obviously corresponds to $AA71's table by address either.

**Corrected picture**: the dictionary-to-verb-number link (word ->
class + index) is real and confirmed. What that index actually gets
used for is genuinely still open - possibly the $AA71 table serves an
entirely different purpose (a message lookup? a canonical-name
lookup for printing "I don't know the verb X"-style errors, given
this project separately confirmed such error messages exist?) than
"the verb's own action handler", which was an assumption, not a
finding. The real per-turn action dispatch mechanism ($CB2C, confirmed
real since several rounds ago) is a separate, still not fully mapped,
system.

**A note on how this happened, for anyone reading this project's
notes as a case study**: the error was not a broken test producing a
false negative (the pattern behind several of this project's other
corrections) - it was a false positive, reached by *not testing a
step at all* and describing it with the same confident language as
the steps that genuinely were tested. The lesson, stated plainly: a
plausible-looking coincidence (an address computed one way lining up
with code that reads sensibly) is not the same evidence as a traced
execution path, and both this file and the overlay should be read
with that distinction in mind for every claim, not just this one.
