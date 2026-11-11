"""
Overlay 04: the verb/action system and the game's data tables, decoded
from the game's own code and checked in the emulator (session of
2026-11-05). The large data tables are generated from the decoders in
dictionary.py and objects.py, so their labels cannot drift from the data.

See world_model_notes.md, section "Session 2026-11-05", for the tests
behind every claim here.
"""

import sys
sys.path.insert(0, '.')
from build_skeleton import A, blk, C, fact, bug
import dictionary as D
import objects as O

b, w = D.byte, D.word16
WORDS = D.by_offset()


def word_name(v):
    o = v & 0x0FFF
    if not o:
        return None
    wd = WORDS.get(o)
    return wd['stem'] if wd else f'?{o:03X}'


# --------------------------------------------------------------------
# Verb patterns ($8259): the verb NUMBER is a record's position here.
# --------------------------------------------------------------------

VERB_TABLE = 0x8259
VERBS = {}
for n in range(1, 60):
    a = VERB_TABLE + (n - 1) * 8
    if w(a) == 0:
        VERB_END = a
        break
    VERBS[n] = ' '.join(x for x in (word_name(w(a + 2 * k)) for k in range(3)) if x)
# Bytes 6-7 are a fourth word slot: GO for the ten directions (GO NORTH),
# CLOSELY for verb 20 and FURIOUSLY for verb 30. Name the two it tells apart.
VERBS[20] = 'EXAMINE CLOSELY'
VERBS[30] = 'GO FURIOUSLY TO'

blk(VERB_TABLE, 'b', 'Verb patterns: the verb number is the position in this table',
    ["54 eight-byte records, one per verb phrase the parser accepts, "
     "ended by $0000. Bytes 0-5 are up to three word slots: the low 12 "
     "bits are a dictionary offset (see the dictionary at $5DC0), the "
     "high 4 bits are flags not yet decoded. Bytes 6-7 are not yet "
     "decoded either (they look like rules for which object slots the "
     "phrase takes).",
     "The verb number is not stored anywhere: $B1AB computes it from "
     "which record the parser matched, as (record - $8259) / 8 + 1, "
     "and stores it in $A033. Confirmed by watching writes to $A033 "
     "during a real TAKE LAMP (41 is written by $B1BF), and by typing "
     "about twenty commands and checking the verb number each one "
     "produced against this table: every one matched (NORTH=1 ... "
     "DOWN=10, CARRY=11, CLOSE=14, DROP=16, ENTER=18, EXAMINE=19, "
     "FOLLOW=21, GET=23, GIVE TO=26, HAIL=31, INVENTORY=33, LOOK=34, "
     "SIT IN=40, TAKE=41, TELL=47, WAIT=49, WEAR=51, KILL=52, LOCK=53, "
     "UNLOCK=54)."],
    subs=[('B', VERB_TABLE + (n - 1) * 8, 8, f'Verb {n}: {VERBS[n]}')
          for n in sorted(VERBS)] + [('B', VERB_END, 2, 'End marker')])

blk(0xB191, 'c', 'Match the typed command against the verb patterns',
    ["Clears the object ids ($A034, $A035), then asks $B39D to match "
     "the parsed words against the verb patterns at $8259. On no match "
     "it returns Z with HL = $B84C (the 'I do not know the verb' "
     "message, not yet rendered). On a match, IX points at the "
     "matching 8-byte pattern; the loop at $B1BA turns that into the "
     "verb number by counting 8-byte steps back to $8259, and stores "
     "it in $A033.",
     "Verb 46 (TALK TO) gets special treatment straight afterwards "
     "(six bytes copied between $A002 and $B172, direction chosen by "
     "bit 0 of $B16D) - not yet traced, but presumably saving or "
     "restoring who is being spoken to."],
    comments={
        0xB191: 'No direct object, no indirect object yet',
        0xB196: '',
        0xB199: '',
        0xB19C: '',
        0xB19E: 'Not yet examined',
        0xB1A1: 'Does the command match any verb pattern?',
        0xB1A4: 'Yes: go and work out which one',
        0xB1A6: "No: 'I do not know the verb...'",
        0xB1A9: '',
        0xB1AA: '',
        0xB1AB: 'Count which pattern IX points at (1 = the first)...',
        0xB1AD: '',
        0xB1AF: '',
        0xB1B0: '',
        0xB1B3: '',
        0xB1B5: '',
        0xB1B7: '',
        0xB1BA: '',
        0xB1BB: '',
        0xB1BD: '',
        0xB1BF: '...and that is the verb number',
        0xB1C2: '',
        0xB1C6: 'Is it verb 46 (TALK TO)?',
    })

# --------------------------------------------------------------------
# Default action for each verb ($9F38) and the shared actions ($AA71).
# --------------------------------------------------------------------

DEFAULTS = []
a = 0x9F38
while b(a) != 0xFF:
    DEFAULTS.append((a, b(a), w(a + 1)))
    a += 3
DEFAULTS_END = a

blk(0x9F38, 'b', "Each verb's default action record",
    ["Three-byte records (verb number, address of an action record), "
     "ended by $FF, searched by $D34E from $C972. 38 of the 54 verbs "
     "have a default here; several verbs share one record (all ten "
     "directions use $DD03; TAKE, GET, CARRY, TAKE FROM and TAKE OUT OF "
     "all use $DCC1; PUT IN, PUT ON and DROP IN use $DEC1).",
     "Verbs with no entry here (CLIMB INTO, CLIMB OUT OF, CLOSE, COUNT, "
     "GET INTO, GET OUT OF, GO TO, HAIL, OPEN, SIT IN, TAKE OFF, TAKE "
     "TO, WEAR, LOCK, UNLOCK) do nothing unless the object itself "
     "lists the verb in its own action list - which is why OPEN only "
     "ever reached a door's own entry.",
     "Confirmed by breakpointing $C972/$C981 during real commands and "
     "logging the verb and the record found (LOOK 34 -> $DC7B, "
     "INVENTORY 33 -> $DE6F, TAKE 41 -> $DCC1, DROP 16 -> $DC8D, WAIT "
     "49 -> $DDB4)."],
    subs=[('B', ra, 3, f'Verb {v} ({VERBS.get(v, "?")}) -> ${p:04X}')
          for ra, v, p in DEFAULTS] + [('B', DEFAULTS_END, 1, 'End marker')])

SHARED = {}
i = 0
while w(0xAA71 + 2 * i):
    SHARED[i + 1] = w(0xAA71 + 2 * i)
    i += 1
SHARED_NAMES = {
    4: 'WEAR (used by the China man\'s disguise)',
    5: 'TAKE OFF (used by the China man\'s disguise)',
    6: 'OPEN (used by every door)',
    7: 'CLOSE (used by every door)',
    8: 'GET OUT OF / CLIMB OUT OF (armchairs, sofa, cabs, trains)',
    9: 'GET INTO / CLIMB INTO / SIT IN (armchairs, sofa, trains)',
    10: 'COUNT (the money objects)',
    11: 'HAIL / GET (the two hansom cabs)',
    12: 'GET INTO / CLIMB INTO a cab (reuses the SIT IN body)',
    16: 'EXAMINE CLOSELY the deep stream (verb 20; CORRECTED, was "EXAMINE")',
    17: 'EXAMINE CLOSELY the drawer (verb 20; CORRECTED, was "EXAMINE")',
    18: 'EXAMINE CLOSELY the bookcase (verb 20; CORRECTED, was "EXAMINE")',
    19: 'EXAMINE CLOSELY the trash pile (verb 20; CORRECTED, was "EXAMINE")',
    20: 'TAKE / GET / TAKE OUT OF the burnt note',
    21: 'OPEN a wall safe',
    23: 'WEAR (used by the old man\'s disguise)',
    24: 'TAKE OFF (used by the old man\'s disguise)',
}
blk(0xAA71, 'w', 'Shared action records, used through objects\' own action lists',
    ["24 addresses of action records, ended by $0000. An object's own "
     "action list (see the entity records at $8CBA) maps a verb number "
     "to an index here; $C960 looks the index up when the target "
     "object has an entry for the verb being carried out. That lets "
     "every door share one OPEN and one CLOSE, every chair one SIT IN, "
     "and so on.",
     "Which objects use which entries was read from all 110 entity "
     "records (objects.py); entries 1-3, 13-15 and 22 are not used by "
     "any object's action list and may be reached some other way - not "
     "yet found.",
     "CORRECTED HISTORY: this table was first taken for the verb "
     "dispatch table (wrong - see $9F38), then 'TAKE is entry 5' was "
     "claimed and withdrawn. Entry 5 is in fact TAKE OFF."],
    subs=[('W', 0xAA71 + 2 * (k - 1), 2,
           f'Shared action {k}: ' + SHARED_NAMES.get(k, 'not used by any object list'))
          for k in sorted(SHARED)] + [('W', 0xAA71 + 2 * len(SHARED), 2, 'End marker')])

# --------------------------------------------------------------------
# The action-record interpreter and the code that chooses a record.
# --------------------------------------------------------------------

blk(0xC933, 'c', "Find the action record for the current command",
    ["Chooses which action record carries out the current verb "
     "($A033). If the actor ($A017) or the direct object ($A013) has "
     "its own entry for the verb (found by $D1DC), the entry's second "
     "byte is an index into the shared action table at $AA71 ($C960). "
     "Otherwise the verb's default record comes from $9F38 ($C972); a "
     "verb with no default fails via $DC15. Either way, $C996 then "
     "runs the record.",
     "Confirmed by logging which path each real command took: OPEN "
     "PLAIN DOOR used the door's own list (object 50, entry 6), SIT IN "
     "YOUR ARMCHAIR the armchair's (object 23, entry 9); LOOK, TAKE, "
     "DROP, INVENTORY and WAIT used their defaults."],
    comments={
        0xC933: 'IX = the actor\'s own record',
        0xC937: 'Not yet explained: bit 6 of the actor\'s flags byte',
        0xC93B: '',
        0xC93D: '',
        0xC93E: 'Does the actor list this verb itself?',
        0xC941: '',
        0xC943: '',
        0xC946: '',
        0xC949: '',
        0xC94B: 'Yes: use the shared action it names',
        0xC94D: 'Not yet explained ($A00F < 7: skip the object check)',
        0xC950: '',
        0xC952: '',
        0xC954: 'IX = the direct object\'s own record',
        0xC958: 'Does the object list this verb?',
        0xC95B: '',
        0xC95E: 'No: use the verb\'s default action',
        0xC960: 'Yes: the entry\'s second byte is a shared-action index',
        0xC963: '',
        0xC964: '',
        0xC966: 'HL = that entry in the shared action table',
        0xC969: '',
        0xC96A: '',
        0xC96B: '',
        0xC96C: 'HL = the action record itself',
        0xC96D: '',
        0xC96E: '',
        0xC96F: '',
        0xC970: 'Run it',
        0xC972: "Look the verb up in the default-action table",
        0xC975: '',
        0xC979: '',
        0xC97C: 'No default for this verb?',
        0xC97E: 'Then fail',
        0xC981: 'HL = the default action record',
        0xC984: '',
        0xC987: 'Run it',
    })

blk(0xC9BF, 'c', 'Run an action record (HL = the record)',
    ["Action records are a small data format that every verb's "
     "behaviour is written in. Byte 0 is a flags byte, byte 1 holds a "
     "value whose high nibble is stored at $A01F (meaning not "
     "confirmed - see below), and the rest depends on the flags:",
     "bit 5: before anything else, refuse (HL = $CBBB) if $D078 says "
     "so; bit 6: bytes 2-3 are the address of a pre-check routine, run "
     "through $CB34 - it returns Z to refuse; bit 4: five more header "
     "bytes follow (not decoded); bit 7: stop after the checks with "
     "carry set, without running the body. The executable body starts "
     "after the header: record + 2, + 2 more if bit 6, + 5 more if "
     "bit 4. $CA64 runs the body through the dispatcher at $CB2C.",
     "Every flag rule above was read from this routine and then "
     "checked against the records it runs: the computed body address "
     "lands on sensible code for all the records examined (e.g. SIT "
     "IN's $78 header puts the body at record + 9, $E413).",
     "Tested and NOT confirmed: that the byte-1 value is the number "
     "of minutes the action takes. The clock does move by 5 for one "
     "WAIT (value 5) and 2 for GET OUT (value 2), but another WAIT "
     "moved it by 1 and SIT IN (value 2) by 1."],
    comments={
        0xC9BF: 'IY = the action record',
        0xC9C0: '',
        0xC9C2: 'Is the action ruled out by $D078?',
        0xC9C5: 'No: carry on',
        0xC9C7: 'Yes - but only refuse if this record says that matters',
        0xC9CA: '',
        0xC9CC: '',
        0xC9CE: 'HL = the refusal handler',
        0xC9D1: 'Refuse (Z)',
        0xC9D2: '',
        0xC9D3: 'Not yet examined',
        0xC9D6: '',
        0xC9D8: 'Not yet examined',
        0xC9DB: '',
        0xC9DD: 'Does the record have a pre-check routine?',
        0xC9E1: '',
        0xC9E3: 'Yes: HL = its address...',
        0xC9E6: '',
        0xC9E9: '',
        0xC9EB: '...run it with the current IX/IY',
        0xC9EE: '',
        0xC9F0: 'Refused? Then stop',
        0xC9F2: 'Not yet explained: nothing more to do unless $A00B is set',
        0xC9F5: '',
        0xC9F6: '',
        0xC9F8: '',
        0xC9FA: '',
        0xC9FB: 'Store the high nibble of byte 1 at $A01F',
        0xC9FD: '',
        0xCA00: '',
        0xCA01: '',
        0xCA02: '',
        0xCA03: '',
        0xCA04: '',
        0xCA06: '',
        0xCA07: '',
        0xCA09: '',
        0xCA0C: 'HL = the record again; skip the two fixed bytes',
        0xCA0D: '',
        0xCA10: '',
        0xCA11: 'Skip the pre-check address if there is one',
        0xCA15: '',
        0xCA17: '',
        0xCA18: 'Skip the five extra bytes if there are any',
        0xCA1B: '',
        0xCA1F: '',
        0xCA21: '',
        0xCA22: "Remember the player's and the target's rooms",
        0xCA25: '',
        0xCA28: '',
        0xCA2C: '',
        0xCA2F: '',
        0xCA32: '',
        0xCA33: '',
        0xCA35: '',
        0xCA37: '',
        0xCA3A: '',
        0xCA3D: '',
        0xCA3F: '',
        0xCA40: 'Checks-only record?',
        0xCA44: '',
        0xCA46: 'Yes: report success without running the body',
        0xCA47: '',
    })

blk(0xD1DC, 'c', "Does this object list verb A in its own action list?",
    ["IX = an entity record, A = a verb number. Skips the record's "
     "fixed part (15 bytes plus the n location bytes, n being byte 0) "
     "to reach its own action list: two-byte (verb, shared action "
     "index) pairs ended by $FF or $00. Returns carry set with IX on "
     "the matching pair, or carry clear if the verb is not listed.",
     "The end test is a compact trick: INC (IX) leaves zero only if "
     "the byte was $FF, and a following DEC (IX) restores it and "
     "leaves zero only if it was $00 - so one byte is tested for both "
     "terminators without loading it.",
     "Confirmed by reading all 110 entity records with this layout "
     "(objects.py): every door lists OPEN->6 and CLOSE->7, both "
     "armchairs list CLIMB OUT OF->8, CLIMB INTO->9, GET OUT OF->8, "
     "GET INTO->9, SIT IN->9, matching the live hits."],
    comments={
        0xD1DC: 'Skip the record\'s fixed part: 15 + n bytes',
        0xD1DD: '',
        0xD1DE: '',
        0xD1E1: '',
        0xD1E3: '',
        0xD1E4: '',
        0xD1E5: '',
        0xD1E7: '',
        0xD1E9: '',
        0xD1EA: 'Is this pair for our verb?',
        0xD1ED: 'Yes: found',
        0xD1EF: 'Is this byte the $FF terminator?',
        0xD1F2: '',
        0xD1F4: '...or the $00 terminator?',
        0xD1F7: '',
        0xD1F9: 'Neither: next pair',
        0xD1FB: '',
        0xD1FD: '',
        0xD1FF: 'Found: carry set, IX on the pair',
        0xD200: '',
        0xD201: 'Put the $FF back',
        0xD204: 'Not listed: carry clear',
        0xD205: '',
    })

# --------------------------------------------------------------------
# Action records. Header bytes are marked as data so the body
# disassembles from the right byte.
# --------------------------------------------------------------------


def header_len(addr):
    f = b(addr)
    return 2 + (2 if f & 0x40 else 0) + (5 if f & 0x10 else 0)


def header_label(addr):
    f = b(addr)
    parts = [f'flags ${f:02X}']
    if f & 0x20:
        parts.append('bit 5: test $D078 first')
    if f & 0x40:
        parts.append(f'bit 6: pre-check at ${w(addr + 2):04X}')
    if f & 0x10:
        parts.append('bit 4: five extra bytes')
    if f & 0x80:
        parts.append('bit 7: checks only')
    parts.append(f'byte 1 ${b(addr + 1):02X}')
    return 'Action record header: ' + '; '.join(parts)


def action_record(addr, title, desc, comments=None):
    hdr = ('B', addr, header_len(addr), header_label(addr))
    if addr in A:
        A[addr]['subs'].append(hdr)
        if title:
            A[addr]['title'] = title
        A[addr]['desc'].extend(desc)
        if comments:
            A[addr]['comments'].update(comments)
    else:
        blk(addr, 'c', title, desc, comments=comments, subs=[hdr])


action_record(0xDD03, 'Default action: move in a direction (verbs 1-10)',
    ["Shared by all ten direction verbs. The pre-check ($DCD2) works "
     "out where the actor would end up; the body moves the actor and, "
     "when the actor is the one being followed by the display, updates "
     "$A00A. Not traced in detail."])
action_record(0xDCC1, 'Default action: take (TAKE, GET, CARRY, TAKE FROM, TAKE OUT OF)',
    ["The body is three instructions: the target's container becomes "
     "the actor - so carrying something is the same containment link "
     "($C86E's field +1) as sitting in a chair or a note being inside "
     "a safe. Confirmed: TAKE LAMP and GET LAMP both reach it, and "
     "INVENTORY afterwards lists the lamp."],
    comments={0xDCC5: "IX = the target's own record",
              0xDCC9: 'Its container becomes the actor taking it',
              0xDCCF: 'Succeed', 0xDCD1: ''})
action_record(0x9FC5, 'Default action: KILL (also BREAK and a profane synonym)',
    ["The pre-check is the body itself: it always refuses, handing "
     "back $9FCE, which prints message $680B. Confirmed in the "
     "emulator: BREAK LAMP and KILL WATSON both answer 'ONLY AN IDIOT "
     "WOULD TRY THAT.'"],
    comments={0x9FC9: 'Always refuse...',
              0x9FCC: '', 0x9FCD: '',
              0x9FCE: '"ONLY AN IDIOT WOULD TRY THAT."',
              0x9FD1: ''})
action_record(0xDEC1, 'Default action: put something into something (PUT IN, PUT ON, DROP IN)',
    ["The pre-check $DED9 sets IX to the thing being moved and IY to "
     "the container, then runs the fit check at $DEE4. The body moves "
     "the thing into the container's room and makes the container its "
     "new container."],
    comments={0xDECA: "The thing goes to the container's room...",
              0xDECD: '', 0xDED0: '...and the container now holds it',
              0xDED3: '', 0xDED6: 'Succeed', 0xDED8: ''})
action_record(0xDE9D, None, [])
action_record(0xDEAF, 'Shared CLOSE action ($AA71 entry #7)',
    ["`LD IX,($A013); RES 5,(IX+5)`: clears the target's 'open' bit. "
     "Confirmed live: CLOSE PLAIN DOOR reaches it through the door's "
     "own list (object 50, the pair at $90E7)."],
    comments={0xDEB6: "IX -> the target object's record",
              0xDEBA: 'Mark it closed', 0xDEBE: ''})
for k in (0xDEB6, 0xDEBA, 0xDEBE):
    A[0xDE9D]['comments'].pop(k, None)
action_record(0xE40A, None, [])
action_record(0xE432, None, [])
action_record(0xE2C7, None, [])
action_record(0xE3EA, 'Shared GET INTO a cab ($AA71 entry #12)',
    ["Has its own pre-check ($E3B8) but no body of its own: the body "
     "is a single JR into the SIT IN body at $E413 - a shared tail, "
     "reused because getting into a cab and sitting in a chair both "
     "just set the actor's container. Confirmed live: Inspector "
     "Lestrade (actor 2) reaches it when he climbs into the hansom "
     "cab (object 30)."],
    comments={0xE3F3: 'Reuse the SIT IN body (the actor\'s container = the cab)'})
action_record(0xE022, 'Shared WEAR action ($AA71 entry #4)',
    ["Used by the China man's disguise (object 14), whose own list "
     "maps WEAR to 4 and TAKE OFF to 5. The body calls $E03A with "
     "A = 1. Not yet tried in the emulator (the disguise starts in "
     "room 9, the closet)."])
action_record(0xE003, 'Shared TAKE OFF action ($AA71 entry #5)',
    ["Used by the China man's disguise (object 14). The body calls "
     "$E03A with A = 0, then clears the disguise's container and sets "
     "its room to $A00A.",
     "CORRECTED HISTORY: this record was once claimed to be TAKE's "
     "handler (wrong - nothing reached it during TAKE LAMP), then "
     "marked 'not confirmed reachable'. The object records show how it "
     "is reached: through the disguise's own TAKE OFF entry."])
A[0xE003]['t'] = 'c'
A[0xE003]['desc'] = [p for p in A[0xE003]['desc']
                     if 'NOT confirmed' not in p and 'Left in the' not in p
                     and 'The bytes here are still' not in p
                     and 'CORRECTED: an earlier pass' not in p]
blk(0xE03A, 'c', 'Set the worn state of the actor (A = 1 wear, 0 take off)',
    ["Called by the shared WEAR (with A = 1) and TAKE OFF (with A = 0) "
     "actions. Finds the actor's compact record via $CC0E, writes A "
     "into its byte 0, then re-resolves the actor and refreshes the "
     "cached record pointer at $A017. Read from the code; not yet "
     "tried in the emulator."],
    comments={
        0xE03A: 'C = 1 to wear, 0 to take off',
        0xE03B: "The actor's id",
        0xE03E: 'Find their compact record',
        0xE041: 'Record whether they are wearing it',
        0xE044: '',
        0xE048: '',
        0xE049: 'Re-resolve the actor...',
        0xE04C: '...and refresh the cached pointer',
    })

# --------------------------------------------------------------------
# The fit check: shared by GET INTO / SIT IN and PUT IN.
# --------------------------------------------------------------------

blk(0xDED9, 'c', 'Pre-check for PUT IN: will the thing fit in the container?',
    ["Sets IX to the thing being moved ($A013), IY to the container "
     "($A015) and A to the container's id, then falls into the fit "
     "check at $DEE4 - which the SIT IN / GET INTO pre-check ($E3F5) "
     "also jumps into with different registers (IX = the actor, IY = "
     "the chair): a shared tail.",
     "$DEE4 refuses if none of bits 0-2 of the container's field +4 "
     "are set (it cannot hold things). Otherwise it fits if "
     "capacity - size - what's already inside is at least 1, where "
     "capacity and size are both field +2 and $D2ED totals what is "
     "already inside.",
     "Confirmed in the emulator, including the boundary: Holmes "
     "(size 96) gets into Watson's armchair (capacity 255) even with "
     "Watson in it ($D2ED returns 96): 255-96-96 = 63. Poking the "
     "armchair's capacity to 193 still lets him in (1 to spare); 192 "
     "refuses (0 to spare), and the refusal is reported as 'I SEE NO "
     "WATSONS ARMCHAIR THAT YOU CAN GET INTO'."],
    comments={
        0xDED9: 'IX = the thing being put somewhere',
        0xDEDD: 'IY = the container',
        0xDEE1: "A = the container's id",
        0xDEE4: 'B = the container\'s id. Can the container hold things?',
        0xDEE5: '',
        0xDEE8: '',
        0xDEEA: 'No: refuse',
        0xDEED: 'Capacity minus the size of the thing...',
        0xDEF0: '',
        0xDEF3: '...too big even for an empty container? Refuse',
        0xDEF5: '',
        0xDEF6: 'How much is already inside the container?',
        0xDEF7: '',
        0xDEFA: '',
        0xDEFB: '',
        0xDEFC: 'Take that off too',
        0xDEFD: 'Not enough room: refuse',
        0xDEFF: 'At least 1 to spare: it fits (NZ)',
        0xDF00: 'Exactly full also refuses (Z)',
        0xDF01: '',
    })

# --------------------------------------------------------------------
# The world data: dictionary and entities.
# --------------------------------------------------------------------

blk(0x5D80, 'w', 'Dictionary index: where each letter\'s words start',
    ["32 two-byte offsets from $5DBF. Entries 1-26 (indexed by a "
     "letter's ASCII code AND $1F) give the first word starting with "
     "that letter; entry 31 marks the end of the dictionary ($67B7). "
     "The tokenizer ($DA34) finds the end of a letter's words by "
     "skipping forward to the next non-zero entry.",
     "CORRECTED: the automatic code/data split had this as code, which "
     "is why it used to disassemble as nonsense."],
    subs=[('W', 0x5D80 + 2 * i, 2,
           (f"'{chr(0x40 + i)}' words" if 1 <= i <= 26 else
            ('End of dictionary' if i == 31 else 'Unused')))
          for i in range(32)])

DICT_SUBS = []
for wd in D.all_words():
    nxt = None
    DICT_SUBS.append(wd)
DICT_SUBS.sort(key=lambda x: x['address'])
subs = []
for i, wd in enumerate(DICT_SUBS):
    end = DICT_SUBS[i + 1]['address'] if i + 1 < len(DICT_SUBS) else D.DICT_END
    label = wd['word']
    if wd['extra'] is not None:
        tgt = WORDS.get(wd['extra'] & 0x0FFF)
        label += f" (synonym of {tgt['word'] if tgt else '?'})"
    subs.append(('B', wd['address'], end - wd['address'], label))
blk(0x5DC0, 'b', 'The dictionary: 592 words',
    ["Each record (see dictionary.py, which decodes them exactly as "
     "$A94D does): byte 0's low nibble picks a suffix from the table "
     "at $A85C ($F = none); byte 1 says how many characters to keep "
     "from the previous word (bits 4-6) and how many new 5-bit letters "
     "follow (bits 0-3); if bit 7 of byte 1 is set, two more bytes "
     "give the offset of the word this one is a synonym of. The first "
     "letter is never stored: it is implied by the letter index.",
     "Because each word is stored as a change to the previous one, "
     "words can only be decoded in order - the reason a standalone "
     "call to $A94D early in this project produced garbage.",
     "Checked against play: every word the game accepted or echoed "
     "decodes correctly, and the synonym links match its behaviour "
     "(READ is EXAMINE: READ CHRONICLE answers '...THAT YOU CAN "
     "EXAMINE'; PICK is CARRY: PICK UP LAMP answers 'I DO NOT KNOW THE "
     "VERB UP CARRY'; BREAK is KILL). One link is unexplained: IN is "
     "recorded as a synonym of VISITED."],
    subs=subs)

ENTS = O.entities()
blk(0x8B6F, 'b', 'Entity index: id -> record address',
    ["Three-byte records (id, address of the entity's record), ended "
     "by $FF; searched by $D34E from $D237. 110 entries: people, "
     "objects, doors, and some topics of conversation (THE CASE, "
     "WHAT HAPPENED, YOUR ALIBI) - see the entity records at $8CBA."],
    subs=[('B', 0x8B6F + 3 * k, 3, f"{e['id']}: {O.display_name(e)}")
          for k, e in enumerate(ENTS)] + [('B', 0x8B6F + 3 * len(ENTS), 1, 'End marker')])

ent_sorted = sorted(ENTS, key=lambda e: e['address'])
ent_subs = []
for i, e in enumerate(ent_sorted):
    end = ent_sorted[i + 1]['address'] if i + 1 < len(ent_sorted) else e['end']
    locs = ','.join(str(x) for x in e['locations'])
    inside = '' if e['container'] == 0xFF else f"; inside {e['container']}"
    ent_subs.append(('B', e['address'], end - e['address'],
                     f"{e['id']}: {O.display_name(e)} (rooms {locs}{inside})"))
blk(0x8CBA, 'b', 'Entity records: every person, object and door',
    ["Layout (from the code that reads it, see objects.py): byte 0 = "
     "n, the number of location bytes; +1 = id of the thing containing "
     "this one ($FF = none) - the link that TAKE, SIT IN and GET OUT "
     "all change; +2 = size (capacity, for a container); +4 bits 0-2 "
     "= can hold things; +5 bit 5 = open; +7 onwards = up to four "
     "two-byte word slots (noun, then adjectives); +15 onwards = the n "
     "rooms this thing is in (a door lists every room it connects); "
     "then the thing's own (verb, shared action) list, ended by $FF.",
     "Checked against play: the player (0) is 'you' in room 8, Watson "
     "(3) is inside his armchair (24), the oil lamp (22) is in room 8, "
     "the Daily Chronicle (25) is inside Watson - which is why READ "
     "CHRONICLE says there is none to examine - and 'your money' (27) "
     "is carried by the player, as INVENTORY reports."],
    subs=ent_subs)

# --------------------------------------------------------------------
# Facts and bugs from this session.
# --------------------------------------------------------------------

fact('verb-system-decoded',
     "The whole verb system, decoded from the game's own tables",
     "Typed commands are matched against 54 verb patterns at $8259; "
     "the verb number is simply the matched pattern's position. Each "
     "verb has an optional default action record (table at $9F38), "
     "and any object can override a verb through its own action list, "
     "pointing into a library of 24 shared actions ($AA71). Action "
     "records are a small data format: a flags byte, an optional "
     "pre-check routine, optional extra bytes, then executable code. "
     "Confirmed by checking about twenty typed commands' verb numbers "
     "against the decoded table, and by logging which record each "
     "real command ran.")

fact('dictionary-front-coded',
     "The dictionary stores each word as an edit of the previous one",
     "Each of the 592 words keeps some letters from the word before it "
     "and adds a few new 5-bit letters, with common endings (S, ES, "
     "ING, ED, LY...) taken from a 15-entry suffix table. 29 words are "
     "synonyms of others, including D/E/N/S/W and NE/NW/SE/SW for the "
     "directions, I for INVENTORY, L for LOOK, READ for EXAMINE and "
     "PICK for CARRY - and one profane synonym for KILL.")

fact('cast-list',
     "The cast and objects, read from the game's own records",
     "110 entities, named from their own word slots: you, Watson, "
     "Inspector Lestrade, Chief Constable Straker, Strachan, Phipps, "
     "Major Percival Ffoulkes, Tricia Fender, a gardener, cook and "
     "maid, two local policemen, a China man and an old man (each "
     "with a wearable disguise), a German agent, Mrs Brown and Mrs "
     "Jones, two hansom cabs and a police cab with their cabbies, "
     "eight steam train carriages, a female corpse with a crumpled "
     "note, a body on a bloodstained sofa, two wall safes, a torn coded "
     "note in a trash pile, a gun under a large rock, and a burnt note "
     "in a fireplace. Some entries are conversation topics rather than "
     "things (THE CASE, WHAT HAPPENED, YOUR ALIBI, YOUR ADDRESS).")

fact('lestrade-hails-a-cab',
     "Inspector Lestrade hails a cab every turn from the very start",
     "Logging every action attempt shows actor 2 - Inspector Lestrade, "
     "who starts in room 11 - trying HAIL on the hansom cab (object 30) "
     "and then GET INTO it, every turn from the first command. Several "
     "of this project's earlier conclusions were thrown off by his "
     "actions running on the same turns as the player's.")

bug('sit-in-occupied-armchair',
    "You can climb into Watson's armchair while he is sitting in it",
    "Confirmed in the emulator: GET INTO WATSONS ARMCHAIR (or FOLLOW "
    "WATSON, which ends up doing the same) answers 'You get into "
    "watsons armchair.' at the start of the game, with Watson still "
    "in it. The fit check ($DEE4) only compares sizes: the armchair's "
    "capacity is 255 and Holmes and Watson are 96 each, leaving 63 "
    "to spare. Poking the capacity shows the limit (192 refuses).")

bug('follow-watson-armchair',
    "FOLLOW WATSON climbs into his armchair and runs on by itself",
    "Confirmed in the emulator: FOLLOW WATSON at the start of the "
    "game answers 'You climb into watsons armchair.' (Watson is "
    "sitting in it), then the clock keeps advancing for several turns "
    "without further input while the follow carries on. Whether that "
    "counts as a bug or a feature of FOLLOW is a judgement call.")


# --------------------------------------------------------------------
# A second, smaller table of action records, reached by number.
# Found because marking $9F38 as data exposed the old code/data split
# starting a code block in the middle of it (round trip failed).
# --------------------------------------------------------------------

blk(0x9FAB, 'w', 'A second table of 13 action records, chosen by number',
    ["13 addresses of action-record-shaped data, immediately after the "
     "verb default table. Its only user is $C583, which takes a value, "
     "removes bit 7, uses the rest as an index here, and copies the "
     "low nibbles of the chosen record's first two bytes into $A00F "
     "and $A010 ($A00F is the value the action-selection code at "
     "$C94D compares with 7).",
     "Some entries are ordinary action records ($E5D8's body is just "
     "OR 1 / RET); others have bit 7 set and contents that do not "
     "read as code, so they may be a different kind of record. Where "
     "the index comes from is not yet traced.",
     "Found the hard way: once the verb default table at $9F38 was "
     "marked as data, the automatic split's code block starting at "
     "$9FC3 - in the middle of this table - collided with the action "
     "record at $9FC5, and the round trip failed until this table was "
     "marked as data too."],
    subs=[('W', 0x9FAB + 2 * k, 2, f'Record {k}: ${w(0x9FAB + 2 * k):04X}')
          for k in range(13)])

blk(0xC583, 'c', 'Pick one of the 13 numbered action records',
    ["A = a record number with bit 7 set (not yet traced where it "
     "comes from). Looks the record up in the table at $9FAB, then "
     "copies the low nibble of its byte 0 to $A00F and of its byte 1 "
     "to $A010 (via $C571 and $C57A), and clears $A00B. Continues "
     "past this disassembly window - not traced further."],
    comments={
        0xC583: 'Drop the flag bit: the record number',
        0xC585: '',
        0xC586: '',
        0xC588: 'HL = that entry in the numbered-record table',
        0xC58B: '',
        0xC58C: '',
        0xC58D: 'IX = the record',
        0xC58E: '',
        0xC58F: '',
        0xC590: '',
        0xC591: '',
        0xC592: '',
        0xC594: "$A00F = low nibble of the record's byte 0",
        0xC597: "$A010 = low nibble of its byte 1",
        0xC59A: '',
        0xC59B: '',
    })
