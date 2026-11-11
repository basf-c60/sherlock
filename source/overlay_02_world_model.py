"""
Overlay: world-model groundwork (Phase 3, partial). See
source/world_model_notes.md and source/dictionary_notes.md for the full
write-up, including honest open questions this overlay doesn't resolve.
"""

import sys
sys.path.insert(0, '.')
from build_skeleton import blk, fact, bug

blk(0xCC0E, 'c', 'Find the actor record whose id matches C',
    ["A plain linear search over the sentinel-terminated array of "
     "8-byte actor/character records at $9860 (see the boot sequence "
     "in overlay_01_boot.py, where this table was first found): given "
     "an id in C, walks the table 8 bytes at a time until either "
     "field +0 matches (found - IY left pointing at that record) or "
     "field +0 is $FF (not found).",
     "This is the routine that turns the loose 'we saw code walk a "
     "table shaped like this' observation from the boot sequence into "
     "a confirmed, general-purpose accessor: it's called from four "
     "separate places in the code ($CC3D, $DDA3, $E03E, $E300 - all "
     "genuine CALL instructions, found by searching for the literal "
     "bytes CD 0E CC), which is real cross-reference evidence this is "
     "a widely-used 'look up an actor' primitive, not a one-off."],
    comments={
        0xCC0E: 'Record size is 8 bytes',
        0xCC11: '',
        0xCC14: 'IY -> first actor record',
        0xCC18: "This record's id byte...",
        0xCC1B: '...is it the one we want?',
        0xCC1C: '',
        0xCC1E: '...or have we hit the end-of-table sentinel?',
        0xCC20: '',
        0xCC22: 'Neither: move to the next record',
        0xCC24: '',
        0xCC26: '',
        0xCC27: '',
        0xCC28: '',
    })

fact('actor-table-record-size',
     'The actor table at $9860 has confirmed 8-byte records',
     "Confirmed two ways: (1) $CC0E's own search step advances by "
     "literally `LD DE,$0008; ADD IY,DE` between candidates, and (2) "
     "separately, the boot-sequence code and two other real writers "
     "found by watching actual memory writes during a room move "
     "(around $CEA0-$CEDE and $D020-$D059) between them touch offsets "
     "+0 (id), +1/+2, +3/+4, +5, and +6/+7 of a record - i.e. every "
     "byte of an 8-byte record is accounted for as genuinely read or "
     "written by real code, not just assumed from the search step's "
     "stride. The individual meaning of fields +1 through +5 is not "
     "yet determined - see source/world_model_notes.md.")

bug('reversed-two-word-verb-error',
     "Two-word verb error messages print with the words reversed",
     "Confirmed by actually typing commands in the emulator: `GET UP` "
     "produces `I DO NOT KNOW THE VERB\" UP GET\"` - the second word "
     "printed before the first. Single-word unknown verbs (`STAND`, "
     "`SCORE`, `HELP`) are not affected, and `ASK ... ABOUT ...` is "
     "not affected either (its two words print in the order typed). "
     "Not yet traced to a specific routine or explained; recorded "
     "here as a genuine, player-visible behaviour rather than "
     "speculated about further.")


# --------------------------------------------------------------------
# The confirmed "get actor's room number" accessor chain
# --------------------------------------------------------------------

blk(0xD34E, 'c', 'Find a 3-byte record by id, in a sentinel-terminated table',
    ["Same shape as $CC0E's actor-table search, but for 3-byte records "
     "(1 id byte + a 16-bit value) instead of 8-byte ones: given a base "
     "in IX and an id in A (via B), walks the table until a record's "
     "id matches (found) or reads $FF (end of table). Uses the shadow "
     "register set (EXX) internally so it doesn't disturb the "
     "caller's own BC/DE/HL while searching."],
    comments={
        0xD34E: 'Switch to the shadow registers to work in',
        0xD34F: 'Record size is 3 bytes',
        0xD351: 'HL -> the table base the caller passed in IX',
        0xD353: '',
        0xD354: 'B = the id we are looking for',
        0xD355: '',
        0xD357: "This record's id byte...",
        0xD358: '...does it match?',
        0xD359: '',
        0xD35B: '...or is it the end-of-table sentinel?',
        0xD35D: '',
        0xD35F: 'Neither: move to the next 3-byte record',
        0xD360: '',
        0xD363: 'Found (or ran off the end): IX -> this record',
        0xD364: '',
        0xD366: 'Set Z if we actually found it (vs. hit the sentinel)',
        0xD368: 'Back to the normal registers',
        0xD369: '',
    })

blk(0xD237, 'c', "Resolve an id (in A) to its full entity record",
    ["Looks the id up in the 3-byte index table at $8B6F (via $D34E "
     "above), which gives back a *pointer* to the entity's real, full "
     "record - one level of indirection past the compact index. Some "
     "register-juggling here (push/EX (SP),HL/pop) nets IX = that "
     "stored pointer on return; it looks unnecessarily roundabout on "
     "the page, but running it and checking IX directly confirms "
     "that's exactly what it does.",
     "Confirmed by calling this routine directly for ids 0-3 and "
     "dumping the records it resolves to: all four are 17 bytes long "
     "and laid out back-to-back in memory (0x8CBA, 0x8CCB, 0x8CDC, "
     "0x8CED), all starting with the same tag byte ($01) that $D495 "
     "(below) checks for. See source/world_model_notes.md for the "
     "full record dumps and what's confirmed about their fields."])

blk(0xD495, 'c', "GET-ACTOR-ROOM: what room is actor A currently in?",
    ["Resolves the id via $D237, confirms the resolved record's own "
     "type tag is $1 (i.e. it really is this kind of record, not "
     "something else living at the same id), and returns the byte at "
     "offset +15 of it. Returns $FF for an invalid id, or if the "
     "resolved record isn't type 1.",
     "Confirmed empirically, not just by reading the code: called "
     "this directly with A=0 while the player was in the sitting "
     "room and got $08 back; moved the player north into the small "
     "closet in the real game and called it again - got $09; moved "
     "back south - got $08 again. This is genuinely 'what room is "
     "this actor in', not a guess from the byte offset alone."],
    comments={
        0xD495: 'Invalid id ($FF)?',
        0xD497: '...then just say so',
        0xD498: 'Resolve the id to its full record',
        0xD49B: 'Is this really an actor/character record (tag $01)?',
        0xD49D: '',
        0xD4A0: '...no: fail',
        0xD4A2: '',
        0xD4A3: 'Yes: the room number lives at offset +15',
        0xD4A6: '',
    })


# --------------------------------------------------------------------
# A real message-printing loop - confirmed genuine, but NOT the one
# room descriptions use (see source/world_model_notes.md for the
# breakpointing that ruled it out, and the honest account of what
# still isn't known about the room-text path).
# --------------------------------------------------------------------

blk(0xC1CB, 'c', 'Print a message: plain ASCII, last byte has bit 7 set',
    ["A short, self-contained loop: read a byte, strip bit 7, print "
     "it (via the gated entry at $C1FD), then check whether the "
     "*original* byte (before stripping) had bit 7 set - if so, that "
     "was the last character of the message and the loop stops; "
     "otherwise it advances and repeats.",
     "This is genuinely real code - confirmed by finding all four of "
     "its actual callers ($C070, $C09C, $C0EA, $C1C0), not assumed "
     "from reading alone. What it is NOT, also confirmed rather than "
     "assumed: the path room descriptions or parser responses take. "
     "Breakpointing this address directly during a real `LOOK` "
     "command in the emulator produced zero hits. Its callers, and "
     "what kind of message actually goes through this simpler, "
     "uncompressed format, haven't been identified yet - see "
     "source/world_model_notes.md."],
    comments={
        0xC1CB: 'A = this message byte, with the terminator bit stripped',
        0xC1CC: '',
        0xC1CE: 'Print it',
        0xC1D1: 'Did the ORIGINAL byte have the terminator bit set?',
        0xC1D3: '...then that was the last character - stop',
        0xC1D4: 'Else: next byte',
        0xC1D5: '',
        0xC1D7: '',
    })

fact('get-actor-room-confirmed',
     "$D495 confirmed as 'get actor A's current room number'",
     "Confirmed empirically: called with A=0 while the player was in "
     "the sitting room, got $08 back; moved the player north into the "
     "small closet in the real, running game and called it again - "
     "got $09; moved back south - got $08 again. The underlying "
     "record format (17 bytes, resolved through a 3-byte id->pointer "
     "index table at $8B6F) is also confirmed by dumping four "
     "consecutive real records - see source/world_model_notes.md.")


# --------------------------------------------------------------------
# The main per-turn action dispatcher - confirmed real (one genuine
# caller, cross-referenced), though the dispatch table itself (what
# fills HL before the jump) is not yet located. See
# source/world_model_notes.md for the surrounding turn-cycle context
# this was found within (the room-change check that follows it).
# --------------------------------------------------------------------

blk(0xCB2C, 'c', 'Dispatch to a handler routine via a computed jump',
    ["Loads IX and IY from a saved 'action context' ($CB28/$CB2A), "
     "calls through to a plain `JP (HL)` at $CB40, then stores "
     "whatever IX/IY the handler left behind back into $CB28/$CB2A. "
     "So IX/IY persist from one dispatched handler to the next, like "
     "a pair of global registers - the caller's own IX/IY are not "
     "protected. $CB34 is a second entry point that skips the load "
     "(used by the action-record interpreter at $C9EB to run a "
     "record's pre-check routine with the current IX/IY).",
     "CORRECTED: an earlier version of this entry (and its line "
     "comments) said the routine 'saves the caller's IX/IY and "
     "restores them afterwards' - exactly backwards. `LD IX,($CB28)` "
     "loads IX from memory; `LD ($CB28),IX` stores it. Caught on a "
     "re-read with a working disassembler, per verification.md item 5 "
     "('re-derive register roles from a fresh trace').",
     "Confirmed as a genuinely real, deliberate mechanism (not "
     "misdecoded data) by finding its one real caller ($CA64, via the "
     "literal bytes CD 2C CB) and by the coherence of what surrounds "
     "that call - it sits in what looks like the main per-turn command "
     "loop, immediately followed by a check for whether the player's "
     "room changed as a result of whatever just got dispatched to.",
     "UPDATED: what loads HL before this call is now fully traced, "
     "correcting the guess in the previous paragraph (that it would "
     "be 'the verb/action dispatch table' - it isn't). $CA64 is "
     "itself called, once per candidate, from the same per-candidate "
     "walk this project found much earlier via $C9C0 (the fixed "
     "5-entry table at $9927, then a command-specific candidate, then "
     "a long shared tail); HL comes from that candidate's own record "
     "fields (the (IY+2)/(IY+3) pattern found at $C9E3), not from the "
     "$AA71 table. See source/world_model_notes.md's 'unifying "
     "several previously-separate threads' section for the full, "
     "now-closed trace."],
    comments={
        0xCB2C: "Load the action context's IX...",
        0xCB30: '...and IY',
        0xCB34: 'Run the handler (second entry point: keep current IX/IY)',
        0xCB37: 'Save whatever IX the handler left as the new context...',
        0xCB3B: '...and IY',
        0xCB3F: '',
        0xCB40: 'HL must already hold the real target address',
    })

fact('action-dispatcher-found',
     "Found the main per-turn action dispatcher (computed JP (HL))",
     "$CB2C saves IX/IY, jumps through HL via a plain `JP (HL)` at "
     "$CB40, then restores IX/IY. Confirmed real by finding its one "
     "genuine caller, $CA64, which turned out to be sitting in what "
     "looks like the main per-turn command-processing routine - "
     "immediately followed by a check (via the already-confirmed "
     "$D495 'get actor's room' accessor) for whether the player's room "
     "changed as a result. UPDATED (see the 'unifying several "
     "previously-separate threads' section of world_model_notes.md): "
     "what loads HL has since been fully traced - $CA64 is itself "
     "called once per candidate from the per-candidate walk this "
     "project found via $C9C0, and HL comes from that candidate's own "
     "record fields, not from a separate global dispatch table.")


# --------------------------------------------------------------------
# The verb dispatch table itself - confirmed real by checking that
# every one of its first 20 entries is a valid in-range address, and
# that at least one (verb 1) genuinely disassembles as real code.
# --------------------------------------------------------------------

blk(0xC960, 'c', "Look up a numbered entry in the table at $AA71",
    ["Given a number in (IX+1), computes $AA71 + (that number - 1)*2 "
     "and reads a 16-bit value from there - a plain, direct-indexed "
     "table lookup, not a search.",
     "Confirmed real: dumped the table's first 20 entries and every "
     "one is a valid address inside the loaded 'p' block. They fall "
     "into two distinct bands - roughly $9Axx and $Exxx - and checking "
     "one entry from each band shows the $9Axx one is genuine "
     "executable code (a real CALL and a real JP Z appear at the very "
     "start of it, 2 bytes in - the first 2 bytes look like they "
     "double as a small header), while the $Exxx ones checked so far "
     "don't look like straight code - more likely a smaller, more "
     "compact per-entry record of some kind. Not yet resolved which; "
     "see source/world_model_notes.md.",
     "IMPORTANT, and corrected from an earlier draft of this comment: "
     "(IX+1) is NOT simply 'which verb the player typed'. Breakpointing "
     "this address during real play shows the exact same value (11, "
     "with IX fixed at $8F08) firing after LOOK, INVENTORY, and TAKE "
     "alike - three different verbs - but never after an unrecognised "
     "command, and OPEN additionally fires a completely different "
     "value (6, IX=$90E5) three times *before* that same 11/$8F08 "
     "check. The cleaner reading, not yet fully confirmed: IX points "
     "at whichever record is currently being tested (a fixed, generic "
     "one at $8F08 that every successfully-parsed command checks at "
     "the end, plus an object-specific one - $90E5, very possibly the "
     "door object itself - tried while resolving which specific thing "
     "OPEN applies to), and the number at +1 is that record's own "
     "'primary action' field - exactly discovery.md's 'an action-"
     "number byte immediately precedes this address' pattern, just "
     "keyed per-record rather than globally per-verb. See "
     "source/world_model_notes.md for the tests behind this."],
    comments={
        0xC960: 'The number to look up (meaning depends on IX - see prose)',
        0xC963: '',
        0xC964: '',
        0xC966: "The table's base",
        0xC969: '',
        0xC96A: '(number-1) * 2, added twice for a word-sized stride',
        0xC96B: '',
        0xC96C: "This entry's own table value...",
        0xC96D: '',
        0xC96E: '...becomes the result',
        0xC96F: '',
    })

fact('verb-table-found',
     "Found the table at $AA71 - but it's not simply 'verb number'",
     "Direct-indexed (not searched): entry N sits at $AA71 + (N-1)*2, "
     "a plain 16-bit value. Confirmed real by checking that all of "
     "the first 20 entries are valid addresses inside the loaded game "
     "block, and that at least one (entry 1, $9A99) genuinely "
     "disassembles as real executable code rather than being a "
     "misread coincidence. CORRECTED after further testing: the index "
     "isn't simply 'which verb the player typed' - breakpointing "
     "confirms the exact same index (11) fires for three different "
     "verbs (LOOK, INVENTORY, TAKE) alike, but never for an "
     "unrecognised command, while OPEN additionally triggers a "
     "different index (6) three times first. See "
     "source/world_model_notes.md for the full account and the "
     "current best reading (a per-record 'primary action number', "
     "not a global verb id).")


# --------------------------------------------------------------------
# A small, static "always checked every turn" table - confirmed by
# finding its bytes directly in the file and matching them exactly
# against what a live breakpoint trace showed. See
# source/world_model_notes.md for the full trace that led here.
# --------------------------------------------------------------------

blk(0x9927, 'b', 'A fixed table of 5 "checked every turn" entries',
    ["Five records, each exactly 5 bytes: a constant $99,$13 header, "
     "a 16-bit address, and a trailing flag byte ($23 for the first "
     "three records, then $2D, then $37). The data stops fitting this "
     "shape immediately afterwards, so the table is exactly these 5 "
     "entries, not a longer list.",
     "Confirmed real by cross-referencing a live emulator trace against "
     "these literal file bytes, not the other way around: breakpointed "
     "the routine that consumes these entries ($C9C0, reached via a "
     "\"push a value, then JP\" idiom rather than a real CALL - which "
     "is why grepping for a caller found nothing) across five different "
     "real commands from five fresh game instances, and every single "
     "one started with the exact same 5 addresses in the exact same "
     "order, before diverging per-command. Searching the file for the "
     "first of those addresses as literal bytes found exactly one hit, "
     "landing on this table.",
     "Not yet determined: what these five checks actually do (a "
     "scheduled NPC remark, the clock, a random event and a game-over "
     "check are plausible guesses, not confirmed), or what the "
     "trailing flag byte means beyond the observation that it's the "
     "same value for the first three entries and different for the "
     "last two."])

fact('always-checked-table-found',
     "Found the static table behind the 5 'checked every turn' entries",
     "$9927: five 5-byte records ($99,$13,<16-bit addr>,<flag byte>), "
     "confirmed by finding the literal bytes of the first entry's "
     "address in the file and matching all five entries exactly "
     "against a live breakpoint trace taken independently, across "
     "five different real commands (each from a fresh game instance). "
     "What the five checks are for, and what the varying flag byte "
     "means, are not yet determined - see source/world_model_notes.md.")

fact('verb-number-hypothesis-double-checked',
     "The 'OPEN = verb 6' coincidence did not hold up - correction",
     "While tracing the table above, one of the five commands "
     "tested (OPEN) happened to produce a command-specific address "
     "that matched the $AA71 table's entry #6 exactly. Before treating "
     "that as confirmation, checked whether the other four commands' "
     "own command-specific addresses appeared *anywhere* in the first "
     "400 entries of the same table - none did. A single coincidental "
     "match out of five, with no supporting pattern from the other "
     "four, is not evidence; recorded here specifically so this near-"
     "miss doesn't get treated as confirmed in a future session. The "
     "actual source of the command-specific and shared-tail entries "
     "seen in that trace is still unidentified.")


# --------------------------------------------------------------------
# The per-actor turn-processing bridge - confirmed real, found while
# chasing why the boot-sequence actor walk turned out to be reentrant
# (see the correction in overlay_01_boot.py and the full chain in
# source/world_model_notes.md).
# --------------------------------------------------------------------

blk(0xCC37, 'c', 'Resolve the current actor and set up room-comparison state',
    ["Given an actor id in A: clears a flag at $CC0B, resolves the id "
     "to its full state record via the already-confirmed $CC0E, "
     "stashes that record's pointer at $9FDB and the id itself at "
     "$A036, calls $B91F (not yet examined), then gets this actor's "
     "current room (via the already-confirmed $CC29/$D495 chain) and "
     "the player's own current room (via the already-confirmed "
     "$D045). On failure to resolve the id, clears $A01F and returns "
     "early instead.",
     "Confirmed real and genuinely on the per-turn NPC-processing "
     "path: this is called (via $CC5A) from $CC78, which is itself "
     "called from inside the actor-table walk that overlay_01_boot.py "
     "originally described as boot-only - see world_model_notes.md "
     "for how that walk was shown to be reentrant, and the correction "
     "now recorded there and in this project's boot-sequence notes."])

blk(0xCC78, 'c', "Dispatch to the current actor's own handler",
    ["Calls into $CC5A (the tail of $CC37 above, reusing its room-"
     "comparison setup), reloads the current actor's resolved record "
     "pointer from $9FDB, calls $D008 (not yet examined), then reads "
     "a 16-bit value from that record's own offsets +1/+2 - a handler "
     "address, on the same pattern as the (IY+2)/(IY+3) handler "
     "lookup found earlier in this project (see the $CB2C dispatch "
     "mechanism above). Not yet traced past this point to confirm "
     "exactly how that address gets used (almost certainly the same "
     "computed-jump dispatch, given the pattern, but not confirmed)."],
    comments={
        0xCC78: "Resolve this actor's room vs the player's room",
        0xCC7B: "Reload this actor's own state record",
        0xCC7F: 'Not yet examined',
        0xCC82: "This actor's own handler address...",
        0xCC85: '...(continues past this point, not yet traced)',
    })

fact('npc-turn-processing-confirmed',
     "The actor-table walk is per-turn NPC processing, not boot-only",
     "A real correction to earlier work in this project: the $9860 "
     "actor-table walk documented in overlay_01_boot.py as part of "
     "the game's boot sequence is genuinely re-entered on every turn "
     "(confirmed by breakpointing deep inside it during an ordinary "
     "command well after boot and seeing it re-walk the same table). "
     "Traced the mechanism as far as $CC37/$CC78/$CC0E/$CC29/$D045: "
     "for each actor, resolve its full state record, compare its room "
     "to the player's, and read a handler address out of the record's "
     "own fields - a real, coherent NPC-behaviour system. See "
     "source/world_model_notes.md for the full chain and what is "
     "still unconfirmed (chiefly: how the main loop re-enters the "
     "walk in the first place, and what $B91F/$C821/$D008 do).")


# --------------------------------------------------------------------
# The print gatekeeper - confirmed real and correctly located this
# time (an earlier attempt at this exact routine, described only in
# prose notes rather than the overlay, used a misaligned disassembly
# window and guessed the wrong start address; this entry uses the
# address confirmed by two independent real call targets, JP $C1E1
# and CALL $C1E1). See source/world_model_notes.md for the full story.
# --------------------------------------------------------------------

blk(0xC1E1, 'c', 'Print gatekeeper: check two flags, then dispatch',
    ["Checks $5C3C first (a flag this project has not fully explained "
     "- 'printer echo' is a guess, not confirmed - but which is never "
     "zero in this project's emulator, since there's no real ROM to "
     "set it, meaning some code paths that check it will always take "
     "their 'disabled' branch here); if it's zero, returns "
     "immediately, printing nothing.",
     "If $5C3C is set, checks $A027 (the same flag this project has "
     "found gating the shared echo/word-buffer routine at $A9B7): "
     "when $A027 is zero, jumps straight to $C2BA to print the "
     "character normally; when $A027 is set, falls through into a "
     "case-folding and quote-tracking region (around $AA12-$AA50, not "
     "fully traced) that eventually calls back into $C2BA anyway.",
     "Confirmed as the real entry point (correcting an earlier, "
     "prose-only attempt at this same routine that guessed a slightly "
     "wrong start address from a misaligned disassembly window) by "
     "finding two genuine, independent call targets landing exactly "
     "here: $AA11 (`JP $C1E1`) and $AA41 (`CALL $C1E1`)."],
    comments={
        0xC1E1: 'Save the character to print',
        0xC1E2: 'Is output enabled at all right now?',
        0xC1E5: '',
        0xC1E6: '',
        0xC1E8: 'No: print nothing',
        0xC1E9: '',
        0xC1EA: 'Are we in the other, quote/case-folding mode?',
        0xC1ED: '',
        0xC1EE: '',
        0xC1F0: 'No: print the character the plain way',
        0xC1F1: '',
    })

fact('room-text-path-resolved',
     "Resolved: the room-text print path, and a false alarm explained",
     "Earlier in this project, breakpointing $C2BA during a real LOOK "
     "command got zero hits, and was written up honestly as an "
     "unresolved worry. That was a bug in the test, not a real "
     "property of the game: re-run cleanly, the same breakpoint "
     "produces 170 real hits with a real, traceable caller chain back "
     "through a print gatekeeper at $C1E1 (found via two independent "
     "confirmed call targets, resolving an address this project had "
     "previously only guessed at from a misaligned disassembly "
     "window). The full confirmed pipeline: $C1E1 (gatekeeper) -> "
     "case-folding/quote logic -> $C2BA (CR handling) -> $C388 "
     "(PLOT-CHAR). See source/world_model_notes.md for the complete "
     "account, including exactly what the original test bug was.")


# --------------------------------------------------------------------
# $B91F - confirmed empirically as intro/setup-only, correcting the
# previous round's tentative framing of it as part of the ongoing
# per-turn NPC loop. See source/world_model_notes.md for the test.
# --------------------------------------------------------------------

blk(0xB91F, 'c', 'Find a record by id in the $9FF0 table (setup-only)',
    ["Same shape as this project's other id-search routines ($CC0E, "
     "$D34E): given an id, walks a table from $9FF0 until a matching "
     "id is found or a sentinel is hit.",
     "CONFIRMED, by testing rather than assuming from its caller "
     "($CC37, which is genuinely part of the per-turn NPC-dispatch "
     "chain documented elsewhere in this file): this specific routine "
     "only actually runs during the game's opening intro sequence. "
     "Breakpointed across boot (zero hits), the four ENTERs that step "
     "through the intro text (25 hits, with the searched-for id "
     "taking a scripted-looking, non-sequential sequence: 0, 2-6, "
     "104, 7-13, 31, 34, 36-43, 0), and an ordinary LOOK command well "
     "after the intro has finished (zero hits again). Read this as "
     "'validate/place these specific objects during setup', not as an "
     "ongoing per-turn check, even though the code that calls it "
     "($CC37) is also reachable from the genuine per-turn path via a "
     "different entry point ($CC5A) that skips over this call "
     "entirely."],
    comments={
        0xB91F: "The table's base",
        0xB923: 'Not yet examined',
        0xB926: '',
        0xB928: 'The id we are looking for',
        0xB92B: "This record's id...",
        0xB92E: '...does it match?',
        0xB92F: 'Neither: keep searching',
        0xB931: '(end of table reached, per whatever $A0F7 signals)',
        0xB933: '',
    })

fact('b91f-is-setup-only',
     "$B91F is intro/setup-only, not part of the ongoing per-turn loop",
     "A correction to last round's tentative framing. Breakpointed "
     "across boot (0 hits), the opening intro sequence (25 hits, with "
     "a scripted-looking, non-sequential id order: 0, 2-6, 104, 7-13, "
     "31, 34, 36-43, 0), and an ordinary LOOK command well after the "
     "intro (0 hits again). Reads as 'validate/place these specific "
     "objects during setup', even though the code that calls it "
     "($CC37) is genuinely reachable from the real per-turn NPC loop "
     "too, via a different entry point that skips this specific call.")


# --------------------------------------------------------------------
# Object/actor resolution and containment-chain walking - confirmed
# real by a genuine id catalog built from testing known present/absent
# objects (LAMP=22, ARMCHAIR=23/24, WATSON=3 - the last cross-
# confirming a room-based finding from several rounds ago). See
# source/world_model_notes.md for the full test results.
# --------------------------------------------------------------------

blk(0xC86E, 'c', "Follow an object's containment chain to its root",
    ["Resolves an id via $D237, then repeatedly follows a 'next id' "
     "held at the resolved record's own offset +1 (not a memory "
     "address - another id, resolved the same way each time), "
     "continuing while bit 5 or bit 3 of the new record's offset +5 "
     "is set, and stopping either when +1 is $FF or when bit 7 of +5 "
     "is clear. Read as 'find what ultimately contains this thing, "
     "walking up through however many levels of nesting' - a room "
     "contains a container, which contains an item, which an actor "
     "might be carrying.",
     "Bit 5 of offset +5 is now confirmed: it's 'is this thing open' "
     "(see $DE9D below, a shared OPEN/CLOSE implementation that sets "
     "and clears exactly this bit). That makes this routine's bit-5 "
     "check read naturally: keep following the chain (i.e. treat "
     "what's inside as reachable) only while each container along the "
     "way is open. Bits 3 and 7 are still not confirmed."])

blk(0xC821, 'c', 'Test whether object/actor A is here (visible to the player)',
    ["Resolves the id in A via $D237 and the current id in $A036 via "
     "$C863 (the containment-chain walker above), and compares them - "
     "essentially 'does this candidate's ultimate container match "
     "the thing in $A036 (usually the player, or the room being "
     "checked)'. Called from 12 real, confirmed sites across the "
     "code, among them the already-documented $CC64 (which uses the "
     "result to decide whether to enable output for an NPC's turn), "
     "which independently confirms this is a genuine 'is this visible "
     "/ present here' test rather than a guess from its name alone.",
     "Confirmed with a real id catalog, not just plausible-sounding "
     "prose: breakpointing this during known commands shows a "
     "stable, repeated id for objects that are actually present "
     "(LAMP -> 22, the two armchairs -> 23 and 24, WATSON -> 3), and "
     "only a handful of never-repeated ids for a typed object that "
     "isn't there (PIPE - not carried or in the room - gives up after "
     "5 hits with no stable id). id 3 for WATSON independently "
     "confirms a guess this project made several rounds earlier (that "
     "actor id 3, whose room this project separately found to match "
     "the player's, was 'very plausibly Watson') - see "
     "source/world_model_notes.md for the full account, including "
     "two lower-confidence results (SOFA, MONEY) that don't fit the "
     "clean pattern as neatly."])

fact('object-id-catalog',
     "Built a real object/actor id catalog via the visibility test",
     "Breakpointing $C821 (confirmed as an 'is this visible here' "
     "test) during known commands gives a stable, repeated id for "
     "things that are actually present: the oil lamp is id 22, 'your "
     "armchair' and 'watsons armchair' are ids 23 and 24, and Watson "
     "himself is id 3 - the last independently confirming a several-"
     "rounds-earlier guess from a completely different test (that "
     "actor id 3, whose room matches the player's, was 'very "
     "plausibly Watson'). Absent objects (a typed PIPE, not present) "
     "give up after a handful of hits with no stable id, which is "
     "itself part of the evidence this is a genuine presence test.")

fact('dispatch-mechanisms-unified',
     "Unified three previously-separate findings into one system",
     "$C9C0 (the per-candidate walk found early on), $CA64 (the "
     "per-turn command loop), and $CB2C (the computed-jump dispatcher) "
     "are confirmed to be one mechanism, not three: for each candidate "
     "in the per-candidate walk (the fixed 5-entry table at $9927, "
     "then a command-specific entry, then a long shared tail), $CA64 "
     "is called with IY pointing at that candidate, and dispatches via "
     "$CB2C to a handler address read from the candidate's own record "
     "fields. Confirmed by breakpointing both $CA64 and $CB2C during a "
     "real TAKE LAMP: $CB2C's one caller is $CA64 (22 times); $CA64's "
     "one caller is $C99C, with IY taking exactly the sequence "
     "$C9C0 was already known to walk, including the command-specific "
     "id ($DCC1) this project's id catalog had independently found "
     "for the same command several rounds earlier. This also confirms "
     "$AA71/$C960 is a genuinely separate system from this dispatch "
     "loop - what it's actually for remains open.")


# --------------------------------------------------------------------
# $AA71's entry #6 - a shared, generic OPEN/CLOSE implementation.
# Confirmed by breakpointing $C960 (the $AA71 lookup) during a range
# of real commands: it fires selectively (INVENTORY, DROP, OPEN - not
# LOOK, TAKE, movement, EXAMINE, TALK), and OPEN reliably produces
# index 6, whose disassembly is genuinely coherent. See
# source/world_model_notes.md for the full account, including why
# this differs from an earlier, explicitly debunked coincidence
# involving the same address.
# --------------------------------------------------------------------

blk(0xDE9D, 'c', 'Shared OPEN action ($AA71 entry #6, CLOSE is #7)',
    ["Confirmed real by breakpointing $C960 (the $AA71 table lookup) "
     "during a real `OPEN PLAIN DOOR` and seeing it reliably look up "
     "index 6 - this address - not as a static coincidence but as a "
     "repeated, live hit during real command execution.",
     "OPEN: `LD IX,($A013); SET 5,(IX+5)` - sets bit 5 of the target "
     "record's field +5. CLOSE is the next record, $AA71 entry #7 at "
     "$DEAF (an earlier version of this entry wrongly called it a "
     "'sub-entry' of #6): the same, but `RES 5,(IX+5)`. This confirms bit 5 of field "
     "+5 means 'is this thing open' - which also explains a flag the "
     "containment-chain walker ($C86E) was found checking several "
     "rounds earlier, without knowing what it meant.",
     "The chunk after CLOSE ($DEC1) is not part of this entry: it is "
     "the default action record for PUT IN / PUT ON / DROP IN (verbs "
     "38, 39 and 17, via the $9F38 table) - see overlay_04_actions.py.",
     "This is one entry in what's best understood as a small library "
     "of shared, generic action implementations that individual "
     "objects' own compact records can reference (rather than every "
     "openable object needing its own custom OPEN code) - see "
     "source/world_model_notes.md for how this reframes $AA71 as a "
     "whole, correcting the earlier 'verb dispatch table' guess."],
    comments={
        0xDEA4: "IX -> the target object's record",
        0xDEA8: 'Mark it open',
        0xDEAC: '',
        0xDEB6: "IX -> the target object's record",
        0xDEBA: 'Mark it closed',
        0xDEBE: '',
    })

fact('aa71-purpose-confirmed',
     "Found what $AA71 is actually for: a shared action library",
     "Breakpointing $C960 (the $AA71 lookup) across boot, the intro, "
     "and ten real commands shows it fires selectively. (CORRECTED: "
     "this originally said 'for INVENTORY, DROP and OPEN'; logging the "
     "actor id later showed the INVENTORY and DROP hits were NPCs - "
     "actor 2 hailing a cab, actor 31 doing GO TO - acting on the same "
     "turn, not the player's command.) OPEN reliably produces index 6, whose entry "
     "($DE9D) turns out to be a genuine, shared OPEN/CLOSE "
     "implementation (SET/RES bit 5 of a record's field +5), "
     "confirming what that bit means along the way. This corrects the "
     "'verb dispatch table' framing from two rounds ago (already "
     "known to be wrong) with something more specific: $AA71 is a "
     "small library of generic action implementations that individual "
     "objects' own records can reference, used only when an object "
     "doesn't need fully custom behaviour. See "
     "source/world_model_notes.md for the full account.")


# --------------------------------------------------------------------
# More $AA71 entries, mapped the same way as $DE9D above: breakpoint
# $C960 across many real commands, confirm which index fires, then
# disassemble that entry properly. See
# source/world_model_notes.md for the full test results.
# --------------------------------------------------------------------

blk(0xE40A, 'c', 'Shared SIT implementation ($AA71 entry #9)',
    ["Confirmed real by breakpointing $C960 during a real `SIT` "
     "command and seeing it reliably look up index 9 - this address.",
     "`LD IY,($A017); LD A,($A034); LD (IY+1),A` - sets the current "
     "actor's own record field +1 (the same field the confirmed "
     "containment-chain walker, $C86E, follows as 'what contains me') "
     "to the target furniture's id. Sitting in something is "
     "implemented as 'you are now contained by it' - the same "
     "mechanism used for an item being inside a box, reused here for "
     "a person sitting in a chair.",
     "Record header (decoded with the format from $C9BF, see "
     "overlay_04_actions.py): flags $78, pre-check routine $E3F5 "
     "(the shared guard $CBA7, then $DCA7, then the 'will it fit' "
     "tail at $DEE4), body at $E413.",
     "CORRECTED: an earlier version said a 'second sub-entry' follows "
     "at $E420. It isn't part of this entry: $E420 is entry #8 (GET "
     "OUT)'s pre-check routine, which entry #8's own header points "
     "at."])

blk(0xE432, 'c', 'Shared GET-OUT implementation ($AA71 entry #8)',
    ["Confirmed real the same way, via a real `GET OUT` command "
     "reliably producing index 8.",
     "`LD IY,($A013); LD A,(IY+1); LD IY,($A017); LD (IY+1),A` - reads "
     "the *target* furniture's own field +1 (whatever contains the "
     "furniture - the room it's in) and copies that into the current "
     "actor's field +1. Getting out of a chair is 'you are now "
     "contained by whatever contains the chair' - the natural inverse "
     "of SIT ($E40A above), built from the same containment field."])

blk(0xE2C7, 'c', 'Shared HAIL action ($AA71 entry #11)',
    ["CORRECTED - this entry previously called this 'a shared generic "
     "message/fallback handler reached by INVENTORY, WAIT and STAND "
     "UP'. Logging the actor and verb at each hit showed every one of "
     "those hits was actor 2 doing HAIL (verb 31) on object 30, which "
     "simply happened to run on the same turns as the player's "
     "commands. The player's INVENTORY/WAIT/STAND UP never reach it. "
     "It is reached through object action lists that map HAIL (and, "
     "for the same object, GET) to shared action 11 - see $8F06.",
     "Also CORRECTED: this entry previously described a 'self-"
     "modifying-code trick' storing into $E2C6. $E2C6 follows a RET "
     "at $E2C5 and is never executed - it is an ordinary one-byte "
     "variable kept just in front of the record, not code.",
     "Record header: flags $47 (bit 6: pre-check routine at $E298), "
     "byte 1 $10; body at $E2CB. The body remembers the player's room "
     "($A00A) and the target's id + 1 in $E2C6, calls $DD0E, then "
     "calls $E2EE with B = actor, C = target and DE = $F2B6, which "
     "puts the actor/target into $A034/$A035. Not yet traced past that "
     "point - what HAIL actually does to the cab is still open."],
    comments={
        0xE2CB: "Remember the player's room...",
        0xE2CF: "...and the target's id + 1, in the variable at $E2C6",
        0xE2D7: 'Not yet examined',
        0xE2DA: 'B = the actor doing the hailing',
        0xE2DE: 'C = the thing being hailed',
        0xE2E2: 'DE = $F2B6 (not yet identified)',
        0xE2E5: '',
        0xE2E8: 'Not yet traced beyond the actor/target swap',
        0xE2EB: 'Succeed',
    })

fact('aa71-action-library-expanded',
     "Mapped a real family of shared actions in $AA71's library",
     "Breakpointing $C960 across many commands, and logging which "
     "actor triggered each hit, confirms the player's own SIT IN, GET "
     "INTO, GET OUT OF and CLIMB OUT OF all reach shared actions 9 "
     "(get in/sit in) and 8 (get out) through each armchair's own "
     "action list. Those two are a matched pair built from the "
     "containment field ($C86E's field +1): getting into something "
     "sets your own 'container' to it; getting out sets it to whatever "
     "contains that thing. CORRECTED: an earlier version of this "
     "entry also listed action 11 as 'a generic fallback reached by "
     "INVENTORY, WAIT and STAND UP'. Those hits were actor 2 hailing "
     "a cab on the same turns; action 11 is HAIL.")


# --------------------------------------------------------------------
# A shared pre-condition guard, called from both SIT and GET OUT.
# --------------------------------------------------------------------

blk(0xCBA7, 'c', 'Shared guard-check: is some blocking condition active?',
    ["Called from both $E40A (SIT) and $E432 (GET OUT) before they do "
     "anything else. Checks bit 6 of a flag byte at $B934; if clear, "
     "returns immediately (continue normally). If set, discards the "
     "return address, prints a fixed message ($681A), and jumps to "
     "the shared failure point ($DC15) this project has seen several "
     "other entries use.",
     "Not yet confirmed: what sets bit 6 of $B934, and therefore what "
     "specific condition this guards against - a reasonable guess "
     "(already engaged in some other action, or otherwise unable to "
     "sit/stand right now) is just a guess, not tested. $B934/$B935 "
     "are the same bytes this project's $B91F investigation touched "
     "a few rounds earlier, not yet tied into a complete account."],
    comments={
        0xCBA7: 'Read the guard flag',
        0xCBAA: 'Is the blocking bit set?',
        0xCBAC: 'No: continue normally',
        0xCBAD: 'Yes: discard our own return address',
        0xCBAE: "Not in the 'quoted' print mode",
        0xCBAF: '',
        0xCBB2: 'A fixed message...',
        0xCBB5: '...print it',
        0xCBB8: '...then bail out via the shared failure point',
    })


# --------------------------------------------------------------------
# $D008 - the last previously-unexamined routine on the per-actor
# NPC-dispatch path, confirmed to belong to the same small accessor
# family as the already-documented $D045.
# --------------------------------------------------------------------

blk(0xD008, 'c', "Cache/sync an entity record's fields +3/+4/+6 (get side)",
    ["Called from the confirmed per-actor dispatch bridge ($CC78). "
     "Reads record IY's own fields +4/+5, compares them (via $CFB6) "
     "against IY's own field +3, and if equal, copies record IX's "
     "fields +3/+4 (16-bit) and +6 (a byte) into the cache variables "
     "$9FD6/$9FD7.",
     "Part of one compact block of get/set accessors for these same "
     "three fields, alongside $D026 (the inverse: write the cache "
     "back if it differs), $D03B (a plain setter), and the already-"
     "confirmed $D045 ('get the player's room') - all reached as "
     "genuine, separate entry points into the same small block, not "
     "one routine falling through by accident. What fields +3/+4/+6 "
     "represent (beyond the confirmed, distinct room-number field at "
     "+$0F) is still not confirmed."])
