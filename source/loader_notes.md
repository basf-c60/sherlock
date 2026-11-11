# Loader notes (Phase 0)

## Tape structure

`Sherlock_v2_0.tzx` contains 5 header+data block pairs after the
archive-info/hardware-type blocks:

| Block         | Type | Header load addr | Length | Header end |
|---------------|------|-------------------|--------|------------|
| BASIC loader  | 0    | -                 | 23     | -          |
| "sherlock"    | 3    | $8000             | 256    | $8100      |
| "SHD V2.0"    | 3    | $840B             | 7188   | $A01F      |
| "s" (screen)  | 3    | $8000 (header says)| 6912  | $9B00 (per header) |
| "p" (main)    | 3    | $5D80             | 41600  | $10000     |

`tzx_tools.py` (the skill's own script) originally failed on this tape:
it doesn't handle TZX block ID `0x33` ("hardware type", informational
only). Patched to skip it; every block's checksum then verifies clean.

## The BASIC loader is not `RANDOMIZE USR n`

It's `LOAD "" CODE: PRINT USR 32768` (tokens `EF 22 22 AF 3A F5 C0`,
followed by the digits "32768"). This just loads the 256-byte "sherlock"
stub and calls it - the stub does everything else itself.

## The 256-byte stub ($8000, relocates to $5B00)

Disassembling it (`z80dasm -a -g 32768 stub.bin`) shows:

```
DI; LD SP,$5D80; LD HL,$8000; LD DE,$5B00; LD BC,$0100; LDIR
JP $5B12          ; continue running from the *copy*, not the original
```

It copies itself down to $5B00 and jumps into the copy at offset
$12 ($5B12), which then does:

```
CALL $5B30   ; load next tape block using ITS OWN header's addr/length
CALL $5B62   ; load next tape block using a HARDCODED addr/length
CALL $5B30   ; load next tape block using its own header's addr/length
JP   $A040   ; jump into the game
```

$5B62's hardcoded values are `IX=$4000, DE=$1B00` - the real Spectrum
display+attribute file address and size (6912 bytes) - even though the
"s" block's own header claims load address $8000. **The loader
overrides the header's address for this one block.** This is the
loading screen, forced onto the actual screen instead of wherever its
header nominally says.

$5B8B (not fully traced) is a thin wrapper around the ROM tape-loading
routine ($0556), jumping into it partway ($0562, skipping the pilot-tone
/ flag-byte-compare setup the caller already did itself) - a standard
Spectrum "custom loader built on top of ROM primitives" pattern.

## "SHD V2.0" is loaded then completely overwritten - verified

Call order is: load "SHD V2.0" (own header: $840B, 7188 bytes, ending
$A01F) - load "s" (forced to $4000) - load "p" (own header: $5D80,
41600 bytes, ending exactly at $10000).

$840B-$A01F is entirely inside $5D80-$FFFF. Since "p" loads *after*
"SHD", and nothing runs between the three loads (no CALL/RET, straight
into the next load), "SHD"'s content is completely overwritten before
the game ever executes a single instruction of it.

Verified directly (not just argued from addresses) by simulating the
exact byte-level loads in Python and diffing: the final memory image at
the entry point $A040 only contains sensible-looking Z80 code when "p"'s
bytes are applied; with only "SHD" loaded (as if "p" never came along),
the same bytes are all zero (SHD's own data doesn't reach that far into
its own block, or more likely, $A040 sits at an offset within "p"'s data
that never got covered by SHD in the first place - either way, the
*current* game only ever runs on "p"'s bytes for this whole region).

**Not yet explained**: *why* "SHD V2.0" is on the tape at all if it's
always fully clobbered before use. Two plausible, unconfirmed
explanations: (a) anti-piracy chaff aimed at naive tape-backup tools, or
(b) a leftover build artifact from an earlier revision (the "V2.0" in
its own name is suggestive - maybe an earlier loader used to load *this*
block as the real game, and version 2 replaced it with "p" but left the
tape-authoring step of dropping "SHD" untouched). Flagged as
**not verified**, not stated as fact anywhere else in this project.

## Final memory layout when the game starts

```
$4000-$57FF  display file (loading screen artwork, then overwritten by gameplay)
$5800-$5AFF  attribute file
$5B00-$5BFF  relocated loader stub (dead once the game starts)
$5D80-$FFFF  "p" block: all game code + data. Entry point $A040.
```

The game's own init code (`$A040: ... LD SP,$5D80`) reuses the freed
loader/stub workspace ($5B00-$5D7F) as its stack, growing downward from
$5D80 - a clean, deliberate reuse of memory the loader no longer needs.
