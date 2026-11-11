"""
Overlay: the boot/entry sequence, keyboard input, screen clear, and the
low-level text printer.

Everything in this file has been checked in the emulator (see
harness_notes.md for the harness itself and how each routine's contract
was confirmed), not just read from the disassembly. Anything not yet
checked this way is called out explicitly rather than stated as fact.
"""

import sys
sys.path.insert(0, '.')
from build_skeleton import blk, C, fact


# --------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------

blk(0xA040, 'c', 'Start the game',
    ["The game's own entry point (the tape loader jumps here once "
     "everything is loaded - see loader_notes.md). Clears two flag "
     "bytes, resets the stack to $5D80 (reusing the loader's own "
     "workspace, which is no longer needed), and clears the screen.",
     "Then it waits for a single keypress to choose New Game vs "
     "Continue: pressing 'n' or 'N' starts a new game (clears a flag "
     "at $A011); anything else leaves that flag set, and the code "
     "that follows loads state back from a table at $9860, so this is "
     "very likely also how a restored/continued game resumes its "
     "characters' positions (not yet confirmed with an actual saved "
     "game in hand - see verification.md's 'say which things are "
     "verified' guidance).",
     "Seeds a simple RNG from the Z80 refresh register (R) - a common "
     "period-accurate trick, since R free-runs on every instruction "
     "fetch and so is effectively unpredictable at the moment the "
     "player first presses a key.",
     "Then walks a sentinel-terminated table of 8-byte records at "
     "$9860 (field +0 is the sentinel/id byte, $FF marks the end; "
     "field +3 and the 16-bit field +6/+7 are also read here). This "
     "is almost certainly the game's character/actor table - each "
     "record's shape here (an id byte, a type-like byte, a stored "
     "16-bit value) matches the general 'sentinel-terminated table of "
     "fixed-size records' pattern from discovery.md. Cross-referenced "
     "since this was first written - see overlay_02_world_model.py "
     "and world_model_notes.md.",
     "CORRECTION, added after further testing: this walk is NOT "
     "boot-only, despite appearing inside the game's entry-point "
     "routine. It is genuinely re-entered on every turn (confirmed by "
     "breakpointing deep inside it during a real, ordinary command "
     "well after boot, and seeing it step through the same $9860 "
     "records again) as part of per-actor turn processing - see "
     "world_model_notes.md's 'the boot sequence is also the per-turn "
     "NPC-processing loop' section for the full chain. Only the "
     "instructions before this point (DI, the stack reset, the RNG "
     "seed, the New-vs-Continue prompt) are genuinely one-time; this "
     "walk itself is shared, reentrant code."],
    comments={
        0xA040: "Clear the 'currently examining' flag",
        0xA041: '',
        0xA044: "Clear another one-shot flag",
        0xA047: 'No interrupts while we set things up',
        0xA048: 'Clear the screen and set up the text window',
        0xA04B: "Stack now safely below the game's own code/data",
        0xA04E: "Wait here for the player's very first keypress",
        0xA051: "Did they press lowercase 'n'?",
        0xA053: '',
        0xA055: "...or uppercase 'N'?",
        0xA057: 'Default: treat as "continue" (flag = 1)',
        0xA059: '',
        0xA05B: '"New game" was chosen instead (flag = 0)',
        0xA05C: '',
        0xA05F: 'A = the free-running refresh register...',
        0xA061: '...used as an unpredictable RNG seed',
        0xA064: '',
        0xA065: 'One-shot guard, cleared here',
        0xA068: 'Immediately re-read (see prose above: not yet',
        0xA06B: 'explained why - possibly reused, boilerplate-looking,',
        0xA06C: 'code also called from elsewhere with the flag already set)',
        0xA06E: 'Not yet explored - called once during boot',
        0xA071: 'Not yet explored - called once during boot',
        0xA074: 'IY -> first record of the actor table',
        0xA078: "This record's field +3 ...",
        0xA07B: '...is it the specific value $32?',
        0xA07D: 'If not this actor, skip to the next record',
        0xA07F: "Poll for a key (non-blocking this time)",
        0xA082: 'Was one waiting?',
        0xA084: '',
        0xA086: "Specifically, was it ENTER ($0D, bit 7 set = $8D)?",
        0xA088: '',
        0xA08A: 'Fetch a stored 16-bit value from $9FDD...',
        0xA08D: "...and copy it into this actor's own record (fields +6/+7)",
        0xA090: '',
        0xA093: 'Restart the walk from the first record',
        0xA097: "This record's sentinel/id byte (field +0)...",
        0xA09A: '...was it $FF (end of table)?',
        0xA09B: 'If not the end, loop back and check the next actor',
        0xA09D: '(record continues past the end of this excerpt)',
    })

fact('boot-actor-table',
     'The $9860 actor-table walk is reentrant, not boot-only',
     "First confirmed in the emulator simply as 'execution reaches "
     "this during boot' - true, but incomplete. Later testing (see "
     "world_model_notes.md) confirmed the same walk is genuinely "
     "re-entered on every turn, as part of per-actor turn processing, "
     "not solely at startup. The individual field meanings beyond "
     "what's confirmed in overlay_02_world_model.py (a handler address "
     "at +1/+2) are still open - this remains a starting anchor for "
     "object/room/character table discovery, not a finished account "
     "of it.")


# --------------------------------------------------------------------
# Screen clear + text window setup
# --------------------------------------------------------------------

blk(0xC10F, 'c', 'Set the border, then clear the screen and attributes',
    ["Sets the border to white, then fills the whole display file "
     "(6,144 bytes at $4000) with zero and the whole attribute file "
     "(768 bytes at $5800) with $38 (INK 0 / PAPER 7: black on white, "
     "no bright, no flash) - i.e. a standard CLS.",
     "Confirmed in the emulator: hooking every write to screen memory "
     "during boot shows exactly 6,144 writes at this routine's first "
     "LDIR and 767-768 at its second, matching the display and "
     "attribute file sizes exactly."],
    comments={
        0xC10F: 'White border while we clear the screen',
        0xC111: '',
        0xC113: 'HL, DE = display file, one byte apart (for the LDIR fill)',
        0xC116: '',
        0xC119: 'BC = 6144, the whole display file',
        0xC11C: 'Seed the first byte with 0...',
        0xC11E: '...then copy it across the rest',
        0xC120: 'BC = 767, the rest of the attribute file',
        0xC123: 'Seed the first attribute byte (black on white)...',
        0xC125: '...then copy it across the rest',
        0xC127: '',
    })

blk(0xC142, 'c', 'Reset the print position and clear to a blank window',
    ["A small init routine: clears the 'alternate window' flag at "
     "$C128, then calls the screen-and-attributes clear above and "
     "resets the print cursor bookkeeping (row count $C1F5, screen "
     "address $C1F6/7, column-shift $C1FB) ready for a fresh page of "
     "text. Called once during boot (from $A048's caller) and again "
     "whenever the text window needs to restart from the top (see "
     "$C306's 'page full, wait for a key, then clear' logic below)."],
    comments={
        0xC142: 'Not currently in the (narrower) alternate window mode',
        0xC143: '',
        0xC146: "Loop counter for the routine this falls into (36 = ",
        0xC148: "full-width window's line count)",
        0xC14A: 'Clear the screen',
        0xC14D: '',
        0xC14F: 'Reset: 36 lines left before the next page-wait',
        0xC152: '',
        0xC155: 'Reset the print position to the top of the text window',
        0xC158: '',
        0xC15A: 'Reset the column sub-pixel shift to 2',
    })


# --------------------------------------------------------------------
# Keyboard input
# --------------------------------------------------------------------

blk(0xC400, 'c', 'Shared RET/POP tail, reused by a joystick-port routine',
    ["Just `POP DE; POP HL; RET` - this only exists as a landing spot "
     "that $C412 jumps into (see below); it is never itself CALLed. "
     "Flagging this explicitly per commenting-style.md's guidance on "
     "tail reuse: whatever calls into the routine at $C403 sometimes "
     "needs to bail out early with two extra values already popped, "
     "and rather than duplicating that pop/pop/ret sequence, the code "
     "jumps straight into the middle of what would otherwise look "
     "like a completely unrelated 3-byte routine."])

blk(0xC403, 'c', 'Read a Kempston-style joystick port, debounced',
    ["Reads I/O port $FB (bit-inverted per the b=3-based SBC A,A/AND "
     "trick at $C403-$C409, a common idiom for turning 'is B < 3' into "
     "an all-0s/all-1s mask) and waits for the port to settle before "
     "reading it again at $C40C, then returns on a specific bit "
     "pattern (RET M) or loops (JR NC) waiting for one.",
     "One branch of that loop falls through to `JP $0F12` at $C412 - "
     "a jump to a low address below our loaded code, which we haven't "
     "explained (dead/leftover code from a shared original codebase, "
     "or a genuine hardware/ROM-dependent path, are both plausible; "
     "not yet confirmed either way - flagged rather than guessed, per "
     "verification.md). Not yet establishied whether real play ever "
     "reaches this branch."])

blk(0xC415, 'c', 'GET-KEY, but block until a key is actually pressed',
    ["A thin blocking wrapper: repeatedly calls the real GET-KEY at "
     "$C41F, ignoring the 'no key' result, until bit 7 of the return "
     "value is set - then masks that bit off and returns the plain "
     "ASCII code. Used wherever the game needs to pause for 'press a "
     "key to continue' (e.g. the page-wait logic in the print-window "
     "routine below), as opposed to the non-blocking poll used "
     "elsewhere (e.g. in the boot sequence above)."],
    comments={
        0xC415: 'Ask if a key is available',
        0xC418: 'Was one?',
        0xC41A: 'No: keep asking',
        0xC41C: 'Yes: strip the "a key was pressed" tag, keep just the ASCII',
        0xC41E: '',
    })

blk(0xC41F, 'c', 'GET-KEY: has the player pressed a key?',
    ["Saves IY/IX/HL/DE/BC, points IY at the standard system-variable "
     "area ($5C3A), then does EI; HALT; DI - i.e. waits for exactly "
     "one interrupt, which is where a real Spectrum's ROM would "
     "normally have scanned the keyboard into FLAGS/LAST-K.",
     "Checks FLAGS bit 5 (\"a new key is waiting\"); if not, returns "
     "A=0. If a key is waiting, clears that bit, reads LAST-K (the "
     "ROM's already-decoded ASCII value), remaps three ROM editing-key "
     "codes (an underscore-shaped delete-left key, and two others) "
     "onto plainer control codes the game's own line editor expects, "
     "calls a small helper at $C240 (not yet examined), then sets bit "
     "7 of A before returning - so the caller's contract is: A=0 means "
     "no key, A = ASCII|$80 means this key was pressed.",
     "Called from three places, all real CALL instructions: $A080 "
     "(non-blocking poll during boot), $A53B, and $C416 (from the "
     "joystick-read wrapper above).",
     "Confirmed in the emulator: this is the only place in the whole "
     "41,600-byte block that reads FLAGS/LAST-K at all, and there are "
     "zero raw `IN A,($FE)`-style port reads anywhere in the block, "
     "so this is genuinely the game's one and only keyboard entry "
     "point, not just a convenient guess. See harness_notes.md for "
     "how this was verified by hooking it directly and recovering "
     "legible printed game text."],
    comments={
        0xC41F: 'Save every register this routine touches',
        0xC421: '',
        0xC423: '',
        0xC424: '',
        0xC425: '',
        0xC426: 'IY -> system variables, as ROM interrupt code expects',
        0xC42A: 'Let exactly one interrupt happen...',
        0xC42B: '...(this is where the keyboard actually gets scanned)',
        0xC42C: '',
        0xC42D: 'Was a new key flagged as available?',
        0xC430: '',
        0xC432: '',
        0xC434: 'No: return with A=0',
        0xC435: '',
        0xC437: 'Yes: consume the "new key" flag',
        0xC439: '',
        0xC43C: 'A = the key, already decoded to ASCII by the ROM',
        0xC43F: "Is it the ROM's DELETE-key code?",
        0xC441: '',
        0xC443: '...remap it to a plain backspace',
        0xC445: 'Is it this other ROM editing code?',
        0xC447: '',
        0xC449: '...remap it too',
        0xC44B: 'Is it this third ROM editing code?',
        0xC44D: '',
        0xC44F: '...remap it to \'[\'',
        0xC451: 'Not yet examined',
        0xC454: 'Tag the result: bit 7 set means "a key was pressed"',
        0xC456: 'Restore every saved register',
        0xC457: '',
        0xC458: '',
        0xC459: '',
        0xC45B: '',
        0xC45D: '',
    })

# --------------------------------------------------------------------
# Text printer
# --------------------------------------------------------------------

blk(0xC388, 'c', 'PLOT-CHAR: draw one character glyph at HL, shifted by C',
    ["The genuine low-level character printer. Computes the source "
     "glyph address as A*8 + $3C00 - which is exactly the real 128K/"
     "48K ROM's own character-bitmap layout (space, code 32, sits at "
     "$3D00 = $3C00 + 32*8), confirming A is a plain ASCII code here, "
     "not some internal token.",
     "For each of the glyph's 8 pixel rows, shifts the byte right by "
     "C bits (carrying into the next screen byte, via the 'or c' "
     "merge at $C3B0/$C3CD) so that text can be printed at any pixel "
     "column, not just 8-pixel-aligned ones - this is why the routine "
     "is more involved than a plain 1:1 glyph copy.",
     "This has no real ROM font table to read from in this project's "
     "emulator harness (see harness_notes.md), so glyphs render as "
     "blank pixels there - but the routine still faithfully receives "
     "the real character codes, which is what matters for recovering "
     "message text: hooking A at this address is how every piece of "
     "game text quoted in this disassembly (the opening room "
     "description, parser responses, etc.) was actually captured, "
     "per message-rendering.md's guidance to call the real printer "
     "rather than hand-decode bytes."],
    comments={
        0xC388: 'Save everything - A is the character to plot',
        0xC389: '',
        0xC38A: '',
        0xC38B: '',
        0xC38C: 'HL = A (as a word)',
        0xC38D: '',
        0xC38F: 'HL = A * 8...',
        0xC390: '',
        0xC391: '',
        0xC392: '...plus the font table base ($3C00: the ROM layout)',
        0xC395: '',
        0xC396: 'DE = this glyph\'s address; HL = the screen position',
        0xC397: '',
        0xC398: '',
        0xC399: '8 pixel rows to plot',
        0xC39B: 'Fetch this row of the glyph',
        0xC39C: '',
        0xC39D: '',
        0xC39E: 'Is the column-shift zero (byte-aligned print)?',
        0xC39F: '',
        0xC3A0: '',
        0xC3A2: 'Fast path: no shifting needed',
        0xC3A4: 'Shift the glyph byte right by the column offset...',
        0xC3A6: '...building a matching mask alongside it',
        0xC3A8: '',
        0xC3A9: '',
        0xC3AB: '',
        0xC3AC: '',
        0xC3AD: 'Clear the bits this glyph will occupy...',
        0xC3AE: '',
        0xC3AF: '...and merge the shifted glyph bits in',
        0xC3B0: '',
        0xC3B1: 'Restore the row counter',
        0xC3B2: '',
        0xC3B3: 'Fast-aligned path rejoins here (from the sign-flag branch above)',
        0xC3B4: '',
        0xC3B5: '',
        0xC3B7: 'Remaining shift = 8 - column offset (the overflow into',
        0xC3B8: 'the next screen byte)',
        0xC3B9: '',
        0xC3BB: '',
        0xC3BC: '',
        0xC3BD: '',
        0xC3BE: 'Shift the glyph byte left by that remaining amount...',
        0xC3C0: '...building a matching mask alongside it',
        0xC3C2: '',
        0xC3C4: '',
        0xC3C5: '',
        0xC3C7: '',
        0xC3C8: '',
        0xC3C9: '',
        0xC3CA: 'Move to the next screen byte along',
        0xC3CB: 'Clear the bits this glyph will occupy there...',
        0xC3CC: '',
        0xC3CD: '...and merge the overflow bits in',
        0xC3CE: 'Move back (net: one screen byte to the right overall)',
        0xC3CF: '',
        0xC3D0: '',
        0xC3D1: 'Next pixel row down',
        0xC3D2: '',
        0xC3D4: 'Restore caller\'s registers',
        0xC3D5: '',
        0xC3D6: '',
        0xC3D7: 'C = the new column-shift for the next character:',
        0xC3D8: 'add the glyph width (7 wide, since 1 col overlaps)...',
        0xC3DA: '...wrapping back into 0-7 and bumping the screen',
        0xC3DC: '...column (inc L) when it does',
        0xC3DE: '',
        0xC3E0: '',
        0xC3E1: '',
        0xC3E2: 'Restore the flags this routine was called with',
        0xC3E3: '',
    })

fact('print-char-verified',
     'PLOT-CHAR ($C388) recovers real game text without a ROM',
     "Confirmed in the emulator: setting a breakpoint on $C388 and "
     "reading A each time (rather than trying to render real pixels, "
     "which needs the ROM font this project doesn't have) reproduces "
     "legible game text directly, e.g. the opening scene: \"Mon "
     "08:00am ... The sun streams in the two broad windows in your "
     "sitting room...\". This is the harness's main tool for message-"
     "rendering going forward (per message-rendering.md).")

blk(0xC37D, 'c', 'Advance the screen address by one text row',
    ["Small helper: adds 32 to L (one row down within an 8-row-tall "
     "character cell block on the Spectrum's interleaved screen "
     "layout), carrying into H (+8) when L overflows - i.e. the "
     "standard 'next pixel line, same column' address step."])

blk(0xC2BA, 'c', 'Print one character (or handle a newline) at the cursor',
    ["The routine PLOT-CHAR's caller: restores the persisted cursor "
     "position/column-shift from $C1F8/$C1FA, and either plots the "
     "passed-in character directly (calling PLOT-CHAR via $C2EE), or, "
     "if the character is a carriage return ($0D), advances the line "
     "counter and - once a full page has been printed (see the 15-"
     "line 'page wait' check the caller at $C306 makes) - waits for a "
     "keypress and clears the window before continuing.",
     "This, plus PLOT-CHAR and the page-wait wrapper at $C306, forms "
     "the game's whole low-level text-output path: every piece of "
     "printed text - room descriptions, parser responses, dialogue - "
     "goes through here one character at a time.",
     "CONFIRMED, not just asserted: an earlier pass in this project "
     "breakpointed this exact address during a real LOOK command and "
     "got zero hits, which was written up (honestly) as an unresolved "
     "worry rather than a disproof. Re-run later with the bug in that "
     "test fixed, the same breakpoint produces 170 real hits during a "
     "single LOOK, with a real, traceable caller chain leading back "
     "through the print gatekeeper at $C1E1 - see "
     "world_model_notes.md's 'room-text print path is resolved' "
     "section for the full account, including what the original bug "
     "was."])

blk(0xC306, 'c', 'Page-wait: flash the cursor, wait for a key, clear',
    ["Called once $C1F5's line-remaining counter reaches zero (a full "
     "page has been printed): sets bit 7 of the attribute byte just "
     "past the last printed line (a crude 'flashing prompt' cue, "
     "since bit 7 of a Spectrum attribute byte is FLASH), blocks for "
     "a keypress via the GET-KEY wrapper at $C412, clears the flash "
     "bit again, then calls the window-reset routine at $C142 to "
     "clear the screen and start a fresh page."],
    comments={
        0xC306: 'Save HL (the print position)',
        0xC307: 'HL -> the attribute byte for the prompt line',
        0xC30A: 'Turn on FLASH there, as a "press a key" cue',
        0xC30C: 'Block here until the player presses something',
        0xC30F: 'Turn FLASH back off',
        0xC311: 'Clear the screen and reset the text window',
        0xC314: 'Restore HL',
        0xC315: '',
    })
