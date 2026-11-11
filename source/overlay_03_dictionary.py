"""
Overlay: the dictionary word-matching mechanism (Phase 3). See
source/dictionary_notes.md for the full story, including a major
self-correction: an earlier pass in this project concluded (wrongly)
that this exact mechanism was NOT what real gameplay uses, based on a
test that turned out to have the same "forgot to step over the entry
breakpoint" bug this project has hit more than once (see
harness_notes.md). Re-tested properly, this IS the real path.
"""

import sys
sys.path.insert(0, '.')
from build_skeleton import blk, fact

blk(0xD9C5, 'c', 'Tokenizer: read and classify the next word from input',
    ["Confirmed, by single-stepping through a real call while typing "
     "a real command (see dictionary_notes.md), to be the tokenizer's "
     "genuine entry point: skips leading spaces, checks for an empty "
     "line or a special character, then (for an ordinary word) calls "
     "the per-letter dictionary index lookup ($DA34), the word-"
     "expansion machinery ($A94D), and the comparison routine "
     "($DA7D) in turn, repeating for each candidate word stored under "
     "the typed word's first letter."])

blk(0xDA34, 'c', "Look up this word's first letter in the dictionary index",
    ["Takes the current word's first character directly from the "
     "input buffer, masks it to 5 bits (giving 1-26 for any letter "
     "without needing a separate packing step - 'A' is $41, whose low "
     "5 bits are 1; 'Z' is $5A, whose low 5 bits are 26), and uses "
     "that to index a 26-entry table at $5D80 of 16-bit offsets, "
     "relative to a second base at $5DBF, to find the first candidate "
     "word stored under that letter.",
     "Confirmed real and correctly understood since early in this "
     "project (the table's entries are clean and monotonically "
     "increasing across all 26 letters), but its connection to real "
     "gameplay wasn't confirmed until much later - see "
     "dictionary_notes.md for the single-step trace that finally "
     "confirmed this is genuinely on the path a real typed command "
     "takes, not merely a plausible-looking table sitting unused."])

blk(0xDA7D, 'c', 'Compare the typed word against one dictionary candidate',
    ["Compares the typed word (already expanded/normalised into a "
     "scratch buffer) against one candidate's own expanded spelling, "
     "up to the length of whichever is shorter - i.e. genuine "
     "abbreviation/prefix matching, not requiring an exact full-length "
     "match. On a match, also follows a synonym chain (a bit in the "
     "next word's own flag byte marks 'this is the last synonym in "
     "the group'; otherwise a 16-bit offset follows, pointing at "
     "another word to also accept as equivalent).",
     "CONFIRMED WITH REAL DATA, correcting an earlier, wrongly-"
     "abandoned conclusion in this project (see dictionary_notes.md): "
     "breakpointing this exact address while typing TAKE shows the "
     "typed buffer holding 'ake' (the leading 't' already consumed by "
     "the per-letter index lookup above) compared in turn against "
     "three expanded dictionary candidates - 'able', 'akeS', 'alkS' - "
     "almost certainly TABLE, TAKES and TALKS. 'ake' against 'akeS' is "
     "exactly a prefix match, real evidence (not just a plausible "
     "story) that this comparison, and the word-expansion machinery "
     "that produced 'akeS' from a stored stem plus a suffix-table "
     "entry, are genuinely how the game recognises typed words."])

fact('dictionary-matching-confirmed',
     "Corrected: the original dictionary-matching path WAS the real one",
     "Earlier in this project, a test of the $DA7D comparison routine "
     "and the $A94D word-expansion routine both appeared to show this "
     "wasn't the code path real typed commands use (zero hits, "
     "garbled output). That was caused by forgetting to step over a "
     "breakpoint on the tokenizer's own entry point before tracing "
     "onward - the same class of bug this project has hit more than "
     "once elsewhere (see harness_notes.md). Fixed and re-tested: "
     "typing TAKE produces exactly the originally-expected call "
     "sequence ($DA34 -> $A94D -> $DA7D), and the comparison routine "
     "shows the typed buffer 'ake' matching a real, dictionary-"
     "expanded candidate 'akeS' (almost certainly TAKES) by prefix - "
     "real, verified confirmation of both the stem+suffix storage "
     "format and the abbreviation-matching comparison logic this "
     "project originally read from the code, then wrongly set aside. "
     "See source/dictionary_notes.md for the full account.")


# --------------------------------------------------------------------
# The dictionary-to-verb-number link - confirmed real by tracing a
# genuine word ("TAKE") all the way from typed input through to a
# verb-table entry that performs coherent, sensible "take an object"
# logic using already-confirmed building blocks. See
# source/dictionary_notes.md for the full trace.
# --------------------------------------------------------------------

blk(0xD6CE, 'c', 'Read one word and classify it as noun or verb',
    ["Calls the tokenizer ($D9C5) and checks its class-byte result: "
     "$D0 means noun (jumps to $D6E0 to handle that), $C0 means verb "
     "(falls through to accept it); anything else retries by calling "
     "the tokenizer again.",
     "Confirmed real by tracing a genuine word (TAKE) through this "
     "exact loop: three tokenizer calls happened in sequence, "
     "returning class bytes $30, then $B0 (the punctuation class this "
     "project found much earlier), then $C0 - accepted on the third "
     "attempt - with the OTHER half of the result (word index, held "
     "in E) staying fixed at 5 throughout all three. Read as: the "
     "tokenizer resolves the word immediately, but offers it under a "
     "sequence of candidate classes until one matches what the caller "
     "is looking for. Exactly why $30 and $B0 are tried first, before "
     "$C0, isn't confirmed."],
    comments={
        0xD6CE: 'Always start reading from the input buffer',
        0xD6D1: 'Ask the tokenizer for the next word',
        0xD6D4: 'Is it a noun?',
        0xD6D6: '',
        0xD6D9: '...or a verb?',
        0xD6DB: 'Neither: try again',
        0xD6DD: 'Verb accepted',
        0xD6DF: '',
    })

blk(0xE003, 'b', "$AA71's entry #5 - NOT confirmed reachable (see correction)",
    ["CORRECTED: an earlier pass in this project described this "
     "address as 'TAKE's own handler', on the reasoning that the "
     "tokenizer resolves 'TAKE' to word-index 5 and this is $AA71's "
     "entry 5. That connection was never actually tested. Breakpointing "
     "this exact address during a real, successful `TAKE LAMP` command "
     "(confirmed successful: real output 'You take the oil lamp.' was "
     "captured) produced **zero hits**, repeated with bare `TAKE`, a "
     "larger patience budget, and alongside a known-real dispatch "
     "point ($CB2C, which fired 22 times for the same command) as a "
     "sanity check that the test itself was working. See "
     "source/dictionary_notes.md's 'MAJOR CORRECTION' section for the "
     "full account.",
     "The bytes here are still genuinely real, valid Z80 instructions "
     "(from $E008 onward: calls $E03A, updates a record's room field "
     "to $A00A) - that part of the read was not wrong, only the claim "
     "that this address is *reached* during real play. Left in the "
     "disassembly as data (not code) reflecting that its role is now "
     "unconfirmed, rather than removed outright."])

blk(0xE03A, 'b', "Helper called from $E003's code - reachability unconfirmed",
    ["Real, valid instructions (given a value in A, finds a target "
     "object's compact record via the confirmed $CC0E, overwrites its "
     "field +0, then re-resolves via $D237 and refreshes a cached "
     "pointer at $A017) - but since $E003 itself is not confirmed "
     "reachable (see above), neither is this. Left documented as "
     "genuinely real code whose actual role in the game is now open, "
     "not as a confirmed 'TAKE helper'."],
    comments={
        0xE03A: 'C = a value (meaning unconfirmed)',
        0xE03B: 'A target id',
        0xE03E: 'Find its compact record',
        0xE041: "Overwrite field +0",
        0xE044: 'Reload a cached record pointer',
        0xE048: '',
        0xE049: 'Re-resolve the same id...',
        0xE04C: '...and refresh the cache',
    })

fact('dictionary-to-verb-number-corrected',
     "CORRECTION: 'TAKE is verb #5, traced to handler' does not hold up",
     "A previous round claimed to have traced TAKE all the way from "
     "typed input to a confirmed handler at $AA71's entry #5 ($E003). "
     "That claim was checked properly this round and falsified: "
     "breakpointing $E003 directly during a real, successful `TAKE "
     "LAMP` (output confirmed: 'You take the oil lamp.') produced "
     "zero hits, while a known-real dispatch point ($CB2C) fired 22 "
     "times for the same command. What genuinely was confirmed and "
     "still stands: the tokenizer correctly resolves 'TAKE' to class "
     "$C0 (verb) and word-index 5. What was never actually tested, "
     "despite being written as if it was: that this index feeds "
     "$AA71's table, or that $AA71's entry 5 is ever executed. See "
     "source/dictionary_notes.md for the full account, including how "
     "this differs from this project's other corrections (a false "
     "positive from an untested step, not a false negative from a "
     "buggy test).")
