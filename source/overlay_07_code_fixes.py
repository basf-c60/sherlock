"""
Overlay 07: code that the automatic code/data split called data.

tools/check.py lists every LD HL,<message> site (found by
render_messages.message_sites) that lands inside a data or text block;
the split mislabels code this way when the code was never executed during
the coverage run. Each region here was checked by disassembling it and
finding what refers to it - "read from code", not traced.
"""

import sys
sys.path.insert(0, '.')
from build_skeleton import A, blk  # noqa: E402
from overlay_04_actions import action_record  # noqa: E402

# $99FC-$9A7C: handlers reached from the records after the 5-entry table
# at $9927 (their addresses appear in those records: $99AD -> $99FC,
# $99E7 -> $9A05, $999B -> $9A13, $9969 -> $9A3D, $9977 -> $9A4B,
# $9985 -> $9A59).
blk(0x99FC, 'c', 'Handlers for the records at $9940-$99FB',
    ["Short routines whose addresses appear in the records between the "
     "five-entry table at $9927 and here ($99AD -> $99FC, $99E7 -> $9A05, "
     "$999B -> $9A13, $9969 -> $9A3D, $9977 -> $9A4B, $9985 -> $9A59). "
     "Each marks the current record done ($9A74: IX+3 bit 1 set, bit 0 "
     "clear), sometimes sets a flag in another record, and prints a "
     "message. The records' own format is not decoded yet.",
     "CORRECTED: the automatic split had these as data ('b' and 't' "
     "blocks); found because message references were landing inside "
     "data (tools/check.py). Read from code, not traced."],
    comments={0x99FC: 'Mark this record done', 0x9A02: '...print it and return',
              0x9A05: 'Set bit 1 of the record at $99FA', 0x9A13: 'Needs bit 1 of $9976...',
              0x9A1A: '...and of $9984', 0x9A21: 'Both: mark done',
              0x9A24: 'Set bit 1 of $99B2', 0x9A2F: 'Otherwise clear both bits',
              0x9A40: 'Set $9E88', 0x9A4E: 'Set bit 1 of $9976',
              0x9A5C: 'Thing $5F (95)...', 0x9A61: '...is in nothing...',
              0x9A65: '...and goes off stage (room 0)', 0x9A69: 'Set bit 1 of $9984',
              0x9A74: 'Mark the record at IX done: bit 1 set...', 0x9A78: '...bit 0 clear'})
blk(0x9A7D, 'b', 'Three bytes ($FF, 0, 0) referenced from $BD4D', [])
blk(0x9A80, 'c', 'Print one of two messages, depending on who is acting',
    ["Referenced from $F725. If the actor ($A036) is you, prints $6915 "
     "and stores 1 at $A027; otherwise prints $6920 and stores 0. "
     "Returns NZ (success). Read from code."],
    comments={0x9A80: 'The actor', 0x9A83: 'You?', 0x9A87: '',
              0x9A8A: '', 0x9A8C: 'Someone else', 0x9A8D: '',
              0x9A90: '', 0x9A93: 'Print it', 0x9A96: 'Succeed'})
action_record(0x9A99, 'Action record: a destination check (body $9A9B)',
    ["Header $04 $00 then code: $9AA3 checks the displayed room and the "
     "direct object against three combinations (room 103 with thing 50, "
     "room 50 with thing 103, room 50 with thing 18) and returns NZ with "
     "a value in L for a match; no match refuses via $DC15. The body "
     "then sets $E2C6 to $6D (the HAIL action's 'target + 1' variable) "
     "and continues at $9B04. Read from code; what the combinations mean "
     "in the game is not established.",
     "CORRECTED: was data in the automatic split."])
action_record(0x9ACB, 'Action record: the same check, other direction (body $9ACD)',
    ["Header $04 $00 then code: runs the check at $9AA3, subtracts $14 "
     "from its result and joins the record above at $9AD7. Read from code.",
     "CORRECTED: was data in the automatic split."])
action_record(0x9AE1, 'Action record (body $9AE3)',
    ["Header $04 $00 then code: calls $9B50 and $9B25, takes the result "
     "record's +2 less 2 as L and joins the next record at $9B02, which "
     "stores L at $A01F (the value the action interpreter also puts "
     "there from a record's byte 1). Read from code.",
     "CORRECTED: was data in the automatic split."])
action_record(0x9AF4, 'Action record (body $9AF6)',
    ["Header $04 $00 then code, like the record above with a different "
     "offset into the record $9B25 finds. Read from code.",
     "CORRECTED: the automatic split started the code at the header "
     "bytes (INC B / NOP)."])

# Spans, so stray boundaries from the automatic split inside them go.
for start, end in ((0x99FC, 0x9A7D), (0x9A80, 0x9A99), (0x9A99, 0x9ACB),
                   (0x9ACB, 0x9AE1), (0x9AE1, 0x9AF4)):
    A[start]['end'] = end

# $BA13-$BF58: the automatic split had all of this as data and text
# except nothing; it is variables, then code all the way to $BF58.
blk(0xBA13, 'b', 'Variables used by the code at $BA20-$BF58',
    ["$BA13 and $BA15 are record pointers stepped by $BE3C and $BE4B; "
     "$BA19-$BA1B are copied to $BA62 by $BB46; $BA1C and $BA1D are "
     "counters/flags for the routine at $BB67; $BA1E holds a record "
     "pointer. Read from code.",
     "CORRECTED: was split into data and text blocks."])
blk(0xBA20, 'c', 'Records whose +7 is 2: pick a routine by actor',
    ["Jumped to from $B946 when the record being handled has 2 at +7. If "
     "the actor ($A036) is 3 (Watson) it uses $BA67, if 2 (Inspector "
     "Lestrade) $BB67, otherwise neither; then returns with carry set "
     "and NZ, popping the HL/IY/IX that $B936 pushed. $BA3E looks the "
     "verb up in the record's own action list ($D1DB) and runs "
     "$A1AF and $B9FA.",
     "Read from code. A breakpoint here was not hit in six turns of "
     "ordinary play (WAIT, LOOK) from the start, so what makes it run "
     "is still open.",
     "CORRECTED: was data in the automatic split."],
    comments={0xBA20: 'The actor', 0xBA23: '', 0xBA26: 'Watson?',
              0xBA28: '', 0xBA2A: '', 0xBA2D: 'Inspector Lestrade?',
              0xBA2F: 'Neither', 0xBA31: '', 0xBA34: 'NZ...',
              0xBA36: "...restore what $B936 saved...", 0xBA3C: '...and carry'})
blk(0xBA60, 'b', 'More variables for $BA67-$BB5C',
    ["$BA60/$BA61 flags set at $BA67 and $BB46; $BA62-$BA64 a 3-byte "
     "copy compared with the table at $9FF6; $BA65 a record pointer."])
blk(0xBA67, 'c', "Routine chosen for Watson at $BA20",
    ["Walks a list ($BD7E/$AEA9), choosing a value 1-4 for the entries "
     "it accepts ($BD4B, $BD51, record +3 bit 5, and two comparisons "
     "against $D29D: below $32, below $46), and records it at $BB46. "
     "If something was chosen it finds or adds a matching 3-byte entry "
     "in the table at $9FF6 ($A0F7, $A104, $A11C). Prints $6F54 when "
     "nothing was found. Read from code only; not traced."])
blk(0xBB46, 'c', 'Remember a choice (A) and the 3 bytes at $BA19',
    [], comments={0xBB4D: 'The choice', 0xBB50: 'Copy 3 bytes to $BA62'})
blk(0xBB5C, 'c', 'Jump to the handler of the record at ($BA65)',
    ["The handler address is the record's +3/+4."])
blk(0xBB67, 'c', 'Routine chosen for Inspector Lestrade at $BA20, and helpers',
    ["Counts the entries of a list that pass $BC21 ($BA1C) and prints "
     "one of several messages depending on the result ($725F when none; "
     "$7295, $72A6, $72BD, $727E, $67FF, $72D6 and $72E1 on other "
     "paths). The helpers after it ($BC21 to $BF58) step through 4- or "
     "6-byte records whose +3 holds flag bits. Read from code only; not "
     "traced.",
     "CORRECTED: the automatic split had $BB38-$BF58 as data and text "
     "(eight message references fell inside it)."])
for start, end in ((0xBA13, 0xBA20), (0xBA20, 0xBA60), (0xBA60, 0xBA67),
                   (0xBA67, 0xBB46), (0xBB46, 0xBB5C), (0xBB5C, 0xBB67),
                   (0xBB67, 0xBF59)):
    A[start]['end'] = end
