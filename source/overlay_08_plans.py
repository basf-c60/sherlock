"""
Overlay 08 (2026-11-07): the plan-script language that drives every
character, the object-requirement codes in action records, and the
corrections these force on earlier overlays. Grew during the session to
cover the main loop ($A064), the node heap and lists, the game
variables and clock, orders and remarks ($B91F/$B936), Watson's and
Lestrade's replies, the case table ($9965) and its relation words, the
endings, the after-turn routines, the flag-naming refusal ($CB7B), the
timed keyboard read, the message printer's entry, word wrap, save/load,
and the generated "cast" and "how it works" pages. Every emulator
experiment named here is a small script in tools/experiments/
(plan_trace.py, verbs_test.py, v129.py, case_test.py, bit6_test.py,
busy_test.py, flags_test.py, timeout_test.py, watson_reply.py ...);
their results are quoted where the claims are made.

Found by following what happens to a "checks-only" action record (flags
bit 7): $C9BF returns carry set with HL just past the header, and $C9A7
hands that address to $CF80 and makes it the actor's new script
position. Everything after a checks-only header is a script in the
language below, and so is every character's behaviour, starting from
the 8-byte actor records at $9860 (+1/+2 = the actor's script position).

How the claims were checked: tools/plan.py decodes scripts from the
interpreter's own rules; tools/allplans.py walks every script reachable
from the actor table, the action tables and RUN instructions. The
emulator check (tools/experiments/plan_trace.py, 106 turns of play, 15,038
instruction fetches by 24 actors) breakpointed the fetch at $CC9B and
found every fetched address in the decoded set, except the hailed
cabbie's script at $F2B6 - which code, not a script, switches the
cabbie onto ($E2E2). That entry point was added and the trace re-checked.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT, 'tools'))   # appended: tools/dis.py must not shadow the stdlib dis

from build_skeleton import A, FACTS, blk, fact, bug, page, C, fix  # noqa: E402
import rooms as _rooms  # noqa: E402
_R = _rooms.rooms()


def room(n):
    if n in SPECIAL:
        return SPECIAL[n]
    if n == 0:
        return 'room 0 (off stage)'
    return f'room {n} ({_rooms.room_name(_R[n])})' if n in _R else f'room {n}'
from overlay_04_actions import action_record, header_label, header_len, VERBS, SHARED_NAMES  # noqa: E402
from objects import entities, display_name  # noqa: E402
import allplans  # noqa: E402
from plan import b, w, decode  # noqa: E402

ENT = {e['id']: display_name(e) for e in entities()}
import json  # noqa: E402
MSGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'messages.json')))


def msg_text(addr, n=70):
    m = MSGS.get(f'{addr:04X}')
    if not m:
        return ''
    t = ' '.join(m['text'].split()).replace('"', "'")
    return ': "' + (t if len(t) <= n else t[:n - 3].rstrip() + '...') + '"'

# ---------------------------------------------------------------------
# Corrections to earlier overlays
# ---------------------------------------------------------------------


def fix_text(addr, old, new):
    rec = A[addr]
    hit = False
    for i, para in enumerate(rec['desc']):
        if old in para:
            rec['desc'][i] = para.replace(old, new)
            hit = True
    assert hit, (hex(addr), old)


def fix_fact(fid, old, new):
    for i, (eid, title, body) in enumerate(FACTS):
        if eid == fid:
            assert old in body or old in title, (fid, old)
            FACTS[i] = (eid, title.replace(old, new), body.replace(old, new))
            return
    raise KeyError(fid)


# $9927 was never a table: it is the middle of the player's own script.
del A[0x9927]
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'always-checked-table-found':
        FACTS[i] = (eid, "CORRECTED: the 5 'checked every turn' entries are the player's plan script",
                    "An earlier round described $9927 as 'five 5-byte records "
                    "($99,$13,<16-bit addr>,<flag byte>)'. That reading was four "
                    "bytes out of step. The bytes are the player's own plan script "
                    "(actor 0's script pointer in the actor table at $9860 is "
                    "$9921): the '$99' is the high byte of a failure address, and "
                    "'$13' is the next RUN instruction's opcode (RUN, with a failure "
                    "address). The five addresses that every command visits "
                    "($D715, $D769, $D77E, $D7D9, $D7FA) are the five RUN targets "
                    "of that script, which reads a line, parses it, and then does "
                    "the parsed command. The live trace that found them was right; "
                    "only the format laid over the bytes was wrong. See the "
                    "'plan scripts' entry.")
for addr in (0xCB2C,):
    for i, para in enumerate(A[addr]['desc']):
        if '5-entry table at $9927' in para:
            A[addr]['desc'][i] = para.replace(
                '(the fixed 5-entry table at $9927, then a command-specific '
                'candidate, then a long shared tail)',
                "(CORRECTED: not a fixed table but the five RUN steps of the "
                "player's plan script at $9921, then the command itself)")
fix_fact('dispatch-mechanisms-unified', 'the fixed 5-entry table at $9927',
         "the five RUN steps of the player's plan script at $9921 - CORRECTED, "
         "this was once taken for a fixed table at $9927")
fix_text(0x99FC, 'five-entry table at $9927',
         "player's plan script (which ends at $994C - CORRECTED, it was once "
         "taken for a five-entry table at $9927)")

# $D008/$D026: these load and save the plan registers.
blk(0xD008, 'c', "Load the current actor's plan registers",
    ["IY = the actor's record in the table at $9860. Copies the actor's "
     "saved plan registers into $9FD6 (the plan's verb) and $9FD7/$9FD8 "
     "(its direct and indirect objects) - from the actor record's +3, "
     "+4 and +5, or, when the actor is inside a sub-script, from the "
     "call frame $CFB6 finds (+6, +3 and +4). Script arguments $FA, $FD "
     "and $FC read these registers (see $CEDE). $D026 is the matching "
     "save. Read from the code.",
     "CORRECTED: this was titled 'Cache/sync an entity record's fields "
     "+3/+4/+6 (get side)' before the plan-script language was found."],
    comments={0xD008: 'HL = the actor\'s own saved objects', 0xD00E: 'Is it inside a sub-script?',
              0xD011: 'A = its own saved verb', 0xD014: 'No: use the actor record\'s',
              0xD016: 'Yes: use the call frame\'s objects...', 0xD01C: '...and verb',
              0xD01F: 'The plan\'s verb', 0xD022: 'The plan\'s direct and indirect objects',
              0xD026: 'Save side: the plan\'s objects', 0xD029: 'Inside a sub-script?',
              0xD02C: '', 0xD02F: 'No: save into the actor record',
              0xD031: 'Yes: save into the call frame', 0xD03B: 'Save into the actor record'})

# ---------------------------------------------------------------------
# The interpreter
# ---------------------------------------------------------------------

LANG = [
    "Each actor (the 8-byte records at $9860: +0 id, +1/+2 script "
    "position, +3/+4/+5 saved plan registers) runs a script in a small "
    "language. Each instruction starts with one byte: the low nibble is "
    "the opcode and the high nibble holds flags. Bit 7: a 2-byte "
    "success address follows the operands. Bit 4: a 2-byte failure "
    "address follows (after the success address, if both). Bit 5: "
    "one-shot - after it succeeds the instruction is overwritten with "
    "zeros ($CF43), and the fetch loop at $CC94 skips zero bytes, so it "
    "never runs again - though no script in the game sets bit 5 (all "
    "decoded instructions were checked), so this is never used. "
    "Bit 6: busy - while a character is on such an "
    "instruction it will not do what the player asks of it: $B936 "
    "copies the instruction's first byte to $B934, and $CBA7 (used by "
    "SIT, GET OUT and the move pre-check $DCD2) refuses with 'SORRY, I "
    "CANNOT DO THAT NOW.' Confirmed in the emulator (see $CBA7).",
    "Opcodes (lengths from $CF03): 1 DO verb (2 bytes); 2 DO verb "
    "dobj iobj (4); 3 RUN record (3); 4 ASK person TO verb dobj iobj "
    "(5): an order to another character, queued on the list at $9FEE "
    "and announced with $682A; 5 SAY TO person message (4), via $6830; "
    "6 PRINT message (3); 7 RUN record dobj iobj (5); 8 SIGNAL actor "
    "(2) and 9 AWAIT actor (2): one actor leaves a token on the $9FE7 "
    "list for another, which AWAIT consumes; A RETURN FAIL and B "
    "RETURN OK (1 each): leave a sub-script; D (2) and F (1) PASS: "
    "spend a minute doing nothing; E GOTO address (3). C is not used: "
    "$CD08 is JR Z,$CD08, a jump to itself with Z set, which would "
    "hang the game.",
    "DO runs a command for the actor exactly as if it had been typed, "
    "through $C4D1: the verb's own default record, the object's own "
    "action list, the requirement codes and the pre-check all apply. "
    "Verbs 128-140 exist only for scripts and are looked up in the "
    "table at $9FAB. RUN skips the verb and runs one action record "
    "directly ($C591). Argument bytes $F5-$FF are not objects: $FA is "
    "the plan's verb ($9FD6), $FB the actor itself, $FC and $FD the "
    "plan's indirect and direct objects ($9FD8, $9FD7), $FE a number "
    "and $FF nothing ($CEDE).",
    "Success ($CE8F) moves to the success address or the next "
    "instruction and returns to the main loop, which runs the next step "
    "at once if the action took no time and otherwise ends the actor's "
    "turn for as many minutes as it took. Failure ($CEB8) moves to "
    "the failure address or the next instruction and tries again at "
    "once, up to ten times in one turn ($CC0B); if the failure address "
    "is the instruction itself, the actor simply waits there. So "
    "'DO verb 136 / 23 [fail -> itself]' means 'wait here until 11pm'.",
    "A RUN or DO that reaches a checks-only action record (flags bit 7) "
    "calls a sub-script: $C9A7 saves a call frame ($CF80: actor, return "
    "position, objects, plan verb) on the list at $9FE9 and points the "
    "actor at the script after the record's header. RETURN OK or "
    "RETURN FAIL ($CFCF) drops the frame and makes the calling "
    "instruction succeed or fail.",
]

blk(0xCC78, 'c', "Run one step of the current actor's plan script",
    LANG + [
        "This routine fetches the actor's script position (+1/+2 of its "
        "record), skips spent one-shot bytes, and dispatches on the "
        "opcode. $CCA7-$CCC6 is a separate path for an actor who has "
        "been given an order (ASK) this turn ($CC0D, set by $CC37 from "
        "$B91F): the order is carried out first, through $B936. Not "
        "traced in detail.",
        "Confirmed in the emulator: a breakpoint at $CC9B over 106 turns "
        "saw 15,038 fetches by 24 actors, every one at an instruction "
        "start that tools/plan.py decodes, and opcodes 1-11, 14 and 15 "
        "all occurred (12 and 13 never did)."],
    comments={
        0xCC78: "Set up this actor's room comparisons",
        0xCC7B: "IY = the actor's record in the actor table",
        0xCC7F: 'Load its plan registers',
        0xCC82: 'HL = its script position',
        0xCC88: '',
        0xCC8C: 'Ten failures this turn already?',
        0xCC91: 'Then give up for this turn',
        0xCC94: 'Skip zero bytes: spent one-shot instructions',
        0xCC9B: 'IX = the instruction; remember where it is',
        0xCCA1: 'Opcodes 10 and up are control flow',
        0xCCA7: 'Has the actor been given an order this turn?',
        0xCCAE: 'Yes: deal with it first (not traced)',
        0xCCC7: 'Dispatch on the opcode',
        0xCCCC: '7: RUN record with objects',
        0xCCD1: '6: PRINT',
        0xCCD6: '5: SAY TO',
        0xCCDB: '4: ASK someone to do something',
        0xCCE0: '1: DO verb',
        0xCCE5: '3: RUN record',
        0xCCEA: '8: SIGNAL',
        0xCCEE: '9: AWAIT',
        0xCCF0: '2: DO verb dobj iobj',
        0xCCF3: '14: GOTO...',
        0xCCF7: '...the script position becomes the address',
        0xCD03: '...and fetch again at once',
        0xCD06: '12: unused - this jumps to itself and would hang',
        0xCD0A: '11: RETURN OK',
        0xCD0E: 'Leave the sub-script',
        0xCD11: '',
        0xCD14: 'The calling instruction succeeds',
        0xCD17: '10: RETURN FAIL',
        0xCD1E: '',
        0xCD21: 'The calling instruction fails',
    })

blk(0xCD24, 'c', 'Plan opcode 8, SIGNAL: leave a token for another actor',
    ["Allocates a 2-byte node (this actor, the argument) on the list "
     "headed at $9FE7. AWAIT (opcode 9) in the other actor's script "
     "looks for it. Always succeeds. Read from the code."],
    comments={0xCD24: 'The actor being signalled', 0xCD28: 'Allocate a 2-byte node',
              0xCD2D: 'Link it in at the head of the $9FE7 list',
              0xCD3A: 'Node +0 = who signalled', 0xCD40: 'Node +1 = who it is for',
              0xCD44: 'Succeed'})
blk(0xCD47, 'c', 'Plan opcode 9, AWAIT: wait for a token from another actor',
    ["Looks along the $9FE7 list for a node left by the actor named "
     "in the argument for this actor. Fails if there is none (scripts "
     "give AWAIT a failure address pointing at itself, so the actor "
     "waits); otherwise unlinks the node, frees it and succeeds. "
     "Confirmed in the emulator that AWAIT runs (3,909 of the 15,038 "
     "fetches were AWAITs, mostly Phipps at $EE2B waiting for Chief "
     "Constable Straker); the hand-over itself was not watched."],
    comments={0xCD47: 'B = who the token must come from', 0xCD4A: 'Walk the token list',
              0xCD51: 'None left: fail', 0xCD54: 'Is this token for this actor...',
              0xCD5C: '...and from that actor?', 0xCD62: 'Yes: unlink it...',
              0xCD7A: '...and free it', 0xCD7F: 'Succeed'})
blk(0xCD82, 'c', 'Plan opcodes 13 and 15, PASS; and giving up for the turn',
    ["$CD82: PASS spends one minute ($A01F = 1) and succeeds. $CD8B: "
     "after ten failures, or a failure address that loops straight "
     "back, the actor spends a minute and saves its plan registers "
     "($D026)."],
    comments={0xCD82: 'This takes one minute', 0xCD88: 'Succeed',
              0xCD8B: 'Give up: one minute', 0xCD91: 'Save the plan registers'})
blk(0xCD95, 'c', 'Plan opcode 6, PRINT: print a message',
    ["The message address follows the opcode. Always succeeds."],
    comments={0xCD95: 'HL = the message', 0xCD9B: 'Print it', 0xCD9E: 'Succeed'})
blk(0xCDA1, 'c', 'Plan opcode 5, SAY TO: say something to someone',
    ["Pushes the message address, makes the argument the direct "
     "object, and prints $6830 (actor SAYS TO object, then the pushed "
     "message in quotes). Always succeeds."],
    comments={0xCDA1: 'The message to say...', 0xCDA7: '...is a parameter for $6830',
              0xCDA8: 'Who is spoken to', 0xCDB1: '', 0xCDB6: '"... SAYS TO ..."',
              0xCDBC: 'Succeed'})
blk(0xCDBF, 'c', 'Plan opcode 4, ASK: order another character to do something',
    ["Verb 46 (TALK TO) with the person as the direct object; queues "
     "an 8-byte node on the list at $9FEE (person, $FF, verb, dobj, "
     "iobj) and prints $682A, which quotes the order: the cabbie is "
     "told 'HAIL THE HANSOM CAB' this way, for example. The person "
     "carries the order out on its next turn ($CCA7). Read from the "
     "code; the message was rendered."],
    comments={0xCDBF: 'Verb 46, TALK TO', 0xCDC4: 'Who is ordered', 0xCDCD: 'The verb ordered',
              0xCDD3: 'Its direct object', 0xCDDC: 'Its indirect object',
              0xCDE5: 'Allocate an 8-byte order node', 0xCDEA: 'Fill it in',
              0xCE03: 'Link it in at the head of the $9FEE list',
              0xCE10: 'Quote the order', 0xCE16: 'Succeed'})
blk(0xCE18, 'c', 'Plan opcodes 1, 2, 3 and 7: DO a command or RUN a record',
    ["$CE18 (opcode 2): verb, direct and indirect object from the "
     "instruction, through $CEDE, then $C4D1 runs the command. $CE3B "
     "(7) and $CE4F (3): run the action record named in the instruction "
     "directly ($C591), with or without objects. $CE6A (1): a verb "
     "alone. In each case carry back from the command means a "
     "sub-script was called (the script position has already moved), "
     "Z means it failed and NZ means it succeeded."],
    comments={0xCE18: 'The verb', 0xCE21: 'The direct object', 0xCE2A: 'The indirect object',
              0xCE33: 'Carry out the command', 0xCE36: 'A sub-script was entered: done',
              0xCE37: 'Refused: the instruction fails', 0xCE39: 'Done: it succeeds',
              0xCE3B: 'RUN with objects: the direct object...', 0xCE44: '...and the indirect object',
              0xCE4F: 'RUN without objects', 0xCE57: 'No verb',
              0xCE5C: 'HL = the action record', 0xCE62: 'Run it',
              0xCE65: 'A sub-script was entered: done', 0xCE66: 'Refused: fail',
              0xCE68: 'Done: succeed', 0xCE6A: 'DO verb: the verb', 0xCE73: 'No objects',
              0xCE7B: 'Carry out the command', 0xCE7E: '', 0xCE7F: '', 0xCE81: ''})
blk(0xCE83, 'c', 'Point IX and HL at the current plan instruction',
    ["IY = the actor's record, HL = IX = the instruction just run "
     "($9FD9), A = its first byte."])
blk(0xCE8F, 'c', 'A plan instruction succeeded: move on',
    ["Skips the instruction ($CF03). With bit 7 set, the script "
     "position becomes the success address; otherwise, with bit 4 set, "
     "the failure address is skipped. With bit 5 set the instruction is "
     "erased ($CF43). Then back to the main loop ($CD91 saves the plan "
     "registers), which ends the actor's turn if the action took time."],
    comments={0xCE8F: 'The instruction just run', 0xCE92: 'Skip it',
              0xCE95: 'Has it a success address?', 0xCE9B: 'Yes: go there',
              0xCEA1: 'No: skip any failure address',
              0xCEA8: 'One-shot?', 0xCEAC: 'Yes: erase it',
              0xCEAF: 'Store the new script position', 0xCEB5: 'End the turn'})
blk(0xCEB8, 'c', 'A plan instruction failed: move on and try again now',
    ["Counts the failure ($CC0B), skips the instruction and any "
     "success address, and takes the failure address if bit 4 is set. "
     "If that leads straight back to the same instruction the actor "
     "gives up for this turn ($CD8B); otherwise the next instruction "
     "is tried at once ($CC82)."],
    comments={0xCEB8: 'Count the failure', 0xCEBC: 'The instruction just run',
              0xCEBF: 'Skip it and any success address', 0xCEC2: 'Has it a failure address?',
              0xCEC8: 'Yes: go there', 0xCECC: 'Store the new script position',
              0xCED2: 'Back to the same instruction?', 0xCED8: 'Then wait there until next turn',
              0xCEDB: 'Otherwise try the next one now'})
blk(0xCEDE, 'c', 'Resolve a plan argument byte',
    ["Values below $F5, and $FE/$FF, are used as they are. $FA = the "
     "plan's verb ($9FD6), $FB = the actor itself ($A036), $FC = the "
     "plan's indirect object ($9FD8); $FD and the unused $F5-$F9 = "
     "the plan's direct object ($9FD7)."],
    comments={0xCEDE: 'An ordinary value?', 0xCEE1: '$FE or $FF: also as it is',
              0xCEE4: '$FA: the plan\'s verb', 0xCEEC: '$FB: the actor itself',
              0xCEF4: '$FC: the plan\'s indirect object', 0xCEFA: 'Otherwise its direct object'})
blk(0xCEFE, 'c', 'Skip past a plan instruction',
    ["$CEFE also skips a success address (bit 7 set in A); $CF03 skips "
     "only the opcode and operands: 1 byte for opcodes 10, 11 and 15, "
     "2 for 1, 8, 9 and 13, 3 for 3, 6 and 14, 4 for 2 and 5, and 5 "
     "for 4, 7 and 12. The INC HL chain at $CF3D-$CF41 is entered at "
     "the point that gives the right count."],
    comments={0xCEFE: 'Success address too?', 0xCF03: 'The opcode',
              0xCF3D: 'Five bytes', 0xCF3E: 'Four', 0xCF3F: 'Three', 0xCF40: 'Two', 0xCF41: 'One'})
blk(0xCF43, 'c', 'Erase a spent one-shot plan instruction',
    ["Overwrites the instruction at IX, including its success and "
     "failure addresses, with zeros, so the fetch loop skips it from "
     "now on. Read from the code. Never used: no instruction in any "
     "script has bit 5 set, and no script byte had changed after 110 "
     "turns in the emulator."])
blk(0xCF80, 'c', 'Save a sub-script call frame',
    ["Allocates a 7-byte node on the list at $9FE9: +0 the actor, "
     "+1/+2 HL (the calling instruction), +3/+4 the command's objects "
     "($A034/$A035), +5 B, +6 the plan's verb ($9FD6). $CFB6 finds the "
     "current actor's frame; $CFCF returns from the sub-script, "
     "restoring the script position and freeing the frame, and gives "
     "A = frame +5."],
    comments={0xCF80: '', 0xCF82: 'Allocate a 7-byte node', 0xCF87: '+0: the actor',
              0xCF8D: '+1/+2: where to come back to', 0xCF93: '+3/+4: the objects',
              0xCF9D: '+5: B', 0xCFA0: '+6: the plan\'s verb',
              0xCFA6: 'Link it in at the head of the list',
              0xCFB6: 'Find this actor\'s call frame: Z if none',
              0xCFCF: 'Return from a sub-script: find the frame',
              0xCFD2: 'Back to the calling instruction',
              0xCFE2: 'Unlink the frame'})

# ---------------------------------------------------------------------
# Script data: every reachable script, decoded into labelled sub-blocks
# ---------------------------------------------------------------------

INTERNAL = {
    128: 'PUT: move the direct object into room (indirect object); room 0 is off stage',
    129: 'IS WITH: are the direct and indirect objects in the same room?',
    130: 'IS HERE: is the direct object with the actor ($C863)?',
    131: 'IS IN: is the direct object in room (indirect object)?',
    132: 'set bit 0 of the direct object\'s +5 flags',
    133: 'clear bit 0 of the direct object\'s +5 flags',
    134: 'sub-script: FOLLOW the direct object until in room (indirect object)',
    135: 'sub-script: OPEN, GO THROUGH and CLOSE a door',
    136: 'IS HOUR: is the clock\'s hour (1-24) the direct object?',
    137: 'sub-script: do verb (direct object), then EXAMINE the indirect object',
    138: 'sub-script: go through a door (135), then CHANCE (indirect object)',
    139: 'sub-script: do verb (direct object), then CHANCE (indirect object)',
    140: 'sub-script: $E4C9 on the direct object, then WAIT (indirect object) minutes',
}
SHORT = {128: 'PUT', 129: 'IS WITH', 130: 'IS HERE', 131: 'IS IN', 132: 'LOCK',
         133: 'UNLOCK', 134: 'FOLLOW UNTIL IN', 135: 'GO THROUGH DOOR', 136: 'IS HOUR',
         137: 'DO THEN EXAMINE', 138: 'DOOR THEN CHANCE', 139: 'DO THEN CHANCE',
         140: '$E4C9 THEN WAIT'}
HELPERS = {
    0xE52F: 'START COUNTDOWN of (dobj) plus a random number below (iobj)',
    0xE57A: 'TICK the countdown (fails, and deletes it, when it runs out)',
    0xE588: 'CANCEL the countdown',
    0xE5A8: 'IDLE (no checks; takes a minute)',
    0xDDBE: 'WAIT (dobj) minutes',
    0xF198: 'CHANCE: succeed if a random 1-99 is at most (dobj)',
    0xDD52: 'ENTER / GO INTO (dobj)',
    0xDCC1: 'TAKE (dobj)',
    0xE7E2: 'HAS IT: is the actor carrying (dobj)?',
}
NUMERIC = {0xE52F, 0xDDBE, 0xF198}   # helpers whose arguments are numbers
SPECIAL = {0xFA: 'plan verb', 0xFB: 'self', 0xFC: 'plan iobj', 0xFD: 'plan dobj',
           0xFE: 'number', 0xFF: '-'}


def arg_obj(n):
    if n in SPECIAL:
        return SPECIAL[n]
    if 0xF5 <= n <= 0xF9:
        return 'plan dobj'
    return f'{n} {ENT.get(n, "?")}'


def arg_num(n):
    return SPECIAL.get(n, str(n))


def _verb_records():
    """verb number -> address of the record or script a DO of that verb runs.
    128+ : the table at $9FAB. Others: the default-record table at $9F38 (three bytes a verb, ended by
    $FF); verbs with no default are done by the objects' own lists, so the shared action most of
    the objects use for the verb (when one clearly dominates)."""
    import collections
    rec = {}
    for v in range(128, 141):
        rec[v] = w(0x9FAB + 2 * (v - 128))
    a = 0x9F38
    while b(a) != 0xFF:
        rec[b(a)] = w(a + 1)
        a += 3
    use = collections.defaultdict(collections.Counter)
    for e in entities():
        for v, sh in e['actions']:
            use[v][sh] += 1
    rec[29], rec[30] = 0x9AF4, 0x9AE1   # a cabbie's GO TO / GO FURIOUSLY TO (the police man's are below)
    for v, cnt in use.items():
        if v not in rec:
            (top, n), = cnt.most_common(1)
            if n * 3 >= 2 * sum(cnt.values()):
                rec[v] = w(0xAA71 + 2 * (top - 1))
    return rec


VERB_REC = _verb_records()


POLICE_REC = {29: 0x9A99, 30: 0x9ACB}   # the local police men's own GO TO / GO FURIOUSLY TO


def verb_name(v, police=False):
    if v in SPECIAL or v >= 0xF5:
        return arg_obj(v)
    name = SHORT[v] if v >= 128 else VERBS.get(v, "?")
    if police and v in POLICE_REC:
        return f'{v} #R${POLICE_REC[v]:04X}({name})'
    if v in VERB_REC:
        return f'{v} #R${VERB_REC[v]:04X}({name})'
    return f'{v} {name}'


def label(r):
    x = r['raw']
    c = r['code']
    if c == 0:
        t = 'spent one-shot byte'
    elif c == 1:
        t = f'DO {verb_name(x[1])}'
    elif c == 2:
        v = x[1]
        if v in (128, 131, 134):
            t = f'DO {verb_name(v)}: {arg_obj(x[2])}, {room(x[3])}'
        elif v in (137, 139):
            t = f'DO {verb_name(v)}: verb {verb_name(x[2])}, ' + (arg_obj(x[3]) if v == 137 else arg_num(x[3]))
        elif v in (138, 140):
            t = f'DO {verb_name(v)}: {arg_obj(x[2])}, {arg_num(x[3])}'
        elif v == 136:
            t = f'DO {verb_name(v)} {arg_num(x[2])}'
        else:
            t = f'DO {verb_name(v)}: {arg_obj(x[2])}, {arg_obj(x[3])}'
    elif c in (3, 7):
        tgt = r['target']
        name = HELPERS.get(tgt, '')
        args = '' if c == 3 else f' ({arg_num(x[3]) if tgt in NUMERIC else arg_obj(x[3])}, '\
            f'{arg_num(x[4]) if tgt in NUMERIC else arg_obj(x[4])})'
        t = f'RUN #R${tgt:04X}' + (f' {name}' if name else '') + args
    elif c == 4:
        t = f'ASK {arg_obj(x[1])} TO {verb_name(x[2], police=x[1] in (11, 12))}: {arg_obj(x[3])}, {arg_obj(x[4])}'
    elif c == 5:
        t = f'SAY TO {arg_obj(x[1])} message #R${r["msg"]:04X}' + msg_text(r['msg'])
    elif c == 6:
        t = f'PRINT message #R${r["msg"]:04X}' + msg_text(r['msg'])
    elif c == 8:
        t = f'SIGNAL {arg_obj(x[1])}'
    elif c == 9:
        t = f'AWAIT {arg_obj(x[1])}'
    elif c == 0xA:
        t = 'RETURN FAIL'
    elif c == 0xB:
        t = 'RETURN OK'
    elif c == 0xE:
        t = f'GOTO #R${r["goto"]:04X}'
    elif c in (0xD, 0xF):
        t = 'PASS'
    else:
        t = 'opcode 12'
    fl = []
    if r['oneshot']:
        fl.append('once')
    if r['op'] & 0x40 and r['code']:
        fl.append('busy')
    if r['ok'] is not None:
        fl.append(f'ok #R${r["ok"]:04X}')
    if r['fail'] is not None:
        fl.append('fail: wait here' if r['fail'] == r['addr'] else f'fail #R${r["fail"]:04X}')
    return t + (f' [{"; ".join(fl)}]' if fl else '')


RECS, STARTS, INSTRS = allplans.collect()
# Two more entry points found by searching code for pointers into the
# script area: $9B20 returns HL = $F3AD with carry set (the sub-script
# convention), and $F05C is a two-instruction idle loop no code or
# script reaches.
EXTRA = {0xF3AD: 'returned as a sub-script by $9B20', 0xF05C: 'not reached from anywhere found'}
for s, why in EXTRA.items():
    STARTS.setdefault(s, set()).add(why)
    INSTRS.update(allplans.walk([s]))

ACTOR_SCRIPTS = {}
a = 0x9860
while b(a) != 0xFF:
    ACTOR_SCRIPTS.setdefault(w(a + 1), []).append(b(a))
    a += 8

cov = {}
for ia, r in INSTRS.items():
    for i in range(r['size']):
        cov[ia + i] = ia
addrs = sorted(cov)
regions = []
s = p = addrs[0]
for x in addrs[1:]:
    if x != p + 1:
        regions.append((s, p + 1))
        s = x
    p = x
regions.append((s, p + 1))


def why_text(ws):
    out = []
    for x in sorted(ws):
        if x.startswith('actor '):
            n = int(x.split()[1])
            out.append(f'{ENT.get(n, "?")} ({x})')
        elif x.startswith('default for verb '):
            n = int(x.split()[3])
            out.append(f'{x} ({VERBS.get(n, "?")})')
        elif x.startswith('shared '):
            n = int(x.split()[1])
            out.append(f'{x} ({SHARED_NAMES.get(n, "no object uses it")})')
        elif x.startswith('internal verb '):
            n = int(x.split()[2])
            out.append(f'{x} ({INTERNAL[n]})')
        else:
            out.append(x)
    return '; '.join(out)


SCRIPT_BLOCKS = []
for (s, e) in regions:
    hdr = [r for r in RECS if b(r) & 0x80 and r + header_len(r) == s]
    start = hdr[0] if hdr else s
    entries = sorted(x for x in STARTS if s <= x < e)
    who = [why_text(STARTS[x]) for x in entries]
    if hdr:
        rw = why_text(RECS[start])
        title = f'Sub-script: {rw}'
    else:
        title = 'Plan script: ' + who[0]
    desc = [f'Entry points: ' + '; '.join(f'${x:04X} = {why_text(STARTS[x])}' for x in entries) + '.',
            'Decoded by tools/plan.py; see $CC78 for the language. Each sub-block is '
            'one instruction. Room and object numbers are as the game uses them '
            '(the reference pages list both). Labels for verbs 128-140 and for the '
            'common helper records ($E52F, $E57A, $E588, $E5A8, $DDBE, $F198) were '
            'read from those records\' code, not tried one by one in the emulator.',
            "In an instruction, 'plan dobj' and 'plan iobj' are not fixed objects: they mean the direct and indirect object currently held in the actor's plan registers (bytes +4 and +5 of its actor record), so the same step works on whatever the actor is dealing with - for the player, the objects of the command just typed. 'plan verb' is the verb register (+3), 'self' is the acting character, and '-' means none."]
    subs = []
    if hdr:
        subs.append(('B', start, header_len(start), header_label(start) + ' - checks-only: the script follows'))
    for ia in sorted(x for x in INSTRS if s <= x < e):
        r = INSTRS[ia]
        lab = label(r)
        if ia in STARTS and ia != s:
            lab = f'Entry ({why_text(STARTS[ia])}): ' + lab
        subs.append(('B', ia, r['size'], lab))
    if start in A:
        A[start]['t'] = 'b'
        A[start]['title'] = title
        A[start]['desc'] = desc + A[start]['desc']
        A[start]['subs'] = subs
        A[start]['comments'] = {}
    else:
        blk(start, 'b', title, desc, subs=subs)
    A[start]['end'] = e
    SCRIPT_BLOCKS.append((start, e))

# Make sure every script block ends at a block boundary: the record or
# code after it gets its own block.
for (_s, e) in SCRIPT_BLOCKS:
    if e in A:
        continue
    if e in RECS and not (b(e) & 0x80):
        action_record(e, f'Action record: {why_text(RECS[e])}',
                      ['Found as the target of a plan script (tools/allplans.py). Not traced.'])
    elif e == 0x994D:
        blk(e, 'b', 'Records not yet decoded (handlers at $99FC-$9A7C)',
            ["Follows the player's plan script. The handlers that read "
             "these records are at $99FC (overlay 07); the format is not "
             "decoded."])
    elif e == 0xF3C2:
        pass   # the picture interpreter, already a block
    else:
        blk(e, 'c', f'Code after a plan script (${e:04X})', ['Not yet examined.'])

# The internal-verb table.
A[0x9FAB]['title'] = 'Verbs 128-140: the verbs only plan scripts use'
A[0x9FAB]['desc'] = [
    "A DO instruction in a plan script with a verb number of 128 or more "
    "comes here instead of to the parser's verb table: $C4D1 sends verbs "
    "with bit 7 set to $C583, which takes the record for verb 128+n from "
    "entry n. The player can never type these. Records with flags bit 7 "
    "set are sub-scripts.",
    "CORRECTED: an earlier version said where the index came from was not "
    "traced and that some records 'do not read as code' - they are plan "
    "scripts."] + A[0x9FAB]['desc'][2:]
A[0x9FAB]['subs'] = [('W', 0x9FAB + 2 * k, 2, f'Verb {128 + k}: ${w(0x9FAB + 2 * k):04X} - {INTERNAL[128 + k]}')
                     for k in range(13)]
fix_text(0xC583, 'not yet traced where it comes from',
         'a verb of 128 or more, from a DO in a plan script')

# The player's script: worth spelling out.
A[0x9921]['title'] = "Plan script: you (actor 0) - read, parse and do the player's commands"
A[0x9921]['desc'].insert(0,
    "The player is a character like any other, and this is its script. "
    "Each pass: $D6BF (its pre-check $D898 not traced; if it refuses, "
    "the player WAITs instead), $D715 turns the line ($5B00) into a "
    "list of words at $5B81 ($D9C5), $D769 checks for words left, $D77E looks the next words up "
    "($AAB2) and splits off one sentence ($9FF0 -> $9FF2), $D7D9 checks "
    "that there is a sentence, $D7FA parses it ($B191) into a verb and "
    "objects and copies them into the plan registers ($D826, $D82C), and "
    "DO plan verb / plan dobj / plan iobj carries it out. When a step "
    "fails the script goes back a step or two, which is how a line with "
    "several commands is worked through one sentence per turn. Read from the code; "
    "the five RUN targets are the same five addresses an earlier live "
    "trace saw at the start of every command.")

# A sub-script return through code: the hailed cab.
if 0xE2C7 not in A:
    action_record(0xE2C7, 'Shared action 11: HAIL / GET a hansom cab',
        ["Sets up the hailed cab ($E2EE) with the plan script at $F2B6, "
         "with the person hailing it as the plan's direct object. That "
         "script takes the fare where it asks to go. Read from the code; "
         "the cabbie (actor 31) was seen running the $F2B6 script in "
         "the emulator during a 106-turn trace."])

# ---------------------------------------------------------------------
# Requirement codes
# ---------------------------------------------------------------------

REQ = [
    "0: none. 1 and 2: the object must be a room whose record ($D224, "
    "the room table at $840B) has bit 7 of byte 0 set; 1 also needs "
    "$D471 to find something. 3: $D471 must find something. 4 and 7: "
    "anything. 5: a number ($A034 = $FE) with bit 7 of the value "
    "clear (WAIT UNTIL); 6: the same with bit 7 set (PAY TO). 8: the "
    "object must be here ($C821). 9: TAKE - here, in exactly one "
    "location ($C8A7), not a person ($C8BE), small enough for the "
    "actor to carry ($C8C6), and not held by a person ($C8AF). 10: "
    "here and held by the actor. 11: here and in more than one "
    "location - a door or passage. 12: a person, with no visibility "
    "check (FOLLOW). 13-15: here and a person.",
    "Confirmed in the emulator: TAKE PLAIN DOOR, TAKE WATSON, GO THROUGH "
    "PLAIN DOOR and TAKE DISGUISE get 'I SEE NO ... THAT YOU CAN ...'; "
    "DROP LAMP when not carried, TALK TO LAMP, GO THROUGH LAMP, FOLLOW "
    "LAMP, GIVE LAMP TO WATSON when not carried and a second TAKE LAMP "
    "get 'YOU CANNOT ... THE ...'; PAY 5 TO WATSON gets 'DON'T BE "
    "SILLY.'",
]
blk(0xC628, 'c', "Check the direct object against the action record's requirement",
    ["The low nibble of an action record's byte 0 is a requirement code "
     "for the direct object, copied to $A00F by $C571; the low "
     "nibble of byte 1 is the same for the indirect object ($C6BE). "
     "Returns Z to refuse ($C632 is JP $DC15). Codes 7-15 are handed to "
     "$C7A6."] + REQ)
blk(0xC6BE, 'c', "Check the indirect object against the action record's requirement",
    ["As $C628, for the indirect object and the low nibble of byte 1 "
     "($A010). $C6B8 sets $A021 = 1 (the indirect object is being "
     "checked); $C654 sets it to 0."])
blk(0xC7A6, 'c', 'Check object C against requirement code A (7-15)',
    ["The second half of the requirement checks; see $C628 for the "
     "codes. Each refusal goes to $C632, each pass to $C62F."])
blk(0xC898, 'c', "Follow IY's containment chain",
    ["Swaps IX and IY ($C89E), follows the chain ($C86E), and swaps back."])
blk(0xC8A7, 'c', 'How many locations has object A? (Z if exactly one)',
    ["Byte 0 of the object's record minus 1."])
blk(0xC8AF, 'c', 'Is object A held, at any depth, by a person?',
    ["Climbs the containment chain (+1) until it reaches nothing ($FF, "
     "Z) or a container that is a person (NZ)."])
blk(0xC8BE, 'c', 'Is object A a person? (NZ if so)',
    ["Bit 6 of the object's +5 flags."])
blk(0xC8C6, 'c', 'Can the actor carry object A as well as what it holds?',
    ["Adds the object's size ($D2F2) to the actor's load and compares "
     "it with the actor's capacity (+3). NZ if it fits. Read from the "
     "code."])
fix_text(0xC9BF, "byte 1 holds a value whose high nibble is stored at $A01F (meaning not confirmed - see below)",
         "byte 1 holds a value whose high nibble is stored at $A01F (meaning not confirmed - see below). "
         "UPDATED: the low nibbles of bytes 0 and 1 are requirement codes for the direct and "
         "indirect objects, checked by $C628 and $C6BE")
fix_text(0xC9BF, "bit 7: stop after the checks with carry set, without running the body.",
         "bit 7: stop after the checks with carry set, without running the body - "
         "UPDATED: the bytes after such a header are a plan script, which the caller "
         "($C9A7) makes the actor run as a sub-script.")

# ---------------------------------------------------------------------
# Trivia
# ---------------------------------------------------------------------

fact('plan-scripts',
     "Every character, the player included, runs a script",
     "Sherlock's characters are not driven by code but by scripts in a "
     "small language of fifteen opcodes (one unused): do a command, run an "
     "action record, order someone else to do something, say or print "
     "a message, signal or wait for another character, return from a "
     "sub-script, pass, and go to. 24 actors (the table at $9860) have "
     "a script; tools/plan.py decodes them and the disassembly labels "
     "every instruction. The player's own script ($9921) is the one "
     "that reads the keyboard: typing a command is just the player's "
     "plan step 'DO plan verb / plan dobj / plan iobj'.",
     "Characters do exactly what the player does: a script's DO goes "
     "through the same command code ($C4D1): requirement checks, default records, object action "
     "lists and pre-checks as a typed command. That is why "
     "characters can fail to do things for the same reasons the "
     "player can.",
     "The interpreter can also erase an instruction once it has "
     "succeeded (bit 5, $CF43), so that it never runs again - but no "
     "script uses that: none of the decoded instructions has bit 5 set. "
     "CORRECTED the same day: an earlier draft of this entry said the "
     "scripts edit themselves. What was "
     "confirmed in the emulator is the decoding itself: across 106 "
     "turns and 15,038 fetches, the interpreter fetched only "
     "instructions tools/plan.py decodes.")
fact('waiting-for-the-hour',
     "Characters keep appointments by failing until the time is right",
     "Verb 136 succeeds only when the clock's hour equals its argument, "
     "counted 1-24: $F1D6 turns 13-24 into 1-12 with 'p', and 1-12 "
     "into 1-12 with 'a', and compares with the hour at $9FE0 and the "
     "letter at $9FE2. A script instruction 'DO 136 23' whose failure "
     "address is itself therefore means 'wait here until 11pm'. 23 "
     "instructions use it, in the scripts of Inspector Lestrade, "
     "Phipps, the Major and Tricia Fender.",
     "Confirmed in the emulator over 110 turns of WAIT from the start: "
     "Tricia Fender (actor 13) asked verb 136 for hour 1 every minute "
     "and was refused all Monday afternoon - at 1pm $9FE0 was 1 but "
     "$9FE2 was 'p', and she is waiting for 1am - and from 2:25pm the "
     "Major (actor 7) began asking for hour 23. No success was seen in "
     "that window, as the reading predicts.")
fact('unused-hang-opcode',
     "Plan opcode 12 would hang the game",
     "The interpreter's test for opcode 12 is CP $0C / JR Z,$CD08 - and "
     "$CD08 is that JR Z itself, so with Z set it jumps to itself for "
     "ever. No script found uses opcode 12 ($CF03 still gives it a "
     "length of five bytes). Read from the code.")
fact('follow-climbs-in',
     "FOLLOW WATSON puts you in Watson's armchair",
     "Confirmed in the emulator: FOLLOW WATSON at the start answers "
     "'You climb into watsons armchair.', the player's container "
     "changes from 255 (none) to 24, and LOOK then says 'You are in "
     "watsons armchair with Watson.' FOLLOW's default record ($E452) "
     "is a sub-script: it runs $E488 on the person followed, which "
     "leaves its choice in the plan's verb register ($9FD6, written at "
     "$E492), then ENTERs or CLIMBs INTO that, giving up when a "
     "countdown of 10 runs out. Read from the script; only the outcome "
     "above was seen in the emulator.")
fact('examine-closely',
     "EXAMINE CLOSELY finds hidden things that EXAMINE does not",
     "Verb 20 is EXAMINE CLOSELY (in that word order: EXAMINE CLOSELY "
     "TRASH PILE; 'EXAMINE TRASH PILE CLOSELY' gets 'WHAT ?'). The trash "
     "pile's own EXAMINE (shared action 19, $E0E0) is a sub-script: "
     "run EXAMINE CLOSELY, then $E0EB, which sets the 'revealed' bit "
     "(+5 bit 7, $9C56) of the torn coded note. Confirmed in the "
     "emulator: in Basils Yard it answers 'You closely examine the "
     "trash pile.', takes 4 minutes, the note's +5 goes from $00 to "
     "$80, LOOK shows the note in the pile and TAKE NOTE works; plain "
     "EXAMINE takes 1 minute and reveals nothing. The drawer's "
     "sub-script (shared 17, $E0F2) does the same for the false bottom "
     "(object 63) - read from the code only.")

# ---------------------------------------------------------------------
# Code/data split fixes found while doing the above
# ---------------------------------------------------------------------

blk(0xB5D3, 'c', "Ask the player which object, or what",
    ["Prints one of the parser's questions, with the words of the "
     "player's own command as message parameters pushed on the stack: "
     "$6888 'WHICH <word> ?' ($B5F5), $6880 '<word> WHAT ?' ($B609) or "
     "$687C '<word> THE <word> WHAT ?' ($B628). $B65F and $B6AE print "
     "$6855 and $6894 instead in some cases (not rendered yet).",
     "Self-modifying: $B62F loads $28 (the opcode of JR Z) and $B633 "
     "$20 (JR NZ); $B635 writes it over the jumps at $B649 and $B658, "
     "which decide whether the words in the saved verb pattern ($B18E, "
     "+2/+3 and +4/+5, with +7 bit 7 and bit 5 of the first word as "
     "flags) are included.",
     "CORRECTED: the automatic split had parts of this as data; found "
     "because the message reference at $B628 landed in a data block."],
    comments={0xB5F5: '"WHICH ... ?"', 0xB609: '"... WHAT ?"', 0xB628: '"... THE ... WHAT ?"',
              0xB62F: 'JR Z opcode...', 0xB633: 'JR NZ opcode...',
              0xB635: '...written into the jumps below (self-modifying)',
              0xB649: 'Modified by $B635', 0xB658: 'Modified by $B635'})
A[0xB5D3]['end'] = 0xB6AE

for addr, msg, txt in ((0xCBBB, 0x68D1, 'SORRY IT IS TOO DARK.'),
                       (0xDCBB, 0x68B7, 'YOU ARE CARRYING THE ...'),
                       (0xE36A, 0x683F, 'YOU DO NOT HAVE ENOUGH.')):
    blk(addr, 'c', f'Refusal: "{txt}"',
        [f"A pre-check that refuses returns HL = this address; the "
         f"caller then runs it. Prints ${msg:04X}. CORRECTED: the "
         f"automatic split had this as data."])

GAME_OVER = {
    0x9E48: ("Game-over record: the ending at $9E4A",
             "Prints $6B79 when $9E60 finds the thing in A (3, then 2) in "
             "the player's room, otherwise $6AF3; both end the game "
             "through $9E74. Run by Phipps's script ($EF89). The two "
             "messages are not rendered yet."),
    0x9E6A: ("Game-over record: 'I do not think you are doing too well'",
             "Ends the game with $693A unless $9D90 is set. Run by "
             "Inspector Lestrade's script ($E932). Confirmed in the "
             "emulator: a player who only types WAIT from the start "
             "gets 'I do not think you are doing too well, surely "
             "Sherlock Holmes could do a better job than you have done "
             "so far. Perhaps you should try again.' at 2:59pm on Monday, "
             "and the game restarts."),
    0x9E85: ("Game-over record: the Major is arrested",
             "Does nothing once $9E88 - the operand of its own "
             "LD A,$00 (self-modifying) - is non-zero, which the routine of "
             "the case statement MAJOR PERCIVAL FFOULKES IS INNOCENT sets "
             "when it is proven ($9A3D, which also prints $70F0: 'VERY GOOD "
             "HOLMES, I SHALL RETURN TO LEATHER HEAD TOMORROW TO HAVE "
             "ANOTHER LOOK AROUND.'). Otherwise prints $6975 ('AS THE MAJOR "
             "ENTERS LESTRADE ATTEMPTS TO ARREST HIM...') and ends the game "
             "with $69BF ('...WELL HOLMES THAT WRAPS UP THIS CASE, SORRY YOU "
             "WERE NOT OF MORE HELP...') if Lestrade is where the player is "
             "($A009 = $A00A), or $6A26 ('INSPECTOR LESTRADE ENTERS AND "
             "SAYS...') if not. Run by Lestrade's script ($E96B). CORRECTED "
             "the same day: this first said the opposite (that it runs only "
             "when $9E88 is set) - the test is AND A / RET NZ. Read from "
             "the code."),
    0x9EA2: ("Game-over record: the ending at $9EA4",
             "Ends the game with $6A33 unless bit 1 of +3 is set in "
             "both $9973 and $9981 (records of the table after the "
             "player's script), in which case $6ABD. Run by Lestrade's "
             "script ($EAB3). Messages not rendered yet."),
}
for addr, (title, text) in GAME_OVER.items():
    if addr in A:
        del A[addr]
    action_record(addr, title, [text, "$9E74 is the shared ending: prints the "
                  "message in HL, waits for a key ($C306), and restarts ($B0AC)."])
blk(0x9E74, 'c', 'End the game with the message in HL',
    ["Prints HL's message, waits for a key ($C306), calls $A296 and "
     "restarts the game ($B0AC). Reached from the game-over records "
     "at $9E48-$9EBF and from $DFCA."])

# Every action record the scripts use gets its own block, so its header
# is shown as data and its body as code. A block ends at the next
# annotated block when that is close; any automatic boundaries between
# (several of which fell inside instructions) are dropped.
NEW = []
for r in sorted(RECS):
    if r in A or b(r) & 0x80:
        continue
    action_record(r, f'Action record: {why_text(RECS[r])}',
                  ['Found as an action record by tools/allplans.py (from the '
                   'action tables or a RUN in a plan script). Not traced.'])
    NEW.append(r)
for r in sorted(A):
    if A[r].get('t') != 'c' or A[r].get('end'):
        continue
    if not (0xDC00 <= r < 0xF3C2 or 0x9E40 <= r < 0x9EC0):
        continue
    nxt = min((k for k in A if k > r), default=None)
    if nxt and nxt - r <= 0x60:
        A[r]['end'] = nxt
blk(0xF3C2, 'c', A[0xF3C2]['title'] if 0xF3C2 in A else 'The picture interpreter',
    A[0xF3C2]['desc'] if 0xF3C2 in A else ['Draws a room picture; not traced (the harness skips it).'])

A[0xE1D6]['end'] = 0xE22A
blk(0xE22A, 'b', 'A table searched by $E207 (part of TELL)',
    ["Read by the loop at $E207, which compares A with each entry's "
     "first byte; $FE and $FF bytes are markers. Format not decoded. "
     "CORRECTED: the automatic split had this as code."])


# ---------------------------------------------------------------------
# A generated page: the cast and what their scripts do
# ---------------------------------------------------------------------
import html as _html  # noqa: E402
from plan import walk as _walk  # noqa: E402


def _summary(start):
    got = _walk([start])
    hours, rooms_, said, partners, ends, puts = set(), set(), [], set(), set(), set()
    for a2, r in sorted(got.items()):
        x = r['raw']
        if r['code'] == 2 and x[1] == 136:
            hours.add(x[2])
        if r['code'] == 2 and x[1] == 131 and x[3] < 0xF5:
            rooms_.add(x[3])
        if r['code'] == 2 and x[1] == 128 and x[3] < 0xF5:
            puts.add((x[2], x[3]))
        if r.get('msg') is not None:
            said.append((a2, r['msg']))
        if r['code'] in (8, 9) and x[1] < 0xF5:
            partners.add(('signals' if r['code'] == 8 else 'waits for', x[1]))
        if r.get('target') in GAME_OVER or r.get('target') == 0xDFCA:
            ends.add(r['target'])
    return got, hours, rooms_, said, partners, ends, puts


def _hour(h):
    return f'{(h - 1) % 12 + 1}{"am" if h < 13 else "pm"}' if 1 <= h <= 24 else str(h)


_rows = []
_seen = set()
for start, ids in sorted(ACTOR_SCRIPTS.items(), key=lambda kv: kv[1][0]):
    got, hours, rooms_, said, partners, ends, puts = _summary(start)
    names = ', '.join(f'{i} {_html.escape(ENT.get(i, "?"))}' for i in ids)
    bits = []
    if hours:
        bits.append('waits for ' + ', '.join(_hour(h) for h in sorted(hours)))
    if partners:
        bits.append('; '.join(f'{k} {_html.escape(ENT.get(n, str(n)))}' for k, n in sorted(partners)))
    if rooms_:
        bits.append('checks where people are: ' + ', '.join(_html.escape(room(n)) for n in sorted(rooms_)))
    if puts:
        bits.append('moves things: ' + ', '.join(f'{_html.escape(arg_obj(o))} to {_html.escape(room(rm))}'
                                                 for o, rm in sorted(puts)))
    if ends:
        bits.append('can end the game: ' + ', '.join(f'#R${e:04X}' for e in sorted(ends)))
    lines = ''.join(f'<li>#R${a2:04X}: {_html.escape(msg_text(m, 110)[2:] or f"${m:04X}")}</li>'
                    for a2, m in said[:12])
    if len(said) > 12:
        lines += f'<li>... and {len(said) - 12} more</li>'
    _rows.append(f'<tr><td>{names}</td><td>#R${start:04X}</td><td>{len(got)}</td>'
                 f'<td>{"<br>".join(bits) or "-"}'
                 f'{"<ul>" + lines + "</ul>" if lines else ""}</td></tr>')

page('cast', 'The cast and their scripts',
     '<p>Every character runs a plan script (see #R$CC78 for the language). This table is '
     'generated from the scripts themselves by tools/plan.py: the instruction count is what '
     'is reachable from the actor\'s starting position, not counting sub-scripts it calls. '
     'Hours come from verb 136 ("is it this hour?"), rooms from verb 131 ("is this person in '
     'this room?") and moves from verb 128. Messages are the PRINT and SAY TO instructions, '
     'rendered by the game\'s own interpreter with "you" standing in for the speaker and '
     'the oil lamp for the object.</p>'
     '<p>The scripts were checked by running the game: over 106 turns every instruction '
     'the interpreter fetched was one this decoding finds. Who a character is waiting for, '
     'and the hours, are read from the scripts; most were not seen happening.</p>'
     '<table class="disassembly"><tr><th>Actor</th><th>Script</th><th>Instructions</th>'
     '<th>What it does</th></tr>' + ''.join(_rows) + '</table>')

# Earlier facts that called +1/+2 a "handler address".
fix_fact("boot-actor-table", "(a handler address at +1/+2)",
         "(UPDATED 2026-11-07: +1/+2 is not a handler but the actor's position in its plan "
         "script; +3/+4/+5 are its plan registers - see the 'plan scripts' entry)")
fix_fact('npc-turn-processing-confirmed', "read a handler address out of the record's own fields",
         "read its script position out of the record's +1/+2 (UPDATED 2026-11-07: "
         "a plan script, not a handler - see the 'plan scripts' entry)")

# ---------------------------------------------------------------------
# Orders and speech waiting for an actor: the list at $9FEE
# ---------------------------------------------------------------------

blk(0xB91F, 'c', 'Is an order or a remark waiting for the current actor?',
    ["Walks the list headed at $9FEE (the pseudo-node at $9FF0 holds "
     "the head) for an 8-byte node whose +0 is the current actor "
     "($A036). Z if one is found (IX = the node), NZ if not. Nodes are "
     "made by a plan script's ASK ($CDBF: +1 = $FF, +2/+3/+4 = verb and "
     "objects) and by $B8D1 when the player speaks to someone (+1 = 0, "
     "+5/+6 = the words, +7 from $A024). $CC37 calls this for every "
     "actor at the start of its turn and sets $CC0D for $CC78.",
     "CORRECTED 2026-11-07: this was titled 'setup-only', from a test "
     "that saw 25 hits during the intro and none during LOOK. Re-tested "
     "with breakpoints stepped over properly: LOOK 19 hits, WAIT 67, "
     "TAKE LAMP 18 - once per actor whose turn comes up, every turn. "
     "N ('YOU CANNOT GO NORTH.', which takes no time) 0. The id "
     "sequence the old test saw (0, 2-6, 104, 7-13, 31, 34, 36-43) is "
     "simply the actor table's order."],
    comments={0xB91F: 'Start of the order/remark list', 0xB923: 'Next node: Z at the end',
              0xB926: 'None left', 0xB928: 'Is it for the current actor?',
              0xB92E: 'Yes: Z, IX = the node', 0xB92F: 'No: keep looking',
              0xB931: 'Not found: NZ', 0xB933: ''})
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'b91f-is-setup-only':
        FACTS[i] = (eid, "CORRECTED: $B91F runs every turn, for every actor",
                    "An earlier round reported $B91F as intro-only: 25 hits "
                    "during the intro, none during LOOK. Re-tested on "
                    "2026-11-07 with every breakpoint stepped over: LOOK "
                    "19 hits, WAIT 67, TAKE LAMP 18, and 0 only for a "
                    "command that takes no time (N when there is no exit). "
                    "It looks for an order or a remark waiting for each "
                    "actor whose turn has come (see $B91F). The old test's "
                    "'scripted-looking' id order was the actor table's order.")
blk(0xB90E, 'c', "Find the current actor's waiting order or remark",
    ["$B91F, then remember the node at $B866 and point IY at its words "
     "(+5/+6)."])
blk(0xB936, 'c', 'Deal with an order or remark addressed to the current actor',
    ["Called from $CCB3, instead of the actor's script step, when "
     "$B91F found something for it. A node with +7 = 2 goes to $BA20 "
     "(Watson's and Lestrade's replies, tables $BA67 and $BB67 - not "
     "traced). A node from a plan script's ASK (+1 = $FF) is handled at "
     "$B98C: its verb and objects become the command, the node is "
     "removed, and the caller carries the command out ($C4D1). "
     "Otherwise the words the player said are parsed for this actor "
     "($B191). Read from the code."])
blk(0xB98C, 'c', "Take the command out of an ASK order",
    ["The order's verb and objects (+2, +3, +4, resolved by $CEDE) "
     "become the command; $B9FA removes the node."],
    comments={0xB98C: 'The ordered verb', 0xB995: 'Its direct object', 0xB99E: 'Its indirect object',
              0xB9A7: 'Remove the order from the list', 0xB9AA: ''})
blk(0xB9FA, 'c', 'Remove node IX from the order/remark list and free it',
    ["Unlinks IX from the list at $9FEE ($A104 finds its predecessor) "
     "and frees it ($A1C7)."])

# ---------------------------------------------------------------------
# The node heap, the actor table, the variables, the clock
# ---------------------------------------------------------------------

blk(0x9570, 'b', 'The node heap: 752 bytes for the engine\'s linked lists',
    ["Free memory for $A11C (allocate) and $A1C7 (free). At start it is "
     "one free block: $02F0 bytes (byte 0-1), no next free block (2-3), "
     "pointed to by the free-list head at $9FE3. Every list node the "
     "engine makes lives here: sub-script call frames ($CF80), orders "
     "and remarks ($CDBF, $B8D1), SIGNAL tokens ($CD24) and countdowns "
     "($E52F). A node of size n takes n + 3 bytes: a size byte and a "
     "2-byte link sit in front of the address the allocator returns.",
     "CORRECTED: the automatic split had this as a 945-byte code block "
     "(the largest unannotated one), together with the actor table."])
A[0x9570]['end'] = 0x9860
_actor_subs = []
a = 0x9860
while b(a) != 0xFF:
    i = b(a)
    _actor_subs.append(('B', a, 8, f'Actor {i} {ENT.get(i, "?")}: script ${w(a + 1):04X}, '
                        f'plan verb/dobj/iobj ${b(a + 3):02X} ${b(a + 4):02X} ${b(a + 5):02X}, '
                        f'+6/+7 ${b(a + 6):02X} ${b(a + 7):02X}'))
    a += 8
_actor_subs.append(('B', a, 1, 'End marker'))
blk(0x9860, 'b', 'The actor table: who acts, and where each is in its plan script',
    ["24 eight-byte records, ended by $FF, walked once per turn. +0 the "
     "actor's thing id; +1/+2 its position in its plan script (see "
     "$CC78); +3 the plan's verb, +4/+5 the plan's direct and indirect "
     "objects ($FF = none; loaded by $D008, saved by $D026); +6/+7 are "
     "0 in every record and were not seen used. $CC0E finds a record "
     "by id. The seven steam trains and two cabbies are actors too.",
     "CORRECTED: earlier rounds read +1/+2 as a handler address; it is "
     "a script position, and it changes as the actor's script runs."],
    subs=_actor_subs)
A[0x9860]['end'] = a + 1

_var_subs = [
    ('B', 0x9FD6, 1, "$9FD6: the plan's verb (argument $FA)"),
    ('B', 0x9FD7, 1, "$9FD7: the plan's direct object (argument $FD)"),
    ('B', 0x9FD8, 1, "$9FD8: the plan's indirect object (argument $FC)"),
    ('W', 0x9FD9, 2, '$9FD9: the plan instruction being run'),
    ('W', 0x9FDB, 2, "$9FDB: the current actor's record in the actor table"),
    ('W', 0x9FDD, 2, '$9FDD: minutes since the start'),
    ('B', 0x9FDF, 1, '$9FDF: the minute'),
    ('B', 0x9FE0, 1, '$9FE0: the hour, 1-12'),
    ('B', 0x9FE1, 1, '$9FE1: the day (0 = Monday)'),
    ('B', 0x9FE2, 1, "$9FE2: 'a' or 'p'"),
    ('W', 0x9FE3, 2, '$9FE3: the heap\'s free list'),
    ('W', 0x9FE5, 2, '$9FE5: countdowns (2-byte nodes: actor, count)'),
    ('W', 0x9FE7, 2, '$9FE7: SIGNAL tokens (2-byte nodes: from, to)'),
    ('W', 0x9FE9, 2, '$9FE9: sub-script call frames (7-byte nodes)'),
    ('B', 0x9FEB, 3, '$9FEB: not identified ($D781 clears $9FEB)'),
    ('W', 0x9FEE, 2, '$9FEE: orders and remarks waiting for actors (8-byte nodes)'),
    ('W', 0x9FF0, 2, '$9FF0: words the player has said, for the next remark'),
]
blk(0x9FD6, 'b', 'Game variables',
    ["The plan-script registers, the clock and the heads of the engine's "
     "linked lists (each list's head word doubles as the link of a "
     "pseudo-node 2 bytes further on, which is the address the list walk "
     "$A0F7 starts from: $9FE9 for tokens, $9FEB for frames, $9FF0 for "
     "orders). The clock fields were read from $BFD9; the rest from their "
     "users. Bytes not listed are not identified yet: among them $A009 "
     "(the room the player is in, which decides what is shown), $A00A (the current actor's room), "
     "$A00F/$A010 (requirement codes), $A013/$A015 (the direct and "
     "indirect objects' records), $A01F (minutes the action takes), "
     "$A033-$A036 (verb, direct object, indirect object, actor).",
     "CORRECTED: the automatic split had this as code."],
    subs=_var_subs)
A[0x9FD6]['end'] = 0xA040

blk(0xBFD9, 'c', 'Advance the clock by one minute',
    ["Counts the minutes since the start ($9FDD), then the minute "
     "($9FDF); at 60 the hour ($9FE0) moves on, 12 wrapping to 1; at "
     "12 the 'a'/'p' letter ($9FE2) flips (XOR $11 turns $61 into $70 "
     "and back), and when it becomes 'a' the day ($9FE1) moves on. "
     "Read from the code; consistent with the clock the game prints."],
    comments={0xBFD9: 'Minutes since the start', 0xBFE0: 'The minute...', 0xBFE5: '...reached 60?',
              0xBFE8: 'Yes: back to 0', 0xBFEA: 'The hour...', 0xBFEF: '...13 becomes 1',
              0xBFF6: 'Reached 12?', 0xBFF9: "Then 'a' and 'p' swap", 0xC001: "Now 'a'?",
              0xC004: 'Then it is the next day'})

blk(0xA0F7, 'c', 'Move IX to the next node of a list',
    ["Every engine list links its nodes through the 2 bytes in front of "
     "each node (IX-2/IX-1). Z at the end of the list."])
blk(0xA104, 'c', 'Find the node before node DE in the list at IY',
    ["Leaves IY at the node (or list head) whose link points at DE, so "
     "the caller can unlink DE."])
blk(0xA11C, 'c', 'Allocate a node of A bytes from the heap',
    ["Best fit: walks the free list ($9FE3) for the smallest free block "
     "of at least A + 3 bytes, splits it (or takes it whole if less than "
     "4 bytes would be left), writes the size byte in front, zeroes the "
     "node and returns IX = the node. With no block big enough it jumps "
     "to $C1D8 (not traced: presumably the out-of-memory end). Read from "
     "the code."])
blk(0xA1AF, 'c', 'Free every node of the list starting at IX', [])
blk(0xA1C7, 'c', 'Free node IX back to the heap',
    ["Puts the block back in the free list in address order and joins "
     "it to free neighbours ($A20C)."])

# Emulator results for the script-only verbs and the actor hand-overs
# (tools/experiments/verbs_test.py: 84 turns of WAIT from the start, until the
# game ends at 3pm).
A[0x9FAB]['desc'].insert(1,
    "Confirmed in the emulator over 84 turns: verb 131 succeeded 864 "
    "times, every time with the direct object really in the room named "
    "by the indirect object; verb 128 ran 4 times (Inspector Lestrade "
    "moving himself to room 53, the Major to room 92, and two others) "
    "and each time the object ended up in the named room. Verb 136 is "
    "checked in the Trivia entry on appointments. The other verbs' "
    "labels are read from their records' code.")
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'plan-scripts':
        FACTS[i] = (eid, title, body + "\n\n" +
                    "Characters really do co-ordinate through SIGNAL and AWAIT. "
                    "In 84 turns of WAIT from the start the emulator saw 19 "
                    "SIGNALs and 18 AWAITs that found their token - mostly "
                    "Inspector Lestrade and Chief Constable Straker, whose "
                    "scripts alternate SIGNAL and AWAIT around their "
                    "conversation, and later Lestrade, the Major and a police "
                    "man - and 13 ASK orders, nearly all given by Lestrade.")
A[0x9FD6]['desc'][0] = A[0x9FD6]['desc'][0].replace(
    "$9FE9 for tokens, $9FEB for frames, $9FF0 for orders",
    "$9FE7 for countdowns, $9FE9 for tokens, $9FEB for frames, $9FF0 for orders")

# The suffix table (task: labelled code by the automatic split).
_SUF = []
for k in range(9):
    raw = [b(0xA85C + 4 * k + j) for j in range(4)]
    txt = ''.join('<delete>' if c == 8 else chr(c) for c in raw if c)
    _SUF.append(('B', 0xA85C + 4 * k, 4, f'Suffix {k}: "{txt}"'))
blk(0xA85C, 'b', 'Word suffixes',
    ["Nine 4-byte entries, zero-padded, chosen by the low nibble of a "
     "dictionary word's flags ($F = no suffix; see dictionary.py). Code "
     "8 is a delete, so suffix 3 turns SPY into SPIES and suffix 7 RIDE "
     "into RIDING. $A93B indexes it.",
     "CORRECTED: the automatic split had this as code."], subs=_SUF)
A[0xA85C]['end'] = 0xA880
blk(0xA880, 'c', 'Print the dictionary word that HL refers to',
    ["HL points at a 2-byte word reference (low 12 bits: offset into the "
     "dictionary; high nibble: flags). Prints nothing when output is "
     "switched off ($5C3C = 0: the text belongs to something the player "
     "cannot see) or the reference is 0. Otherwise prints a space, finds "
     "the word through the per-letter index at $5D80, prints it ($A95B) "
     "and its suffix. Called by the object-name printers at $A39F-$A3F8 "
     "and by $D5E5. Read from the code, not traced in detail."],
    comments={0xA880: 'The word reference', 0xA887: 'Is output switched on?',
              0xA88B: 'No: print nothing', 0xA88C: 'Remember the reference',
              0xA890: 'A null reference?', 0xA89A: 'A space before the word'})

# Two of the largest 'code' blocks the automatic split left are data:
# nothing calls or jumps into them, the instructions do not hang
# together, and they are not message bytecode either (rendering from
# several points gives gibberish). Their format is not decoded.
for _a, _e in ((0xFBED, 0xFD6E), (0xFDED, 0xFEEA)):
    blk(_a, 'b', 'Data, not decoded',
        ["No code refers to any address in here (searched for LD rr,nn and "
         "CALL/JP operands), its 'instructions' do not hang together, and "
         "the message interpreter prints gibberish from it, so it is data "
         "of a kind not yet identified. It has runs of $80-$9F bytes "
         "(which look like dictionary references) separated by $08 and $FF "
         "bytes, perhaps the word patterns behind TELL and the replies at "
         "$BA67/$BB67 - not checked.",
         "CORRECTED: the automatic split had this as code. A false 'LD HL,"
         "$6F59' inside it ($FCD5) had been taken as a message reference; "
         "that entry has been dropped."])
    A[_a]['end'] = _e

blk(0xBA20, 'c', 'A remark for Watson or Inspector Lestrade: let them reply',
    ["Reached from $B936 when the node waiting for the actor has +7 = 2 "
     "(made by $B8D1 when the player speaks to someone). For Watson "
     "(actor 3) the reply code is at $BA67, for Lestrade (2) at $BB67; "
     "$BA3E runs it on the player's words (IY = node +5/+6, through "
     "$D1DB), then frees the words ($A1AF) and the node ($B9FA). Other "
     "actors ignore remarks. The reply code itself is not traced; the "
     "messages it prints include Lestrade's 'I DO NOT BELIEVE THAT YOU "
     "HAVE THE EVIDENCE TO PROVE THAT ...' ($BBC4)."],
    comments={0xBA20: 'Who is being spoken to?', 0xBA23: "Watson's reply code",
              0xBA2A: "Lestrade's reply code", 0xBA2D: '', 0xBA2F: 'Anyone else: ignore it',
              0xBA31: 'Let them reply', 0xBA34: 'Done (carry set: the turn is used)',
              0xBA3E: 'Run reply code HL on the remark at IX', 0xBA4E: '',
              0xBA54: 'Free the words', 0xBA5B: 'Remove the remark'})
A[0x9FAB]['desc'].insert(2,
    "Verb 129 was checked the same way: in 84 turns its comparison ran "
    "482 times and came out equal exactly when the two things' rooms "
    "(record +$0F) were equal.")

# ---------------------------------------------------------------------
# Header bit 4: flag tests on the objects, and the refusal that names
# the failing flag ("YOUR DOOR IS OPEN")
# ---------------------------------------------------------------------
A[0xC628]['end'] = 0xC6BE
A[0xC6BE]['end'] = 0xC74E
A[0xC7A6]['end'] = 0xC821
A[0xC628]['desc'].append(
    "After the code check, a record with flags bit 4 has five more "
    "header bytes: a byte of test modes and two pairs of masks, tested "
    "against the objects' +5 flags by $C74E ($C691 for the direct "
    "object; the indirect object's half is the same at $C6BE's end).")
blk(0xC74E, 'c', "Test object C's +5 flags against a record's masks",
    ["B holds two 2-bit modes and L/H two masks. Mode 0: every mask "
     "bit must be set; 1: at least one (or the mask is 0); 2: none may "
     "be set; 3: not all may be set (read from the code; modes 1 and 3 "
     "were not tried). On failure the offending bits go to $CB79 (bit 7 "
     "set when a bit was present that should not be) and HL = $CB7B, "
     "the refusal that names the flag.",
     "Confirmed in the emulator: OPEN YOUR DOOR when it is open leaves "
     "$CB79 = $A0 and prints 'YOUR DOOR IS OPEN'; CLOSE YOUR DOOR when "
     "it is closed leaves $20 and prints 'YOUR DOOR IS CLOSED'. The "
     "door's +5 goes $80 -> $A0 when opened and back when closed."])
A[0xC74E]['end'] = 0xC7A6
blk(0xCB7B, 'c', 'Refuse by naming the flag that failed: "THE ... IS <word>"',
    ["Takes the lowest bit in $CB79 and prints $6817 ('THE <object> "
     "IS') followed by that bit's word: from $C471 when a needed bit "
     "was missing, from $C481 (bit 7 of $CB79 set) when a forbidden bit "
     "was present. The object is $CB7A, saved by $C685."])
_wt = {0xC471: ['UNLOCKED', None, 'EMPTY', None, 'OFF', 'CLOSED', 'DEAD', None],
       0xC481: ['LOCKED', None, 'FULL', None, 'ON', 'OPEN', None, None]}
for _t, _words in _wt.items():
    blk(_t, 'w', ('Words for a +5 flag that should be set but is not' if _t == 0xC471 else
                  'Words for a +5 flag that is set but should not be'),
        ["Dictionary word references, one per bit of an object's +5 "
         "flags, printed by $CB7B after 'THE <object> IS'. 0 = no word. "
         "Together the two tables name the flags: bit 0 locked, bit 2 "
         "full, bit 4 on (lit), bit 5 open, bit 6 alive; bit 7 is "
         "'revealed' ($9C56). Bits 5 and 7 are confirmed by play; the "
         "rest are read from these words."],
        subs=[('W', _t + 2 * k, 2, f'Bit {k}: ' + (_words[k] or 'none')) for k in range(8)])
fix_text(0xC9BF, "bit 4: five more header bytes follow (not decoded)",
         "bit 4: five more header bytes follow (UPDATED: flag tests on the objects' +5 bits, "
         "done by $C74E - see $C628)")
fact('object-flag-words',
     "The game's own error words name the object flags",
     "When an action needs an object's flag to be set or clear and it "
     "is not, $CB7B prints 'THE <object> IS' and a word from one of two "
     "tables, one per flag bit: UNLOCKED/LOCKED (bit 0), EMPTY/FULL "
     "(bit 2), OFF/ON (bit 4), CLOSED/OPEN (bit 5) and DEAD (bit 6, the "
     "bit that makes a thing a person). So the tables are a key to the "
     "+5 flags. Confirmed in the emulator for OPEN and CLOSE: 'YOUR DOOR "
     "IS OPEN' and 'YOUR DOOR IS CLOSED'.")
A[0xC471]['end'] = 0xC481
A[0xC481]['end'] = 0xC491
blk(0xC491, 'b', 'Rooms saved before an action',
    ["$C491: the current actor's room, and $C492: the direct object's "
     "room, saved by $CA22 before the action body runs, so $CAAF can "
     "tell afterwards whether anything moved. Read from the code."],
    subs=[('B', 0xC491, 1, "The actor's room"), ('B', 0xC492, 1, "The direct object's room")])
A[0xC491]['end'] = 0xC493

blk(0xC493, 'c', "Set the direct object's requirement from the parsed words",
    ["For a command that has not reached an action record yet: $A00F "
     "becomes 0, 4, 5 (a number) or 7 from the parser's word-class "
     "flags in $A01D/$A01E. $C4B2 does the same for the indirect object "
     "($A010). Read from the code."])
blk(0xC4B2, 'c', "Set the indirect object's requirement from the parsed words", [])
blk(0xC4D1, 'c', 'Carry out the command in $A033-$A035 for the current actor',
    ["The one entry point for doing a command, used for the player's "
     "typed commands and for every DO in a plan script. Verbs 128 and "
     "up go to $C583 (the script-only verbs). Otherwise the requirement "
     "codes are set from the parse ($C493, $C4B2); when the verb needs "
     "an object but none was given ($A034 = $FF), each candidate object "
     "($C463) is tried in turn until one works ($C55A) - which is how a "
     "character's 'DO TAKE' with no object picks something up. Then "
     "$C929 finds and runs the action record. Read from the code."],
    comments={0xC4D1: 'The verb', 0xC4D4: 'A script-only verb (128 and up)?', 0xC4D6: 'Yes: $C583',
              0xC4E2: 'Requirements for the direct object...', 0xC4E5: '...and the indirect object',
              0xC517: 'Needs an object but none given?', 0xC520: 'Try the next candidate',
              0xC525: 'Make it the direct object', 0xC529: 'Does the command work with it?',
              0xC53A: 'Find and run the action record'})

# ---------------------------------------------------------------------
# The main loop (task: find the main game loop and turn sequence)
# ---------------------------------------------------------------------
for _k in [k for k in A[0xA040]['comments'] if k >= 0xA064]:
    del A[0xA040]['comments'][_k]
A[0xA040]['desc'] = [p for p in A[0xA040]['desc']
                     if not p.startswith('Then walks a sentinel') and not p.startswith('CORRECTION, added')]
A[0xA040]['desc'].append(
    "CORRECTED 2026-11-07: the actor-table walk that follows is not part "
    "of start-up. From $A064 on is the game's main loop - see there.")
blk(0xA064, 'c', 'The main loop: one minute of game time per pass',
    ["Each pass is one minute. The clock moves on ($BFD9) and is "
     "printed ($BF79); then every actor in the table at $9860 whose "
     "next-turn time (+6/+7) has come takes its turn. A turn starts "
     "with $CC37 (find the actor, check for orders or remarks waiting "
     "for it) and then runs plan-script steps ($CC78) until one takes "
     "time ($A01F non-zero); that many minutes are added to the actor's "
     "next-turn time, and the actor's own after-turn routine, if it has "
     "one, runs ($9C77). The player is an actor like the rest: the "
     "player's script step is the one that waits for a typed command.",
     "Before the walk, if the player is in the middle of WAIT UNTIL "
     "(plan verb 50) and ENTER is pressed, the player's next-turn time "
     "is pulled back to now, so a long wait can be cut short.",
     "$A0DA is set at the end of the minute's walk to leave the loop: 1 "
     "($B0AC, after a game-over message) loads a saved game ($B0D7) and "
     "starts again from $A040; 2 ($B0C6, not traced back to the command "
     "that sets it) saves the game ($B0E4) and carries on.",
     "Confirmed in the emulator: the player's +6/+7 equals the minute "
     "counter ($9FDD) whenever the game waits for a command, and moves "
     "on by 5 for WAIT and by 1 for TAKE LAMP or EXAMINE LAMP; Watson's "
     "and Lestrade's move on in step. The per-actor call counts in the "
     "$B91F note ($CC37 once per actor per turn) agree."],
    comments={
        0xA064: 'Not ending yet', 0xA068: 'Is the game ending?', 0xA06C: 'Yes: restart or reload',
        0xA06E: 'A minute passes', 0xA071: 'Print the clock',
        0xA074: 'The player (first actor)...', 0xA078: '...waiting until a time (plan verb 50)?',
        0xA07F: 'Is a key down...', 0xA086: '...and is it ENTER?',
        0xA08A: 'Then the player acts now: next-turn time = this minute',
        0xA093: 'Walk the actor table', 0xA097: 'End of the table?',
        0xA09B: 'Yes: the next minute', 0xA09D: "Has this actor's time come?",
        0xA0A3: 'Not yet: next actor', 0xA0A5: 'Start its turn',
        0xA0AE: 'One plan step', 0xA0B3: 'Did it take any time?',
        0xA0B8: 'No: another step',
        0xA0BD: 'Add the time to its next-turn time',
        0xA0CA: 'Its own after-turn routine, if any',
        0xA0D1: 'Next actor (8 bytes on)',
        0xA0DB: "Compare the minute counter (HL) with the actor's next-turn time",
        0xA0E7: 'Ending: 2 = carry on (reloaded?), 1 = start again',
        0xA0EB: '', 0xA0F1: ''})
A[0xA064]['end'] = 0xA0F7

_ah = []
_a = 0x9C85
while b(_a) != 0xFF:
    _ah.append(('B', _a, 3, f'Actor {b(_a)} {ENT.get(b(_a), "?")}: ${w(_a + 1):04X}'))
    _a += 3
_ah.append(('B', _a, 1, 'End marker'))
blk(0x9C77, 'c', "Run the current actor's own after-turn routine",
    ["After every turn (from the main loop at $A0CC), looks the actor "
     "up in the table at $9C85 ($9C6A, through $D34E) and jumps to its "
     "routine. Nine characters have one. Read from the code; the "
     "routines are not traced."],
    comments={0x9C77: 'Has this actor a routine?', 0x9C7A: 'No',
              0x9C7B: 'Its address...', 0x9C84: '...jump to it'})
blk(0x9C85, 'b', 'After-turn routines for nine characters', [
    "Three-byte entries (actor id, routine address), ended by $FF, "
    "searched by $9C6A."], subs=_ah)
A[0x9C85]['end'] = _a + 1

# Actor table +6/+7: correct the claim made earlier in this overlay.
A[0x9860]['desc'][0] = A[0x9860]['desc'][0].replace(
    "+6/+7 are 0 in every record and were not seen used",
    "+6/+7 the minute (counted like $9FDD from the start) at which the "
    "actor next acts, set by the main loop ($A064); 0 at the start, so "
    "everyone acts in the first minute")
A[0x9860]['subs'] = [(d_, a_, l_, t_.replace('+6/+7', 'next turn at'))
                     for (d_, a_, l_, t_) in A[0x9860]['subs']]

blk(0x9CCE, 'c', 'Is thing C in the same room as the current actor, and visible to the player?',
    ["Z if C is in the actor's room ($A017's +$0F) and the player can "
     "see it ($C821); NZ otherwise. Read from the code."])
blk(0x9CE9, 'c', 'Say good morning to C, if just met',
    ["Used by after-turn routines: $9CF2 checks whether C is here and "
     "seen and whether the greeting countdown at HL has run out; if so "
     "the countdown is set to 30-44 minutes (30 plus a random number "
     "below 15) and $6929 is printed: '<actor> SAYS TO <C> \"GOOD "
     "MORNING\".' While C stays away the countdown runs down by one a "
     "turn, so characters greet each other again only after a while "
     "apart. Read from the code."],
    comments={0x9CE9: 'Just met C?', 0x9CEC: '"... SAYS TO ... GOOD MORNING"',
              0x9CF2: 'C becomes the direct object', 0x9CF6: 'Here and seen?',
              0x9CF9: 'Yes', 0x9CFB: 'No: count down (not below 0)',
              0x9D00: 'Return from the caller too: no greeting',
              0x9D02: 'Is the countdown over?', 0x9D06: 'Yes: wait 30-44 minutes before the next',
              0x9D0E: 'Greet'})
blk(0x9D13, 'c', "Watson's after-turn routine",
    ["Greets the player, Inspector Lestrade and Chief Constable Straker "
     "when he meets them (countdowns at $9D10-$9D12, through $9CE9), "
     "then continues at $E691 (not traced)."])
A[0x9921]['desc'].insert(1,
    "Confirmed in the emulator: 'TAKE LAMP. EXAMINE LAMP. INVENTORY' "
    "typed as one line is carried out one sentence a minute - the lamp "
    "is taken at 8:02, examined at 8:03 and the inventory listed at "
    "8:04, with the clock printed between, before the next prompt.")

# After an action body: narrate it and report what the player sees.
blk(0xCA60, 'c', 'Run the action body, then report what the player saw',
    ["Clears $CAAE, runs the body through the dispatcher ($CB2C), then "
     "$CA7F (the player's own view changed?) and, unless the body set "
     "$CAAE, $CAAF (someone came into the player's room?)."])
blk(0xCA76, 'c', 'Narrate the action, unless the verb is script-only',
    ["Calls $A2E4 for verbs below 128. $A2E4 copies the verb and objects "
     "and is very probably what prints the 'You take the oil lamp.' "
     "line (not traced)."])
blk(0xCA7F, 'c', "If the player's own view changed, describe the room",
    ["When the room seen by the player ($A009) is no longer the "
     "player's room, the room is described as if the player were the "
     "actor ($CA9E): in full the first time ($D102, which also sets bit "
     "6 of the room record: visited), briefly after that ($D1B2). Read "
     "from the code."])
blk(0xCAAF, 'c', "Announce a character coming into the player's room",
    ["For any actor but you (0), 1 and 100 ($DC6C): if it was not in "
     "the player's room before the action ($C491) and is now, prints "
     "$68ED, '<actor> ENTERS.' ($CBC2). Then, for actions whose direct "
     "object has to be here (requirement 7 or more), something similar "
     "for the object - not traced in detail. Read from the code."])
blk(0xCBC2, 'c', "Print message DE about thing A, if it is in the player's room",
    ["Does nothing for $FF or 0, or when the thing is somewhere else. "
     "Otherwise switches output on ($5C3C = 1) and prints DE with the "
     "thing as its subject."])

A[0xCBA7]['title'] = "Refuse if the character is busy: 'SORRY, I CANNOT DO THAT NOW.'"
A[0xCBA7]['desc'].append(
    "RESOLVED 2026-11-07: $B934 holds the first byte of the plan-script "
    "instruction the character was on when the player's request arrived "
    "($B953; cleared each step at $CC89), and bit 6 of that byte marks "
    "the instruction as busy. Confirmed in the emulator: SAY TO WATSON "
    "\"GET OUT\" at the start gets 'Watson gets out of watsons "
    "armchair.'; with bit 6 poked into Watson's current instruction "
    "($52 instead of $12) it gets 'Watson says \" Sorry, I cannot do "
    "that now. \"' and he stays in the chair.")
fact('busy-characters',
     "Characters can be too busy to do what you ask",
     "Bit 6 of a plan-script instruction marks it as busy: a character "
     "on such an instruction answers a request with 'Sorry, I cannot do "
     "that now.' ($CBA7). 181 of Inspector Lestrade's 223 instructions "
     "and 70 of Chief Constable Straker's 76 are busy; none of Watson's "
     "32 is, so SAY TO WATSON "
     "\"GET OUT\" works at the start. Confirmed in the emulator by "
     "setting the bit on Watson's current instruction: he then refuses "
     "and stays in his armchair.")

# ---------------------------------------------------------------------
# After-turn routines: the introduction to Lestrade, and the guards
# ---------------------------------------------------------------------
blk(0x9D30, 'c', "Chief Constable Straker's after-turn routine",
    ["Once Lestrade has been introduced ($9D90 set), greets the player "
     "and Watson when he meets them ($9CE9; countdowns at $9D2E/$9D2F)."])
blk(0x9D48, 'c', "A police man's after-turn routine: 'no one is to get by'",
    ["Until Lestrade has been introduced ($9D90 clear), tells the "
     "player, Watson or the Major (7), on meeting them, 'I AM SORRY SIR "
     "BUT I HAVE MY ORDERS, NO ONE IS TO GET BY.' ($6D9A, through "
     "$9D65). $9D73 is the same for the other police man. Read from the "
     "code."])
blk(0x9D73, 'c', "The other police man's after-turn routine", ["As $9D48."])
blk(0x9D90, 'b', "Lestrade's flags",
    ["$9D90: set when Inspector Lestrade has met the player together "
     "with Chief Constable Straker ($9E14) - the introduction. Until "
     "then the police men let no one by, Straker does not greet anyone, "
     "and at 3pm on Monday Lestrade's script ends the game ($9E6A: 'I "
     "do not think you are doing too well...'). $9D91-$9D94: Lestrade's "
     "message and greeting state. Read from the code; the 3pm ending is "
     "confirmed in the emulator for a player who never meets him."],
    subs=[('B', 0x9D90, 1, 'Lestrade has been introduced'), ('B', 0x9D91, 4, "Lestrade's message state")])
A[0x9D90]['end'] = 0x9D95
blk(0x9D95, 'c', "Lestrade's after-turn routine, after the introduction",
    ["Greets the player in his own way ($9DC6: 'WELL, HOLMES FANCY "
     "SEEING YOU HERE.' the first time), asks whether the player can "
     "prove the case yet ($9DD8: 'WELL CAN YOU PROVE THAT ... YET, "
     "HOLMES ?', worded from the deduction state at $BC46-$BC9C - not "
     "traced), greets Watson, and clears bit 0 of +3 in three of the "
     "records after the player's script. Read from the code."])
blk(0x9DFF, 'c', "Lestrade's after-turn routine, until the introduction",
    ["Waits until Chief Constable Straker and the player are both with "
     "Lestrade, in sight of the player ($9CCE); until then it does the "
     "same as $9D95. Then: sets $9D90, clears +$0A of rooms 92 and 62, "
     "rewrites Lestrade's own entry in the after-turn table ($9C86) to "
     "$9D95 so this never runs again (self-modifying data), and prints "
     "Straker's introduction - $7207, 'LESTRADE I WOULD LIKE YOU TO "
     "MEET MR SHERLOCK HOLMES...', or $7224. Read from the code."],
    comments={0x9DFF: 'Is Straker here?', 0x9E04: 'No: the usual routine',
              0x9E06: 'Is the player here?', 0x9E0D: 'Straker is the one speaking',
              0x9E12: 'Lestrade has been introduced', 0x9E17: 'Room 92...',
              0x9E20: '...and room 62: clear +$0A',
              0x9E29: 'From now on run $9D95 after his turns',
              0x9E34: 'Which introduction?', 0x9E44: 'Print it'})
fix_text(0x9E6A, "Ends the game with $693A unless $9D90 is set.",
         "Ends the game with $693A unless $9D90 is set - that is, unless the "
         "player has been introduced to Lestrade (see $9DFF).")
blk(0x9EC1, 'c', "After-turn routines for Strachan, the cook and the gardener",
    ["$9EC1 (Strachan), $9ECB (the cook) and $9ED1 (the gardener) share "
     "$9ED7, with a one-byte state each ($9EC0, $9ECA, $9ED0). Not "
     "traced."])
fact('meet-lestrade-by-3pm',
     "Be introduced to Lestrade by 3pm on Monday, or the game ends",
     "Confirmed in the emulator: a player who only types WAIT from the "
     "start is told at 2:59pm on Monday 'I do not think you are doing "
     "too well, surely Sherlock Holmes could do a better job than you "
     "have done so far. Perhaps you should try again.' and the game "
     "restarts. Read from the code: the record that ends it ($9E6A, run "
     "from Lestrade's script) does nothing once $9D90 is set, and $9D90 "
     "is set by Lestrade's after-turn routine ($9DFF) the first time "
     "Chief Constable Straker and the player are both with him. The same "
     "flag tells the police men to stop turning people away ('I AM SORRY "
     "SIR BUT I HAVE MY ORDERS, NO ONE IS TO GET BY.').")

blk(0xA9B5, 'w', 'Word buffer pointer for $A9B7',
    ["Where the next character of the word being collected goes; the "
     "buffer starts at $5C0B."], subs=[('W', 0xA9B5, 2, 'Next free byte in the word buffer')])
A[0xA9B5]['end'] = 0xA9B7
blk(0xA9B7, 'c', 'Print character A, a word at a time (word wrap)',
    ["Every character the message interpreter prints comes here. Unless "
     "quoted printing is on ($A027: straight to $C1E1), characters are "
     "collected in the buffer at $5C0B, a backspace (8) taking the last "
     "one off again - which is how suffixes such as '<delete>IES' work. "
     "A space, a carriage return or a quote mark ends the word: if the "
     "word is longer than the count at $C1F5 allows, a new line is "
     "started first, and then the word is sent to $AA14 character by "
     "character. $AA14 turns letters to lower case and drops spaces at "
     "the start of a line ($A025 = 0 there). Read from the code."],
    comments={0xA9B7: 'Quoted printing on?', 0xA9BC: 'Yes: print it as it is',
              0xA9C1: 'The end of the word so far', 0xA9C4: 'A space...', 0xA9C8: '...a carriage return...',
              0xA9CC: '...or a quote mark ends the word', 0xA9D0: 'A delete...',
              0xA9D4: '...takes the last letter back', 0xA9D7: 'Otherwise add the letter',
              0xA9DF: 'An empty word?', 0xA9E8: 'Does the word fit?', 0xA9EF: 'No: new line first',
              0xA9F4: 'Send the word out', 0xAA0B: '...then the character that ended it'})
blk(0xAA14, 'c', 'Send one character to the screen layer',
    ["Letters become lower case; a space at the start of a line is "
     "dropped; carriage returns, quote marks and full stops get special "
     "handling (not traced past $AA46)."])

A[0x9EA2]['end'] = 0x9EC0
for _a, _n, _who in ((0x9D10, 3, "Watson's greeting countdowns: the player, Lestrade, Straker"),
                     (0x9D2E, 2, "Straker's greeting countdowns: the player, Watson"),
                     (0x9D45, 3, "A police man's warning countdowns: the player, Watson, the Major"),
                     (0x9D70, 3, "The other police man's warning countdowns"),
                     (0x9EC0, 1, "Strachan's after-turn state"),
                     (0x9ECA, 1, "The cook's after-turn state"),
                     (0x9ED0, 1, "The gardener's after-turn state")):
    blk(_a, 'b', _who, ["Minutes to go before the next greeting or warning (see $9CE9)."
                         if _a < 0x9EC0 else "Used by $9ED7; not traced."])
    A[_a]['end'] = _a + _n
for _a in (0x9ECB, 0x9ED1):
    if _a not in A:
        blk(_a, 'c', 'After-turn routine: ' + ('the cook' if _a == 0x9ECB else 'the gardener'), ['See $9EC1.'])

A[0xDDD0]['title'] = 'Default action: WAIT UNTIL (verb 50)'
A[0xDDD0]['desc'] = [
    "Works out how many minutes there are from now until the time typed "
    "(the number at $A02F: hour and minute in 6-bit fields, bit 6 of "
    "the hour marking am and bit 6 of the minute pm), converting both "
    "times to minutes past 12 o'clock ($DE48: hours x 60 + minutes, 12 "
    "counting as 0) and, when neither am nor pm was typed, taking "
    "whichever comes next; the result becomes the time "
    "the action takes ($A01F), so the player's next turn simply comes "
    "that much later (see the main loop at $A064, which also lets ENTER "
    "cut the wait short). $DDCB-$DDCF hold the two times and the am/pm "
    "letter. Read from the code.",
    "CORRECTED: the automatic split had most of this body as text and "
    "data."]
A[0xDDD0]['end'] = 0xDE6F

# ---------------------------------------------------------------------
# The case: statements and the evidence each needs ($9965-$99FB)
# ---------------------------------------------------------------------
_case = []
_a = 0x9965
_depth = 0
while b(_a) != 0xFF:
    _f = b(_a + 3)
    _n = 4 + (2 if _f & 0x30 else 0)
    _h = f'; when proven ${w(_a + 4):04X}' if _f & 0x30 and w(_a + 4) else ''
    if _depth == 0:
        _lab = (f'Statement: {b(_a)} {ENT.get(b(_a), "?")} / relation {b(_a + 1)} / '
                f'{b(_a + 2)} {ENT.get(b(_a + 2), "?")}; flags ${_f:02X}{_h}')
    elif b(_a) == 0 and b(_a + 2) == 0:
        _lab = f'  (empty; flags ${_f:02X})'
    elif b(_a + 1):
        _lab = (f'  Evidence statement: {b(_a)} {ENT.get(b(_a), "?")} / relation {b(_a + 1)} / '
                f'{b(_a + 2)} {ENT.get(b(_a + 2), "?")}; flags ${_f:02X}')
    else:
        _lab = (f'  Evidence: {b(_a)} {ENT.get(b(_a), "?")} / {b(_a + 2)} '
                f'{ENT.get(b(_a + 2), "?")}; flags ${_f:02X}')
    if _f & 8:
        _lab += ' (last of the group)'
    _case.append(('B', _a, _n, _lab))
    if _f & 4:
        _depth += 1
    if _f & 8:
        _depth = max(0, _depth - 1)
    _a += _n
_case.append(('B', _a, 1, 'End marker'))
del A[0x994D]
blk(0x994D, 'b', 'Not decoded: 24 bytes before the case table',
    ["Pointed to from $ABFF, $BDD1 and $BF4E. Format not decoded."])
A[0x994D]['end'] = 0x9965
blk(0x9965, 'b', 'The case: statements about the crime, and the evidence each needs',
    ["Eleven groups. Each starts with a statement record: +0 a thing or "
     "person, +1 a relation number, +2 another thing; +3 flags; and, "
     "with bit 4 or 5 of the flags, +4/+5 a routine run when it is "
     "proven. Bit 2 of the flags opens a group of evidence records "
     "(+0 and +2 are things, +1 is 0) and bit 3 closes it; $BE5A steps "
     "over one record and $BE72 over a whole group. In the state bits, "
     "bit 0 means the statement is waiting to be proven and bit 1 that "
     "it has been ($BCC9 sets bit 1 and runs the routine once the "
     "evidence checks out through $BF08; $9A74 does the same from a "
     "routine).",
     "The statements read naturally once the names are filled in - Mrs "
     "Brown / 5 / herself, Mrs Jones / 5 / Tricia Fender, the sale "
     "location / 4 / Old Mill Road, the Major / 6 / the opium den - and "
     "the evidence for 'Mrs Brown / herself' includes the female corpse "
     "and the sandstone bridge. Four statements with no evidence and no "
     "routine (flags $B4) name Tricia Fender and Phipps with the two "
     "victims. What the relation numbers mean, how the player's words "
     "are matched against these ($BD06, the list at $9FF6) and what the "
     "flags $40/$48 on evidence test are not decoded. Read from the "
     "code; nothing here was tried in the emulator.",
     "This is what Lestrade's 'WELL CAN YOU PROVE THAT ... YET, HOLMES "
     "?' ($9DD8, through $BC46-$BC9C) is about, and the routines here "
     "are the 'handlers' at $99FC-$9A7C (overlay 07)."],
    subs=_case)
A[0x9965]['end'] = _a + 1
blk(0xBC46, 'c', 'Check every statement that is waiting to be proven',
    ["Walks the case table ($9965) and, for each statement with bit 0 "
     "set and bit 5 clear, tries to prove it ($BCC9)."])
blk(0xBC74, 'c', 'Count the waiting statements that can now be proven', [
    "B = how many; IX ($BA1E) = the last one. Read from the code."])
blk(0xBC9C, 'c', 'Find the first waiting statement that cannot be proven yet', [
    "IX ($BA1E) = that statement; B = how many there are. Read from the "
    "code."])
blk(0xBCC9, 'c', 'Try to prove statement IX',
    ["If it has evidence (flags bit 2), checks it ($BF08) and fails if "
     "it is not all there. Then marks it proven (bit 1 set, bit 0 clear) "
     "and runs its routine (+4/+5) if bit 4 is set; a statement with "
     "bit 5 set is only marked as waiting (bit 0). Z = proven."])
blk(0xBE5A, 'c', 'Step IX over one case record (4 bytes, or 6 with a routine)', [])
blk(0xBE72, 'c', 'Step IX over a whole group of case records', [])
fact('the-case-table',
     "The solution is a table of statements and evidence",
     "The case lives at $9965: eleven statements of the form 'thing / "
     "relation / thing', each with the evidence it needs and a routine "
     "to run when it is proven, built from eleven verbs (BLACKMAILED, "
     "HAD, HAS, IS, KILLED, VISITED, HATED, EXAMINED, HID, OWNS, MADE): "
     "MRS BROWN KILLED HERSELF, SALE LOCATION IS OLD MILL ROAD, PHIPPS "
     "HAS PLANS, TRICIA FENDER BLACKMAILED MRS BROWN and so on, plus four "
     "with no evidence at all and a flag (bit 5) whose effect is not "
     "fully traced, saying that Tricia Fender or Phipps killed one of the "
     "victims. "
     "The evidence is pairs of things the player must have seen or "
     "examined (bits 7 and 6 of each thing's +6, which the game sets as "
     "you look and EXAMINE - confirmed). Lestrade's 'WELL CAN YOU PROVE "
     "THAT ... YET, HOLMES ?' is driven by it. The format was read from "
     "the code that walks the table; proving a statement was not tried "
     "in the emulator.")

A[0x99FC]['title'] = 'Routines run when a statement of the case is proven'
fix_text(0x99FC, "The records' own format is not decoded yet.",
         "UPDATED 2026-11-07: the records are the case table at $9965 (statements "
         "and their evidence); each of these routines belongs to one statement.")

# The relation words, and what the evidence tests (2026-11-07, later).
import dictionary as _D  # noqa: E402
_WS = {x['offset']: x['word'] for x in _D.all_words()}
REL = {}
_r = []
_a = 0x994D
_i = 1
while w(_a):
    REL[_i] = _WS.get(w(_a) & 0xFFF, '?')
    _r.append(('W', _a, 2, f'Relation {_i}: {REL[_i]}'))
    _a += 2
    _i += 1
_r.append(('W', _a, 2, 'End marker'))
A[0x994D]['title'] = "The case's relation words"
A[0x994D]['desc'] = [
    "Word references for the verbs a statement about the case can use; "
    "a statement's relation number is a position here (1-based). $BDD1 "
    "finds the verb of what the player said in this list; $BF45 looks "
    "a relation up to print it ($BF1C prints a statement, with AND, "
    "word $005D, for relation 0).",
    "CORRECTED: an earlier version of this overlay left these 24 bytes "
    "undecoded."]
A[0x994D]['subs'] = _r
import re as _re  # noqa: E402
A[0x9965]['subs'] = [(d_, a_, l_, _re.sub(r'/ relation (\d+) /',
                                          lambda m_: '/ ' + REL.get(int(m_.group(1)), m_.group(0)) + ' /', t_))
                     for (d_, a_, l_, t_) in A[0x9965]['subs']]
A[0x9965]['desc'][1] = (
    "With the relation words filled in ($994D) the statements read as "
    "sentences: MAJOR PERCIVAL FFOULKES IS INNOCENT, MRS BROWN KILLED "
    "HERSELF, MRS JONES KILLED TRICIA FENDER, PHIPPS HAS PLANS, SALE "
    "LOCATION IS OLD MILL ROAD, TRICIA FENDER HAD PLANS, TRICIA FENDER "
    "BLACKMAILED MRS BROWN, and four with no evidence and no routine "
    "(flags $B4: bit 5 set) saying that Tricia Fender or Phipps killed "
    "one of the two victims. What bit 5 does is not fully traced: "
    "$BCC9 only marks such a statement as waiting, and Watson's reply "
    "($BA8C) answers it differently. The order is as stored (first "
    "thing, verb, second thing), which is also the order the player's "
    "words are matched in ($BD69). Some groups also hold a statement as evidence "
    "(MAJOR PERCIVAL FFOULKES VISITED OPIUM DEN, under the Major's "
    "innocence). An evidence record with relation 0 is a pair of things "
    "that the player must have seen ($BE91: flags $00, both things' +6 "
    "bit 7) or examined (flags $40, +6 bit 6). Confirmed in the emulator "
    "that +6 bit 7 is set on everything in view in the first room and "
    "that EXAMINE LAMP sets bit 6 of the lamp's +6 ($80 -> $C0); the "
    "proving itself was not tried. Which order (subject first) the "
    "statements are matched in is read from $BD69.")
_CASE_TEST = (
    "Confirmed in the emulator (tools/experiments/case_test.py): with the player "
    "moved to Inspector Lestrade's room at the start, SAY TO LESTRADE "
    "\"MRS BROWN KILLED HERSELF\" gets 'I do not believe that you have the "
    "evidence to prove that Mrs Brown killed herself' and the statement's "
    "flags go $A4 -> $A5 (bit 0: waiting). With the evidence poked in "
    "first - the female corpse and the sandstone bridge marked seen and "
    "examined (+6 bits 7 and 6), the large rock marked seen - the same "
    "words get 'So Mrs Brown killed herself, excellent Holmes, another "
    "brilliant conclusion.' and the flags go $A4 -> $A6 (bit 1: proven).")
A[0x9965]['desc'][1] = A[0x9965]['desc'][1].replace(
    "the proving itself was not tried.", "the proving was tried too: " + _CASE_TEST)
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'the-case-table':
        FACTS[i] = (eid, title, body.replace(
            "The format was read from the code that walks the table; proving "
            "a statement was not tried in the emulator.",
            "The format was read from the code that walks the table. " + _CASE_TEST))
A[0xCDBF]['desc'].append(
    "Confirmed in the emulator: with the player moved to Inspector "
    "Lestrade at the start, his script hails a hansom cab, climbs in, and "
    "at 8:04 runs ASK (bytes 44 FA 1D FC FF: the person is the plan's "
    "remembered thing, here the cabbie; verb 29 GO TO; the plan's indirect "
    "object, a room); $CE10 then prints 'Inspector Lestrade remarks to the "
    "cabbie \" Go to Kings Cross Road. \"'. (Rendered with 'you' as the "
    "actor, $682A reads 'YOU SAY TO ...'.)")

fix_fact('lestrade-hails-a-cab', "actions running on the same turns as the player's.",
         "actions running on the same turns as the player's. UPDATED 2026-11-07: this is "
         "his plan script ($E7E7): DO WEST, then the sub-script at $EB72 (a cab, a walk "
         "and a train journey), "
         "then a conversation with Chief Constable Straker paced by SIGNAL and AWAIT.")

for _a, _t in ((0xEBA4, "Sub-script: take a hansom cab to room (indirect object)"),
               (0xEBE1, "Sub-script: take a steam train to room (direct object)"),
               (0xEB72, "Sub-script: Inspector Lestrade's journey to Leatherhead")):
    A[_a]['desc'].insert(0, A[_a]['title'] + '.')
    A[_a]['title'] = _t
A[0xEBA4]['desc'].insert(1,
    "HAIL until a cab stops, climb in, ASK the cabbie (the plan's verb "
    "register holds who answered) TO GO TO the room, wait until there "
    "(verb 131), pay ($E506) and climb out. Confirmed in the emulator for "
    "Lestrade: 'Inspector Lestrade hails the hansom cab.', '...climbs into "
    "the hansom cab.', then 'Inspector Lestrade remarks to the cabbie \" Go "
    "to Kings Cross Road. \"'.")
A[0xEBE1]['desc'].insert(1,
    "Wait until steam train 42 or 43 is here (verb 129), climb in, wait "
    "until in the room, climb out. Read from the script.")
A[0xEB72]['desc'].insert(1,
    "A cab to Kings Cross Road (room 18), four steps north-east, a train "
    "to platform one (room 54), then verb 128 puts him in Leatherhead "
    "station (room 53). Read from the script; his order to the cabbie to "
    "go to Kings Cross Road was seen in the emulator.")

for _a, _t, _d in (
        (0xE506, 'Sub-script: pay the cab fare',
         "If $E518 allows it, PAY TO ($E370) with the plan's objects; run by "
         "the cab sub-script at $EBA4 ($EBCB). Read from the script."),
        (0xE08D, 'Sub-script: shared action 13, GO TO in a cab',
         "If the cab is with the actor (verb 130), GO TO the place; otherwise "
         "say 'YOU HAVE TO GET INTO THE CAB FIRST.' Read from the script."),
        (0xDF7E, 'Sub-script: shared action 20, TAKE the burning note',
         "TAKE it ($DCC1), then $DF8B. Read from the script."),
        (0xDFA7, 'Sub-script: shared action 21, OPEN a wall safe',
         "$DFB6 (the safe's own check), then the ordinary OPEN ($DE9D). Read "
         "from the script."),
        (0xE0A0, 'Sub-script: shared action 16, EXAMINE CLOSELY the deep stream',
         "$E0AD, then EXAMINE CLOSELY ($E135). Read from the script."),
        (0xE0E0, 'Sub-script: shared action 19, EXAMINE CLOSELY the trash pile',
         "EXAMINE CLOSELY ($E135), then $E0EB, which reveals the torn coded "
         "note - confirmed in the emulator (see the Trivia entry on EXAMINE "
         "CLOSELY)."),
        (0xE0F2, 'Sub-script: shared action 17, EXAMINE CLOSELY the drawer',
         "EXAMINE CLOSELY ($E135), then $E0FD, which reveals the false bottom "
         "(object 63). Read from the script.")):
    A[_a]['desc'].insert(0, _d)
    A[_a]['title'] = _t

blk(0xBA67, 'c', "Watson's reply to something the player says",
    ["Parses the remark into a statement ($BD7E: subject $BA19, relation "
     "$BA1A from the verb's place in $994D, object $BA1B), then looks for "
     "it in Watson's own list at $9A7D (empty: $FF at once) and in the "
     "case table ($BD51). A statement about the case is remembered: added "
     "to the list at $9FF4 (5-byte heap nodes holding the three bytes) "
     "unless already there. Watson then answers 'THAT IS BRILLIANT "
     "HOLMES.' ($6F54) or, by chance, asks whether there is 'SOME "
     "CONNECTION BETWEEN THE ... AND ...' two things ($6F62, using "
     "$BD06); a statement with flags bit 5 set (the four 'Tricia Fender / "
     "Phipps KILLED ...' ones) gets a "
     "different answer.",
     "Confirmed in the emulator: SAY TO WATSON \"MRS BROWN KILLED "
     "HERSELF\" at the start gets a reply and the list at $9FF4 gains a node "
     "5E 05 60 (Mrs Brown / KILLED / herself); \"PHIPPS HAS PLANS\" gets a "
     "reply and a node 06 03 61. The reply is one of two wordings that "
     "alternated in the runs of 9 November, whichever statement was said: "
     "'Watson remarks \" That is brilliant Holmes, I do not know how you do "
     "it. \"' and 'Watson says \" That is brilliant Holmes. \"' (the "
     "earlier version of this note tied each wording to a statement; that "
     "was wrong). \"THE LAMP IS ON\", which is not about the case, gets "
     "'Watson says \" What \"'; \"THE LAMP IS OPEN\" gets no reply at all."])
blk(0xBD51, 'c', 'Find the statement $BA19-$BA1B in the case table',
    ["Z with IX = the statement if found ($BD69 compares subject, "
     "relation and object in that order). $BD4B searches Watson's own "
     "list at $9A7D the same way."])
blk(0xBDC2, 'c', "Turn the player's remark into a statement",
    ["The relation is the position of the remark's verb in the list at "
     "$994D; the subject and object are the first two things named "
     "($BE3C, $BE4B), each copied as a 6-byte entry into $9FF6 (people) "
     "or $9FFC (things) by $BE22. Carry set if the remark names more than "
     "that. Read from the code."])
fact('watson-remembers',
     "Watson remembers what you tell him about the case",
     "Telling Watson a statement about the case (SAY TO WATSON \"MRS "
     "BROWN KILLED HERSELF\") adds it to a list of three-byte statements "
     "at $9FF4, and he answers 'That is brilliant Holmes...'; something "
     "that is not about the case gets 'What'. Confirmed in the emulator. "
     "The statement is matched against the same table Lestrade uses "
     "($9965); the verb must be one of eleven: BLACKMAILED, HAD, HAS, IS, "
     "KILLED, VISITED, HATED, EXAMINED, HID, OWNS, MADE.")
A[0xBA67]['end'] = 0xBB67
blk(0xBB67, 'c', "Lestrade's reply to something the player says",
    ["Parses the remark into a statement the same way as Watson's reply "
     "($BA67) and checks it against the case table: a statement whose "
     "evidence is complete is proven ($BCC9) and Lestrade says so; "
     "otherwise it is marked as waiting and he says he does not believe "
     "the player has the evidence ($72A6, $72BD). Not traced line by "
     "line.",
     "Confirmed in the emulator (see the case table at $9965): 'I do not "
     "believe that you have the evidence to prove that Mrs Brown killed "
     "herself' without the evidence, 'So Mrs Brown killed herself, "
     "excellent Holmes, another brilliant conclusion.' with it."])
A[0xBB67]['end'] = 0xBC46

# A key to the flag bytes on the Characters and things page.
from build_skeleton import PAGES  # noqa: E402
for _i, (_pid, _title, _html) in enumerate(PAGES):
    if _pid == 'things':
        PAGES[_i] = (_pid, _title, _html.replace(
            '<table class="disassembly">',
            '<p>Flag bytes (added 2026-11-07). +5: bit 0 locked, bit 2 full, bit 4 on '
            '(lit), bit 5 open, bit 6 alive (a person), bit 7 revealed - named by the '
            'words in #R$C471 and #R$C481, which the game prints when an action needs '
            'one of them; bits 5 and 7 confirmed by play. +6: bit 7 the player has '
            'seen it, bit 6 the player has examined it (confirmed: EXAMINE LAMP turns '
            '$80 into $C0); these are what the evidence in the case table at #R$9965 '
            'tests.</p><table class="disassembly">', 1))

A[0x9E48]['title'] = "Game-over record: Basil comes in with a gun"
A[0x9E48]['desc'][0] = (
    "Run by Phipps's script ($EF89). If Watson (3) and Lestrade (2) are "
    "both in the player's room ($9E60), ends the game with $6AF3: 'AS "
    "BASIL ENTERS HE SEES YOU AND PULLS A GUN. WITH SUPRISING AGILITY "
    "WATSON PUSHES YOU OUT OF THE WAY OF BASILS...'; if either is missing, "
    "with $6B79: '...WITH HIS USUAL SKILL HIS FIRST SHOT DISPOSES OF YOU. "
    "PERHAPS YOU...'. Read from the code; messages rendered (the first "
    "only in part).")
A[0x9EA2]['title'] = "Game-over record: the morning papers"
A[0x9EA2]['desc'][0] = (
    "Run by Lestrade's script ($EAB3). Unless both MRS BROWN KILLED "
    "HERSELF ($9973) and MRS JONES KILLED TRICIA FENDER ($9981) have been "
    "proven (bit 1 of their flags), ends with $6A33: 'NOT ONLY HAVE YOU "
    "FAILED TO SOLVE THE CRIMES AT HAND BUT THE MORNING PAPERS CARRY A "
    "REPORT OF MR BROWNS LOST P...'; if both have, with $6ABD: 'YOU HAVE "
    "DONE EXTREMELY WELL TO SOLVE THE CASE AT HAND BUT THE MORNING PAPERS "
    "CARRY A REPORT OF MR BROWNS LOST...'. Read from the code; both "
    "messages rendered only in part.")
fact('three-endings',
     "How the case can end",
     "The game ends through records the characters' scripts run, all "
     "finishing at $9E74. Lestrade ends it at 3pm on Monday if you have "
     "not met him with Chief Constable Straker ($9E6A, confirmed by "
     "play); later he can end it with the morning papers' report of Mr "
     "Brown's lost plans - 'NOT ONLY HAVE YOU FAILED...' or 'YOU HAVE DONE "
     "EXTREMELY WELL...', depending on whether both murders have been "
     "proven ($9EA2); and with the Major's wrongful arrest ($9E85), "
     "which proving MAJOR PERCIVAL FFOULKES IS INNOCENT prevents. "
     "Phipps's script has Basil come in with a gun ($9E48): Watson saves "
     "you only if he and Lestrade are both there. $DFCA has Basil shoot "
     "you too. All but the first are read from the code.")

# The keyboard: the time limit that lets the game go on without you.
blk(0xA536, 'c', 'Wait for a key, but not for ever',
    ["Polls the keyboard ($C41F) up to $A03B times (reset to 3,000 each "
     "call), with a 256-step delay loop between polls. A key: returns it "
     "with bit 7 cleared. No key in that time: rubs out whatever has been "
     "typed on the line ($D9B7) and returns 0 with Z set. Read from the "
     "code; the time limit is a few seconds of real time (not measured - "
     "the harness answers key reads itself)."],
    comments={0xA537: 'How many polls before giving up', 0xA53A: 'A key?',
              0xA53D: 'Yes', 0xA541: 'No: a short delay...', 0xA548: '...and count a poll',
              0xA54B: 'Try again', 0xA54F: 'Time is up: rub out the line', 0xA552: 'Z: nothing typed',
              0xA553: 'The key', 0xA555: 'Reset the limit for next time'})
blk(0xD898, 'c', "Read a line from the keyboard, with a time limit",
    ["The pre-check of the player's first script step ($D6BF). Sets the "
     "limit ($A03B = 3,000 polls), switches quoted printing on while the "
     "line is typed, and runs the line editor ($D8AD). If the player "
     "stops typing for too long the editor gives up, the step fails, and "
     "the player's script does WAIT HERE instead ($9948) - so the clock "
     "and the other characters carry on while the player thinks. Read "
     "from the code."])
blk(0xD8AD, 'c', 'The line editor',
    ["Prints the '> ' prompt and reads up to 128 characters into $5B00 "
     "through $A536: DELETE rubs out (and keeps track of quote marks, "
     "$D897), $18 clears the line ($D9B7), letters, digits and a few "
     "punctuation marks are accepted, ENTER ends the line ($D949). A "
     "time-out from $A536 ends it with nothing ($D9AC). Read from the "
     "code."])
A[0x9921]['desc'][0] = A[0x9921]['desc'][0].replace(
    "Each pass: $D6BF (its pre-check $D898 not traced; if it refuses, "
    "the player WAITs instead),",
    "Each pass: $D6BF reads a line from the keyboard with a time limit "
    "($D898; if the player types nothing for a few seconds the step "
    "fails and the player WAITs instead, so the game goes on),")
A[0xD898]['desc'].append(
    "Confirmed in the emulator: leaving the prompt with no key pressed "
    "(the harness answers every keyboard poll with 'no key') gives "
    "'> You wait.' and the clock runs on from 8:02 to 8:05, then again "
    "to 8:10, with no command typed.")
A[0xA536]['desc'][0] = A[0xA536]['desc'][0].replace(
    "Read from the code; the time limit is a few seconds of real time (not measured - "
    "the harness answers key reads itself).",
    "Read from the code; the real-time length of the limit was not measured (the "
    "harness answers key reads itself), but the give-up path was seen working - see "
    "$D898.")
fact('the-game-goes-on',
     "The game does not wait for you",
     "The player's script reads each line with a time limit ($D898, "
     "$A536: 3,000 keyboard polls). If nothing is typed in time the line "
     "is rubbed out and the player WAITs, so the clock and every other "
     "character carry on. Confirmed in the emulator: at a prompt with no "
     "key pressed the game prints 'You wait.' and the clock moves on by "
     "several minutes at a time. During WAIT UNTIL the main loop also "
     "looks at the keyboard every minute ($A07F) so that ENTER can cut "
     "the wait short.")

# The message printer's entry, its control-code table and its stack trick.
blk(0xA55D, 'w', 'Routines for the message control codes $00-$1F',
    ["One address per control code, used by $A621. Codes below $1D are "
     "called and the interpreter carries on; $1D-$1F are jumped to "
     "instead ($A62F). CORRECTED: the automatic split had all but the "
     "first entry as code."],
    subs=[('W', 0xA55D + 2 * k, 2, f'Code ${k:02X}: ${w(0xA55D + 2 * k):04X}') for k in range(32)])
A[0xA55D]['end'] = 0xA59D
blk(0xA59D, 'w', "Where the message's stack parameters end",
    ["Set by $A5A9 to the stack pointer as it was before the caller "
     "pushed the message's parameters; $A5BF reloads it on the way out, "
     "so the printer itself throws the parameters away."],
    subs=[('W', 0xA59D, 2, 'Stack pointer to return with')])
A[0xA59D]['end'] = 0xA59F
blk(0xA59F, 'c', 'Print the message at HL',
    ["The message interpreter's entry point; almost every word the game "
     "prints comes through here (see the message area at $67B7 for the "
     "bytecode). Parameters - extra messages or words, such as what a "
     "character says - are pushed on the stack before the call and "
     "control codes pick them up; on the way out the stack pointer is "
     "reset past them ($A59D), so callers push and never pop. Saves the "
     "registers, runs the byte loop ($A5C4 / $A5CD) and returns through "
     "JP (HL). Read from the code; the rendering of 118 messages in the "
     "emulator relies on it."],
    comments={0xA5A5: 'Where the stack will be once the parameters are dropped',
              0xA5A9: '', 0xA5AD: '', 0xA5B6: 'Interpret the message',
              0xA5BE: 'The return address', 0xA5BF: 'Drop the parameters', 0xA5C3: 'Return'})
blk(0xA5C4, 'c', 'Interpret message bytes until the end of the message',
    ["IX walks the message; $A5CD handles one element - a dictionary "
     "word (bit 7 set: two bytes), packed letters, a literal character "
     "or a control code ($A621) - and returns Z at the end. Not traced "
     "in detail."])
blk(0xA2E4, 'c', "Narrate a command as a sentence ('You take the oil lamp.')",
    ["Saves the verb and objects ($A35D-$A35F), then - unless it is too "
     "dark and the player is the one acting, when it prints 'SORRY IT IS "
     "TOO DARK.' ($68D1) - prints the actor ($A724), the verb's words "
     "from its pattern ($A2B1/$A2BD) and the objects, ending the line "
     "($A2A2). This is the sentence every successful action shows, for "
     "the player and for characters in sight ('Inspector Lestrade hails "
     "the hansom cab.'). Read from the code; the output it describes is "
     "what the emulator shows."])
A[0xCA76]['desc'] = ["Calls $A2E4 for verbs below 128, so script-only verbs "
                     "are never narrated."]

# ---------------------------------------------------------------------
# An overview page: how the engine fits together (written last)
# ---------------------------------------------------------------------
_OV = [
    ("The main loop", [
        "#R$A064 is the whole game: one pass per minute. The clock moves on "
        "(#R$BFD9) and is printed (#R$BF79), then every actor in the table at "
        "#R$9860 whose next-turn time (+6/+7) has come takes a turn. A turn "
        "starts with #R$CC37 (is an order or a remark waiting for this actor? "
        "#R$B91F) and runs plan-script steps (#R$CC78) until one of them takes "
        "time; that time is added to the actor's next-turn time, and the "
        "actor's after-turn routine, if it has one (#R$9C77), runs. When the "
        "game ends, #R$9E74 prints the ending and the game restarts.",
        "The player is actor 0 and is treated like everyone else. Its script "
        "(#R$9921) reads a line with a time limit (#R$D898 - if nothing is "
        "typed, the player WAITs and the game goes on), splits it into "
        "sentences, parses one, and DOes it; a line of several sentences is "
        "worked through one a minute."]),
    ("Plan scripts", [
        "Every character's behaviour is a script in a small bytecode "
        "(#R$CC78 describes it): DO a command, RUN an action record, ASK "
        "someone to do something, SAY or PRINT a message, SIGNAL and AWAIT "
        "another character, RETURN from a sub-script, PASS, GOTO; each "
        "instruction can branch on success or failure. Success that took time ends the "
        "actor's turn, failure tries the next instruction at once, so "
        "'fail -> itself' means 'wait here until this works'. Script-only "
        "verbs 128-140 (#R$9FAB) test where people are, the hour, chances "
        "and countdowns, and move things about. Instructions marked busy "
        "make a character refuse what the player asks (#R$CBA7). See "
        "<a href=\"cast.html\">The cast and their scripts</a>."]),
    ("Commands and action records", [
        "A command - typed or from a script - is a verb and up to two "
        "objects, carried out by #R$C4D1. The verb's default record "
        "(#R$9F38) or the object's own action list (shared records at "
        "#R$AA71) gives an action record, which #R$C9BF interprets: "
        "requirement codes for each object (#R$C628: here, carried, a person, "
        "a door, a number...), optional flag tests on the objects (#R$C74E, "
        "with refusals such as 'YOUR DOOR IS OPEN' from #R$CB7B), an "
        "optional pre-check routine, and then either a code body or - for a "
        "checks-only record - a sub-script. #R$CA60 runs the body and then "
        "reports what the player sees: the narrated sentence (#R$A2E4), a "
        "new room (#R$CA7F), someone arriving (#R$CAAF)."]),
    ("Things and words", [
        "Things, people and places are entity records (the "
        "<a href=\"things.html\">Characters and things</a> page), rooms have "
        "their own table (<a href=\"map.html\">Map and rooms</a>), and the "
        "dictionary, verb patterns and parser turn typed words into verb and "
        "object numbers (<a href=\"vocabulary.html\">Vocabulary</a>). Every "
        "word printed goes through the message interpreter (#R$A59F), whose "
        "parameters ride on the stack, and the word-wrapping printer "
        "(#R$A9B7). Memory for the engine's lists - orders, tokens, "
        "countdowns, sub-script frames, what Watson has been told - comes "
        "from a small heap (#R$9570, #R$A11C). Fourteen rooms have a "
        "picture, drawn from compact drawing commands by #R$F3C2 (see the "
        "<a href=\"pictures.html\">Pictures</a> page)."]),
    ("Typing", [
        "A typed line is turned into tokens - verbs, nouns, prepositions, "
        "numbers, special words, punctuation (#R$AE7F) - with numbers, "
        "clock times and pre-decimal money (£1, 2/6, 3S) read by #R$DAC6 "
        "and #R$DB67. #R$AAB2 parses one sentence at a time; special words "
        "such as SAVE, QUIT (the same as LOAD), ALL BUT and pronouns are "
        "handled through the table at #R$AF6B; words in quotes become "
        "remarks for the person spoken to (#R$B86A). The player's typing "
        "is echoed in the command window (#R$C1FC), and if nothing is typed "
        "for a while the player simply waits (#R$A536)."]),
    ("Light and darkness", [
        "Outdoors from 8pm to 6am the player needs a light (#R$D078, "
        "#R$C00C): the oil lamp, lit from the start."]),
    ("The case", [
        "The solution is data: #R$9965 lists statements such as MRS BROWN "
        "KILLED HERSELF, each with the evidence (things the player must have "
        "seen or examined) needed to prove it, using eleven verbs at #R$994D. "
        "Telling Lestrade a statement (#R$BB67) proves it if the evidence is "
        "there; telling Watson (#R$BA67) makes him remember it. Lestrade has "
        "to be met, with Chief Constable Straker, by 3pm on Monday "
        "(#R$9DFF); later endings depend on what has been proven (#R$9EA2, "
        "#R$9E85) and on who is with you when Basil arrives (#R$9E48). "
        "See <a href=\"the-case.html\">The case</a> for every statement and its evidence."]),
]
page('how-it-works', 'How the engine works',
     '<p>A summary of the engine as far as this disassembly has got (written '
     '2026-11-07). Each claim is explained, and marked as confirmed by play '
     'or read from the code, at the address linked.</p>' +
     ''.join(f'<h3>{h}</h3>' + ''.join(f'<p>{p}</p>' for p in ps) for h, ps in _OV))
A[0x9965]['desc'].insert(2,
    "Also tried in the emulator: TRICIA FENDER KILLED MRS JONES (one of "
    "the bit-5 statements) told to Lestrade gets the same 'I do not "
    "believe that you have the evidence to prove that Tricia Fender "
    "killed Mrs Jones' and its flags go $B4 -> $B5; MRS JONES KILLED "
    "TRICIA FENDER gets the same answer with its flags $A4 -> $A5. Told "
    "to Watson, all three statements tried get 'That is brilliant "
    "Holmes...'. So nothing visible yet separates the bit-5 statements.")

# Proper titles and line comments for the script helpers most used.
def _helper(addr, title, desc, comments):
    A[addr]['title'] = title
    A[addr]['desc'] = desc + ['Used by: ' + why_text(RECS[addr]) + '.']
    A[addr]['comments'].update(comments)


_helper(0xE52F, 'Script helper: start a countdown for the actor',
    ["RUN $E52F / n / m: puts a 2-byte node (the actor, n plus a random "
     "number below m) on the countdown list at $9FE5. $E57A ticks it and "
     "$E588 cancels it. Read from the code."],
    {0xE531: 'A 2-byte node', 0xE536: 'Link it in at the head of the countdown list',
     0xE543: '+0: whose countdown', 0xE549: 'The random part, if any...',
     0xE552: '...a random number below it', 0xE556: 'Plus the fixed part',
     0xE55A: '+1: the count', 0xE55D: 'Done',
     0xE560: "Find the actor's countdown: Z if none", 0xE573: 'Refuse if there is none'})
_helper(0xE57A, 'Script helper: tick the countdown (fail when it runs out)',
    ["Its pre-check ($E573) refuses when the actor has no countdown. The "
     "body counts it down: still running, the instruction succeeds - "
     "taking no time, so the script goes straight on (scripts pair it "
     "with IDLE, $E5A8, which takes a minute); at "
     "zero the countdown is removed and the "
     "instruction fails, so a script can 'do X until the time is up' with "
     "a success branch back to X. Read from the code."],
    {0xE57E: 'Count down', 0xE581: 'Still running: succeed',
     0xE582: 'Run out: remove it...', 0xE585: '...and fail'})
_helper(0xE588, "Script helper: cancel the actor's countdown",
    ["Unlinks the actor's countdown node from $9FE5 and frees it; the "
     "pre-check refuses when there is none. $E58C is the shared tail "
     "also used by $E57A. Read from the code."],
    {0xE58C: 'DE = the node', 0xE58F: 'Find the node before it', 0xE596: 'Unlink it',
     0xE5A2: 'Free it', 0xE5A5: 'Done'})
_helper(0xE5A8, 'Script helper: idle for a minute',
    ["No checks; byte 1's high nibble makes it take one minute, and the "
     "body just succeeds. Read from the code."], {})
_helper(0xDDBE, 'Script helper: wait n minutes',
    ["RUN $DDBE / n: the action takes n minutes ($A01F = n), so the "
     "actor's next turn comes n minutes later. Pre-check $DDB8 as for "
     "WAIT HERE. Read from the code."],
    {0xDDC2: 'n...', 0xDDC5: '...is how long this takes', 0xDDC8: 'Done'})
_helper(0xF198, 'Script helper: succeed by chance (n in 100)',
    ["RUN $F198 / n: refuses unless a random number from 1 to 99 "
     "($D29D) is at most n. Read from the code; the emulator saw it "
     "succeed 75 times in 84 turns of play."],
    {0xF19A: 'A random number, 1-99', 0xF19E: 'n', 0xF1A1: 'Is n below it?',
     0xF1A2: 'Yes: refuse', 0xF1A5: 'No: succeed'})
_helper(0xF1D6, 'Verb 136 (scripts only): is it hour n?',
    ["n counts 1-24. Succeeds only when the clock shows that hour: 13-24 "
     "are the pm hours, 1-12 the am ones. Confirmed in the emulator (see "
     "the Trivia entry on appointments)."],
    {0xF1D8: 'n', 0xF1DB: "'a'...", 0xF1DD: '...unless n is 13 or more:', 0xF1E1: "'p'",
     0xF1E3: 'and 12 less', 0xF1E5: 'Is that the hour?', 0xF1E9: 'No: refuse',
     0xF1EC: "And is it 'a' or 'p' as wanted?", 0xF1F0: 'No: refuse', 0xF1F3: 'Yes: succeed'})
_helper(0xE5AD, 'Verb 131 (scripts only): is the direct object in room n?',
    ["Confirmed in the emulator: 864 successes in 84 turns, each with the "
     "thing really in that room."],
    {0xE5B1: "The direct object's record", 0xE5B5: 'The room asked about...',
     0xE5B8: '...is that where it is?', 0xE5BB: 'No: refuse', 0xE5BE: 'Yes: succeed'})
_helper(0xE5D8, 'Verb 129 (scripts only): are two things in the same room?',
    ["Refuses if the direct and indirect objects are in different rooms, "
     "or are the same thing. Confirmed in the emulator: 482 tests, equal "
     "exactly when the rooms were."],
    {0xE5DF: "The direct object's room...", 0xE5E6: "...and the indirect object's",
     0xE5EA: 'The same?', 0xE5F0: 'No: refuse', 0xE5F3: 'Not the same thing as well?',
     0xE5F7: 'It is: refuse', 0xE5FA: 'Succeed'})
_helper(0xE497, 'Verb 128 (scripts only): put a thing in a room',
    ["Takes the direct object out of whatever holds it and puts it in the "
     "room given as the indirect object ($DD0E); room 0 is off stage. "
     "Confirmed in the emulator: each of the 4 times it ran in 84 turns, "
     "the thing ended up in that room."],
    {0xE49B: 'The room', 0xE49F: 'The thing', 0xE4A2: '',
     0xE4A6: 'Out of any container', 0xE4AA: 'Into the room', 0xE4AD: 'Done'})
_helper(0xF203, "Verb 133 (scripts only): clear bit 0 of a thing's +5 flags",
    ["Bit 0 is 'locked' (see $C471), so this unlocks it. Read from the "
     "code."], {0xF205: 'The thing', 0xF209: 'Clear bit 0 (unlock)', 0xF20D: 'Done'})
_helper(0xF210, "Verb 132 (scripts only): set bit 0 of a thing's +5 flags",
    ["Bit 0 is 'locked' (see $C471), so this locks it. Read from the "
     "code."], {0xF212: 'The thing', 0xF216: 'Set bit 0 (lock)', 0xF21A: 'Done'})
for _k, _t in ((132, 'LOCK: set bit 0 (locked) of the direct object\'s +5 flags'),
               (133, 'UNLOCK: clear bit 0 (locked) of the direct object\'s +5 flags')):
    INTERNAL[_k] = _t
A[0x9FAB]['subs'] = [('W', 0x9FAB + 2 * k, 2, f'Verb {128 + k}: ${w(0x9FAB + 2 * k):04X} - {INTERNAL[128 + k]}')
                     for k in range(13)]
A[0xCF80]['comments'].update({
    0xCFB9: 'Walk the call-frame list', 0xCFBE: 'Next frame: Z at the end',
    0xCFC4: "This actor's?", 0xCFC9: 'Yes: NZ, IX = the frame', 0xCFCC: 'None: Z',
    0xCFD8: 'The script continues from there', 0xCFDC: '',
    0xCFEE: '', 0xCFFA: 'A = frame +5 for the caller',
    0xCFFE: 'Free the frame', 0xD001: 'Reload the plan registers (the caller\'s)'})
A[0xC9BF]['desc'].append(
    "UPDATED 2026-11-07: $A01F is how many minutes the action takes - the "
    "main loop ($A064) adds it to the actor's next-turn time. Confirmed in "
    "the emulator by watching the player's next-turn time (actor table "
    "+6/+7): WAIT (WAIT HERE, byte 1 $50) moves it on by 5, TAKE LAMP "
    "($DCC1, $10) and EXAMINE LAMP ($DF40, $10) by 1 each. Records run "
    "inside sub-scripts and characters' interruptions make the clock look "
    "less regular from the player's side, which is probably what threw "
    "the earlier test.")
A[0x9EC1]['title'] = 'After-turn routines for Strachan, the cook and the gardener: bedtime'
A[0x9EC1]['desc'] = [
    "$9EC1 (Strachan, with B = room 74, Daphne's room), $9ECB (the cook) "
    "and $9ED1 (the gardener, both with B = 0, off stage) share $9ED7, "
    "with a one-byte state each ($9EC0, $9ECA, $9ED0). At 9pm the "
    "character's room is saved in the state byte, the character moves to "
    "room B, is described as SLEEPING (word $07F0 written to its +9/+10 "
    "by $F1C1), stops counting as a person (+5 bit 6 cleared, so it "
    "cannot be talked to) and has its next turn put back 504 to 533 "
    "minutes - until about 5:30am. On that next turn it goes back to the "
    "saved room and is a person again. Read from the code; not watched in "
    "the emulator."]
blk(0xF1C1, 'c', "Set a thing's state word and state bits",
    ["Thing A's +9/+10 = DE (a dictionary word shown with it, such as "
     "SLEEPING, or 0) and the high nibble of +8 = B. Read from the code."])
blk(0x9CA2, 'c', "Phipps's after-turn routine",
    ["Once thing $55 (85, the burning note) has been revealed (+5 bit 7), "
     "counts down $9CA1; when it reaches 0, the note is described as BURNT "
     "(word $015B into its +9/+10), its +$0D/+$0E are cleared, and bit 1 "
     "of +3 of the case record at $99B7 is cleared. Read from the code."])
_helper(0xE7E2, 'Script helper: is the actor carrying this?',
    ["A record with no code to speak of (OR 1 / RET): all the work is the "
     "requirement code 10 in its header - the direct object must be here "
     "and held by the actor - so RUN $E7E2 / thing simply fails unless the "
     "actor has the thing (Watson and his newspaper, Lestrade and the large "
     "rock). Read from the code; requirement 10 itself is confirmed by "
     "play (see $C628)."], {0xE7E4: 'Nothing else to check: succeed'})
A[0xCC37]['title'] = "Start an actor's turn"
A[0xCC37]['desc'].insert(0,
    "UPDATED 2026-11-07, from the main loop ($A064) and the plan "
    "interpreter: clears the failure count ($CC0B), finds the actor's "
    "record (IY, saved at $9FDB, id at $A036), sets $CC0D when an order "
    "or remark is waiting for it ($B91F), works out its room and the "
    "player's ($CC29, $D045), and switches output on ($5C3C = 1) only if "
    "the player can see the actor ($C821) - which is why you only read "
    "what characters do when they are with you. $A01F starts at 0 (1 if "
    "the actor is not found). Consistent with the emulator: Lestrade "
    "hailing a cab and giving the cabbie his orders appears in the "
    "output only in the runs where the player was moved to his room.")

# ---------------------------------------------------------------------
# Saving and loading (read from the code: the harness has no tape)
# ---------------------------------------------------------------------
blk(0xB0AC, 'c', 'After a game-over message: get ready to load a saved game',
    ["Resets the minute counter and the player's next-turn time to 0 and "
     "sets $A0DA = 1, so the main loop ($A064) goes to $B0D7 at the end of "
     "the minute. $B0C6 is the other way out: $A0DA = 2 (save, then carry "
     "on). Read from the code."])
blk(0xB0D7, 'c', 'Load a saved game from tape',
    ["Loads the game state ($B0EE: from $840B, 7,188 bytes, up to $A01F) "
     "with the ROM's LD-BYTES ($C0DF), asking again until it loads, then "
     "restores IY from $9FD4 and returns to the main loop's restart at "
     "$A040. $B0E4 is the save: it keeps IY at $9FD4 and saves the same "
     "block ($C040). Read from the code; the harness cannot run the "
     "ROM's tape routines. Confirmed in the emulator only that a game over "
     "ends with 'PLAY SAVED GAME TAPE TO BE LOADED'."],
    comments={0xB0D7: 'Which block', 0xB0DA: 'Load it...', 0xB0DD: '...until it works',
              0xB0DF: 'IY as saved', 0xB0E4: 'Save: remember IY', 0xB0E8: 'Which block',
              0xB0EB: 'Save it (and verify)'})
blk(0xB0EE, 'c', 'The block a saved game holds: $840B up to $A01F',
    ["IX = $840B (the room table), DE = $A01F - $840B. So a saved game is "
     "the rooms, the entities, the case table, the actor table, the heap "
     "and the variables - but not the plan scripts, which never change "
     "(no script uses one-shot instructions)."])
blk(0xC040, 'c', 'Save the game to tape, then verify it',
    ["Prints a prompt taken from the ROM's tape messages ($C1C0 with "
     "HL = $09A2; not checked which words), "
     "writes a 17-byte header ($C0FE: a code file named 'SHD V2.0') and "
     "the block with SA-BYTES ($04C2), then asks for the tape to be "
     "rewound ('REWIND TAPE', $C0A5) and verifies both with LD-BYTES "
     "($0556) - 'TAPE ERROR' ($C0B1) if they do not match. Read from the "
     "code."])
blk(0xC0DF, 'c', 'Load the saved-game block from tape',
    ["DE = length, IX = start (kept at $C109/$C10B). Prints 'PLAY SAVED "
     "GAME TAPE TO BE LOADED' ($C0BC), reads the 17-byte header into "
     "$C0FE with LD-BYTES until one arrives, then the block ($C089). Read "
     "from the code."])

# The cast page, again, with where each character starts and its
# after-turn routine.
from objects import entities as _ents  # noqa: E402
import html as _h2  # noqa: E402
_EREC = {e['id']: e for e in _ents()}
_AFTER = {}
_a = 0x9C85
while b(_a) != 0xFF:
    _AFTER[b(_a)] = w(_a + 1)
    _a += 3
_rows2 = []
for start, ids in sorted(ACTOR_SCRIPTS.items(), key=lambda kv: kv[1][0]):
    got, hours, rooms_, said, partners, ends, puts = _summary(start)
    names = ', '.join(f'{i} {_h2.escape(ENT.get(i, "?"))}' for i in ids)
    where_ = ', '.join(_h2.escape(room(_EREC[i]['room'])) if _EREC.get(i) and _EREC[i].get('room') is not None
                       else '-' for i in ids)
    after = ', '.join(f'#R${_AFTER[i]:04X}' for i in ids if i in _AFTER) or '-'
    busy = sum(1 for r in got.values() if r['code'] and r['op'] & 0x40)
    bits = []
    if hours:
        bits.append('waits for ' + ', '.join(_hour(h) for h in sorted(hours)))
    if partners:
        bits.append('; '.join(f'{k} {_h2.escape(ENT.get(n, str(n)))}' for k, n in sorted(partners)))
    if rooms_:
        bits.append('checks where people are: ' + ', '.join(_h2.escape(room(n)) for n in sorted(rooms_)))
    if puts:
        bits.append('moves things: ' + ', '.join(f'{_h2.escape(arg_obj(o))} to {_h2.escape(room(rm))}'
                                                 for o, rm in sorted(puts)))
    if ends:
        bits.append('can end the game: ' + ', '.join(f'#R${e:04X}' for e in sorted(ends)))
    lines = ''.join(f'<li>#R${a2:04X}: {_h2.escape(msg_text(m, 110)[2:] or f"${m:04X}")}</li>'
                    for a2, m in said[:12])
    if len(said) > 12:
        lines += f'<li>... and {len(said) - 12} more</li>'
    _rows2.append(f'<tr><td>{names}</td><td>{where_}</td><td>#R${start:04X}</td>'
                  f'<td>{len(got)} ({busy} busy)</td><td>{after}</td>'
                  f'<td>{"<br>".join(bits) or "-"}{"<ul>" + lines + "</ul>" if lines else ""}</td></tr>')
for _i, (_pid, _title, _html_) in enumerate(PAGES):
    if _pid == 'cast':
        _head = _html_[:_html_.index('<table')]
        PAGES[_i] = (_pid, _title, _head +
                     '<p>"Starts in" is the room in the file, before the opening '
                     'minutes are played. "Busy" instructions make the character '
                     'refuse what the player asks (#R$CBA7). The after-turn routine '
                     'runs after each of its turns (#R$9C77).</p>'
                     '<table class="disassembly"><tr><th>Actor</th><th>Starts in</th>'
                     '<th>Script</th><th>Instructions</th><th>After-turn</th>'
                     '<th>What it does</th></tr>' + ''.join(_rows2) + '</table>')
A[0x9EC1]['desc'][0] = A[0x9EC1]['desc'][0].replace(
    "Read from the code; not watched in the emulator.",
    "Confirmed in the emulator for the evening (tools/experiments/"
    "bedtime_test.py, with $9D90 poked so the 3pm ending does not come "
    "first): at 9:00pm the cook (room 65) and the gardener were still "
    "about; at 9:05pm both were in room 0 and Strachan in room 74, each "
    "with +5 gone from $E0 to $A0 (bit 6 cleared) and +9/+10 = $07F0, "
    "SLEEPING. The return in the morning was not watched.")
fact('bedtime',
     "The household goes to bed at 9pm",
     "At 9pm Daphne Strachan goes to her room and the cook and the "
     "gardener leave the game for the night, each marked SLEEPING and no "
     "longer counted as a person (so they cannot be talked to); they come "
     "back about eight and a half hours later. Their after-turn routines "
     "do it ($9EC1). Confirmed in the emulator for the evening; the "
     "morning return was read from the code.")

# ---------------------------------------------------------------------
# Pictures (2026-11-07, evening): the two "undecoded data" blocks at
# $FBED and $FDED, and everything from $F638 up, are room pictures.
# ---------------------------------------------------------------------
_PICS = []
_a = w(0xA0D8)          # $F60C
while b(_a) != 0xFF:
    _PICS.append((b(_a), w(_a + 1), _a))
    _a += 3
_PIC_END = _a
blk(0xF60B, 'b', 'Fill pattern for the picture interpreter',
    ["Set by $F490 (A on entry) and used while filling. CORRECTED: the "
     "automatic split had this as code."], subs=[('B', 0xF60B, 1, 'Fill pattern')])
A[0xF60B]['end'] = 0xF60C
blk(0xF60C, 'b', 'Which rooms have a picture',
    [f"{len(_PICS)} three-byte entries (room, address of its picture), ended "
     "by $FF; $A0D8 points here and $A25D searches it ($D34E) when a room "
     "is described with pictures switched on ($A011). Rooms 54 and 55 "
     "share one picture."],
    subs=[('B', _e, 3, f'Room {_r} ({room(_r)[len(str(_r)) + 7:-1] if _r in _R else "?"}): ${_p:04X}')
          for _r, _p, _e in _PICS] + [('B', _PIC_END, 2, 'End marker, and a spare byte')])
A[0xF60C]['end'] = _PIC_END + 2
_starts = sorted({_p for _r, _p, _e in _PICS})
for _i, _p in enumerate(_starts):
    _prooms = [_r for _r, _q, _e in _PICS if _q == _p]
    _end = _starts[_i + 1] if _i + 1 < len(_starts) else 0x10000
    if _p in A:
        del A[_p]
    blk(_p, 'b', 'Picture: ' + ', '.join(room(_r) for _r in _prooms),
        ["Picture bytecode for $F3C2, read from the interpreter: $00 ends "
         "it; $08 x y moves the pen; a byte with bit 7 set draws a line "
         "(direction and length packed into it and the next byte, $F56E); "
         "bit 6 fills from a point with a pattern ($F490); bit 5 colours "
         "runs of character cells (an attribute address, then length/"
         "direction bytes up to $FF). Not drawn in the emulator: the "
         "harness skips pictures because they need the ROM.",
         "CORRECTED: the automatic split had parts of this as code and "
         "text, and an earlier version of this overlay called $FBED and "
         "$FDED 'data, not decoded'."])
    A[_p]['end'] = _end
for _a in (0xFBED, 0xFDED):
    if _a in A and A[_a]['title'] == 'Data, not decoded':
        del A[_a]
A[0xF3C2]['title'] = 'Draw a picture (the picture interpreter)'
A[0xF3C2]['desc'] = [
    "HL = the picture's bytecode (from the table at $F60C via $A277). "
    "The pen starts at (127, 63). Commands, read from the code: $00 end; "
    "$08 move the pen (next two bytes); bit 7 set: draw a line ($F56E); "
    "bit 6: fill ($F490); bit 5: colour runs of attribute cells. Plots "
    "through the ROM's PIXEL-ADD ($22AA), which is why the harness skips "
    "it."]

_cells = []
for _p in _starts:
    _prooms = [_r for _r, _q, _e in _PICS if _q == _p]
    _cells.append(f'<div style="display:inline-block;margin:6px;vertical-align:top;width:260px">'
                  f'<img src="pictures/pic-{_p:04X}.png" width="256" height="256" alt="picture">'
                  f'<br>#R${_p:04X}: ' + _h2.escape(', '.join(room(_r) for _r in _prooms)) + '</div>')
page('pictures', 'Pictures',
     '<p>The 13 room pictures, drawn by the game\'s own picture interpreter '
     '(#R$F3C2) running in the emulator with the Spectrum ROM loaded '
     '(tools/draw_pictures.py; tools/package.sh regenerates them). Each '
     'picture fills the top right quarter of the screen; only 14 of the '
     'rooms have one (#R$F60C), rooms 54 and 55 sharing a picture. '
     'Every one ran to its end marker and returned, which confirms the '
     'picture-data boundaries used in this disassembly.</p>'
     '<p>And the whole game screen, from the emulator with the ROM loaded and '
     'pictures switched on (tools/experiments/screen_test.py): the player moved '
     'to Baker Street and typed LOOK. The room text wraps in the narrow window '
     'beside the picture, the clock sits in the bar, and the commands scroll '
     'below.</p><p><img src="pictures/screen.png" width="512" height="384" '
     'alt="The game screen on Baker Street"></p>' + ''.join(_cells))
for _p in _starts:
    A[_p]['desc'][0] = A[_p]['desc'][0].replace(
        "Not drawn in the emulator: the harness skips pictures because they "
        "need the ROM.",
        "Drawn in the emulator with the ROM loaded (tools/draw_pictures.py): "
        "see the Pictures page.")
A[0xF3C2]['desc'].append(
    "Confirmed in the emulator: with SkoolKit's copy of the 48K ROM at "
    "$0000, calling this for each of the 13 pictures draws a recognisable "
    "scene (Baker Street's lamp post and door, the entrance hallway's stairs, a grand piano, "
    "Brown's house at night...) in the top right quarter of the screen and "
    "returns. The game harness still skips it, to keep play fast.")
fact('thirteen-pictures',
     "Only fourteen rooms have a picture",
     "The picture table at $F60C lists 14 of the game's rooms, and two of "
     "them (platforms one and two) share a picture, so there are 13 "
     "pictures in all, stored as drawing commands from $F638 to the very "
     "top of memory. Run in the emulator with the ROM loaded, the game's "
     "own interpreter draws every one of them in the top right quarter of "
     "the screen - see the Pictures page. An earlier version of this "
     "disassembly had two of them down as 'data, not decoded'.")

for _a, _k, _t, _d in (
        (0xF48E, 'b', 'Fill state', "Two flags used by the fill ($F490) to remember whether the rows above and below have been seeded."),
        (0xF490, 'c', 'Fill the area around the pen in colour A', "A scan-line flood fill: the colour goes to $F60B, seeds are kept on the stack (a $00B0 marker ends them), and each row is filled left and right, seeding the rows above and below ($F48E/$F48F). Read from the code; the drawn pictures show it works."),
        (0xF50D, 'c', 'Is the pixel under the pen set? (NZ if so)', "Through $F5FB (the ROM's PIXEL-ADD)."),
        (0xF514, 'c', 'Move attribute address HL up a row (not past the top)', "$F525 down, $F536 left, $F540 right: the four moves of a colour run (bit 5 commands in $F3C2)."),
        (0xF54A, 'c', 'Move the pen one pixel (Z when it would leave the picture area)',
         "E is the pen's y and D its x. $F54A moves down (stopping at 176), $F555 up (stopping at 0), $F55E right (stopping at 255), $F565 left - stopping when bit 7 of D would clear, so the pen can never leave the right half of the screen, which is why every picture sits there."),
        (0xF56E, 'c', 'Draw a line from the pen',
         "L = the number of steps, B the run length before a step on the minor axis, C the directions (bit 0: which axis is major; bits 1 and 2: up or down, left or right). Plots each point with $F5D2. Read from the code."),
        (0xF5D2, 'c', 'Plot the pen position in the current colour',
         "Sets the pixel at (D, E) and gives its character cell the ink in $F60B, keeping the cell's paper."),
        (0xF5FB, 'c', 'Find the screen byte and bit for the pen', "The ROM's PIXEL-ADD ($22AA) with B = y and C = x, then a mask for the bit.")):
    blk(_a, _k, _t, [_d])
A[0xF48E]['end'] = 0xF490
for _a, _e in ((0xF490, 0xF50D), (0xF50D, 0xF514), (0xF514, 0xF54A), (0xF54A, 0xF56E),
               (0xF56E, 0xF5D2), (0xF5D2, 0xF5FB), (0xF5FB, 0xF60B)):
    A[_a]['end'] = _e
A[0xF3C2]['end'] = 0xF48E

# ---------------------------------------------------------------------
# The parser's special words ($AF6B), and the quoted-speech hand-over
# ---------------------------------------------------------------------
_SW = []
_a = 0xAF6B
while _a < 0xAFB3:
    _SW.append(('B', _a, 4, f'{_WS.get(w(_a) & 0xFFF, "a quote mark") if w(_a) else "a quote mark"} -> ${w(_a + 2):04X}'))
    _a += 4
blk(0xAF67, 'c', 'Not a special word: NZ', [])
blk(0xAF6B, 'b', 'Special words and their handlers',
    ["Four-byte entries (word reference, handler). $AFB3 searches the "
     "first twelve for an ordinary sentence, and only the last six - "
     "THATS, HE, IT, THEY, BECAUSE, THEREFORE - inside something said to a "
     "character ($A024 = 2). HE, IT and THEY appear twice with different "
     "handlers, one per search. CORRECTED: the automatic split had this "
     "as code."], subs=_SW)
A[0xAF6B]['end'] = 0xAFB3
blk(0xAFB3, 'c', 'Is word BC a special word? Then run its handler',
    ["Searches the table at $AF6B (see there for which part) and jumps "
     "to the handler; otherwise NZ ($AF67). Read from the code."],
    comments={0xAFB3: 'The ordinary words...', 0xAFB6: '...unless this is speech',
              0xAFBD: 'Speech: the last six', 0xAFC1: 'Twelve entries...', 0xAFC5: '...or six',
              0xAFC7: 'This word?', 0xAFD0: 'No: next entry', 0xAFD6: 'Not special',
              0xAFDA: 'Yes: its handler', 0xAFE0: 'Run it'})
A[0xAFB3]['end'] = 0xAFE1
blk(0xAFE1, 'c', 'Handler guards: only at the start of a sentence (not traced)',
    ["$AFE1 and $AFE8 throw the word back as ordinary ($AF67) when the "
     "parse so far ($A012, $A01B, flags in E) says it is not where a "
     "command word belongs."])
A[0xAFE1]['end'] = 0xAFFA
blk(0xAFFA, 'c', 'Handlers for BECAUSE / THEREFORE, PRINT and NOPRINT',
    ["$AFFA (BECAUSE, THEREFORE): carry on as a sentence break ($ACCC) "
     "- not traced. $AFFF (PRINT) and $B00B (NOPRINT) switch the copy of "
     "the text to the ZX printer on or off ($A008, with a call to $C03B "
     "that was not traced). Confirmed only that NOPRINT is accepted quietly."])
A[0xAFFA]['end'] = 0xB01C
blk(0xB01C, 'c', 'Handlers for BUT, ALL and a quote mark',
    ["$B01C (BUT, after ALL) and $B033 (ALL) set $A01A to 2 and 1 for "
     "'all but' and 'all'. $B049 (a quote mark): the words that follow "
     "are speech; their position is added to the list at $9FEC and the "
     "parser skips to the closing quote, marking it as the end of a "
     "sentence. $B86A hands them on when SAY TO / TALK TO runs. $B09A "
     "(PAUSE) waits ($C415). $B0A3 (LOAD, and QUIT too) goes to $B0AC: "
     "the game asks for a saved-game tape. Read from the code.",
     "Confirmed in the emulator: QUIT and LOAD both print 'PLAY SAVED "
     "GAME TAPE TO BE LOADED' and set $A0DA to 1; PAUSE and NOPRINT are "
     "accepted with no message."])
A[0xB01C]['end'] = 0xB0AC
blk(0xB0C6, 'c', 'Handler for SAVE', ["$A0DA = 2: at the end of the minute the main loop saves the game ($B0E4) and carries on."])
blk(0xB0FD, 'c', 'Handlers for THATS, HE, IT and THEY',
    ["Pronouns: HE sets bit 7 and IT/THEY bit 6 of the current parse "
     "record's +$19 (resolved later to the last person or thing "
     "mentioned - not traced); the first-word versions ($B135, $B151) "
     "also mark the sentence as a statement to a character ($A024 = 2). "
     "THATS ($B0FD) rearranges the parse record's object slots (not "
     "traced). Read from the code. "
     "CORRECTED: the automatic split had $B0FD-$B16C as data."])
A[0xB0FD]['end'] = 0xB16D
blk(0xB16D, 'b', 'Parser variables',
    ["Work space for the parser: $B16D/$B16E counters, the object slots "
     "at $B172 and $B178 (6 bytes each; $BDC2 reads them as the "
     "statement's things), $B182-$B186, and the saved verb pattern at "
     "$B18E that the questions at $B5D3 quote from. CORRECTED: the "
     "automatic split had this as code."])
A[0xB16D]['end'] = 0xB191
blk(0xB866, 'b', 'Speech hand-over variables',
    ["$B866: the order or remark node found by $B90E. $B868: where the "
     "quoted words being handed over start."],
    subs=[('W', 0xB866, 2, 'Node found by $B90E'), ('W', 0xB868, 2, 'Start of the quoted words')])
A[0xB866]['end'] = 0xB86A
blk(0xB86A, 'c', 'Hand quoted words to the person spoken to (SAY TO / TALK TO)',
    ["Called by the TALK TO body ($DDAE) with A = 1 if the person has a "
     "plan script (an actor, $CC0E) and 0 if not. Takes the next quoted "
     "sentence off the list at $9FEC. For an actor, $B8AA puts it on the "
     "order/remark list ($9FEE) as an 8-byte node: +0 the person, +1 0, "
     "+5/+6 the words, +7 = $A024 (2 for a statement); the person deals "
     "with it on its next turn ($B936). For anyone else the words are just "
     "used up. Read from the code; the effect (Watson getting out of his "
     "chair, Watson and Lestrade answering statements) is confirmed in "
     "the emulator - see $CBA7, $BA67 and $BB67.",
     "CORRECTED: the automatic split had $B866-$B90D as data and text."])
A[0xB86A]['end'] = 0xB90E
A[0x9FD6]['subs'] = [s_ for s_ in A[0x9FD6]['subs'] if s_[1] != 0x9FEB] + [
    ('B', 0x9FEB, 1, '$9FEB: not identified ($D781 clears it)'),
    ('W', 0x9FEC, 2, '$9FEC: quoted speech waiting to be handed over ($B049, $B86A)')]
A[0x9FD6]['subs'].sort(key=lambda s_: s_[1])
fact('quit-means-load',
     "QUIT does not quit",
     "QUIT and LOAD share one handler in the parser's table of special "
     "words ($AF6B): both end the game the way a game-over message does "
     "and ask for a saved-game tape ('PLAY SAVED GAME TAPE TO BE LOADED'). "
     "Confirmed in the emulator. The same table holds SAVE, PAUSE, PRINT "
     "and NOPRINT (a copy to the ZX printer), ALL and ALL BUT, the quote "
     "mark that starts speech, and the pronouns.")
A[0xBDC2]['end'] = 0xBE5A
A[0xBDC2]['desc'].append("$BE22 copies thing A's 6-byte entry to $9FF6 (a person, +5 bit 6) "
                         "or $9FFC; $BE3C and $BE4B step through the parser's object slots "
                         "at $B172 and $B178. CORRECTED: the automatic split had $BE1A-$BE59 as data.")
A[0xB98C]['end'] = 0xB9FA
A[0xB98C]['desc'].append("$B9AC-$B9F9 belong to the remark path of $B936: $B9CA hands the "
                         "remark's remaining words back (node +5/+6) one sentence at a time, "
                         "freeing what has been used. Not traced in detail. CORRECTED: the "
                         "automatic split had $B9AC-$B9F9 as data.")

# ---------------------------------------------------------------------
# Typed numbers: clock times and pre-decimal money ($DAC6-$DC12)
# ---------------------------------------------------------------------
blk(0xDAC6, 'c', 'Read a token that is not a word: money, a number or punctuation',
    ["A '£' (character $60) starts an amount of money ($DB67); a digit "
     "starts a time or a number ($DAEF); a full stop, comma or quote mark "
     "gives the punctuation tokens $B0, $A0 and $90. Read from the code."])
blk(0xDAE8, 'c', 'Is A a digit? (carry if not)', [])
blk(0xDAEF, 'c', 'Read a time, or a number that may turn out to be money',
    ["A number followed by ':' (minutes), 'A' or 'P' (then 'M') is a "
     "time: B = the hour with bit 7 set and bit 6 for AM, C = the "
     "minutes with bit 6 for PM. Anything else goes to the money reader "
     "at $DB84 (so '2/6' and '3S' need no '£'). Returns A = $F0 for a "
     "number token, or $D0 and BC = 0 if it makes no sense."])
A[0xDAEF]['end'] = 0xDB56
blk(0xDB56, 'c', 'Is A a separator (full stop, comma or space)? Z if so', [])
blk(0xDB64, 'b', 'Pounds, shillings and pence',
    ["The three parts of an amount being read, added up at $DBC0."],
    subs=[('B', 0xDB64, 1, 'Pounds'), ('B', 0xDB65, 1, 'Shillings'), ('B', 0xDB66, 1, 'Pence')])
A[0xDB64]['end'] = 0xDB67
blk(0xDB67, 'c', 'Read an amount of pre-decimal money',
    ["'£n' gives pounds; then 'nS' is shillings, 'nD' pence, and 'n/m' "
     "shillings and pence ('n/-' for none). The total is worked out in "
     "pence - (pounds x 20 + shillings) x 12 + pence - and packed into "
     "BC seven bits per byte with bit 7 of both bytes set, which is what "
     "tells a sum of money from a time (requirement code 6, PAY TO, wants "
     "bit 7 set in the low byte; code 5, WAIT UNTIL, wants it clear).",
     "Confirmed in the emulator (tools/experiments/money_test.py): '£1' "
     "reads as $81F0 (240 pence), '2/6' as $809E (30), '3S' as $80A4 "
     "(36), '1/-' as $808C (12), and '9:30AM' as $C91E; the game echoes "
     "them back as 'You pay £1 to Watson.', '2/6', '3/-' and '1/-'."],
    comments={0xDB67: "After the '£'", 0xDB68: 'Pounds', 0xDB84: 'No pounds',
              0xDB8F: 'S: shillings', 0xDB9A: 'D: pence', 0xDBA4: '/: shillings, then pence or -',
              0xDBC0: 'Total in pence: pounds x 20...', 0xDBCE: '...plus shillings...',
              0xDBD5: '...times 12...', 0xDBDB: '...plus pence',
              0xDBE4: 'Too much?', 0xDBEA: 'Pack it: 7 bits a byte, bit 7 set in both'})
A[0xDB67]['end'] = 0xDBF7
blk(0xDBF7, 'c', 'Read a decimal number at HL into A', [])
A[0xDBF7]['end'] = 0xDC13
fact('pounds-shillings-pence',
     "The parser understands pounds, shillings and pence",
     "Typed sums of money are pre-decimal: £1, 3S, 6D, 2/6 or 1/- all "
     "work, and are converted to pence ((pounds x 20 + shillings) x 12 + "
     "pence, $DB67). Confirmed in the emulator: PAY 2/6 TO WATSON reads "
     "as 30 pence and the game answers 'You pay 2/6 to Watson.'; PAY 3S "
     "comes back as '3/-'. Times are read by the same code ('9:30AM').")

# Narration details and number printing.
blk(0xA37D, 'c', 'Print the rest of a narrated command: verb words, objects, numbers',
    ["Part of $A2E4. From the verb pattern ($A2B1/$A2BD) and the parse "
     "flags ($A01D/$A01E) prints the verb's words ($A880), then the "
     "direct object - as a number or money ($A419) when it is one ($FE), "
     "as 'yourself' (word $055B) when it is the actor, or by name "
     "($A745) - then any preposition and the indirect object the same "
     "way, and a full stop. Read from the code; 'You pay 2/6 to Watson.' "
     "in the emulator is one of its sentences."])
blk(0xA419, 'c', 'Print an amount of money',
    ["HL = a sum in the packed form the parser makes ($DB67). Prints it "
     "the old way: '£n' if there are pounds, then shillings and pence as "
     "'s/d', 's/-' or 'dD'. Divides with $A476 and prints digits with "
     "$A490. Confirmed in the emulator through PAY: 30 pence prints as "
     "'2/6', 36 as '3/-', 240 as '£1'."])
A[0xA419]['end'] = 0xA476
blk(0xA476, 'c', 'Divide HL by DE: A = quotient, HL = remainder', [])
blk(0xA480, 'c', 'Print one digit of HL / DE, skipping leading zeros (C)', [])
blk(0xA490, 'c', 'Print the number B (0-255) in decimal', [])
blk(0xA4AB, 'c', "HL = room A's record + 1", [])
blk(0xA4BC, 'c', "HL = thing A's record + 7", [])
blk(0xBF59, 't', 'Day names, and the clock text being built',
    ["Seven three-letter day names (Mon-Sun) for $BFC6, then $BF6E, the "
     "11-character clock text ('MON 00:00am' as it stands in the file) "
     "that $BF79 fills in and prints."],
    subs=[('T', 0xBF59, 21, 'Mon Tue Wed Thu Fri Sat Sun'), ('T', 0xBF6E, 11, 'The clock text')])
A[0xBF59]['end'] = 0xBF79
blk(0xBF79, 'c', 'Print the clock: day, hour, minute, a or p',
    ["Builds 'Mon 08:02am' in $BF6E from the day ($9FE1), the hour "
     "($9FE0), the minute ($9FDF) and the letter ($9FE2), and prints it "
     "in the status bar ($C1A8). Confirmed by every emulator run: the "
     "clock text is what the harness captures between commands."],
    comments={0xBF79: 'Where the text goes', 0xBF7D: 'The day...', 0xBF83: '...as three letters',
              0xBF88: 'The hour, two digits', 0xBF90: 'The minute, two digits',
              0xBF96: "'a' or 'p'", 0xBF9C: 'Print the 11 characters'})
A[0xBF79]['end'] = 0xBFD9

blk(0xA20C, 'c', 'Join free block IX to the next one if they touch',
    ["Used by $A1C7. NZ if there is no next free block; Z after joining "
     "(sizes added, link taken over)."])
blk(0xC1F4, 'b', 'Command-window state',
    ["The bottom window, where the player's typing is echoed. $C1F4: "
     "characters left on the line (36 to a line: the font is 7 pixels "
     "wide); $C1F6/$C1F7: the screen address being written; $C1FB: the "
     "pixel offset within the byte. $C1F5 is also used by the page wait "
     "(overlay 01). Read from the code."],
    subs=[('B', 0xC1F4, 1, 'Characters left on the line'), ('B', 0xC1F5, 1, 'Line count (see $C306)'),
          ('W', 0xC1F6, 2, 'Screen address'), ('B', 0xC1F8, 3, 'Not identified'),
          ('B', 0xC1FB, 1, 'Pixel offset')])
A[0xC1F4]['end'] = 0xC1FC
blk(0xC1FC, 'c', 'Echo a typed character in the command window',
    ["Letters are shown in capitals ($C240); ENTER becomes a space and a "
     "new line, DELETE steps back 7 pixels ($C249, $C267); at the end of "
     "a line the window scrolls ($C271). A '+' is drawn after the "
     "character as the cursor - the '+' at the bottom of the screen in "
     "the emulator screenshot (Pictures page)."])
A[0xC1FC]['end'] = 0xC240
blk(0xC240, 'c', 'Upper-case A if it is a lower-case letter', [])
blk(0xC249, 'c', 'Rub out the last character in the command window', [])
blk(0xC267, 'c', 'Step the print position back one 7-pixel character', [])
blk(0xC271, 'c', 'Scroll the command window up one line and clear the bottom line',
    ["Copies the text rows of the bottom third of the screen up by one "
     "character row ($5080 to $5060, 8 pixel lines) and blanks the last "
     "line."])

# ---------------------------------------------------------------------
# Describing a room ($D045-$D1DB)
# ---------------------------------------------------------------------
blk(0xD045, 'c', "Note the room the player is in ($A009)",
    ["Called at the start of every actor's turn ($CC5E): the room "
     "everything shown is judged against."])
blk(0xD04F, 'c', 'IX = just before the start of the thing index ($8B6F)', [])
_PREP = []
for _i in range(8):
    _PREP.append(('W', 0xD05A + 2 * _i, 2, f'Room kind {_i}: {_WS.get(w(0xD05A + 2 * _i) & 0xFFF, "?")}'))
blk(0xD05A, 'w', "How a room is entered in words: 'You are ON Baker Street'",
    ["Indexed by bits 1-3 of the room record's first byte ($D0DD): "
     "OUTSIDE, INSIDE, IN, ON, AT, NORTH, SOUTH, EAST. The word is "
     "written into the message 'YOU ARE IN' at $68DD itself (its second "
     "word, at $68DE) before it is printed - self-modifying message data. "
     "Confirmed in the emulator in effect: Baker Street is described "
     "'You are on Baker Street.' CORRECTED: the automatic split had this "
     "as code."], subs=_PREP)
A[0xD05A]['end'] = 0xD06A
blk(0xD06A, 'b', 'Not identified (14 bytes)', [])
A[0xD06A]['end'] = 0xD078
blk(0xD078, 'c', 'Is it too dark for the actor to see? (carry if so)',
    ["Not dark unless the actor's room is a dark one (its record's +4 "
     "bit 7). Then it is dark unless a light is found ($D09E): a thing "
     "whose +5 flags, masked with $5C, match $B7 (lit, among others) "
     "and that the player can see ($C821). Some conditions on the way "
     "($C86E, $D33C, $C00C) were not traced. Used by action records ($C9C3), the "
     "narration ($A30A) and the brief room description ($D1BB). Read "
     "from the code."])
A[0xD078]['end'] = 0xD0D0
blk(0xD0D0, 'c', "Put word HL into the 'YOU ARE ...' message", ["Writes it, as a word token (bit 7 set), at $68DE."])
blk(0xD0DC, 'b', "Set to use 'YOU CAN SEE' instead of 'YOU ARE ...'", [], subs=[('B', 0xD0DC, 1, 'Flag')])
A[0xD0DC]['end'] = 0xD0DD
blk(0xD0DD, 'c', "Get the room's opening: 'YOU ARE ON/IN/AT ...' or 'YOU CAN SEE'",
    ["HL = the message to start the description with; for 'YOU ARE' the "
     "preposition is chosen from $D05A by the room's kind."])
blk(0xD102, 'c', 'Describe room A in full (the first visit)', ["$D0DD, then $D113."])
blk(0xD113, 'c', 'Describe room A in full',
    ["The picture, if pictures are on and the room has one ($A277); 'YOU "
     "ARE IN <thing>' when the actor is inside something ($C863); the "
     "room's own text or 'YOU ARE ON/IN ... <name>' ($D182); the exits "
     "($D60B); the things here ($D68C); the people here ($D4A7); end of "
     "line. Read from the code; the emulator's LOOK output follows this "
     "order ('You are on Baker Street. To the north there is the front "
     "door.')."])
blk(0xD182, 'c', "Print a room's description",
    ["HL = the room's own description text (+7/+8 of its record); if it "
     "has none, the opening from $D0DD with the room's name ($D1C6) and a "
     "full stop. $D1B2 is the brief version for a room already visited, "
     "adding 'IT IS TOO DARK TO SEE MUCH ELSE.' ($68C1) when dark."])
A[0xD078]['desc'] = [
    "Only for actors that need light: those with +4 bit 7 in their own "
    "record ($A017) - the player, the cabs and cabbies, the trains and a "
    "few others; everyone else sees in the dark. For them it is dark "
    "when inside something, or when the room's record has bit 7 of its "
    "first byte clear (outdoors, it seems) and $C00C says it is night "
    "(8pm to 6am) - unless a light is about: a thing that also has +4 "
    "bit 7, whose +5 flags masked with $5C give $14 (full and on, not a "
    "person: the oil lamp starts like this, +5 = $94), and that $C821 "
    "says is here.",
    "Confirmed in the emulator (tools/experiments/dark_test.py): walking "
    "to Baker Street and setting the clock to 9pm, LOOK gets 'SORRY IT IS "
    "TOO DARK.' without the oil lamp and the normal description with it. "
    "Moving the player by poking memory instead leaves a carried lamp's "
    "own room behind and the test fails - a harness trap worth knowing."]
blk(0xC00C, 'c', 'What part of the day is it? (A = 1-5)',
    ["1 night (8pm to 5:59am), 5 dawn (the 6am hour), 4 day (7am to "
     "12:59pm), 3 afternoon (1pm to 6:59pm), 2 dusk (the 7pm hour). Read "
     "from the code; $D078 treats 1 as dark."])
A[0xC00C]['end'] = 0xC03B
fact('bring-a-lamp',
     "It gets dark at 8pm",
     "Outdoors between 8pm and 6am the player cannot see without a light: "
     "LOOK on Baker Street at 9pm says 'SORRY IT IS TOO DARK.' unless the "
     "oil lamp from Holmes's room is being carried. The lamp is lit from "
     "the start (there is no verb to light it). Only the player and a few "
     "others need light at all ($D078). Confirmed in the emulator.")

for _a, _t, _d in (
        (0xD2A4, 'A random number below A', "$D2AD, made positive."),
        (0xD2AD, 'The random number generator',
         "Steps a pointer ($A039) through memory and mixes the byte it finds with $A037. Used for chances, countdowns and greeting delays. Read from the code."),
        (0xD36A, "Find the next thing that matches a word slot of the parse", "HL = the slot ($B172 or $B178); matches names through $A4E0. Read from the code."),
        (0xD405, "Print a thing's name with its adjectives (IY = its name words)", ""),
        (0xD4A7, "List the people here: 'YOU CAN SEE ...'", "$D4CC counts them, $68E4 starts the sentence, $D51A lists them."),
        (0xD4CC, 'Count the things in place B that should be listed (B)', "Each through $D4EF."),
        (0xD4EF, 'Should this thing be listed here?',
         "In the place, not the actor itself, visible to the player ($C821), and in exactly one location (so not a door). Read from the code."),
        (0xD51A, 'List the things in a place, with commas and AND', "$D526 does the work: it also marks each thing listed as seen by the player (+6 bit 7), which is what the case's evidence tests (see $9965)."),
        (0xD590, "Say what a person is carrying, or what is on or in a thing",
         "'<thing> IS CARRYING' ($68B1) for a person (+5 bit 6), otherwise IS or ARE and the relation word ($D5D3)."),
        (0xD5D3, "Print how a thing is held: IN, ON, BEHIND, UNDER or TIED TO",
         "From bits 0-2 of the container's +4 and the word table at $D5C9."),
        (0xD60B, "Describe the ways out through things: 'TO THE NORTH THERE IS THE FRONT DOOR'",
         "For each exit that passes through a thing (a door) that has been revealed (+5 bit 7). Confirmed in the emulator in effect: 'To the north there is the front door.' on Baker Street."),
        (0xD68C, "List the plain exits: 'VISIBLE EXITS ARE ...'", "$68F1, then the direction names ($D5FB)."),
        (0xD6E5, "Say 'I DO NOT KNOW THE WORD \"...\"'",
         "Quotes the unknown word from the typed line ($6859). Confirmed in the emulator: an old harness glitch produced 'I DO NOT KNOW THE WORD AIT'.")):
    blk(_a, 'c', _t, [_d] if _d else [])

blk(0xAE7F, 'c', 'Read the next token of the typed line',
    ["The word list built by $D715 ($5B81 on) is a run of tokens: a "
     "class byte, followed by a 2-byte word reference (BC) for classes "
     "$E0, $F0 (a number or money, the value from $DAC6), $90 (a quote "
     "mark) and those below $80 (words: $00, $20, $30 and $40 are the "
     "kinds of word the parser sorts on); the punctuation classes $A0 "
     "(comma) and $B0 (full stop) and $C0 (end of a sentence) have none. "
     "Returns the class in A and D, keeps the previous class at $A02D "
     "and the token's address at $A029. Read from the code."],
    comments={0xAE7F: 'Where this token starts', 0xAE85: 'Remember the previous class',
              0xAE89: 'The class', 0xAE8F: 'Classes with a word after them...',
              0xAE9F: '...BC = the word', 0xAEA4: 'Step past the token'})
blk(0xAAB2, 'c', 'Parse the next sentence from the word list',
    ["Called for the player's typed line ($D78F, part of the player's "
     "script step $D77E) and for the words of a remark ($B8BF). Sorts "
     "tokens into the parse record (IY) - the verb and its particles "
     "($AB91), objects ($AC24) - and dispatches on punctuation: a full "
     "stop finishes the sentence ($AD57), a comma starts another object "
     "or sentence ($ACCC), a quote mark goes to the special-word code "
     "($AFB3). NZ if it does not make sense ($AF67). Read from the code; "
     "only its outline was traced."])
A[0xAE7F]['desc'] = [
    "The word list built by $D715 ($5B81 on) is a run of tokens: a class "
    "byte, then - for classes below $80 and for $90, $E0 and $F0 - a "
    "2-byte word reference (high byte first) or value. Returns the class "
    "in A and D and the reference in BC, keeps the previous class at "
    "$A02D and the token's address at $A029.",
    "Confirmed in the emulator (tools/experiments/tokens_test.py): 'TAKE "
    "THE LAMP, EXAMINE IT. PAY 2/6 TO WATSON' becomes $30 TAKE, $80 (THE, "
    "no reference), $50 LAMP, $A0 (comma), $30 EXAMINE, $90 IT, $B0 (full "
    "stop), $30 PAY, $F0 $809E (2/6, 30 pence), $70 TO, $50 WATSON, $B0, "
    "$C0 (end). So $30 is a verb, $50 a noun, $70 a preposition, $80 a "
    "word with no meaning to the parser, $90 a special word (the table "
    "at $AF6B: IT, HE, QUIT, a quote mark...), $F0 a number or money, $A0 "
    "a comma, $B0 a full stop, $C0 the end. Other classes ($00, $20, $40, "
    "$E0, read by $AB91) were not seen in this line."]
A[0xAAB2]['desc'][0] = A[0xAAB2]['desc'][0].replace(
    "a quote mark goes to the special-word code ($AFB3)",
    "a special word (class $90) goes to $AFB3")
A[0x9965]['desc'].insert(3,
    "How a piece of evidence is checked ($BE91, read from the code): the "
    "top two bits of its flags choose the test. $00: both things seen "
    "(+6 bit 7); $40: both examined (+6 bit 6); $80: never true by itself "
    "- it only counts once something else has marked it done (bit 1), as "
    "the statement routines do through $9A74, so a nested statement such "
    "as MAJOR PERCIVAL FFOULKES VISITED OPIUM DEN ($8C) has to be "
    "established first; $C0: no test of its own, only its group. A "
    "record with children (bit 2) also needs all of them ($BF08). Once a "
    "piece of evidence passes it is marked done and stays so.")
blk(0xBE91, 'c', 'Check one piece of evidence (NZ if it holds)',
    ["See the case table at $9965 for the four kinds. Marks it done (bit "
     "1 set, bit 0 clear) when it holds."],
    comments={0xBE91: 'Already done?', 0xBE97: 'Which kind of test?', 0xBEA0: 'Seen: the first thing...',
              0xBEB0: '...and the second', 0xBEC0: 'It holds: mark it done', 0xBECD: 'Kind $80: never by itself',
              0xBED1: 'Kind $40: examined?', 0xBED5: 'The first thing...', 0xBEE5: '...and the second',
              0xBEF6: 'Children to check as well?', 0xBEFC: 'All of them'})
A[0xBE91]['end'] = 0xBF08
blk(0xBF08, 'c', 'Check every piece of evidence in the group after IX (Z if one fails)', [])

_MAJ = ("Confirmed in the emulator (tools/experiments/major_test.py): with the "
        "player moved to Lestrade at the start, MAJOR FFOULKES IS INNOCENT is "
        "marked waiting ($A4 -> $A5) and Lestrade at once asks 'Well can you "
        "prove that Major Percival Ffoulkes is innocent yet, Holmes ?'; MAJOR "
        "FFOULKES VISITED THE OPIUM DEN gets 'I do not believe that you have "
        "the evidence...'. With bit 1 of $9972 set first - as $F103 does when "
        "the Major confesses - the opium-den statement is proven, the waiting "
        "innocence statement is proven with it ($9968 $A5 -> $A6), $9A3D "
        "sets $9E88 and Lestrade says 'Very good Holmes, I shall return to "
        "Leather head tomorrow to have another look around.'")
A[0x9965]['desc'].insert(4, _MAJ)
if 0xF103 in A:
    A[0xF103]['title'] = "The Major's confession: establish 'MAJOR VISITED OPIUM DEN'"
    A[0xF103]['desc'] = [
        "Run by the Major's script ($F0E6) right after he tells the player "
        "'WELL HOLMES YOU HAVE FOUND OUT MY SHAMEFUL SECRET, I AM ADDICTED "
        "TO...' - which he only does when the player is with him in the "
        "opium den late at night (his script: after 11pm, by chance, to room "
        "40 and through the heavy oak door). Marks the empty evidence record "
        "at $996F done, which is the only way to prove MAJOR PERCIVAL "
        "FFOULKES VISITED OPIUM DEN and so MAJOR PERCIVAL FFOULKES IS "
        "INNOCENT. " + _MAJ]
fact('catch-the-major',
     "To clear the Major, catch him at the opium den",
     "MAJOR PERCIVAL FFOULKES IS INNOCENT can only be proven through a "
     "second statement, MAJOR PERCIVAL FFOULKES VISITED OPIUM DEN, whose "
     "only evidence is an empty record that nothing but the Major's own "
     "script marks: after 11pm he may slip off to the opium den, and if "
     "the player is there with him he confesses ('WELL HOLMES YOU HAVE "
     "FOUND OUT MY SHAMEFUL SECRET...', $F0E2) and the evidence is set "
     "($F103). Proving his innocence then stops the ending in which "
     "Lestrade arrests him ($9E85). The chain from the evidence onwards is "
     "confirmed in the emulator by setting the evidence bit and talking to "
     "Lestrade; the Major's night-time trip was read from his script.")

# ---------------------------------------------------------------------
# A generated page: the case, statement by statement
# ---------------------------------------------------------------------
_KIND = {0x00: 'seen', 0x40: 'examined', 0x80: 'established elsewhere', 0xC0: 'its group only'}
_SET_BY = {0x996F: "set by the Major's confession in the opium den (#R$F103)",
           0x998F: "set by #R$E1CB in shared action 3, which Tricia Fender performs when asked to tell about the bloodstained clothes away from them",
           0x9993: "set by #R$E199 in shared action 22, which Mrs Jones performs when asked what happened or about her alibi - she becomes an actor once Tricia Fender, asked about the bloodstained clothes, turns out to be her (#R$E03A)",
           0x99AF: "set by proving PHIPPS HAS PLANS (#R$9A13)",
           0x99B7: "already set at the start; cleared when the burning note burns (#R$9CA2)",
           0x99F7: "set by proving TRICIA FENDER HAD PLANS (#R$9A05)"}
_ROUT = {0x9A3D: "sets $9E88, so Lestrade will not arrest the Major (#R$9E85)",
         0x9A4B: "", 0x9A59: "Mrs Jones is led away (moved off stage)",
         0x9A13: "only if both murders are already proven; otherwise it is un-proven again",
         0x99FC: "", 0x9A05: "also establishes the evidence for TRICIA FENDER BLACKMAILED MRS BROWN",
         0x9A0A: ""}
_ROUT_MSG = {0x9A3D: 0x70F0, 0x9A4B: 0x6FAB, 0x9A59: 0x6FCA, 0x9A13: 0x7099, 0x99FC: 0x7079,
             0x9A05: 0x70E3, 0x9A0A: 0x70E3}
_rows3 = []
_a = 0x9965
_cur = None
_dep = 0
while b(_a) != 0xFF:
    _f = b(_a + 3)
    _n = 4 + (2 if _f & 0x30 else 0)
    def _thing(x):
        return _h2.escape(ENT.get(x, str(x)))
    if _dep == 0:
        _rt = w(_a + 4) if _f & 0x30 else 0
        _st = f'{_thing(b(_a))} {REL.get(b(_a + 1), "?")} {_thing(b(_a + 2))}'.upper()
        _cur = dict(addr=_a, st=_st, ev=[], rt=_rt, flags=_f)
        _rows3.append(_cur)
    else:
        if b(_a) == 0 and b(_a + 2) == 0:
            _cur['ev'].append(f'#R${_a:04X}: a marker - ' + _SET_BY.get(_a, 'nothing sets it, so this can never be proven'))
        elif b(_a + 1):
            _cur['ev'].append(f'#R${_a:04X}: the statement ' +
                              f'{_thing(b(_a))} {REL.get(b(_a + 1), "?")} {_thing(b(_a + 2))}'.upper() +
                              ', proven in its own right (tell it to Lestrade); its evidence follows')
        else:
            _cur['ev'].append(f'#R${_a:04X}: {_thing(b(_a))} and {_thing(b(_a + 2))} {_KIND[_f & 0xC0]}')
    if _f & 4:
        _dep += 1
    if _f & 8:
        _dep = max(0, _dep - 1)
    _a += _n
_tr = []
for r_ in _rows3:
    msg = _ROUT_MSG.get(r_['rt'])
    proven = '-'
    if r_['rt']:
        proven = f'#R${r_["rt"]:04X}'
        if msg:
            proven += ': "' + _h2.escape(msg_text(msg, 200)[3:-1]) + '"'
        if _ROUT.get(r_['rt']):
            proven += ' - ' + _ROUT[r_['rt']]
    _tr.append(f'<tr><td>#R${r_["addr"]:04X}</td><td>{r_["st"]}</td><td><ul>' +
               ''.join(f'<li>{e_}</li>' for e_ in r_['ev']) + f'</ul></td><td>{proven}</td></tr>')
page('the-case', 'The case',
     '<p>The solution, as the game stores it (#R$9965). Say a statement to '
     'Inspector Lestrade (SAY TO LESTRADE "MRS BROWN KILLED HERSELF"); if all '
     'its evidence holds it is proven and its routine runs, otherwise it waits '
     'and is proven later, as soon as the evidence is complete (#R$BC46). '
     'Evidence is "seen" (the player has seen both things), "examined" (has '
     'examined both), or a marker that only the code named can set. '
     'Proven or not, the statements decide the endings (#R$9EA2, #R$9E85).</p>'
     '<p>Confirmed in the emulator: MRS BROWN KILLED HERSELF refused without '
     'its evidence and accepted with it; the Major\'s two statements proven '
     'together once his confession marker is set; TRICIA FENDER KILLED MRS '
     'JONES only ever waiting. And the whole chain '
     '(tools/experiments/solve_test.py, with every piece of evidence poked in, the '
     '$9993 marker poked in, and Lestrade parked on the idle loop at '
     '#R$F05C so that he stays to listen): MRS BROWN KILLED HERSELF, MRS JONES KILLED '
     'TRICIA FENDER, PHIPPS HAS PLANS ("Very good Holmes, Basil will likely try to '
     'sell them..."), THE SALE LOCATION IS OLD MILL ROAD, TRICIA FENDER HAD PLANS ("I '
     'do not see the importance of that") and TRICIA FENDER BLACKMAILED MRS BROWN are '
     'each proven in turn; MAJOR FFOULKES VISITED THE OPIUM DEN, said on its own, gets '
     '"Thats fine Holmes but what does it prove". The rest is read from the table and '
     'the code.</p>'
     '<p>Markers set by shared actions 3 and 22 come from Tricia Fender\'s and '
     'Mrs Jones\'s own action lists, which are used when that person is the one '
     'acting (#R$C933). <b>Tricia Fender is Mrs Jones in disguise.</b> Ask her '
     'about the bloodstained clothes while they are in the room (SAY TO TRICIA '
     'FENDER "TELL ME ABOUT BLOODSTAINED CLOTHES") and shared action 3 sets '
     '$998F and turns her actor-table entry into thing 95, Mrs Jones '
     '(#R$E03A): "Oh my god, you found out, I am really Mrs Jones." Now Mrs '
     'Jones is an actor, and SAY TO MRS JONES "TELL ME ABOUT YOUR ALIBI" (or '
     'WHAT HAPPENED) runs shared action 22 and sets $9993 - both confirmed in '
     'the emulator (the scratchpad test of 8 November evening). An earlier '
     'version of this page called $9993 unreachable; that was wrong.</p>'
     '<table class="disassembly"><tr><th>Record</th><th>Statement</th>'
     '<th>Evidence</th><th>When proven</th></tr>' + ''.join(_tr) + '</table>')
_NIGHT = ("Confirmed in the emulator (tools/experiments/night_test.py: $9D90 "
          "poked so the 3pm ending passes, then only WAIT): Lestrade's script "
          "reaches this record at about 1am on Tuesday with $9E88 still 0, and "
          "the game ends with 'Inspector Lestrade enters and says to you \" "
          "Well Holmes that wraps up this case, sorry you were not of more help "
          "but you cannot solve them all you know. \". Despite his assurances "
          "you cannot help feeling there should be more to this case. Perhaps "
          "you should try again.' (the player was elsewhere, so $6975 was not "
          "shown).")
A[0x9E85]['desc'].insert(1, _NIGHT)
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'three-endings':
        FACTS[i] = (eid, title, body.replace("All but the first are read from the code.",
            "The 3pm ending is confirmed by play, and so is the Major's arrest: with "
            "the introduction poked in and nothing else done, Lestrade ends the game "
            "at about 1am on Tuesday ('Well Holmes that wraps up this case, sorry "
            "you were not of more help...'). The others are read from the code."))

# ---------------------------------------------------------------------
# A person's own action list is used when that person acts ($C933)
# ---------------------------------------------------------------------
A[0xC933]['desc'].insert(0,
    "UPDATED 2026-11-07: when the one acting is a person (+5 bit 6 of "
    "$A017), its own record is searched first: $D1DC with A = 0 finds the "
    "zero entry that starts a person's list, and $D349 then looks along "
    "the pairs after it for the verb. So a person's list holds actions it "
    "does itself, not actions done to it - Tricia Fender's (TELL ABOUT / "
    "TELL, shared 3) and Mrs Jones's (shared 22) are the only ones. Only "
    "if that fails is the direct object's list searched. Confirmed in the "
    "emulator (tools/experiments/tell_test.py): SAY TO TRICIA FENDER \"TELL "
    "ME ABOUT THE BLOODSTAINED CLOTHES\" reaches shared action 3 ($E1B4) "
    "with Tricia acting and the clothes as indirect object, while TELL "
    "TRICIA FENDER ABOUT ... (the player acting) does not.")
fact('tricia-is-mrs-jones',
     "Tricia Fender is Mrs Jones in disguise - and that is how the last marker is earned",
     "Shared action 3 ($E1A3, in Tricia Fender's own action list) is not just a question. "
     "If you ask her about the bloodstained clothes while they are in the room "
     "(SAY TO TRICIA FENDER \"TELL ME ABOUT BLOODSTAINED CLOTHES\"), $E1B4 "
     "calls $E03A with A = $5F, which rewrites her actor-table entry from thing 13 "
     "to thing 95, Mrs Jones, moves her holder and room across, and sets the "
     "case marker $998F: 'Oh my god, you found out, I am really Mrs Jones. Tricia "
     "was blackmailing Mrs Brown...'. Mrs Jones is then an actor, so her own "
     "action list is used: SAY TO MRS JONES \"TELL ME ABOUT YOUR ALIBI\" (or WHAT "
     "HAPPENED, or the clothes) runs shared action 22 ($E17B, $E188) and sets "
     "$9993, the other marker MRS JONES KILLED TRICIA FENDER needs. Confirmed in the "
     "emulator on 8 November (evening) with Tricia and the clothes put in the "
     "player's room: $998F went 00 -> 02, the actor table lost 13 and gained 95, "
     "and $9993 went 08 -> 0A. Tricia herself is only on stage on Tuesday morning "
     "(room 46 at 8:05, room 47 at 8:10, back at 2:05pm; observed by waiting). "
     "CORRECTION: an earlier version of this project listed this as a bug "
     "('Mrs Jones never acts, so the game cannot be won'). That was wrong; the "
     "actor table is changed while the game runs, so a table read at the start "
     "does not show her.")

blk(0xA5CD, 'c', 'Interpret one message element at IX',
    ["Bit 7 set: a two-byte dictionary reference, printed by $A887 - "
     "unless its flag nibble is $20, $30 or $60, which $A647 treats as "
     "references to the command's own words (actor, objects). $00-$1F: a "
     "control code ($A621). $20-$3F: that character. $40-$5F: a run of "
     "(low 5 bits + 1) letters packed 5 bits each, unpacked by $A990. $60 "
     "and up: $A83A. Read from the code; it is what the 118 rendered "
     "messages went through."],
    comments={0xA5CD: 'The next byte', 0xA5D0: 'A word reference?', 0xA5D4: 'DE = the reference',
              0xA5DC: 'One of the command\'s own words?', 0xA5EA: 'No: print the dictionary word',
              0xA5ED: 'Move on', 0xA5F2: 'A control code?', 0xA5F6: '$60 and up',
              0xA5FB: 'A literal character?', 0xA5FF: 'Packed letters: how many',
              0xA609: 'Unpack one...', 0xA60C: '...and print it', 0xA61C: 'Print the character'})
A[0xA5CD]['end'] = 0xA621
blk(0xA621, 'c', 'Run control code A', ["Through the table at $A55D (see there)."])
_helper(0xEB11, "Script helper: is THE SALE LOCATION IS OLD MILL ROAD proven?",
    ["Succeeds when bit 1 of the statement's flags ($99AC) is set; $EB19 "
     "is the same for PHIPPS HAS PLANS ($999A). Lestrade's script uses "
     "them at $EA2C/$EA31 to decide to set off for Old Mill Road ($EA5B). "
     "Read from the code."], {})
for i, (eid, title, body) in enumerate(FACTS):
    if eid == 'three-endings':
        FACTS[i] = (eid, title, body + "\n\n" +
            "Confirmed in the emulator (tools/experiments/papers_test.py, with "
            "the 3pm and Major endings poked out of the way): at 10am on "
            "Thursday Lestrade's script ends the game with the morning papers - "
            "'Not only have you failed to solve the crimes at hand...' or, with "
            "both murders marked proven, 'You have done extremely well to solve "
            "the case at hand but...'. Both lose. The win is Basil's entrance "
            "on platform one at Victoria with Watson and Lestrade there ($9E48, $6AF3: "
            "'...YOU TRULY DESERVE THE TITLE OF WORLDS GREATEST DETECTIVE.'), "
            "which needs the sale location proven first, and that in turn the "
            "two murders (see The case for how to earn the last marker).")

# Give each character's plan script a block of its own. The decoder above
# makes one block per run of contiguous instructions, so a script that
# happens to follow another (Phipps's after the cook's and the maid's, all
# after verb 138's sub-script) was buried in someone else's block.
for (_s, _e) in list(SCRIPT_BLOCKS):
    _cuts = sorted(x for x in STARTS if _s < x < _e and any(t.startswith('actor ') for t in STARTS[x]))
    if not _cuts:
        continue
    _all = A[_s]['subs']
    _bounds = [_s] + _cuts + [_e]
    for _k, _c in enumerate(_cuts):
        _lo, _hi = _c, _bounds[_k + 2]
        _mine = [(d, a2, n, lab.split('): ', 1)[1] if a2 == _lo and lab.startswith('Entry (') else lab)
                 for (d, a2, n, lab) in _all if _lo <= a2 < _hi]
        blk(_lo, 'b', 'Plan script: ' + why_text(STARTS[_lo]),
            [f'Entry point: ${_lo:04X} = {why_text(STARTS[_lo])}.',
             'Decoded by tools/plan.py; see $CC78 for the language. Each sub-block is '
             'one instruction. Split off from the block before, which it merely follows '
             'in memory.',
             "In an instruction, 'plan dobj' and 'plan iobj' are not fixed objects: they mean the direct and indirect object currently held in the actor's plan registers (bytes +4 and +5 of its actor record), so the same step works on whatever the actor is dealing with - for the player, the objects of the command just typed. 'plan verb' is the verb register (+3), 'self' is the acting character, and '-' means none."], subs=_mine)
        A[_lo]['end'] = _hi
    A[_s]['subs'] = [t for t in _all if t[1] < _cuts[0]]
    A[_s]['end'] = _cuts[0]
    A[_s]['desc'][0] = 'Entry points: ' + '; '.join(
        f'${x:04X} = {why_text(STARTS[x])}' for x in sorted(STARTS) if _s <= x < _cuts[0]) + '.'

# The fifteen zero bytes between the shared-action table's end marker and
# the sentence parser at $AAB2: as words they ran one byte into the code.
if not any(t[1] == 0xAAA3 for t in A[0xAA71]['subs']):
    A[0xAA71]['subs'].append(('B', 0xAAA3, 15, 'Unused (zeros)'))

# ---- The endgame: Phipps's flight and the last scene -------------------
A[0xEE2B]['title'] = 'Plan script: Basil Phipps (actor 6) - the spy with the plans'
A[0xEE2B]['desc'] += [
    "His week, logged in the emulator with nobody interfering "
    "(tools/experiments/phipps_route.py, 3pm and Major endings poked out "
    "of the way): Monday off stage from 3pm, by train and cab to Camden "
    "Street and Basil's house on Tuesday morning (rooms 32, 33), back out "
    "on Wednesday at 9:55am, by cab and train to Leatherhead and on to Old "
    "Mill Road (room 103) at 12:10pm.",
    "At Old Mill Road ($EF26) he waits for 3pm, then starts a countdown of "
    "16 minutes plus a random number ($EF34). Each minute he checks whether "
    "you are at Old Mill Road ($EF39). If the countdown runs out first he "
    "leaves the game for good ($EF8C) - logged at 3:20pm - and the plans "
    "are sold: at 10am on Thursday Lestrade's script ends the game with the "
    "papers. If you arrive in time, 'AS YOU ENTER HE WHIPS HIS HORSES INTO "
    "ACTION AND SPEEDS OFF DOWN THE ROAD.' ($EF47, message $7573): he is "
    "put in Leatherhead's Main Street, waits for 4pm and 48 minutes more, "
    "walks to the station, takes a train to platform four in London, walks "
    "five steps south-west to Kings Cross Road, takes a cab to Buckingham "
    "Palace Road and walks east twice, to platform one at Victoria (room "
    "30). If you are there ($EF83) he runs $9E48 - the last scene; if not, "
    "he leaves the game ($EF8C).",
    "The last scene was staged in the emulator "
    "(tools/experiments/endgame_test.py): you on platform one at Victoria, "
    "Phipps's script pointed at $EF7F in Buckingham Palace Road. With "
    "Watson and Lestrade beside you: 'Basil Phipps enters. ... As Basil "
    "enters he sees you and pulls a gun. With suprising agility Watson "
    "pushes you out of the way of Basils first shot allowing Lestrade time "
    "to pull his gun and capture the culprits. As incredible as it may seem "
    "you have solved this case. You truly deserve the title of worlds "
    "greatest detective.' Without Lestrade, or without Watson: '...With his "
    "usual skill his first shot disposes of you. Perhaps you should try "
    "again.' With you one room away, he walked in and left the game."]
A[0xE7E7]['desc'] += [
    "The endgame ($EA25-$EAF5). Once PHIPPS HAS PLANS is proven ($EB19) "
    "he keeps asking 'HAVE YOU FOUND WHERE THE SALE LOCATION IS.' whenever "
    "you are with him. As soon as THE SALE LOCATION IS OLD MILL ROAD is "
    "proven too ($EB11) he sets off ($EA5B) - with or without you: he "
    "signals Chief Constable Straker, travels to Leatherhead ($EB72), "
    "climbs into the police cab ($EA69) and has the constable drive to Old "
    "Mill Road. There, if you are not in the cab with him ($EA78) he gives "
    "up and goes home ($EA84). If you are, and Phipps is still there "
    "($EA7E), they drive back to Main Street and walk north to platform two at Leatherhead (room 55), and he says 'I AM AFRAID THAT BASIL HAS ELUDED US HOLMES.'. Left alone he waits there for a train and goes home on it ($EAD0, then $EA95 and $EB28: platform four, Kings Cross Road, a cab to Parliament Street). But that waiting loop is the one stretch of this part of his script without the busy flag, so he takes orders there; and once off platform two with no train in, his script follows you (verb 134, $EAE2) until you reach platform one at Victoria (room 30) - where Phipps is heading, and where Lestrade has to be for the winning ending ($9E48). Confirmed in the emulator (tools/experiments/lestrade_follow.py): on platform two with his script at $EAD0, SAY TO LESTRADE \"FOLLOW ME\" and he followed every step south to Main Street and beyond (carrying out the order - his script position moved to the order's own sub-script, $E482 then $DD5F). Either way, if he gets back to Scotland Yard he says that Basil has eluded you, and ends the game with the papers at 10am ($EAB3).",
    "Logged in the emulator with both statements poked proven "
    "(tools/experiments/lestrade_route.py): he set off from Parliament "
    "Street at 7:05am on Wednesday and reached Old Mill Road at 10:45am, "
    "before Phipps; started at 11am instead (tools/experiments/win_test.py) "
    "he arrived at 3:13pm.",
    "The chase, played in the emulator (tools/experiments/chase.py, from 11am "
    "on Wednesday with the statements poked proven and you put in Leatherhead's "
    "Main Street as Lestrade arrives). The police cab holds only so much: climb "
    "in too early and you and Watson fill it, so Lestrade is left behind and the "
    "cab drives off without him; too late and Lestrade and Chief Constable "
    "Straker fill it ('I SEE NO POLICE CAB THAT YOU CAN CLIMB INTO'); in the "
    "minute Lestrade climbs in, you, Watson and Lestrade fit and Straker stays "
    "out. Then: Old Mill Road at 3:13pm, 'As you enter Basil Phipps whips his "
    "horses into action...' at 3:14, back in Main Street at 4:47, and Phipps "
    "walks to platform two and boards the train at 4:54. It leaves at 4:55 - "
    "one minute before Lestrade, still saying that Basil has eluded you, will "
    "take an order. Told to follow, he and Watson came on the next train "
    "(6:18), which reached platform four at 7:30; Phipps had left the game by "
    "6:45 (between 6:30 and 6:45 in the logs), having found nobody at Victoria. Asking the constable to drive "
    "the police cab to Buckingham Palace Road did nothing; asked for Kings "
    "Cross Road - one of its three routes ($9AA3) - it went, with Lestrade "
    "and Watson aboard, but took 95 minutes and arrived at 6:42, just as "
    "Phipps walked onto platform one at Victoria. The trains run every 90 "
    "minutes ($F278), so missing the 4:55 costs an hour and a half. In "
    "these runs the chase was lost by about a minute; no quicker line was "
    "found.",
    "Why no other line works, as far as these runs show: you have to be at "
    "Old Mill Road between 3:00 and about 3:16 for Phipps to bolt, and only "
    "the police cab goes there; the police cab only comes to Leatherhead "
    "when Lestrade's endgame summons it ($EAF6); and from then until he "
    "reaches platform two at 4:55 every instruction of his script carries "
    "the busy flag, so he cannot be told to follow you sooner."]
A[0x9E48]['desc'] = [
    "Run by Phipps's script ($EF89) when he walks onto platform one at "
    "Victoria and finds you there. If Watson (3) and Lestrade (2) are both "
    "in your room ($9E60), ends the game with $6AF3: 'AS BASIL ENTERS HE "
    "SEES YOU AND PULLS A GUN. WITH SUPRISING AGILITY WATSON PUSHES YOU OUT "
    "OF THE WAY OF BASILS FIRST SHOT ALLOWING LESTRADE TIME TO PULL HIS GUN "
    "AND CAPTURE THE CULPRITS. AS INCREDIBLE AS IT MAY SEEM YOU HAVE SOLVED "
    "THIS CASE. YOU TRULY DESERVE THE TITLE OF WORLDS GREATEST DETECTIVE.' - "
    "the only winning ending. If either is missing, with $6B79: 'AS BASIL "
    "ENTERS HE SEES YOU AND PULLS A GUN. WITH HIS USUAL SKILL HIS FIRST "
    "SHOT DISPOSES OF YOU. PERHAPS YOU SHOULD TRY AGAIN.'",
    "Confirmed in the emulator, all three ways (tools/experiments/endgame_test.py)."]
A[0x9E48]['title'] = 'The last scene: Basil arrives at Victoria (the winning ending)'
fact('the-last-scene', 'How the game is won',
     "The only winning text in the game is at $6AF3, and it is printed in one "
     "place: Phipps's script, when he walks onto platform one at Victoria and "
     "finds you waiting with Watson and Lestrade ($9E48). Staged in the "
     "emulator, it reads: 'As Basil enters he sees you and pulls a gun. With "
     "suprising agility Watson pushes you out of the way of Basils first shot "
     "allowing Lestrade time to pull his gun and capture the culprits. As "
     "incredible as it may seem you have solved this case. You truly deserve "
     "the title of worlds greatest detective.' Leave either companion behind "
     "and Basil's first shot disposes of you instead.\n\n"
     "Getting there, as read from the scripts ($E7E7, $EE2B): prove that "
     "Phipps has plans and that the sale is at Old Mill Road, ride with "
     "Lestrade in the police cab to Old Mill Road on Wednesday after 3pm "
     "(Phipps waits there from 12:10 and gives up at about 3:20), let Phipps "
     "bolt, and on the platform at Leatherhead, where Lestrade waits for a "
     "train home, tell him to follow you (SAY TO LESTRADE \"FOLLOW ME\" "
     "works - tried in the emulator); his script then follows you until you "
     "reach platform one at Victoria, which is exactly where Phipps is "
     "going. Be there, with Watson, before Phipps walks in.\n\n"
     "Played through in the emulator with the statements poked proven, this "
     "fell a minute short: Phipps's train left Leatherhead at 4:55pm, one "
     "minute before Lestrade would take the order, and the next train was "
     "far too late (details under $E7E7). The police cab fills up: board it "
     "in the same minute as Lestrade, or he or you is left behind. The spelling "
     "'SUPRISING' is the game's.")
for _i, _p in enumerate(PAGES):
    if _p[0] == 'the-case':
        _h = _p[2].replace('<table class="disassembly">',
            '<p>What the proofs are for. Proving PHIPPS HAS PLANS and THE SALE '
            'LOCATION IS OLD MILL ROAD sends Lestrade to Old Mill Road in the police '
            'cab (#R$E7E7). Phipps waits there on Wednesday from 12:10 until about '
            '3:20pm and bolts if you turn up after 3pm; he then makes his way to '
            'platform one at Victoria (#R$EE2B), and if you are there with Watson and '
            'Lestrade when he walks in, you win (#R$9E48 - staged and confirmed in the '
            'emulator). If the statements are not proven, the papers end the game at '
            '10am on Thursday (#R$9EA2). See <a href="reference/facts.html#the_last_scene">How '
            'the game is won</a>.</p><table class="disassembly">', 1)
        PAGES[_i] = (_p[0], _p[1], _h) + tuple(_p[3:])

# ---- Cab journeys ------------------------------------------------------
_STANDS = {45: 'Portman Street', 5: 'Baker Street', 10: 'Parliament Street',
           12: 'Slater Street', 14: 'Aldergate Street', 18: 'Kings Cross Road',
           24: 'Bishops Road', 28: 'Buckingham Palace Road', 32: 'Camden Street',
           40: 'Sidmouth Street'}
_cabsubs = []
_a = 0x9B7F
while b(_a) != 0xFF:
    _cabsubs.append(('B', _a, 3, f'{_STANDS.get(b(_a), b(_a))} (room {b(_a)}) - {_STANDS.get(b(_a + 1), b(_a + 1))} '
                               f'(room {b(_a + 1)}): {b(_a + 2)}'))
    _a += 3
_cabsubs.append(('B', _a, 1, 'End marker'))
for _x in (0x9B7F, 0x9B91, 0x9BA9):
    A.pop(_x, None)
blk(0x9B7F, 'b', 'Cab journeys: which cab stands a hansom cab runs between, and how long it takes',
    ["Three-byte entries (one stand, the other stand, a number), ended by "
     "$FF, searched either way round by $9C07. The ten stands are street "
     "rooms: Portman, Baker, Parliament, Slater, Aldergate and Sidmouth "
     "Streets, Kings Cross Road, Bishops Road, Buckingham Palace Road and "
     "Camden Street; every pair of them has an entry (45 entries). The third "
     "byte is the journey's length in minutes: the cab-ride action record "
     "at $9AE3 puts it, less 2, in $A01F, the number of minutes an action "
     "takes; and Parliament Street to Kings Cross Road, 12 here, matches "
     "Lestrade's cab ride logged in the emulator (7:10 to 7:20am). $9B25 "
     "also prices the ride from it. Leatherhead and Old Mill Road are not "
     "here: they are reached by train and the police cab."],
    subs=_cabsubs)
A[0x9B7F]['end'] = _a + 1
blk(0x9C07, 'c', 'Find the cab journey between two rooms',
    ["Searches $9B7F for an entry joining room A and room C, in either "
     "order; C = 0 matches any entry with A at either end. Returns Z with IX "
     "on the entry, or NZ if there is none. Read from the code."],
    ['Input:A one room', 'C the other (0 = any)', 'Output:F Z if found', 'IX the entry'])
blk(0x9B50, 'c', 'A cabbie told where to go: can he get there from here?',
    ["Sets up the cab ($A017) for the journey - its +1 from the actor in "
     "$A036, its room (+15) and $A00A from the cabbie's - and looks for a "
     "journey from here to the destination in $A034 ($9C07). If there is "
     "one, returns Z. If not, the cabbie replies 'SORRY GUV'NOR I CANNOT GET "
     "THERE FROM 'ERE' ($6C34) and this returns NZ to its caller's caller "
     "(it drops its own return address). Read from the code."])
blk(0x9B25, 'c', 'Price a cab ride from its journey time',
    ["IX is the journey's entry in $9B7F. Works out HL = DE x (minutes / 5, "
     "rounded down, + 1), and unless $E619 says otherwise for the actor in "
     "$A036, takes it off the money ($E39C, SBC HL,DE, $E38F); then $CFB6, "
     "and $A035 from the entry's +3. Read from the code; the amounts were "
     "not checked in the emulator."])
blk(0x9C56, 'c', "Set an object's 'revealed' flag (+5 bit 7)",
    ["Finds the object ($D237) and sets bit 7 of its +5 flags - the bit "
     "the flag-word tables at $C471 call revealed - then returns NZ. Read "
     "from the code."])
blk(0x9C60, 'c', "Clear an object's 'revealed' flag (+5 bit 7)",
    ["As $9C56, but clears the bit."])
blk(0x9C6A, 'c', "Look up the actor's after-turn routine",
    ["Searches the table at $9C85 ($D34E) for the actor in $A036. Returns "
     "Z if there is none (the search's $FF end marker), NZ if found. Read "
     "from the code."])

# ---- Small printing helpers before the narrator ------------------------
blk(0xA296, 'c', 'Print 18 newlines',
    ["Clears the text window by scrolling it: 18 newlines ($A2A2), "
     "clearing $A019 after each. Used by $9E80 (the end of the game), "
     "$A282 and $B00F. Read from the code."])
A[0xA296]['end'] = 0xA2A2
blk(0xA2A2, 'c', 'Print a newline (A kept)',
    ["Prints character $0D through the word-wrapping printer ($A9B7). "
     "Fifteen callers. Read from the code."])
A[0xA2A2]['end'] = 0xA2AA
blk(0xA2AA, 'b', 'A flag read by the number printer ($A7F2)',
    ["Read with $A027 by $A7EB to choose between the two word tables at "
     "$A24D and $A255; nothing in this stretch writes it. Read from the code."],
    subs=[('B', 0xA2AA, 1, 'Flag')])
A[0xA2AA]['end'] = 0xA2AB
blk(0xA2AB, 'c', 'Fill B bytes at HL with zero (or, from $A2AC, with A)',
    ["Read from the code."], ['Input:B how many', 'HL where'])
A[0xA2AB]['end'] = 0xA2B1
blk(0xA2B1, 'c', "HL = verb A's record in the verb table",
    ["HL = $8259 + 8 x (A - 1): the 8-byte records of the verb table, "
     "verb 1 first (see $8259). Read from the code."],
    ['Input:A verb number', 'Output:HL its record'])
A[0xA2B1]['end'] = 0xA2BD
blk(0xA2BD, 'c', "Gather nibbles from a record into $A01D and $A01E",
    ["$A01E = the high nibble of (IX+5), moved down, plus the high nibble "
     "of (IX+7); $A01D likewise from (IX+1) and (IX+3). Read from the code; "
     "what the two bytes are used for was not traced."])

# ---- The message control codes ($A55D) ---------------------------------
_CC = [
 (0xA63A, "Codes $08 and $0D: print the code itself",
  "Prints A - the control code, so a backspace or a newline - through the "
  "word-wrapping printer ($A9B7), and carries on (XOR A). Code $08 is $A736, "
  "the same three instructions."),
 (0xA63F, "Codes $1D and $1E (and $A647): finish a sentence",
  "Jumped to rather than called ($A62F). D = $60 ($1D) or $30 ($1E), or, "
  "entered at $A647, D from a word reference just printed by $A887. Then: "
  "with D bit 6 set, a newline ($A2A2); with bit 4 set, a full stop and a "
  "newline. Read from the code."),
 (0xA65A, "Code $1F: end of message", "XOR A and return: the interpreter stops."),
 (0xA65C, "Code $12: does nothing", "A bare RET."),
 (0xA65D, "Code $00: print the thing whose address is the next parameter",
  "Clears $A028 and takes the next word from the message's parameters "
  "($A66C); if it is not zero, prints that thing's name ($A7BA, $D405)."),
 (0xA66C, "Code $01: print the next parameter as a word (and: fetch the next parameter)",
  "DE = the next word of the parameters the caller pushed before printing "
  "the message, at $A59D, which moves on by two. Returns NZ, and a handler "
  "that returns NZ has DE printed as a dictionary word reference ($A633, "
  "$A5EA) - so as code $01 it prints the parameter as a word. The other "
  "codes call it to read their parameters."),
 (0xA679, "Code $02: jump within the message",
  "IX moves on by the two-byte offset that follows, less one. Read from "
  "the code."),
 (0xA682, "Code $1C: does nothing", "XOR A and return."),
 (0xA684, "Code $1A: carry on with the message at the next parameter",
  "IX = the next parameter ($A66C): the rest of the printing comes from "
  "there."),
 (0xA68C, "Codes $0F, $14-$17: only in one part of the day",
  "Each asks $C00C what part of the day it is (1-5) and, unless it is "
  "the code's own (code $0F: 5, $14: 4, $15: 3, $16: 2, $17: 1), skips the "
  "next element of the message ($A6B2, $A6BB). So a message can say "
  "different things by day and by night."),
 (0xA6BB, "Skip one message element at IX",
  "A word reference (bit 7) is two bytes, codes $02 and $0B are three, "
  "everything else one. Read from the code."),
 (0xA6D3, "Code $0A: one of the next n elements, at random",
  "The byte after the code is n; a random number below n ($D2A4) picks "
  "which of the following n elements is printed ($A5CD), the others "
  "being skipped ($A6BB). The count and the choice are kept at $A6D1 and "
  "$A6D2."),
 (0xA702, "Code $03: print the word reference in $A00D",
  "DE = ($A00D), returned NZ so that the interpreter prints it as a word."),
 (0xA709, "Code $04: print the next parameter as a word or number",
  "Takes the next parameter ($A66C) and prints it with $A80E."),
 (0xA711, "Code $05: print the case statement at the next parameter",
  "IX = the next parameter, a statement record of the case table "
  "($9965), printed by $BF1C: 'MRS JONES KILLED TRICIA FENDER' in "
  "Lestrade's 'Well can you prove that ... yet, Holmes ?'. Read from the "
  "code."),
 (0xA720, "Code $06: name the actor", "Clears $A028 and names the actor in $A036 ($A82F)."),
 (0xA72C, "Code $07: name the direct object",
  "Sets $A028 and names the direct object in $A034 ($A751: $A4BC, $A7C5)."),
 (0xA736, "Code $08: print the code itself", "As $A63A."),
 (0xA73B, "Code $09: name the indirect object", "As code $07, for $A035."),
 (0xA745, "Name room or thing A",
  "Entered with carry from $A3DF/$A412: carry clear names a room "
  "($A4AB, $A7BA), carry set - and $A751, used by codes $07 and $09 - a "
  "thing ($A4BC, $A7C5)."),
 (0xA75B, "Code $0B: print a message at an offset from here",
  "HL = IX + the two-byte offset that follows; prints the message there "
  "($A5C4) and steps over the offset: a sub-message."),
 (0xA771, "Code $19: print the message at the next parameter",
  "If the parameter is not zero ($A5C4)."),
 (0xA780, "Codes $0C and $0E: YOUR or HIS",
  "DE = $09F2 if the actor in $A036 (code $0C) or the direct object in "
  "$A034 (code $0E) is the player (0), $0414 otherwise; returns NZ so "
  "that the interpreter prints DE as a word reference ($A633 -> $A5EA): "
  "$09F2 is YOUR and $0414 is HIS (looked up with source/dictionary.py)."),
 (0xA793, "Codes $10, $11 and $13: name someone, then ARE or IS",
  "Names the actor ($10), the direct object ($11) or the person in the "
  "next parameter ($13) with $A82F, then DE = $007A if it was the player "
  "and $0485 if not - ARE and IS - for the interpreter to print: 'you "
  "are', 'Watson is'. Read from the code; words looked up with "
  "source/dictionary.py."),
 (0xA7BA, "Print the name of the thing at HL (as $D405)", "With IY = HL."),
 (0xA7C5, "Print the name of the thing at HL (as $D3E8)", "With IY = HL."),
 (0xA7D0, "Is word reference DE the word YOU?",
  "Sets $A7EA to 1 unless DE is a word reference to YOU ($09EE). When DE is not "
  "a word reference at all ($A7EB) prints one of the words in the tables "
  "at $A24D/$A255, chosen by D's bits 4-1. Also used by $D0E3, $D3F1 and "
  "$D40E. Read from the code."),
 (0xA80E, "Print word reference DE (code $04's printer)",
  "Through $A7D0, then as a dictionary word ($A887) with flag nibble $5 "
  "unless it is empty; ORs $A7EA into $A026."),
 (0xA82F, "Name actor A ($FF: SOMEONE)",
  "A thing name ($A751) unless A is $FF, which prints SOMEONE ($080E)."),
 (0xA83A, "Message bytes $60 and up: a common word",
  "Byte - $60 indexes the two-byte table at $67B7; the word reference it "
  "holds (with $50 added to the high byte) is printed like any other "
  "($A5EA). $A840 does the lookup and is also used by $B7D6."),
 (0xA852, "Code $1B: flip $A851", "Toggles bit 0 of $A851. Read from the code; what reads it was not traced."),
]
_starts = sorted(a for a, *_ in _CC)
for _x in list(A):
    if 0xA63A <= _x < 0xA85C and _x not in _starts:
        A.pop(_x)
for _a, _t, _d in _CC:
    blk(_a, 'c', _t, [_d])
for _a, _n, _t in ((0xA6D1, 2, 'Code $0A: the count, then the choice'),
                   (0xA7EA, 1, '$A7D0: set when the word was not YOU'),
                   (0xA851, 1, 'Code $1B: the flag it flips')):
    blk(_a, 'b', _t, [], subs=[('B', _a, _n, _t)])
_all = sorted(_starts + [0xA6D1, 0xA7EA, 0xA851, 0xA85C])
for _i, _a in enumerate(_all[:-1]):
    A[_a]['end'] = _all[_i + 1]

# ---- Money held by a thing ----------------------------------------------
blk(0xE38F, 'c', "Store HL as the money a thing holds (+9/+10)",
    ["Packs HL seven bits to a byte (the 'pounds, shillings and pence' "
     "fact has the format) into IX+9 and IX+10. With $E39C and $E3A9 it is "
     "how PAY TO ($E370) and a cab fare ($9B25) move money. Read from the "
     "code."], ['Input:HL total in pence', 'IX the thing'])
A[0xE38F]['end'] = 0xE39C
blk(0xE39C, 'c', "HL = the money a thing holds (+9/+10)",
    ["Unpacks IX+9/+10, seven bits a byte, keeping the sign. Read from the "
     "code."], ['Input:IX the thing', 'Output:HL total in pence'])
A[0xE39C]['end'] = 0xE3A9
A.pop(0xE3A9, None)
blk(0xE3A9, 'c', "DE = the sum of money in the command ($A02F)",
    ["Unpacks the number the parser stored at $A02F (set by $DB67 from "
     "'2/6', '3S' and the like) the same way, bit 7 of the high byte "
     "dropped. Returns NZ. CORRECTED: the automatic split had it as data. "
     "Read from the code."], ['Output:DE total in pence'])
A[0xE3A9]['end'] = 0xE3B8

# ---- Containment helpers -----------------------------------------------
blk(0xD249, 'c', "Move everything inside thing A, at any depth, to room B",
    ["Walks the things ($D04F, $D21C) and, for each one whose container "
     "(+1) is A, sets its room (+15) to B and does the same for what it "
     "holds (calling itself). This is what keeps carried things with "
     "their carrier when the game moves someone - and what the harness "
     "skips when it pokes the player's room directly (see "
     "harness_notes.md). Callers: $DD30, $DF1F. Read from the code."],
    ['Input:A the container', 'B the room'])
A[0xD249]['end'] = 0xD26C
blk(0xD26C, 'c', "Is the direct object carried by the actor? (carry = yes)",
    ["$D275 for the thing in $A034. Read from the code."])
A[0xD26C]['end'] = 0xD275
blk(0xD275, 'c', "Is thing A carried by the actor, perhaps inside something? (carry = yes)",
    ["Follows thing A's container (+1) upwards ($D288, through $D237) "
     "until it reaches the actor in $A036 (carry set) or something not "
     "held by anything ($FF: carry clear). A = $FF or $FE (no thing, a "
     "number) also gives carry. Read from the code."],
    ['Input:A the thing', 'Output:F carry if the actor has it'])
A[0xD275]['end'] = 0xD29D
blk(0xD29D, 'c', "A random number from 1 to 99",
    ["$D2A4 with A = 99, plus one: a percentage roll. Seven callers ($BA93, $BA9E, $BB1E, $E687, ...). Read "
     "from the code."], ['Output:A 1-99'])
A[0xD29D]['end'] = 0xD2A4

# ---- Code the automatic split had as data, next to $D36A ---------------
for _x in list(A):
    if 0xD39B <= _x < 0xD3D5:
        A.pop(_x)
blk(0xD39B, 'c', "Find the next room that matches a word slot of the parse",
    ["The room counterpart of $D36A: B counts on through the rooms (up "
     "to 105, then A = $FF for none), each room's record ($D224) has its "
     "name words matched against the slot ($A4E0), and - unless $A038 is "
     "set - only rooms that pass $D471 count. Returns the room in A and "
     "IX. Its address is handed to the parser's search at $B4E9 and $B590 "
     "(LD IY,$D39B), as $D36A's is for things. CORRECTED: the automatic "
     "split had it as data and text. Read from the code."])
A[0xD39B]['end'] = 0xD3D5
blk(0xD3D5, 'c', "Print thing IX's name",
    ["IY = IX + 7, its name words, then $D3E8. Callers: $D148, $D5B8, "
     "$D659, $DF77. Read from the code."])
A[0xD3D5]['end'] = 0xD3E8
blk(0xD3E8, 'c', "Print the name words at IY",
    ["Checks for YOU ($A7D0) and, by the record's flag bits just before "
     "IY, joins $D405's printing with or without its adjectives. Used by "
     "the message code that names things ($A7C5) and by the statement "
     "printer $BF1C. Read from the code."])
A[0xD3E8]['end'] = 0xD405

blk(0xBF1C, 'c', "Print a case statement: thing, relation, thing",
    ["IX is a statement record of the case table ($9965): prints the "
     "first thing's name ($A4BC, $D3E8), the relation's verb words from "
     "the table at $994D ($BF45; relation 0 prints AND), then the second "
     "thing. Used by message code $05 ($A711). Read from the code; the "
     "output is what Lestrade says when a statement is waiting."])
A[0xBF1C]['end'] = 0xBF45
blk(0xBF45, 'c', "DE = the words for a statement's relation (+1)",
    ["Relation n (1-11) gives entry n-1 of $994D, returned NZ; 0 returns Z. "
     "Read from the code."])
A[0xBF45]['end'] = 0xBF59

# ---- Filling in a missing indirect object, and some small pieces --------
_small = [
 (0xC542, 0xC55A, "Should the indirect object be guessed?",
  "NZ when the action record wants an indirect object ($A010, its "
  "header byte 1's low nibble, is not 0), none was typed ($A035 = $FF) "
  "and bit 1 of $A01D is clear. Read from the code."),
 (0xC55A, 0xC571, "Guess the indirect object: try each one until the record's checks pass",
  "If $C542 says so, puts 0, 1, 2... in $A035 in turn (up to the limit "
  "from $C45E) and runs the record's checks ($C929) until one passes - "
  "so a command can work without naming the second thing. Read from the "
  "code; not tried in the emulator."),
 (0xC571, 0xC57A, "$A00F = an action record's requirement code (header byte 0, low nibble)", ""),
 (0xC57A, 0xC583, "$A010 = the record's header byte 1, low nibble (the indirect object's requirement)", ""),
 (0xC5FC, 0xC60D, "Should the indirect object be guessed? (numbered records)",
  "As $C542 without the $A01D test, for the numbered action records ($C583)."),
 (0xC60D, 0xC61A, "Guess the indirect object for a numbered record",
  "As $C55A, with the checks run through $C989. Read from the code."),
 (0xC45E, 0xC471, "Is B below the last number for this object slot?",
  "Carry when B is below 106 if the slot's requirement code ($A010, or "
  "$A00F when entered at $C463) is below 5, or below 110 if it is 5 or "
  "more - 106 and 110 being one past the last room and the last thing. "
  "Used by the guessing loops $C55A and $C60D. Read from the code."),
 (0xCA9E, 0xCAAE, "Describe the player's room: in full the first time, briefly after",
  "Bit 6 of the room record's first byte marks it as visited: clear, it "
  "is set and the room is described in full ($D102); set, briefly "
  "($D1B2). Confirmed in the emulator: OPEN PLAIN DOOR, NORTH, SOUTH, "
  "NORTH, SOUTH gives the closet's and the sitting room's long texts the "
  "first time ('The sun streams in the two broad windows...') and 'You "
  "are in a small closet.' / 'You are in Your Room.' the second. (The "
  "sitting room's long text came again on the first return: the opening "
  "description does not go through here.)"),
 (0xD1B2, 0xD1C6, "Describe room A briefly (a room seen before)",
  "Its name line ($D0DD, $D187) and then, unless it is too dark "
  "($D078, message $68C1), the rest ($D178). Read from the code."),
 (0xCB40, 0xCB41, "Jump to HL", "The CALL $CB40 at $CB34 and $CB6E is a CALL (HL)."),
 (0xCB41, 0xCB43, "Return Z (does nothing)", ""),
]
for _a, _e, _t, _d in _small:
    blk(_a, 'c', _t, [_d] if _d else [])
    A[_a]['end'] = _e
A.pop(0xCB28, None)
blk(0xCB28, 'b', "The saved IX and IY for $CB2C's calls",
    ["$CB2C loads IX and IY from here, calls HL ($CB40) and stores them "
     "back: so a handler can keep its place between calls."],
    subs=[('W', 0xCB28, 2, 'IX'), ('W', 0xCB2A, 2, 'IY')])
A[0xCB28]['end'] = 0xCB2C

# ---- Direction words and the thing-position words ------------------------
A[0xD05A]['desc'].append(
    "Kinds 5-7 are really the start of the next table: the direction "
    "words at $D064 (NORTH, SOUTH, EAST, then WEST to DOWN at $D06A), "
    "which $D5FB indexes by direction number. No room uses kinds 0, 1 or "
    "5-7: 65 rooms are IN, 32 ON and 9 AT (counted from the room records).")
_dw = {}
import dictionary as _dictm
_DB = _dictm.by_offset()
A.pop(0xD06A, None)
blk(0xD06A, 'w', "Direction words, continued: WEST to DOWN",
    ["The direction-word table starts at $D064, overlapping the last three "
     "room kinds (NORTH, SOUTH, EAST); $D5FB reads entry n-1 for direction "
     "n. CORRECTED: was 'not identified'."],
    subs=[('W', 0xD06A + 2 * _k, 2, f'Direction {4 + _k}: {_DB.get(w(0xD06A + 2 * _k) & 0xFFF, {}).get("word", "?")}')
          for _k in range(7)])
A[0xD06A]['end'] = 0xD078
A.pop(0xD5C9, None)
blk(0xD5C9, 'w', "Where a thing is: IN, ON, BEHIND, UNDER, TIED",
    ["Indexed by bits 0-2 of a thing's +4 (1-5) by $D5D3, which adds TO "
     "after TIED. Words looked up with source/dictionary.py. CORRECTED: "
     "the automatic split had it as code."],
    subs=[('W', 0xD5C9 + 2 * _k, 2, f'{_k + 1}: {_DB.get(w(0xD5C9 + 2 * _k) & 0xFFF, {}).get("word", "?")}')
          for _k in range(5)])
A[0xD5C9]['end'] = 0xD5D3
blk(0xD5EF, 'c', "IX = room A's exits (record + 6), BC = 3 (their size)", ["Read from the code."])
A[0xD5EF]['end'] = 0xD5FB
blk(0xD5FB, 'c', "DE = the word for direction A (NORTH ... DOWN)",
    ["From the table at $D064 (bit 7 of A ignored). Read from the code."])
A[0xD5FB]['end'] = 0xD60B
A[0xD60B]['end'] = 0xD671
blk(0xD671, 'c', "Step IX to the room's next plain exit (Z at the end)",
    ["Skips exits through a door (+1 not 0) and anything that is not a "
     "direction 1-10; Z at the $FF end marker. Read from the code."])
A[0xD671]['end'] = 0xD68C

# ---- The line editor's helpers ------------------------------------------
_le = [
 (0xD87D, 0xD88A, "Free the current sentence's word list ($9FF0)",
  "Clears the pointer and hands the list to $A1AF. Read from the code."),
 (0xD88A, 0xD897, "Free the rest of the typed line's word list ($9FF2)", "As $D87D."),
 (0xD95C, 0xD968, "Close a quotation: a full stop if needed, then the closing quote mark",
  "Puts '.' ($D968) and then '\"' into the line buffer at HL, printing "
  "each. Read from the code."),
 (0xD968, 0xD978, "End the typed line with a full stop if it has none",
  "Read from the code."),
 (0xD978, 0xD99E, "A cursor key on an empty line is a compass move",
  "Key codes $08, $09, $0A and '[' become W, E, S and N - stored in the line, printed, and followed at once by "
  "ENTER. GET-KEY ($C41F) turns cursor-up ($0B) into '[' and DELETE "
  "($0C) into $08, so on a Spectrum CAPS SHIFT with 5, 6, 7 or 8 (or "
  "DELETE) walks west, south, north or east with one key. Confirmed in "
  "the emulator: after OPEN PLAIN DOOR, the single key '[' gave 'N. You "
  "go north. You are in a small closet...', $0A gave 'S. You go "
  "south.', $08 gave 'W. YOU CANNOT GO WEST.'"),
 (0xD9B7, 0xD9C3, "Rub out the typed line",
  "Prints a backspace ($08), steps HL back and counts B up, until B "
  "reaches $80 (at once if bit 7 is already set). Read from the code; it is what $A536 uses to wipe an "
  "unfinished line when the time limit runs out."),
 (0xDC15, 0xDC19, "Fail: A = 0, HL = 0, Z set",
  "The common 'no' exit of action-record checks (the destination check "
  "at $9AA3 refuses through it). Read from the code."),
]
for _a, _e, _t, _d in _le:
    blk(_a, 'c', _t, [_d])
    A[_a]['end'] = _e
blk(0xD897, 'c', "Read the player's line with a fresh key time limit",
    ["Sets the poll limit $A03B to 3,000 and $A027 to 1, runs the line "
     "editor ($D8AD) and clears $A027 again. (The byte at $D897 itself is "
     "a NOP.) Read from the code."])
A[0xD897]['end'] = 0xD8AD
fact('cursor-keys', 'One-key moves',
     "On an empty command line the cursor keys are compass moves: the line "
     "editor ($D978) turns the codes for left, right, down and up into W, "
     "E, S and N and presses ENTER for you, and GET-KEY ($C41F) makes "
     "DELETE count as left. Confirmed in the emulator by feeding the key "
     "codes: 'N. You go north. You are in a small closet...'")

# ---- After the TELL table: two checks that the split had as data ---------
A[0xE22A]['end'] = 0xE28D
for _x in list(A):
    if 0xE28D <= _x < 0xE2C7:
        A.pop(_x)
blk(0xE28D, 'c', "Refuse if the actor is the direct object",
    ["Fails ($DC15) when $A036 = $A034 - doing the thing to yourself. "
     "Reached by the JP at $E44F. CORRECTED: was the tail of the table "
     "above. Read from the code."])
A[0xE28D]['end'] = 0xE298
blk(0xE298, 'c', "Can this hansom cab be hailed here?",
    ["The direct object must be one of the two hansom cabs (30 or 33); "
     "the room ($A00A) must be one of the cab stands ($9C07 with C = 0: "
     "any journey from here); the cab ($A013) must be off stage (room 0), "
     "i.e. not already on a job; and $CFB9 must agree. Otherwise it "
     "refuses ($DC15). The HAIL action ($E2C7) runs it. CORRECTED: was "
     "data. Read from the code."])
A[0xE298]['end'] = 0xE2C6
blk(0xE2C6, 'b', "HAIL: the cab hailed, plus one", ["Written by $E2D3."],
    subs=[('B', 0xE2C6, 1, 'Cab + 1')])
A[0xE2C6]['end'] = 0xE2C7
blk(0xB39D, 'c', "Look the typed verb up in the verb table ($8259)",
    ["Takes the verb's two word references from IY (bit 7 of the first "
     "kept in $B39C), clears and fills a match pattern at $B186-$B18D "
     "($B483), then walks the 8-byte verb records from $8259 comparing "
     "each ($A4CD) until one matches - then $B405 and NZ - or the zero "
     "record that ends the table (Z). Read from the code."])
A[0xB39D]['end'] = 0xB405
blk(0xB39C, 'b', "$B39D: bit 7 of the verb's first word reference", [],
    subs=[('B', 0xB39C, 1, 'Flag')])
A[0xB39C]['end'] = 0xB39D

# ---- Articles, dictionary spelling, word matching ----------------------
for _x in list(A):
    if 0xA24D <= _x < 0xA25D:
        A.pop(_x)
blk(0xA24D, 'w', "Articles: A / AN / SOME, or THE",
    ["Two tables of four word references, chosen between by $A7EB: the "
     "first (THE, A, AN, SOME) normally, the second (THE, THE, THE, SOME) "
     "when $A027 or $A2AA is set - so a thing is 'a lamp' or 'the lamp' "
     "as the sentence needs. The entry is picked by bits 4-5 of D, the "
     "high byte of the article code in a thing's name. Words looked up with source/dictionary.py. CORRECTED: "
     "the automatic split had it as code."],
    subs=[('W', 0xA24D + 2 * _k, 2, ('Normal ' if _k < 4 else 'Definite ') + f'{_k % 4}: ' +
           _DB.get(w(0xA24D + 2 * _k) & 0xFFF, {}).get('word', '?')) for _k in range(8)])
A[0xA24D]['end'] = 0xA25D
blk(0xA25D, 'c', "Is thing B in the list at ($A0D8)? (only when $A011 is set)",
    ["Z when $A011 is 0 or there is no list; otherwise searches it "
     "($D34E) and returns NZ if B is there. Used by $A27D. Read from the "
     "code."])
A[0xA25D]['end'] = 0xA277
A[0xA2AA]['title'] = "Use THE: a flag for the article printer ($A7F2)"
A[0xA2AA]['desc'] = ["Set, the article printer at $A7EB takes its words from the "
                     "second table at $A255 (THE, THE, THE, SOME). Set to 1 around "
                     "$D5B7's naming. Read from the code."]
A[0xA7D0]['desc'] = ["Sets $A7EA to 1 unless DE is a word reference to YOU ($09EE). "
                     "When DE is not a word reference at all (bit 7 of D clear) it is "
                     "an article code: $A7EB prints THE, A, AN or SOME from $A24D - or "
                     "from $A255, all THE but SOME, when $A027 or $A2AA is set. Also "
                     "used by $D0E3, $D3F1 and $D40E. Read from the code."]
A[0xA7D0]['title'] = "Print an article, or note whether the word is YOU"
for _x in list(A):
    if 0xA35D <= _x < 0xA360:
        A.pop(_x)
blk(0xA35D, 'b', "A remembered command: verb, direct object, indirect object",
    ["Copied from $A033-$A035 by the narrator ($A2F4, $A2FA) and written "
     "by the plan interpreter ($CDD1-$CDE3); read back when a command is "
     "narrated ($A31B, $A382, $A3DC-$A40F)."],
    subs=[('B', 0xA35D, 1, 'Verb'), ('B', 0xA35E, 1, 'Direct object'),
          ('B', 0xA35F, 1, 'Indirect object')])
A[0xA35D]['end'] = 0xA360
blk(0xA360, 'c', "Code $18: narrate the remembered command",
    ["Narrates the command at $A35D ($A37D) with the actor ($A036) set to "
     "0 for the duration; if the actor was that command's direct object, "
     "the direct object is set to 0 as well. 0 is the player, YOU. Read "
     "from the code; where code $18 is used was not looked up."])
A[0xA360]['end'] = 0xA37D
blk(0xA51B, 'c', "Does the word reference at HL match the one at IY? (Z)",
    ["An empty one (0) at HL matches anything. Otherwise compares the low "
     "byte and the low nibble of the high byte. HL and IY both move on two "
     "bytes. Read from the code."])
A[0xA51B]['end'] = 0xA536
blk(0xA92F, 'c', "Add a dictionary word's suffix to the spelling at IX",
    ["The low nibble of (HL) picks one of the four-letter suffixes at "
     "$A85C (15 = none), copied to IX and ended with 0. Read from the code."])
A[0xA92F]['end'] = 0xA94D
blk(0xA94D, 'c', "Spell dictionary record HL into the buffer at $5C42",
    ["Its letters ($A95B), then its suffix ($A92F)."])
A[0xA94D]['end'] = 0xA95B
blk(0xA95B, 'c', "Unpack a dictionary record's letters (front-coded)",
    ["The dictionary is front-coded: bits 6-4 of a record's count byte say "
     "how many letters to keep from the word before (IX simply starts that "
     "far into $5C42), bits 3-0 how many new letters follow, packed five "
     "bits each ($A990). Records with bit 7 set carry two extra bytes. Read "
     "from the code; it is the format source/dictionary.py decodes."])
A[0xA95B]['end'] = 0xA990
blk(0xA990, 'c', "Unpack the next five-bit letter (C = bit position)",
    ["Returns 'a' + n - 1 style codes ($60 + n). Read from the code."])
A[0xA990]['end'] = 0xA9B5

# ---- More small pieces: greetings, the gardener, the memory allocator ---
blk(0x9DC6, 'c', "Lestrade greets you: 'WELL, HOLMES FANCY SEEING YOU HERE.' the first time",
    ["Once the greeting countdown allows ($9CF2), says $71ED the first "
     "time (the flag at HL becomes 1) and an ordinary greeting ($9CEC, "
     "$6929: '... SAYS TO ... \"GOOD MORNING\"') after that. Called by "
     "Lestrade's after-turn routine $9D95. Read from the code; both lines "
     "seen in the emulator ('Inspector Lestrade with a surprised look on "
     "his face, says \" Well, Holmes fancy seeing you here. \"' and "
     "'Inspector Lestrade says to you \" Good afternoon \"')."])
A[0x9DC6]['end'] = 0x9DD8
blk(0x9DD8, 'c', "Lestrade asks whether you can prove a waiting statement yet",
    ["Re-checks the waiting statements ($BC46) and, if one is still "
     "waiting for evidence ($BC9C, $BC74), says $722D: 'WELL CAN YOU PROVE "
     "THAT <statement> YET, HOLMES ?' (code $05 prints the statement). "
     "Seen in the emulator in jones_test.py ('Well can you prove that Mrs "
     "Jones killed Tricia Fender yet, Holmes ?'). Read from the code."])
A[0x9DD8]['end'] = 0x9DFF if 0x9DFF in A else A[0x9DD8].get('end')
blk(0x9F1E, 'c', "Store A at HL, put the actor in room B, and its next turn DE minutes on",
    ["The actor's own record ($A017) gets room B and no container; the "
     "actor-table entry at IY has its next-turn minute (+6/+7) moved on "
     "by DE. Used twice by the gardener's after-turn routine ($9ED1): at "
     "9pm he is put off stage (room 0, his room remembered at $9ED0) with "
     "his next turn about 504 minutes later (plus a random number below "
     "30, added to the low byte only), and on that turn he is put back. "
     "Read from the code."])
A[0x9F1E]['end'] = 0x9F38
A[0xA1AF]['end'] = 0xA1C7
A.pop(0xA11A, None)
blk(0xA11A, 'b', "$A11C: the free-list link before the best block so far", [],
    subs=[('W', 0xA11A, 2, 'Link address')])
A[0xA11A]['end'] = 0xA11C
blk(0xA11C, 'c', "Allocate A + 3 bytes from the free list, cleared",
    ["Walks the free blocks from $9FE3 (each starts with its size and a "
     "link) and takes the smallest that is big enough - best fit. If what "
     "would be left is under 4 bytes the whole block is unlinked, "
     "otherwise it is split. The block is zeroed, its size stored before "
     "it, and IX returned on it with NZ. No block big enough: $C1D8 (out "
     "of memory). Word lists, remarks and orders are built in these "
     "blocks; $A1AF frees them. Read from the code."])
A[0xA11C]['end'] = 0xA1AF

# ---- Variable bytes that sat between routines as NOPs --------------------
for _a, _n, _t, _d in (
        (0xCAAE, 1, "Flag: the player's view has changed",
         "Set by $DF4C, $E109 and $E141, read by $CA6D (which describes the room again) and cleared by $CA62."),
        (0xCB79, 2, "The flags $CB7B is to name",
         "Written by $C798 (with bit 7 cleared); $CB7B prints the word for each set bit from $C471 or $C481."),
        (0xD714, 1, "A flag for the unknown-word message",
         "Set by $D9A8, cleared by $D6C9, read by $D721."),
        (0xD9C3, 2, "Two bytes before the tokenizer", "Not traced."),
        (0xDA32, 2, "The tokenizer's word pointer", "Stored by $DA55 (LD ($DA32),HL)."),
        (0xDC13, 2, "The number reader's working bytes", "Written at $DA78, read at $DA1C and $DA80.")):
    A.pop(_a, None)
    blk(_a, 'b', _t, [_d + " Read from the code."], subs=[('B', _a, _n, _t)])
    A[_a]['end'] = _a + _n
blk(0xD2ED, 'c', "Total size (+2) of the things directly in thing A",
    ["$D305 with B = 1: adds the size byte (+2) of every thing whose "
     "container (+1) is A; C = $FF if it goes over 127. The fit check at "
     "$DEE4 compares this with the container's capacity ($DEF8). Read from "
     "the code."], ['Input:A the container', 'Output:A the total'])
A[0xD2ED]['end'] = 0xD2F2
blk(0xD2F2, 'c', "Total weight (+3) of everything in thing A, at any depth",
    ["$D305 with B = 0: adds the +3 byte of every thing inside A, and of "
     "what is inside those; $FF if it goes over 127. Used by $C8C6 (can "
     "the actor carry it as well as what it holds?) at $C8CE and $C8DF. "
     "Read from the code."], ['Input:A the container', 'Output:A the total'])
A[0xD2F2]['end'] = 0xD305
blk(0xD305, 'c', "Add up a byte of the things in thing A (the work of $D2ED/$D2F2)",
    ["Walks the things from $8B6F ($D21C); B selects +2 (and no "
     "recursion) or +3 (and recursion into each thing's own contents). "
     "Read from the code."])
A[0xD305]['end'] = 0xD33C
blk(0xD1C6, 'c', "Print room IX's name (its name words at +1)",
    ["With no article ($A028 = 0), through $D405. Read from the code."])
A[0xD1C6]['end'] = 0xD1DB
blk(0xD1DB, 'c', "Jump to HL", ["A CALL $D1DB is a CALL (HL). Read from the code."])
A[0xD1DB]['end'] = 0xD1DC

# ---- The tape messages' last bytes, the printer check, save/load variables
for _x in (0xC0B0, 0xC0BB, 0xC0DD):
    A.pop(_x, None)
for _a, _e, _t in ((0xC0A5, 0xC0B1, "'REWIND TAPE.'"), (0xC0B1, 0xC0BC, "'TAPE ERROR.'"),
                   (0xC0BC, 0xC0DF, "'PLAY SAVED GAME TAPE TO BE LOADED', newline, '.'")):
    if _a not in A:
        blk(_a, 't', 'Tape message: ' + _t,
            ["Printed by $C1CB, which stops after the character with bit 7 "
             "set (the full stop, $AE). CORRECTED: the last byte had been split "
             "off as data."])
    else:
        A[_a]['title'] = 'Tape message: ' + _t
    A[_a]['end'] = _e
A.pop(0xC03B, None)
blk(0xC03B, 'c', "Read the ZX Printer's status (port $FB, bit 6)",
    ["IN A,($FB) and AND $40. Called by $B003, the PRINT special word, "
     "before turning printing on. CORRECTED: was data. Read from the "
     "code; not tried (the harness has no printer)."])
A[0xC03B]['end'] = 0xC040
A.pop(0xC109, None)
blk(0xC109, 'b', "Save and load: the block's length and start",
    ["Stored by $C046/$C04A and $C0DF, reloaded for the second SA-BYTES or "
     "LD-BYTES call."],
    subs=[('W', 0xC109, 2, 'Length (DE)'), ('W', 0xC10B, 2, 'Start (IX)'), ('B', 0xC10D, 2, '')])
A[0xC109]['end'] = 0xC10F
for _x in (0xC0FF, 0xC109):
    A.pop(_x, None)
A[0xC0DF]['end'] = 0xC0FE
blk(0xC0FE, 'b', "The saved game's tape header: a CODE file 'SHD V2.0'",
    ["The standard 17-byte header SA-BYTES writes first: type 3 (code), "
     "the ten-letter name 'SHD V2.0  ', then the length, start and second "
     "parameter. The length and start words are where $C046/$C04A and "
     "$C0DF keep DE and IX between the header and the block, so they are "
     "filled in when the game is saved. A load reads a header into the "
     "same place. The original tape carries a block with this very name "
     "and range ($840B-$A01F, the saved-game block of $B0EE) - apparently a saved "
     "game, loaded before the main block and overwritten by it (see "
     "loader_notes.md). Read from the code."],
    subs=[('B', 0xC0FE, 1, 'Type: 3 (code)'), ('T', 0xC0FF, 10, 'Name'),
          ('W', 0xC109, 2, 'Length (DE)'), ('W', 0xC10B, 2, 'Start (IX)'),
          ('W', 0xC10D, 2, 'Parameter 2')])
A[0xC0FE]['end'] = 0xC10F
A.pop(0xE31C, None)
blk(0xE31C, 'c', "COUNT's pre-check: is the thing countable?",
    ["The pre-check named in the header of shared action 10 (COUNT, the "
     "money objects, $E328): refuses ($DC15) unless the direct object "
     "($A013) has bit 5 of its +6 flags set. CORRECTED: was data. Read "
     "from the code."])
A[0xE31C]['end'] = 0xE328
fact('saved-game-on-the-tape', 'A saved game on the original tape',
     "Besides the loading screen and the game, the tape carries a third "
     "block, a CODE file called 'SHD V2.0' for $840B-$A01F. That is exactly "
     "the header the game's own SAVE writes ($C0FE) and exactly the range a "
     "saved game holds ($B0EE: the rooms, things, case table, actors and "
     "variables). It is loaded first and then overwritten by the main block, "
     "so it does nothing - apparently a saved position left on the master "
     "tape. See loader_notes.md.")

# ---- Sentence nodes: the parser's list helpers ($AE59-$AF67) -------------
for _a, _e, _t, _d in (
    (0xAE59, 0xAE6A, "Fill in a word reference at HL from DE, unless HL already has one",
     "Byte by byte; HL and DE both move on two. Read from the code."),
    (0xAE6A, 0xAE7F, "Add a new node to the end of the sentence list",
     "Finds the last node ($AEEA), allocates 30 bytes ($A11C) and links "
     "the new block in after it; IY = the new node. Read from the code."),
    (0xAEA9, 0xAEB6, "IY = the next node in the list (Z at the end)",
     "The link is the two bytes before the node (IY-2, IY-1), as in every "
     "heap block ($A11C). Read from the code."),
    (0xAEB6, 0xAEC5, "Step forward over nodes marked with bit 6 of +1",
     "IX = the node before. Read from the code."),
    (0xAEC5, 0xAEEA, "IY = the node before IY in the sentence list ($9FF0)",
     "Through $A104, stepping back over nodes marked with bit 6 of +1 and "
     "stopping at the head ($9FF2). Read from the code."),
    (0xAEEA, 0xAEF1, "IY = the last node of the sentence list",
     "$AEC6 with IY = 0: the node before 'none' is the last."),
    (0xAEF1, 0xAF38, "Merge parse node IX into node IY",
     "ORs in IX's flag byte (bit 7 dropped) and takes its first byte; if "
     "IX has words at +4/+5 and IY's ten bytes from +$0E are empty "
     "($AF38), moves IY's six bytes from +8 up to +$12 and copies IX's "
     "words in ($AF52, and $AF56 for the +2 pair if IY has none). Read "
     "from the code; what each field holds was not traced."),
    (0xAF38, 0xAF4E, "Z if the ten bytes at IY + A are all zero", "Read from the code."),
    (0xAF4E, 0xAF67, "Copy 6, 10 or 2 bytes from IX + DE to IY + DE",
     "Entries $AF4E (6), $AF52 (10) and $AF56 (2). Read from the code.")):
    A.pop(_a, None)
    blk(_a, 'c', _t, [_d])
    A[_a]['end'] = _e

# ---- Filling the command's objects from the typed words ($B405-$B5D2) ----
for _a, _e, _t, _d in (
    (0xB405, 0xB483, "Copy the typed objects into the two object slots, in the verb's order",
     "Once a verb record has matched ($B39D): works out from the record "
     "($A2BD, $A01D/$A01E) and the preposition typed whether the parse "
     "node's first or second group of words is the direct object, notes "
     "the order at $B182, and copies six bytes of words from the node "
     "into the direct-object slot $B172 and the indirect-object slot "
     "$B178, setting bit 0 of $B16D/$B16E when a slot is not empty. Read "
     "from the code."),
    (0xB483, 0xB4A0, "Copy the word pair at IY + E to HL, if B is not 0",
     "B counts down when the pair is not empty; HL moves on two. Used by "
     "$B39D to build its match pattern. Read from the code."),
    (0xB4A0, 0xB4A2, "Call the search routine in IY",
     "$D36A for things or $D39B for rooms, chosen by the slot's "
     "requirement code ($B4E2, $B589)."),
    (0xB4C1, 0xB4FD, "The next candidate for the direct object ($A034)",
     "Requirement code 5 ($A00F) means a number: the first time, if the "
     "slot holds one (bit 7 of $B173), $A034 = $FE and the number goes to "
     "$A02F. Otherwise searches rooms (codes below 5, $D39B) or things "
     "($D36A) for the next one the slot's words name, continuing from "
     "$B17E. A = $FF when there are no more. Read from the code."),
    (0xB4FD, 0xB517, "Next thing or room the direct-object slot names, skipping those $B517 rejects",
     "Sets bit 1 of $B16D when one is found. Read from the code."),
    (0xB517, 0xB549, "Reject a candidate named again in a later marked node?",
     "Only when $A01C is set (bit 7 of the verb's first word reference, "
     "copied from $B39C at $B1ED): walks the following nodes marked with "
     "bit 6 of +1 and returns NZ if the candidate matches the words of "
     "one - $B4FD then passes over it. Read from the code; what typed "
     "commands produce such nodes was not traced."),
    (0xB568, 0xB5A4, "The next candidate for the indirect object ($A035)",
     "As $B4C1, for the second slot ($B178, $B180, $A031, and $A010's "
     "requirement code)."),
    (0xB5A4, 0xB5B6, "Next thing or room the indirect-object slot names",
     "Sets bit 1 of $B16E when one is found."),
    (0xB5B6, 0xB5D3, "Move on to the next sentence of the typed line",
     "$A01B = A; the sentence list $9FF0 becomes what was the rest of the "
     "line ($9FF2), and $9FF2 the rest after that, the link being cut. "
     "Read from the code.")):
    A.pop(_a, None)
    blk(_a, 'c', _t, [_d])
    A[_a]['end'] = _e
for _a, _t in ((0xB4A2, "$B4C1: $FF until the number in the direct-object slot has been used"),
               (0xB549, "$B568: $FF until the number in the indirect-object slot has been used")):
    A.pop(_a, None)
    blk(_a, 'b', _t, [], subs=[('B', _a, 1, 'Flag')])
    A[_a]['end'] = _a + 1
blk(0xB4A3, 'c', "The direct object is a number: use it once",
    ["The first time ($B4A2 still $FF), if the direct-object slot holds a "
     "number (bit 7 of $B173), $A034 = $FE and the number goes to $A02F; "
     "after that, or if there is no number, A = $FF: no more candidates. "
     "Reached from $B4C1 when the requirement code is 5. Read from the code."])
A[0xB4A3]['end'] = 0xB4C1
blk(0xB54A, 'c', "The indirect object is a number: use it once",
    ["As $B4A3, for the second slot ($B549, $B179, $A035, $A031)."])
A[0xB54A]['end'] = 0xB568
blk(0xA7EB, 'c', "Print the article for article code DE",
    ["THE, A, AN or SOME from $A24D - or from $A255 when $A027 or $A2AA "
     "is set - picked by bits 4-5 of D ($A887 prints it). Reached from "
     "$A7D0 when DE is not a word reference. Read from the code."])
A[0xA7EB]['end'] = 0xA80E

# ---- Screen, printer and prompt helpers ---------------------------------
for _a, _e, _t, _d in (
    (0xC1C0, 0xC1CB, "Print a prompt at HL, wait for a key, newline",
     "$C1CB, then $C415, then a newline. The save and load routines use "
     "it with HL pointing into the ROM's own tape messages ($09A2, $09AC, "
     "$09B2). Read from the code."),
    (0xC3E4, 0xC400, "Send the screen's top character row to the ZX Printer, if printing is on",
     "Only when $A008 is set (by the PRINT special word; NOPRINT clears "
     "it): eight pixel lines from $4000, each through $C403, then the "
     "printer motor is stopped (OUT ($FB),4). Read from the code; not "
     "tried (no printer in the harness)."),
    (0xC316, 0xC37D, "Scroll the text up a line, printing the line that goes if printing is on",
     "If $C128 is 0 the top row goes to the printer first ($C3E4); then "
     "the screen is moved up a character row. Called by $C2E0. Read from "
     "the code; the details of the move were not traced.")):
    A.pop(_a, None)
    blk(_a, 'c', _t, [_d])
    A[_a]['end'] = _e
A[0xC1CB]['desc'].append(
    "Its callers turn out to be the save and load routines: the tape "
    "messages at $C0A5-$C0DE ('REWIND TAPE.', 'TAPE ERROR.', 'PLAY SAVED "
    "GAME TAPE TO BE LOADED') are in this form, and $C1C0 prints the ROM's "
    "own tape messages through it.")
A[0xC403]['title'] = 'Print one pixel line on the ZX Printer'
A[0xC403]['desc'] = [
    "Port $FB is the ZX Printer's. Sets the printer speed (slower for the "
    "last two of the eight lines: the B < 3 test at $C403-$C407), waits "
    "until the printer is ready (IN A,($FB), RET M / JR NC) and joins the "
    "48K ROM's COPY-LINE code at $0F12, which prints one pixel line. "
    "Called eight times by $C3E4 for each character row sent to the "
    "printer, so it is reached only when printing is on (PRINT special "
    "word). CORRECTED: was 'Read a Kempston-style joystick port' - the "
    "Kempston joystick is port $1F; $FB with a jump into the ROM's "
    "COPY-LINE is the printer. Read from the code; not tried (no printer "
    "in the harness)."]
A[0xC400]['title'] = "The end of $C3E4 (POP BC/DE/HL, RET)"
A[0xC400]['desc'] = [
    "The last instructions of $C3E4, after its OUT ($FB),4. CORRECTED: was "
    "described as a shared tail for a joystick routine; $C403 is the "
    "printer, and $C412's JP $0F12 goes into the ROM, not here."]
A[0xC400]['title'] = "The end of $C3E4 (POP DE, POP HL, RET)"
A[0xC41F]['desc'] = [d.replace('$C416 (from the joystick-read wrapper above)',
                               '$C416 (the wait-for-a-key loop at $C415)') for d in A[0xC41F]['desc']]

# ---- Another batch of small routines ------------------------------------
for _a, _e, _t, _d in (
    (0xC863, 0xC86E, "Is thing number A here? ($C86E)", "Finds its record ($D237) and runs $C86E. Read from the code."),
    (0xCC29, 0xCC37, "Set up the current actor: its record and room",
     "$A017 = the record of the actor in $A036 and $A00A = its room "
     "($D495). Read from the code."),
    (0xD21C, 0xD224, "Step to the next thing's record ($D206), keeping A", ""),
    (0xD349, 0xD34E, "Search a table of two-byte entries for A",
     "As $D34E (three-byte entries) with an entry size of 2."),
    (0xD526, 0xD57C, "List the things in place A, then what each of them holds",
     "Names each listable thing ($D57D) with commas and a final AND "
     "($D3D9, $A414), marking each as seen (+6 bit 7); then, for each "
     "that has things of its own to list ($D4CC), says how they are held "
     "($D590) and lists those too (calling itself). Read from the code; "
     "it produces 'In watsons armchair there is Watson. Watson is "
     "carrying the daily chronicle.'"),
    (0xD57C, 0xD590, "The next listable thing in place A (carry at the end)",
     "Steps through the things ($D21C) and returns the next for which "
     "$D4EF says yes. Read from the code."),
    ):
    A.pop(_a, None)
    blk(_a, 'c', _t, [_d] if _d else [])
    A[_a]['end'] = _e
for _a, _n, _t, _d in (
        (0xCC0B, 3, "Bytes for the actor's turn ($CC37)", "Cleared by $CC38, read at $CC8D, its address used at $CEB9."),):
    A.pop(_a, None)
    blk(_a, 'b', _t, [_d + " Read from the code."], subs=[('B', _a, _n, _t)])
    A[_a]['end'] = _a + _n

A[0xD6BF]['title'] = "Action record: read the player's line (RUN at $9923)"
A[0xD6BF]['desc'].insert(0, "The body reads a line with the line editor ($D898, with a fresh "
    "key time limit), fails ($DC15) if nothing came, and clears $D714. Part "
    "of the player's own plan script. Read from the code.")
A.pop(0xD6B8, None)
blk(0xD6B8, 'b', "A flag of the player's script step, and spare bytes",
    ["$D6B8 is written at $A042 (the start of the game), $D7AD, $D81C and "
     "$D85D and read at $D7FE and $D836 - the player's script step - and "
     "the word at $D6BB is saved at $D833 and reloaded at $D808 by the "
     "same code. Read from the code; what they hold was not traced."],
    subs=[('B', 0xD6B8, 1, 'Flag'), ('B', 0xD6B9, 2, 'Zeros'), ('W', 0xD6BB, 2, 'A saved pointer'),
          ('B', 0xD6BD, 2, 'Zeros')])
A[0xD6B8]['end'] = 0xD6BF

def _newblk(a, e, kind, title, desc, subs=()):
    """Title a block that has no title yet; never overwrite a titled one."""
    if a in A and A[a].get('title'):
        raise ValueError(f'${a:04X} already titled: {A[a]["title"]}')
    A.pop(a, None)
    blk(a, kind, title, desc, subs=list(subs))
    A[a]['end'] = e

for _a, _e, _t, _d in (
    (0xB2DF, 0xB303, "Choose the indirect object: the candidate that passes the record's checks",
     "Restarts the indirect-object search ($B36B) and tries each candidate "
     "($B568) with the record's checks ($C929), counting those that pass "
     "in $B171 and keeping the last in $B185; stops at the first unless "
     "$B190 is set. $A035 is left holding the one chosen. Read from the "
     "code."),
    (0xB303, 0xB308, "HL = $B6AE (ask which one), Z", ""),
    (0xB308, 0xB32D, "Count the candidates for the direct object",
     "Runs the direct-object search to the end ($B34F, $B4C1), counting "
     "in $B170, and puts the search state back as it was. A = the count. "
     "Read from the code."),
    (0xB32D, 0xB34F, "Count the candidates for the indirect object",
     "As $B308, with $B36B, $B568 and $B171."),
    (0xB34F, 0xB36B, "Start the direct-object search afresh",
     "$B170 = 0, the number flag $B4A2 = $FF, and the search position "
     "$B17E at the first thing ($D04F) - or 0 when the requirement code "
     "($A00F) is below 7. Read from the code."),
    (0xB36B, 0xB387, "Start the indirect-object search afresh", "As $B34F, for $B171, $B549, $B180 and $A010."),
    (0xB387, 0xB39C, "Test the verb record's flags against the indirect-object slot",
     "Z if bit 2 of $A01D is clear; otherwise NZ if the indirect-object "
     "slot has words (bit 0 of $B16E) or bit 1 of $A01D is clear, Z if "
     "not. Read from the code; what the two flag bits mean was not traced."),
    (0xC8EF, 0xC929, "Point $A013 and $A015 at the direct and indirect objects' records",
     "Rooms ($D224) for requirement codes below 5, things ($D237) "
     "otherwise; a number or nothing ($FE, $FF) is left alone. Read from "
     "the code."),
    (0xC929, 0xC933, "Check the action record against the command's objects",
     "Points at the objects' records ($C8EF), then on into the checks at "
     "$C933. Read from the code."),
    (0xC996, 0xC9BF, "Run a numbered action record; a script record becomes the actor's plan",
     "Runs it through $C9BF; with carry (a script) the record is started "
     "as the actor's plan ($CF80, the actor's entry at $9FDB). Read from "
     "the code.")):
    _newblk(_a, _e, 'c', _t, [_d] if _d else [])
for _a, _e, _k, _t, _d, _s in (
    (0xE2EE, 0xE31C, 'c', "Start actor A on the script at DE, with objects B and C",
     ["$A034 = B and $A035 = C; with A as the current actor ($CC0E) the "
      "script is pushed as its plan ($CF80, B = 2) and its script position "
      "(+1/+2 of its actor-table entry) set to DE. The HAIL action ($E2C7) "
      "uses it with DE = $F2B6 to set the cab and cabbie off. Read from the "
      "code."], ()),
    (0xB772, 0xB77E, 'c', "A = the class of dictionary word DE",
     ["The high nibble of the word's first byte in the dictionary at $5DBF: "
      "$50 for nouns, $60 for adjectives (the parse at $B6FD looks for "
      "these). Read from the code; classes checked against "
      "source/dictionary.py (ACID, ALDERGATE $6x; AGENT $5x)."], ()),
    (0xB77E, 0xB77F, 'b', "$B6FD's flag", ["Cleared by $B6FE, tested by $B77F."], [('B', 0xB77E, 1, 'Flag')]),
    (0xDB5F, 0xDB64, 'c', "Step HL back one and return Z with A = $F0",
     ["Read from the code."], ())):
    _newblk(_a, _e, _k, _t, _d, _s)
_newblk(0xB77F, 0xB83C, 'c', "Fetch the next word for $B6FD's name match",
        ["Used by $B6FD with the flag at $B77E. Read from the code only "
         "in outline; not traced."])
A[0xC1CB]['end'] = 0xC1D8
for _a, _e, _k, _t, _d, _s in (
    (0xD770, 0xD77E, 'c', "Fail if the next token is of class $C0",
     ["The pre-check named in the header of the record at $D769 (flags "
      "$40, part of the player's own script): looks at the token at "
      "($D6BD). Read from the code."], ()),
    (0xD7E0, 0xD7E1, 'b', "A flag for $D7E1", ["Set by $D873, cleared by $D7E8."], [('B', 0xD7E0, 1, 'Flag')]),
    (0xD7E1, 0xD7FA, 'c', "More of the typed line to do?",
     ["If the flag at $D7E0 is set: clear it, drop the rest of the line "
      "($D88A) and fail. Otherwise succeed only if the line has another "
      "sentence waiting ($9FF2). The pre-check named in the header of the "
      "record at $D7D9. Read from the code."], ()),
    (0xC128, 0xC129, 'b', "Flag: the text window has been set up", ["Set to 1 by $C129; read by $C316 (scrolling)."], [('B', 0xC128, 1, 'Flag')]),
    (0xC129, 0xC142, 'c', "Set up the text window",
     ["$A019 = 0, $C128 = 1, and the window variables at $C1F5-$C1FA: 18 "
      "lines, starting at screen address $5020, $C1FA = 2. Read from the "
      "code."], ())):
    _newblk(_a, _e, _k, _t, _d, _s)

A[0xD77E]['title'] = "Action record: parse the next typed sentence into a command (RUN at $9932)"
A[0xD77E]['desc'].insert(0,
    "The body runs the sentence parser ($AAB2) from the token at ($D6BD). "
    "On success the rest of the line ($9FF0) is kept at $9FF2 for next "
    "time and $D6B8 cleared. On failure both word lists are freed ($D87D, "
    "$D88A) and - unless the parser's result was 2 and an action time was "
    "set - the game says 'WHAT ?' ($6866) and fails. Part of the player's "
    "own plan script. Read from the code; 'WHAT ?' seen in play.")
_newblk(0xAB91, 0xAC24, 'c', "Read a sentence's verb words into the node at IY",
        ["Tokens ($AE7F) of class $30 (a verb, see $AE7F) go to IY+0/+1, "
         "class $00 to IY+2/+3, $40 and $20 to one or the other by the "
         "flags in E; $E0 tokens are skipped; anything else ends the verb "
         "(carry when a slot was wanted twice). In statement mode ($A024 = "
         "2, while a case statement is being said) the verb must instead be "
         "one of the eleven relation words at $994D - KILLED, HAD, ... - "
         "and NZ means it is not. Read from the code; classes $00, $20, "
         "$40 and $E0 were not seen in the emulator."])
for _a, _e, _t, _d in (
    (0xAC24, 0xAC8F, "Read a noun phrase into the pattern at $AAA8",
     "Clears ten bytes at $AAA8, then takes tokens: an article ($80) once; "
     "up to three of class $10 or $70 (prepositions; counted in $AAA7, "
     "stored by $AC8F); adjectives ($60, by $AC94); and ends on the noun "
     "($50) or a number ($F0), whose reference goes to $AAAC. Carry when a "
     "word comes in the wrong place; on return NZ if bit 5 of E is set. "
     "Read from the code; the meaning of each E flag bit was not traced."),
    (0xAC8F, 0xAC94, "Put word BC in the first empty pair at $AAA8 (NZ if both are taken)", ""),
    (0xAC94, 0xAC97, "Put word BC in the first empty pair at $AAAE (NZ if both are taken)", ""),
    (0xACA6, 0xACCC, "Copy the noun-phrase pattern into the node: first or second object",
     "Ten bytes from $AAA8 to IY+4 (if E bit 6, which it clears) or to "
     "IY+$0E (if E bit 7); returns NZ, or Z if neither bit was set. Read "
     "from the code."),
    (0xACCC, 0xACFB, "Note where this sentence started, so it can be read again",
     "Skips commas ($A0), then keeps the token position ($A029, also in "
     "$A02B), E, IY and $A012 at $AAA1-$AAA6; when $A01A is 2 it marks the "
     "node with bit 6 of +1. Read from the code."),
    (0xACFB, 0xAD57, "After a sentence: copy the objects on, or rewind to read it again",
     "In statement mode ($A024 = 2) copies the node's six bytes from +8 to "
     "+$18 and parses on ($AB4C). Otherwise, unless $A01B is set, goes "
     "back to the position saved by $ACCC and frees the nodes after it "
     "($A1AF). Read from the code; what makes the parser re-read a "
     "sentence was not traced.")):
    _newblk(_a, _e, 'c', _t, [_d] if _d else [])
_newblk(0xB934, 0xB936, 'b', "The actor an order is for (two copies)",
        ["$B935 is set from A on entry to $B936 and copied to $B934 once an "
         "order is being taken. Read from the code."],
        [('B', 0xB934, 1, 'Actor (taken)'), ('B', 0xB935, 1, 'Actor (asked)')])
_newblk(0xC989, 0xC996, 'c', "Run the numbered action record IX",
        ["HL = the record; the objects' records are set up ($C8EF) and the "
         "record run ($C996). Read from the code."])
_newblk(0xAD57, 0xAD70 if 0xAD70 in A else 0xAE59, 'c', "Count the sentence, then on to the next or finish",
        ["Bumps the sentence counter $A012 (not for a comma in mode 2 of "
         "$A01A); a comma ($A0) goes back to read another sentence "
         "($AABD). Read from the code in outline."])
A[0x9B7F]['desc'].append(
    "Confirmed in the emulator (tools/experiments/cab_test.py): hailed in "
    "Baker Street, the cab took 19-20 minutes to Parliament Street (the "
    "table says 20), and the cabbie then said 'Right guv'nor that will be "
    "10d.'; asked for Old Mill Road, which is not in the table, he replied "
    "'Sorry guv'nor I cannot get there from'ere'.")
A[0x9B25]['desc'] = [
    "IX is the journey's entry in $9B7F. The fare is HL = DE x (minutes / "
    "5, rounded down, + 1). The cabbie's 10d for the 20-minute ride from "
    "Baker Street to Parliament Street in the emulator fits a rate of 2d "
    "in DE (2 x 5). Unless $E619 says otherwise for the "
    "actor in $A036, it is taken off the money ($E39C, SBC HL,DE, $E38F); "
    "then $CFB6, and $A035 from the entry's +3. Read from the code; the "
    "fare confirmed (tools/experiments/cab_test.py)."]
A[0x9B50]['desc'][0] = A[0x9B50]['desc'][0].replace("Read from the code.",
    "Confirmed in the emulator: asked for Old Mill Road from Baker Street, "
    "'The cabbie replies \" Sorry guv'nor I cannot get there from'ere \".'")
fact('cab-fares', 'Cab fares',
     "A hansom cab ride costs 2d for every five minutes of the journey, "
     "plus 2d: the journey times are in the table at $9B7F and the fare is "
     "worked out at $9B25. Confirmed in the emulator: Baker Street to "
     "Parliament Street took 20 minutes and the cabbie asked 'Right "
     "guv'nor that will be 10d.' Only the ten cab stands in the table can "
     "be reached; anywhere else gets 'Sorry guv'nor I cannot get there "
     "from'ere'.")
A[0xA24D]['desc'].append("Seen in every room listing: 'You can see an oil lamp, your armchair "
                         "and watsons armchair.' - AN from the first table, and THE in 'You "
                         "open the plain door.'")

# ---- Session of 2026-11-08 ------------------------------------------------
_newblk(0xD46C, 0xD495, 'c', "Find the exit from the actor's room through door A ($D46C) or to room A ($D471)",
        ["Walks the exits of the actor's room ($D33C; three-byte entries: "
         "direction, door, room, stepped by $D206) comparing byte 1 (the "
         "door, entry $D46C) or byte 2 (the room beyond, entry $D471) with "
         "A. The offset is written into the instruction at $D48B (its "
         "displacement byte $D48D) - self-modifying code. Returns IX on the "
         "exit, or A = $FF if there is none. $D471 is why a room can only "
         "be named in a command when it is next door: the room search "
         "$D39B lets through only rooms it finds. Read from the code."],
        [])
_newblk(0x9C41, 0x9C56, 'c', "Action record: move the vehicle the actor is in to the direct object's room", [
    "Header $04 $00, then: takes the actor's container (+1 of $A017 - the "
    "cab or train it is riding in), sets that thing's bit 7 of +5 ($9C56), "
    "and moves it to the room in $A034, with everything in it, by jumping "
    "into the move code of the direction action at $DD0E (which also "
    "updates $A00A, $DD01 and $DCFF when the mover is the actor). Run by "
    "the vehicle sub-script at $F3AD ($F3AD+4: RUN $9C41 with the plan's "
    "direct object), which $9B20 returns. CORRECTED: was untitled data. "
    "Read from the code."])
_newblk(0xD99E, 0xD9B7, 'c', "The '@' key on an empty line: do the last command again",
        ["Reached from the line editor ($D8CF) when '@' is typed on an "
         "empty line. Unless a typed line still has sentences waiting "
         "($A01B, when the key is ignored), sets $D714 and ends the input. "
         "The word-list builder at $D715 sees $D714 and, instead of "
         "tokenizing the line again, reuses the tokens already at $5B81 - "
         "the previous command's. ($D9AC, shared with the time-out path, "
         "prints two backspaces.) Confirmed in the emulator: after NORTH "
         "into the closet, '@' gave 'YOU CANNOT GO NORTH.' twice."])
A[0xD714]['title'] = "Flag: repeat the last command ('@')"
A[0xD714]['desc'] = ["Set by the '@' key on an empty line ($D99E); the word-list builder "
                     "at $D720 then reuses the previous tokens; cleared by $D6C9. Read "
                     "from the code; confirmed in the emulator."]
fact('repeat-key', "'@' repeats the last command",
     "Typing '@' (SYMBOL SHIFT and 2) on an empty command line does the last "
     "command again: the line editor ($D99E) sets a flag that makes the word-"
     "list builder reuse the previous command's tokens instead of reading "
     "the line. Confirmed in the emulator: after NORTH into the closet, '@' "
     "gave 'YOU CANNOT GO NORTH.' With the one-key cursor moves ($D978), the "
     "game has two keyboard shortcuts that are easy to miss.")
_newblk(0xCB43, 0xCB79, 'c', "End of an actor's go: hand the turn back to the player",
        ["Reached from $C9A2. Unless $DC6C says otherwise, makes the first "
         "actor in the table ($9860, the player) current again; when $A00B "
         "is set, either clears $A00C and narrates ($CA76) or - with HL not "
         "zero - calls HL with $A027 set ($CB40). Read from the code in "
         "outline."])
_newblk(0xE3B8, 0xE3EA, 'c', "Pre-check for getting into a cab",
        ["Named in the header of the shared GET INTO action at $E3EA. Runs "
         "$E3F5 first (busy? already there? will you fit?); then, for a "
         "moment taking the next number after the cab (its driver) as the "
         "actor, asks $CFB6, and if that says yes requires the thing at the "
         "cab's +3 and the actor to share one of bits 4-6 of +4, refusing "
         "($DC15) otherwise. Read from the code in outline."])
_newblk(0xE3F5, 0xE40A, 'c', "Pre-check for sitting on or getting into something",
        ["Named in the header of the shared SIT action at $E40A. Refuses if "
         "the actor is busy ($CBA7) or already in or on the thing ($DCA7: "
         "is the actor held by it, $D278), then the size check: will the actor fit in or "
         "on it ($DEE4)? Read from the code."])
_newblk(0xB6AE, 0xB6D6, 'c', "No indirect object: DON'T BE SILLY, or YOU CANNOT ... THE ...",
        ["The second-slot counterpart of $B65F, handed out by $B303. If the "
         "slot wants a number (requirement codes 5 and 6) or holds one, "
         "prints 'DON'T BE SILLY.' ($B671, $6855). Otherwise, if the slot "
         "has words, checks them against the room's scenery ($B6F0) and "
         "then asks the question at $B68C. Read from the code."])
_newblk(0xB6D6, 0xB6DA, 'b', "$B6FD's working pointers",
        ["Written and read by $B6FD-$B825."],
        [('W', 0xB6D6, 2, 'Position in the scenery list'), ('W', 0xB6D8, 2, 'The slot being matched')])
_newblk(0xB6DA, 0xB6FD, 'c', "If the slot names scenery: 'YOU CANNOT <verb> THE <word>'",
        ["$B6DA for the first slot (verb pattern from $B633), $B6F0 for the "
         "second ($B62F): if $B6FD finds the words in the room's scenery, "
         "the caller's return address is dropped, the words are pushed as "
         "parameters ($B83C) and $68A2 is printed. Confirmed in the "
         "emulator, in Holmes's sitting room (whose description mentions "
         "'the two broad windows'): TAKE WINDOWS gave 'YOU CANNOT TAKE THE "
         "WINDOW', EXAMINE WINDOWS 'YOU CANNOT EXAMINE THE WINDOW' and TAKE "
         "LAMP FROM WINDOWS 'YOU CANNOT TAKE FROM THE WINDOW', while TAKE "
         "ELEPHANT gave 'I DO NOT KNOW THE WORD\"ELEPHANT \"'."])
_newblk(0xB6FD, 0xB772, 'c', "Do the slot's words name some of the room's scenery?",
        ["The actor's room record ($D33C) has at +7/+8 the address of a list "
         "of scenery words - things its description mentions that are not "
         "objects (none: Z). The list is read word by word ($B77F); "
         "adjectives (class $60) and a noun ($50, $B772 gives the class) are "
         "gathered into a pattern at $AAAC and matched against the slot at "
         "HL ($A4E0). NZ when they match. Read from the code; the effect "
         "confirmed (see $B6DA)."])
_newblk(0xB83C, 0xB84C, 'c', "Push the three words at HL as message parameters",
        ["Takes its own return address off the stack, pushes the three word "
         "references from HL, and returns under them, so that the message "
         "printed next ($A59F) finds them as its parameters. Read from the "
         "code."])
_newblk(0xB84C, 0xB863, 'c', "I DO NOT KNOW THE VERB \"<word>\"",
        ["Pushes the typed verb's words ($B186-$B18D) and prints $686A. Its "
         "address is handed out at $B1A7 when no verb record matches. Read "
         "from the code."])
_newblk(0xB863, 0xB866, 'c', "JP $C929 (check the record)",
        ["An address the parser hands out at $B210 when a verb record has "
         "matched: the command is then checked against the record ($C929)."])
fact('scenery-words', 'Scenery',
     "Rooms can mention things that are not objects - the 'two broad "
     "windows' of Holmes's sitting room, say. Each room record points to a "
     "list of such scenery words, and a command naming one gets 'YOU CANNOT "
     "TAKE THE WINDOW' instead of 'I DO NOT KNOW THE WORD' ($B6FD, $B6DA; "
     "confirmed in the emulator).")
_newblk(0xC190, 0xC1A8, 'b', "The chain strip that holds the clock: a 32-pixel pattern, six lines deep",
        ["Drawn once at start-up ($A049 calls $C14A): each of the six "
         "four-byte rows is repeated eight times across the screen from "
         "$5140, one pixel line apart, and the attribute row at $5A40 is "
         "set to $78. It is the chain-like strip between the room text and "
         "the command window, which the clock is printed into ($C1A8) - see "
         "the screenshot on the Pictures page. Read from the code; checked "
         "against the emulator's screen."],
        [('B', 0xC190 + 4 * _k, 4, 'Pixel line %d: %s' % (_k + 1, ' '.join(
            format(b(0xC190 + 4 * _k + _j), '08b').replace('0', '.').replace('1', '#') for _j in range(4))))
         for _k in range(6)])
_newblk(0xC1A8, 0xC1C0, 'c', "Print the clock line: B characters from HL at screen address $5041",
        ["A space, the B characters, a space, through PRINT-CHAR ($C388). "
         "The clock printer jumps here ($BFA1) with the eleven characters of "
         "'Mon 08:02am' built at $BF6E. Read from the code."])
_newblk(0xC29C, 0xC2BA, 'c', "Move part of the command window down a row and clear the gap",
        ["LDDR of 128 bytes - four character rows ending at $50DF - down by "
         "32 bytes, for each of the eight pixel lines; then HL = $5060 and on "
         "into the row-clearing code of $C271 ($C28D). Called at $C260 by "
         "the character printer when the typed line runs past the end of a "
         "screen line. Read from the code."])
_newblk(0xA4CD, 0xA51B, 'c', "Do the pattern words at IY name the words at HL? ($A4CD, $A4E0)",
        ["$A4E0: the first pair must match ($A51B; an empty pattern word "
         "matches anything), then the next two pairs are tried both ways "
         "round, so two adjectives can be typed in either order; A = 1 and "
         "$A02E = 1 for a match on the second pair. NZ means no match. "
         "$A4CD first requires the fourth pair (six bytes on) to match, "
         "and is used by the verb lookup ($B3EC); "
         "$A4E0 by the thing and room searches ($D37B, $D3B8) and the "
         "scenery check ($B764). Read from the code."])

# ---- The Leatherhead line's timetable --------------------------------------
_TT = ("Each DO 140 is internal verb 140: put the train in room n ($E4C9) and "
       "wait m minutes. Rooms 2, 3 and 4 are 'between stations' - also the "
       "rooms a passenger is in while riding. The two Leatherhead trains run "
       "the same three-hour circuit half a cycle apart: 60 minutes on the "
       "way, platform four at Kings Cross (room 23) for 10, 5 minutes, "
       "platform three (22) for 10, 5 minutes, 60 minutes on the way, "
       "Leatherhead platform one (54) for 10, 5 minutes, platform two (55) "
       "for 10, 5 minutes. So a train leaves each platform every 90 minutes "
       "and the run takes about 65. Matches every ride logged in the "
       "emulator: trains left Leatherhead platform two at 12:25, 1:55, 4:55 "
       "and 6:25 and reached platform four 65 minutes later. This is what "
       "decides the endgame chase: Phipps catches the 4:55, and the next "
       "is 90 minutes behind him (see $E7E7).")
for _a, _which in ((0xF278, 'first stop Kings Cross'), (0xF28D, 'first stop Leatherhead')):
    A[_a]['title'] = f"Plan script: steam train (actor {42 if _a == 0xF278 else 43}) - the Leatherhead line, {_which}"
    A[_a]['desc'].append(_TT)
A[0x9F1E]['desc'].append(
    "Confirmed in the emulator (tools/experiments/phipps_route.py 8): the "
    "gardener left at 9:05pm each night and came back at 5:30am on "
    "Tuesday, but at 1:40am on Wednesday and 1:35am on Thursday - see the "
    "Bugs page.")
bug('gardener-early-riser', "Bedtime is sometimes four hours short",
    "At 9pm the bedtime routine that Strachan, the cook and "
    "the gardener share ($9EC1, $9ECB, $9ED1, all ending at $9ED7) puts the "
    "character to bed - Strachan in Daphne's room, the other two off stage "
    "- until its next turn, 504 minutes plus a random number up to 30 later "
    "($9EFE: LD DE,$01F8, then ADD A,E / LD E,A with the random number). "
    "The add is to E alone, so when the random number is 8 or more the low "
    "byte wraps and the carry into D is lost: 256 minutes vanish and he "
    "is back after about 4 hours 10 minutes instead of 8 hours 25. Logged in "
    "the emulator for the gardener (tools/experiments/phipps_route.py 8): off at 9:05pm "
    "every night; back at 5:30am on Tuesday (a small random number), but at "
    "1:40am on Wednesday and 1:35am on Thursday - 4 hours 35 and 4 hours "
    "30, i.e. 248 + 27 and 248 + 22 minutes. A gardener pottering about "
    "in the small hours is harmless, but it is plainly not what the 504 "
    "was for; the same goes for the cook and for Strachan, who share the "
    "code.")

# ---- The police cab's routes, and the two speeds of cab ride ---------------
A[39577]['title'] = "Shared action 1: drive the police cab (Leatherhead routes, $9AA3)"
A[39577]['desc'] = [
    "Header $04 $00 then code. $9AA3 knows the police cab's only three "
    "routes, from the room it is in ($A00A) to the direct object: Old Mill "
    "Road to Main Street (L = 112), Main Street to Old Mill Road (114) and "
    "Main Street to Kings Cross Road (94); anything else refuses ($DC15). "
    "L becomes the journey's length ($A01F, at $9B04), the vehicle to move "
    "is the police cab (thing 109 = $6D, put in $E2C6), and the "
    "ride ends at $9B20 by handing back the vehicle sub-script $F3AD.",
    "Confirmed in the emulator (tools/experiments/chase.py stage P): told "
    "SAY TO POLICE MAN \"GO TO KINGS CROSS ROAD\" in Leatherhead's Main "
    "Street at 5:07pm, the police cab - with Lestrade and Watson aboard - "
    "reached Kings Cross Road at 6:42, 95 minutes. Asked for Buckingham "
    "Palace Road it did nothing. CORRECTED: was data in the automatic split."]
A[39627]['title'] = "Shared action 2: drive the police cab, 20 minutes quicker"
A[39627]['desc'] = [
    "Header $04 $00 then code: the same routes ($9AA3) with 20 minutes "
    "taken off - 94 out to Old Mill Road and 92 back. That matches "
    "Lestrade's own trips logged in the emulator (Main Street 1:39pm to "
    "Old Mill Road 3:13, and back 3:14 to 4:47). Which verb reaches which "
    "of the two records was not traced; both are listed as GO TO (verbs 29 "
    "and 30). CORRECTED: was data in the automatic split."]
A[39649]['title'] = "Shared action 14: a hansom cab ride, dearer and two minutes quicker"
A[39649]['desc'] = [
    "Header $04 $00 then code: the route check ($9B50), the fare at 6d a "
    "step ($9B25 with DE = 6), and the table's minutes less 2 as the ride's "
    "length; then on as $9AF4. Read from the code; not seen used."]
A[39668]['title'] = "Shared action 13: a hansom cab ride"
A[39668]['desc'] = [
    "Header $04 $00 then code: the route check ($9B50), the fare at 2d a "
    "step ($9B25 with DE = 2) and the table's minutes as the ride's length "
    "($9B02 stores it at $A01F); then the cab is moved ($DD0E) and the ride "
    "handed to the vehicle sub-script $F3AD. Confirmed in the emulator: 20 "
    "minutes and 10d from Baker Street to Parliament Street "
    "(tools/experiments/cab_test.py)."]

# ---- Line comments for routines worked out in this session ----------------
C(0x9ED1, {
    0x9ED1: "The gardener's state byte $9ED0: the room he left, or 0 while about",
    0x9ED4: "B = 0, C = 0 (the cook joins here too; Strachan comes in at $9ED7 with B = 74, C = $80)",
    0x9ED9: "Not away: see whether it is time to go",
    0x9EDB: "Away, and this is the turn to come back: B = the room left",
    0x9EDC: "Store 0 at $9ED0, put him in room B, next turn in 0 minutes ($9F1E)",
    0x9EE3: "State word and bits back to none ($F1C1, DE = 0, B = C)",
    0x9EED: "and +5 bit 6 set: a person again",
    0x9EF2: "Is it am?",
    0x9EF7: "Yes: nothing to do",
    0x9EF8: "Is it 9 (pm)?",
    0x9EFE: "DE = 504 minutes (8 hours 24)",
    0x9F01: "A = a random number from 0 to 30",
    0x9F06: "BUG: added to E only - from 8 up the carry into D is lost and 256 minutes go with it",
    0x9F08: "Remember the room in the state byte, move to room B (0, or 74 for Strachan), next turn DE minutes on",
    0x9F0E: "State word SLEEPING ($07F0), bit 4 of +8 ($F1C1)",
    0x9F19: "and +5 bit 6 cleared: no longer a person to talk to",
})
A[0x9ED1]['desc'].append(
    "At 9pm he is put off stage with the state word SLEEPING ($07F0, looked "
    "up with source/dictionary.py) and +5 bit 6 cleared (the bit the "
    "flag-word table at $C471 calls DEAD when it is clear); at his next turn "
    "he is put back in the room he left and woken. Logged in the emulator: "
    "off at 9:05pm, back at 5:30am, 1:40am and 1:35am - see the Bugs page.")
_newblk(0xF1C1, 0xF1D6, 'c', "Set a thing's state word (+9/+10) and state bits (+8 high nibble)",
        ["Thing A ($D237) gets DE as its state word - SLEEPING for the "
         "gardener at night - and B as the high nibble of +8, keeping the "
         "low nibble. Returns NZ. Read from the code."],
        ['Input:A the thing', 'B the new high nibble of +8', 'DE the state word (0 = none)']) if not A.get(0xF1C1, {}).get('title') else None
C(0xA11C, {
    0xA121: "C = the size wanted, A + 3",
    0xA124: "B bit 0: a block has been chosen",
    0xA126: "HL = the first free block; IY = the link that points to it",
    0xA12D: "End of the free list?",
    0xA131: "DE = this block's size; HL on to its link",
    0xA135: "A size over 255 is always big enough",
    0xA139: "Under 256: too small for C?",
    0xA13B: "Yes: next block",
    0xA13D: "Big enough. Nothing chosen yet?",
    0xA141: "Otherwise is it smaller than the chosen block (size at IX-2)?",
    0xA14C: "No: keep the one we have",
    0xA14E: "Choose it: IX = its link field",
    0xA151: "and remember the link that points to it",
    0xA157: "IY = this block's link field; follow it to the next block",
    0xA160: "End of the list: was anything chosen?",
    0xA164: "HL = what would be left of the chosen block after taking C",
    0xA171: "256 or more: split it",
    0xA174: "4 or more: split it",
    0xA178: "Under 4: take the whole block - point the previous link past it",
    0xA18A: "Split: the free block keeps the first part, now HL bytes",
    0xA190: "and IX moves to the part being handed out",
    0xA193: "Store the block's size before it",
    0xA198: "Clear the C - 1 bytes of the block",
    0xA1A4: "NZ: success, IX = the block",
    0xA1AC: "Nothing big enough: out of memory",
})
C(0x9B25, {
    0x9B25: "A = the journey's minutes",
    0x9B2A: "HL = DE x (minutes / 5 + 1): DE per five minutes, started",
    0x9B32: "DE = the fare",
    0x9B33: "Does the actor ($A036) pay? ($E619)",
    0x9B3B: "Take the fare off the actor's money",
    0x9B44: "Narrate the action ($CFB6)",
    0x9B47: "$A035 = (IX+3), with IX as $CFB6 left it",
})
C(0x9B50, {
    0x9B50: "The cab is the cabbie's number less one (cabbie 31 drives cab 30, 34 drives 33)",
    0x9B54: "The cabbie is in the cab; remember the cab at $E2C6",
    0x9B5E: "The cabbie's room becomes the cab's room, and the current room",
    0x9B6A: "Is there a journey from here to the destination ($A034)?",
    0x9B74: "Yes: Z",
    0x9B75: "No: drop the return address, so the record stops here,",
    0x9B76: "and say SORRY GUV'NOR I CANNOT GET THERE FROM 'ERE",
})
C(0x9C07, {
    0x9C0D: "End of the table: NZ, not found",
    0x9C14: "Is A this entry's first stand?",
    0x9C1A: "or its second?",
    0x9C1F: "A is the second stand: C = 0 matches anything,",
    0x9C23: "otherwise C must be the first",
    0x9C2A: "A is the first stand: C = 0 or C the second",
    0x9C33: "Next entry",
    0x9C3B: "Z: found, IX on the entry",
})
C(0x9C41, {
    0x9C41: "Header $04 $00",
    0x9C43: "A = the actor's container: the vehicle it is in",
    0x9C4B: "Set the vehicle's +5 bit 7",
    0x9C4E: "B = the destination",
    0x9C53: "Move the vehicle and all in it to room B",
})
C(0x9A99, {
    0x9A99: "Header $04 $00",
    0x9A9B: "Is this one of the police cab's routes? No: refuse",
    0x9AA3: "From Old Mill Road (room 103)...",
    0x9AAA: "...to Main Street (50): 112 minutes",
    0x9AB5: "From Main Street (50)...",
    0x9AB9: "...to Old Mill Road (103): 114 minutes,",
    0x9AC2: "or to Kings Cross Road (18): 94 minutes",
    0x9AC8: "NZ: a route, L = its minutes",
})
C(0xE38F, {
    0xE38F: "Shift HL's bit 7 up into H...",
    0xE393: "...and clear it in L: L = pence & $7F, H = pence >> 7",
})
C(0xE39C, {
    0xE3A2: "Put them back together: HL = H x 128 + L, H's sign kept by SRA",
})
C(0xE3A9, {
    0xE3AD: "Drop the number marker bit, then unpack as $E39C",
    0xE3B5: "NZ",
})
C(0xD249, {
    0xD24D: "Start at the first thing",
    0xD250: "Next thing (IX its list entry, IY its record); Z at the end",
    0xD255: "Held by A?",
    0xD25A: "Yes: it goes to room B",
    0xD25E: "and so does everything it holds",
})
C(0xD275, {
    0xD275: "HL points at the actor",
    0xD278: "No thing ($FF) or a number ($FE): carry",
    0xD288: "Find thing A's record",
    0xD28C: "Its container; $FF = held by nothing: not carried (NC)",
    0xD293: "Is the container the actor? If not, go up a level",
    0xD298: "Carry: the actor has it",
})
C(0xD305, {
    0xD307: "Start at the first thing",
    0xD30B: "Next thing; Z at the end",
    0xD310: "Is it in A?",
    0xD316: "B = 0: weights (+3), all the way down; B <> 0: sizes (+2), this level only",
    0xD31B: "Add its size; over 127 gives $FF",
    0xD324: "Add its weight; over 127 gives $FF",
    0xD32B: "and the weight of what it holds",
    0xD337: "Overflow: C = $FF",
})
C(0xD978, {
    0xD978: "Cursor right: E",
    0xD97C: "Cursor left (or DELETE, made $08 by GET-KEY): W",
    0xD980: "Cursor down: S",
    0xD984: "Cursor up (made '[' by GET-KEY): N; any other key: back",
    0xD989: "Put the letter in the line and print it",
    0xD98E: "One more character in the line",
    0xD98F: "and press ENTER",
})
C(0xE298, {
    0xE298: "Must be one of the two hansom cabs, 30 or 33",
    0xE2A4: "Must be at a cab stand: any journey from here ($9C07, C = 0)",
    0xE2AF: "The cab must be in room 0 - free, not on a job",
    0xE2BA: "And $CFB9 must agree",
    0xE2C3: "NZ: it can be hailed",
})
C(0xC3E4, {
    0xC3E4: "Printing off (no PRINT command): nothing to do",
    0xC3EC: "The top character row: eight pixel lines from $4000",
    0xC3F3: "Print one",
    0xC3F7: "Next pixel line down",
    0xC3FB: "Stop the printer motor",
    0xC403: "Slow the motor for the last two lines (B < 3): the start of the ROM's COPY-LINE ($0EF4), copied without its BREAK test",
    0xC40C: "Wait for the printer: bit 6 set (no printer) returns, bit 7 is the stylus",
    0xC412: "Join the ROM's COPY-LINE where it starts sending the 32 bytes",
})
C(0xA95B, {
    0xA95C: "The spelling goes to $5C42 on (a ROM system-variable area the game reuses)",
    0xA960: "A = the count byte; a record with bit 7 set has two more bytes before the letters",
    0xA969: "Bits 6-4: letters kept from the word before - just skip over them",
    0xA974: "C = the bit position in the packed letters",
    0xA976: "Bits 3-0: new letters to unpack",
    0xA97C: "Unpack one and store it",
    0xA986: "End the spelling with 0",
    0xA98A: "If the letters ended part-way through a byte, step HL past it",
    0xA990: "DE = the two bytes at HL",
    0xA995: "Shift the wanted letter to the top of D",
    0xA9A0: "Move C on five bits, and HL on a byte when it passes eight",
    0xA9AB: "A = the top five bits of D, plus $60: 'a' is 1",
})
C(0xF3C2, {
    0xF3C5: "IY = the bytecode",
    0xF3CA: "The pen starts at (127, 63)",
    0xF3D4: "Next command; 0 ends the picture",
    0xF3DD: "$08: move the pen to (x, y) from the next two bytes",
    0xF3E4: "x always has bit 7 set: the pen stays in the right half of the screen",
    0xF3EF: "Bit 7: a line",
    0xF3F3: "C = bits 2-0: which way it goes",
    0xF3F7: "B = bits 6-3 of this byte and bits 7-6 of the next: one length, plus 1",
    0xF3FC: "L = bits 5-0 of the next byte: the other length, plus 1",
    0xF40F: "Draw it ($F56E)",
    0xF414: "Bit 6: fill in colour bits 2-0 from the point in the next two bytes ($F490)",
    0xF42E: "Bit 5: runs of attribute cells in paper colour bits 2-0 (any other byte is ignored)",
    0xF43C: "HL = the attribute address: high byte, then low byte + $10",
    0xF449: "Next run; $FF ends them",
    0xF452: "E = bits 1-0: the direction (0 up, 1 right, 2 down, 3 left)",
    0xF456: "B = bits 7-2, plus 1: how many cells",
    0xF45D: "Give the cell the new paper; if its ink is that colour too, flip the ink",
    0xF46D: "Step to the next cell: up ($F514), right ($F540), down ($F525) or left ($F536)",
    0xF488: "End of the picture",
})
C(0xBCC9, {
    0xBCC9: "Does the statement have evidence to check (flags bit 2)?",
    0xBCD2: "Yes: is it all there ($BF08)? If not, NZ - not proven",
    0xBCDA: "Bit 5: such a statement only goes on the waiting list (bit 0)",
    0xBCE6: "Proven: bit 1 set, no longer waiting",
    0xBCEE: "Bit 4: it has a routine to run when proven",
    0xBCF4: "HL = the routine (+4/+5); call it ($D1DB is JP (HL))",
    0xBD01: "Z: done",
    0xBD03: "NZ: the evidence is not all there",
})
C(0xD8AD, {
    0xD8AD: "Print the prompt '> '",
    0xD8B7: "The line goes to $5B00; B counts down from $80 (bit 7 set: nothing typed yet)",
    0xD8BC: "$D897 = 1: not inside quotes; C = 0: no key yet",
    0xD8C3: "Wait for a key, with the time limit ($A536); time up: give up the line",
    0xD8C9: "On an empty line '@' repeats the last command ($D99E)",
    0xD8D2: "The first key of a line may be a cursor key: a one-key move ($D978)",
    0xD8D9: "$18 ('_', made so by GET-KEY): rub out the whole line and start again",
    0xD8E2: "$08 (DELETE): back one character, unless the line is empty",
    0xD8F1: "Rubbing out a quote mark flips the inside-quotes flag back",
    0xD900: "Letters ($40 up) are always taken",
    0xD904: "A quote mark flips the flag; closing a quotation first ends it with a full stop ($D968)",
    0xD917: "Space, ENTER, . , / ` - : are taken...",
    0xD937: "...and digits ($DAE8); anything else is ignored",
    0xD93C: "Store and print it, if the 128-character line has room",
    0xD949: "ENTER: close an open quotation ($D95C),",
    0xD950: "end with a full stop ($D968) and a carriage return",
    0xD959: "NZ: a line was typed",
})
A.pop(0xD897, None)
blk(0xD897, 'b', "The line editor's inside-quotes flag",
    ["1 outside quotation marks, 0 inside: set to 1 at the start of each "
     "line ($D8BE) and flipped by each quote mark typed or rubbed out "
     "($D8F6, $D908). At ENTER an open quotation is closed for you "
     "($D949). CORRECTED: was taken for a NOP at the head of $D898."],
    subs=[('B', 0xD897, 1, 'Flag')])
A[0xD897]['end'] = 0xD898
A[0xD9C3]['title'] = "The tokenizer's current dictionary candidate"
A[0xD9C3]['desc'] = ["The address of the dictionary record being compared, stored at $D9E4 "
                     "for each candidate and read back at $DA22 when the best one has been "
                     "chosen. CORRECTED: was 'not traced'. Read from the code."]
A[0xD9C5]['desc'].append(
    "Abbreviations, tried in the emulator: EX LAMP, EXA LAMP and EXAM LAMP "
    "all examine the oil lamp, EXAMINE LAM too, and INVE takes stock; but "
    "EXAMINE LA finds the LABEL and EXAMINE L, TA LAMP and T LAMP give "
    "'WHAT ?', while words with letters added (EXAMINATION, EXAMINEXYZ) are "
    "not recognised. So a typed word is matched as the start of a "
    "dictionary word ($DA7D counts the letters that agree, keeping the best "
    "in $DC14; the typed length is $DC13), the first word under its letter "
    "winning a tie.")
C(0xD9C5, {
    0xD9C6: "Skip spaces",
    0xD9CD: "Remember where this word starts ($A029)",
    0xD9D0: "End of the line: a $C0 token",
    0xD9D4: "A special character ($DAC6)? Its own token",
    0xD9D9: "Find the dictionary words under its first letter ($DA34); none: a $D0 token (unknown word)",
    0xD9E1: "Best match so far: none",
    0xD9E4: "Next candidate: spell it out ($A94D)",
    0xD9F8: "Skip records of class $D0",
    0xD9FF: "Compare it with the typed word ($DA7D); Z at the end of this letter's words",
    0xDA06: "$C0: end of the line",
    0xDA0A: "$D0: not a word the game knows",
    0xDA12: "Fewer than four letters agree: they must be all the letters typed",
    0xDA21: "BC = the chosen word's offset from the dictionary base $5DBF, A = its class",
})
fact('abbreviations', 'Short words',
     "Commands can be abbreviated: the tokenizer ($D9C5, $DA7D) matches what "
     "you type against the start of each dictionary word. Tried in the "
     "emulator: EX LAMP, EXA LAMP and EXAMINE LAM all examine the oil lamp "
     "and INVE lists what you carry; EXAMINE LA, though, finds the label "
     "first, and a word with letters added - EXAMINATION - is not "
     "understood.")
A[0xD9C3]['subs'] = [('W', 0xD9C3, 2, 'The dictionary record being compared')]
C(0xAAB2, {
    0xAAB2: "$A01A and the sentence count $A012 start at 0",
    0xAAB9: "E: flags for what may come next; D: the token class last read",
    0xAAC1: "A new parse node for this sentence ($AE6A)",
    0xAAC4: "Sentences still waiting from the same line: an ordinary command (mode 1)",
    0xAAD2: "Mode ($A024) not settled: does the sentence open with a noun phrase ($AC24)?",
    0xAAEA: "Yes, with no preposition: a statement such as 'MRS JONES KILLED TRICIA FENDER' (mode 2); its subject goes to the node at +$18",
    0xAB08: "No: an ordinary command (mode 1) - go back to the start of the sentence",
    0xAB16: "The verb and its particles ($AB91); carry: nonsense",
    0xAB1D: "A special word ($90): handled at $AFB3",
    0xAB22: "A comma ($A0): another sentence ($ACCC)",
    0xAB2B: "No verb at the very start of a line, just a full stop: return NZ with A = 2",
    0xAB47: "No verb and no more allowed: on to $ACFB",
    0xAB4C: "Objects: read a noun phrase ($AC24) and file it in the node ($ACA6), as long as they come",
    0xAB60: "A full stop ($B0): the sentence is complete ($AD57)",
    0xAB6F: "Anything else is only allowed in a statement: a relation word ($ABF3) starts the next part",
    0xAB8E: "It makes no sense ($AF67)",
})
C(0xA37D, {
    0xA37D: "No article flag; the remembered command's verb...",
    0xA384: "...gives its record in the verb table ($A2B1) and its flags ($A2BD, $A01D/$A01E)",
    0xA38E: "($C493, $C4B2: also from the record)",
    0xA399: "Print the verb's words: the pair at +6, then the pair at +0 ($A880)",
    0xA3A5: "Flags bit 3: the verb takes a direct object",
    0xA3A9: "A word before it (bit 5), and one more if $A01E bit 7 is set",
    0xA3B6: "A number or a sum of money ($FE): print it ($A419)",
    0xA3C7: "The actor itself: ME ($055B)",
    0xA3D6: "Otherwise its name: a room for requirement codes below 5, else a thing ($A745)",
    0xA3E2: "An indirect object, if there is one and the flags (bit 2) allow it",
    0xA3ED: "Its preposition: the words not printed before",
    0xA3FA: "A number or money ($A419), or a name ($A745)",
    0xA414: "And a full stop",
})
A[0xA37D]['desc'] = [d.replace("as 'yourself' (word $055B) when it is the actor",
                               "as ME (word $055B, looked up with source/dictionary.py; CORRECTED, was "
                               "'yourself') when it is the actor") for d in A[0xA37D]['desc']]
C(0xB86A, {
    0xB86B: "Take the next quoted sentence off its list ($9FEC, $A0F7); none: done",
    0xB874: "Remember where its words are ($B868) and unlink it",
    0xB88A: "A person with a plan script (A = 1): parse it and hand it over ($B8AA)",
    0xB894: "Otherwise just use the words up, to the end of the line ($C0),",
    0xB8A3: "and mark the end with a $90 token",
    0xB8AA: "Parse the words as a sentence of their own",
    0xB8B4: "with an empty sentence list (the player's own is kept on the stack)",
    0xB8BE: "Parse ($AAB2); A = 2 counts as parsed; anything else is nonsense",
    0xB8C7: "Go on until the end of the quotation, then mark it with $90",
    0xB8D3: "An 8-byte node on the order/remark list $9FEE ($A11C)",
    0xB8E5: "+5/+6: the parsed words",
    0xB8F2: "+1 = 0, +0 = the person spoken to",
    0xB8FC: "+7 = the mode: 2 for a statement",
    0xB904: "Nonsense: free the words ($D87D) and put the player's list back",
})
C(0xD078, {
    0xD07D: "Only actors with +4 bit 7 can be in the dark",
    0xD088: "($C86E, then the room and the hour)",
    0xD08E: "A lit room (record byte 0 bit 7) is never dark",
    0xD097: "Nor is anywhere by day ($C00C: 1 means night, 8pm to 6am)",
    0xD09E: "Night, unlit room: look through the things for a light",
    0xD0A7: "One with n = 1,",
    0xD0AE: "+5 & $5C = $14 (lit: the oil lamp once lit),",
    0xD0B7: "+4 bit 7,",
    0xD0BE: "and here ($C821): not dark after all",
    0xD0C6: "NC: the actor can see",
    0xD0C9: "Carry: too dark",
})
C(0xDA34, {
    0xDA34: "The first letter (A = 1 ... Z = 26) indexes the table of offsets at $5D80",
    0xDA43: "DE = where this letter's words start in the dictionary",
    0xDA48: "The next letter that has words marks where they end ($DA32)",
    0xDA58: "No words under this letter: Z",
    0xDA5F: "Copy the typed word to $5C0B in lower case, as the dictionary spells",
    0xDA74: "End it with 0; $DC13 = its length + 1",
})
C(0xDA7D, {
    0xDA7F: "Already matched every typed letter with an earlier word: skip this one",
    0xDA89: "Count the letters of the typed word ($5C0B) that agree with this word ($5C42)",
    0xDA9D: "As good as the best so far? Then this word becomes the best ($DC14)",
    0xDAAD: "A record whose count byte has bit 7 set holds the offset of another record in its next two bytes: follow such links",
    0xDAC1: "NZ: more words to try",
})
fact('synonyms', 'Synonyms in the dictionary',
     "Twenty-nine dictionary records stand for another word: their count "
     "byte has bit 7 set and two more bytes give the record to use instead, "
     "which the tokenizer follows ($DAAD). They are: BREAK = KILL, CALL = "
     "HAIL, CAREFULLY = CLOSELY, EVERYTHING = ALL, EXCEPT = BUT, MADLY and "
     "QUICKLY = FURIOUSLY, ME = YOU, MINE and MY = YOUR, PICK = CARRY, READ "
     "= EXAMINE, SAY = TALK, ST = STREET, the one- and two-letter compass "
     "points N, S, E, W, NE, NW, SE, SW, U, D, I = INVENTORY, L and LO = "
     "LOOK - and one rude word, which also means KILL. (IN is linked to "
     "VISITED, which makes it vanish: see the Bugs page.) Tried in the "
     "emulator: READ LAMP examines the oil lamp, PICK LAMP gives 'You carry "
     "the oil lamp.', I lists what you carry, L looks, and BREAK WATSON gets "
     "'ONLY AN IDIOT WOULD TRY THAT.' Read with source/dictionary.py.")
C(0xA419, {
    0xA41A: "Unpack the sum: HL = total pence (seven bits a byte, marker bit dropped)",
    0xA422: "A space",
    0xA427: "Pounds = pence / 240 ($A476)",
    0xA431: "Any: the pound sign (character $60 in the Spectrum's set) and the pounds",
    0xA439: "Nothing left: done",
    0xA442: "Shillings = what is left / 12",
    0xA449: "None: just the pence and 'D.' ($A469), as in '6D.'",
    0xA44B: "The shillings, a stroke, and the pence - or '-' for none: '2/6', '1/-'",
    0xA463: "($A026 = 0)",
})
C(0xDAEF, {
    0xDAEF: "B = the first number ($DBF7)",
    0xDAF3: "Followed by ':', 'A' or 'P' it is a time; otherwise money ($DB56)",
    0xDB05: "The hour must be below 60 - the same test as the minutes; bit 7 marks it as a time",
    0xDB0E: "':' and the minutes in C",
    0xDB21: "'A': bit 6 of the hour; 'P': bit 6 of the minutes",
    0xDB37: "then 'M'",
    0xDB3C: "Skip full stops; the time must end the word",
    0xDB4F: "Not a time: a $D0 token (not understood)",
})
A[0xB517]['title'] = "ALL BUT: is the candidate one of the things after BUT?"
A[0xB517]['desc'] = [
    "Only when $A01C is set (bit 7 of the verb's first word reference, "
    "copied from $B39C at $B1ED): walks the parse nodes after IY ($AEA9) "
    "and, in any marked with bit 6 of +1 - the node $B029 opens when BUT "
    "(or EXCEPT, a synonym) follows ALL - looks for things the words at +8 "
    "name ($D36A); NZ if the candidate in $A034 is one of them, and $B4FD "
    "then passes over it.",
    "It does not work in practice: in the emulator, with $A01A = 2 (ALL "
    "BUT) and $A01C = $80 both set, TAKE ALL BUT MONEY, DROP ALL BUT MONEY, "
    "GET ALL BUT MONEY and TAKE ALL EXCEPT DISGUISE all included the thing "
    "named after BUT, because IY here is not a parse node at all but the "
    "search routine's address ($D36A), loaded by $B4C1 - see the Bugs page."]
bug('all-but', 'ALL BUT leaves nothing out',
    "The parser understands ALL BUT (and ALL EXCEPT): BUT after ALL sets "
    "$A01A to 2 and opens a parse node marked with bit 6 ($B01C, $B029), and "
    "$B517 is there to skip any candidate named in such a node. But in the "
    "emulator the exception was never made. In the closet, with the money "
    "dropped: TAKE ALL BUT MONEY gave 'You take the china mans disguise. "
    "... You take your money.'; DROP ALL BUT MONEY dropped both; GET ALL "
    "BUT MONEY and TAKE ALL EXCEPT DISGUISE took both, the disguise "
    "included. $A01A was 2 and $A01C $80 after each, so the check at $B517 "
    "was reached.\n\n"
    "The cause, found with breakpoints on $B517-$B541: $B517 expects IY to "
    "be the current parse node and walks on from it ($AEA9) looking for the "
    "BUT node. But by then IY holds the address of the search routine - "
    "$B4C1 loads it with LD IY,$D36A (or $D39B) so that $B4A0 can call it. "
    "Every time, IY was $D36A on entry, so the 'next node' was read from the "
    "bytes before that routine's code ($C9D9, then $CDF9...), none of which "
    "has bit 6 of +1 in the right place, and no candidate was ever excluded. "
    "The fix would be to keep the parse node in another register, or to "
    "push it before $B4C1 changes IY.")
C(0xB4C1, {
    0xB4E7: "IY = the room search, or...",
    0xB4ED: "...the thing search - IY is no longer the parse node, which $B517 still assumes (the ALL BUT bug)",
})
C(0xB517, {
    0xB517: "Only for verbs whose first word has bit 7 ($A01C)",
    0xB521: "IY = the next parse node - but IY is $D36A here, not a node (see the Bugs page)",
    0xB524: "A BUT node (bit 6 of +1)?",
    0xB52A: "Then each thing its words (+8) name ($D36A)...",
    0xB53B: "...is it the candidate?",
    0xB541: "NZ: yes, leave it out",
})
C(0xD526, {
    0xD528: "First pass: name everything listable in A",
    0xD52C: "Next one ($D57D); carry: no more",
    0xD531: "Mark it as seen (+6 bit 7)",
    0xD535: "Its name with an article ($D3D9)",
    0xD53C: "C counts down the things still to name: the last gets a full stop ($A414),",
    0xD546: "the one before it AND ($005D), the rest a comma",
    0xD55A: "Second pass: for each listed thing that holds things itself ($D4CC)...",
    0xD56C: "...say how they are held ($D590) and list them too (recursion)",
})
A[0xAFFA]['desc'] = [d.replace("($A008, with a call to $C03B that was not traced)",
                               "($A008; PRINT first reads the printer's status, $C03B)") for d in A[0xAFFA]['desc']]
A[0xB0FD]['desc'] = [d.replace("(resolved later to the last person or thing mentioned - not traced)",
    "(used only when Watson or Lestrade weigh a statement: $BD7E then takes "
    "the statement's subject from $9FF6, the last person a statement named, "
    "for HE, or from $9FFC, the last thing, for IT/THEY)") for d in A[0xB0FD]['desc']]
A[0xB0FD]['desc'].append(
    "So pronouns are for statements, not commands. In the emulator TAKE IT "
    "and DROP IT after EXAMINE LAMP, and TAKE LAMP AND EXAMINE IT, all gave "
    "'WHAT ?'; HIM and THEM are not in the dictionary at all.")
C(0xBD51, {
    0xBD7E: "The statement's subject: the node's words at +$18...",
    0xBD85: "...or for HE the last person named ($9FF6)...",
    0xBD8E: "...or for IT/THEY the last thing ($9FFC)",
    0xBD97: "into the first object slot; the words at +8 into the second",
    0xBDAE: "$BA17 = the verb word; then make the statement ($BDC2)",
})

for _a, _who in ((40640, 'Strachan'), (40650, 'the cook'), (40656, 'the gardener')):
    A[_a]['desc'] = [f"The room {_who} left at bedtime, or 0 while up and about: written and "
                     "read by the shared bedtime code at $9ED7 (see $9EC1). CORRECTED: was "
                     "'not traced'."]
A[40641]['desc'].append("The 504 to 533 minutes are only right when the random part is "
                        "below 8; otherwise 256 minutes are lost and the character is back "
                        "at about 1:30am - see the Bugs page.")
A[0xBA20]['desc'] = [d.replace("The reply code itself is not traced; the messages it prints include "
                               "Lestrade's 'I DO NOT BELIEVE THAT YOU HAVE THE EVIDENCE TO PROVE THAT ...' ($BBC4).",
                               "The two reply routines are described at $BA67 and $BB67, and both were "
                               "tried in the emulator.") for d in A[0xBA20]['desc']]
A[0xB936]['desc'] = [d.replace("(Watson's and Lestrade's replies, tables $BA67 and $BB67 - not traced)",
                               "(Watson's and Lestrade's replies, $BA67 and $BB67)") for d in A[0xB936]['desc']]
A[0xAFFA]['desc'].append(
    "Tried in the emulator: TAKE LAMP BECAUSE EXAMINE LAMP and DROP LAMP "
    "THEREFORE INVENTORY both give 'WHAT ?' - the guards at $AFE1/$AFE8 "
    "turn them away in a command - while TAKE LAMP, EXAMINE LAMP does both "
    "commands, the comma being the sentence break ($ACCC).")
C(0xB6FD, {
    0xB701: "Remember the slot's words",
    0xB704: "The actor's room record: +7/+8 point at its scenery words; none: Z",
    0xB719: "Build each scenery phrase as a pattern at $AAAC",
    0xB71D: "Clear the pattern",
    0xB725: "Next word ($B77F); none left: Z, not scenery",
    0xB729: "A noun ($50) ends the phrase; an adjective ($60) goes in the first adjective place",
    0xB73A: "Second word: a noun ends it, a second adjective is kept",
    0xB74F: "Third word: must be the noun",
    0xB75A: "The noun goes first in the pattern",
    0xB760: "Do the slot's words name it ($A4E0)? No: on to the next phrase",
    0xB768: "Yes: free the word list $B77F built ($A1AF) and return NZ",
})
A[58877]['desc'] = [
    "Internal verb 130, IS HERE. The header (flags $47) names a pre-check "
    "at $E604, which is the whole test: where the actor is ($C863) and "
    "where the direct object is ($C863) - each being the place found by "
    "climbing out through open containers ($C86E), handed back in the "
    "alternate A register, hence the EX AF,AF' - must be the same, and "
    "the direct object must not be the actor itself ($E5F3); otherwise the "
    "record refuses ($DC15). So a person in a cab IS HERE for someone in "
    "the same cab, and Lestrade's 'is the player in the police cab with "
    "me' ($EA78) works the same way. Read from the code; the cab case "
    "behaved so in the chase runs (tools/experiments/chase.py)."]
C(58877, {0xE604: "The actor's place ($C863), from A'", 0xE60C: "The direct object's place",
          0xE613: "Not the same place: refuse ($E5F0)", 0xE5F3: "Nor may it be the actor itself"})

# ---- The winning line, played (2026-11-08) ------------------------------------
_WIN = (
    "The winning line, played in the emulator (tools/experiments/chase.py "
    "stages A B C D E F2 G3). The case statements were poked proven and you "
    "and Watson were put in Leatherhead's Main Street at about 1:33 on "
    "Wednesday, as Lestrade reached the station with the police cab "
    "waiting for him; everything after that was "
    "typed: (1) CLIMB INTO POLICE CAB in the minute Lestrade climbs in, so "
    "that you, Watson and he fit and Straker stays out; (2) Old Mill Road "
    "at 3:13pm, and Phipps bolts at 3:14; (3) the police cab is back in Main "
    "Street at 4:47 - CLIMB OUT, NORTH three times, and at 4:56 on platform "
    "two, where his script stops being busy, SAY TO LESTRADE \"FOLLOW ME\"; "
    "(4) SOUTH three times, CLIMB INTO POLICE CAB (Lestrade and Watson "
    "follow), SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS CROSS ROAD\" - "
    "verb 30, which the constable's action list sends to the 20-minutes-"
    "quicker record ($9ACB): Kings Cross Road at 6:22; (5) CLIMB OUT, "
    "NORTHEAST twice to platform one, CLIMB INTO TRAIN at 6:28 - the "
    "underground train that runs Kings Cross, Paddington, Victoria (actors "
    "36-41, $F21D); (6) platform one at Victoria at 6:40, where a German "
    "agent is waiting; (7) at 6:42 'Basil Phipps enters.' and 'As Basil "
    "enters he sees you and pulls a gun. With suprising agility Watson "
    "pushes you out of the way of Basils first shot allowing Lestrade time "
    "to pull his gun and capture the culprits. As incredible as it may seem "
    "you have solved this case. You truly deserve the title of worlds "
    "greatest detective.' Two minutes to spare. The hansom cabs are no use "
    "for the last leg: at 6:22 both are already on the road, cab 30 "
    "carrying Phipps and cab 33 the German agent (their containers, logged), "
    "a minute apart. "
    "Played again with less help (stages A B2 C2 D E F2 G3): from Holmes's "
    "rooms at 11am on Wednesday, with only the statements poked proven, "
    "$9D90 and $9E88 poked - the marks a player earns by meeting Lestrade "
    "with Straker on Monday and by proving the Major's statement, without "
    "which the game ends early (at 3pm on Monday, or about 1am on "
    "Tuesday) - and "
    "Watson put beside you on his follow loop (in stage A you never left "
    "your room, so his own script had gone idle) - OPEN YOUR DOOR, WEST, "
    "DOWN, OPEN FRONT DOOR, SOUTH, HAIL CAB, CLIMB INTO HANSOM CAB, SAY TO "
    "CABBIE \"GO TO KINGS CROSS ROAD\", NORTHEAST four times to platform "
    "three, the 12:25 to Leatherhead, SOUTH twice to Main Street (1:36, with "
    "Lestrade), CLIMB INTO POLICE CAB when his script reaches $EA69, and the "
    "rest as above: won again at 6:42.")
_d = A[0xE7E7]['desc']
for _i, _t in enumerate(_d):
    if _t.startswith("Why no other line works"):
        _d[_i] = _WIN
    _d[_i] = _d[_i].replace("In these runs the chase was lost by about a minute; no quicker line was found.",
                            "The plain GO TO and the train both lose; the furious police cab and the underground train win - see below.")
for _i, (eid, title, body) in enumerate(FACTS):
    if eid == 'the-last-scene':
        body = body.replace(
            "Played through in the emulator with the statements poked proven, this "
            "fell a minute short: Phipps's train left Leatherhead at 4:55pm, one "
            "minute before Lestrade would take the order, and the next train was "
            "far too late (details under $E7E7). The police cab fills up: board it "
            "in the same minute as Lestrade, or he or you is left behind.",
            "Played through in the emulator, with the statements poked proven: "
            "the 4:55 train is gone before Lestrade will take the order, but the "
            "police cab can be told SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS "
            "CROSS ROAD\" (74 minutes instead of 94), and from Kings Cross "
            "platform one the underground train reaches Victoria at 6:40 - two "
            "minutes before Basil. The game was won that way. Board the police "
            "cab in the same minute as Lestrade at the start, or he or you is "
            "left behind. Full steps under $E7E7.")
        body = body.replace("Getting there, as read from the scripts ($E7E7, $EE2B):",
                            "Getting there ($E7E7, $EE2B):")
        FACTS[_i] = (eid, 'How the game is won (and was won, in the emulator)', body)
A[0x9E48]['desc'].append("Reached by play too: see the winning line under $E7E7.")
fact('go-furiously', 'GO FURIOUSLY TO',
     "The verb table has two GO TOs: verb 29, GO TO, and verb 30, GO "
     "FURIOUSLY TO (MADLY and QUICKLY are synonyms of FURIOUSLY). People who "
     "drive have both in their own action lists: the local police man sends "
     "GO TO to shared action 1 and GO FURIOUSLY TO to shared action 2, 20 "
     "minutes quicker; a cabbie sends them to shared actions 14 and 15, the "
     "furious ride 2 minutes quicker at three times the fare (6d a step "
     "instead of 2d). Lestrade himself says 'Furiously go to the old mill "
     "road'. It is what wins the game: see $E7E7.")
A[39649]['title'] = "Shared action 15: GO FURIOUSLY TO in a hansom cab - dearer, two minutes quicker"
A[39649]['desc'] = [
    "Header $04 $00 then code: the route check ($9B50), the fare at 6d a "
    "step ($9B25 with DE = 6), and the table's minutes less 2 as the ride's "
    "length; then on as $9AF4. A cabbie's own action list sends verb 30 "
    "(GO FURIOUSLY TO) here. Read from the code."]
A[39668]['title'] = "Shared action 14: GO TO in a hansom cab"
A[39668]['desc'][0] = A[39668]['desc'][0].replace("Header $04 $00 then code:",
    "Header $04 $00 then code (a cabbie's action list sends verb 29, GO TO, here):")
A[39577]['title'] = "Shared action 1: the police cab, GO TO (Leatherhead routes, $9AA3)"
A[39627]['title'] = "Shared action 2: the police cab, GO FURIOUSLY TO - 20 minutes quicker"
A[39627]['desc'] = [d.replace("Which verb reaches which of the two records was not traced; both are listed as GO TO (verbs 29 and 30).",
                              "The local police man's action list (after its 00 entry) sends verb 29, GO TO, to shared "
                              "action 1 and verb 30, GO FURIOUSLY TO, here. Lestrade's orders use verb 30 both ways "
                              "in the chase, and SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS CROSS ROAD\" took 75 "
                              "minutes against 95 for plain GO TO (tools/experiments/chase.py stages F2 and P).")
                     for d in A[39627]['desc']]
_lab = {1: "Shared action 1: GO TO for the police cab (the local police man's own list)",
        2: "Shared action 2: GO FURIOUSLY TO for the police cab (the local police man's own list)",
        13: "Shared action 13: TAKE TO for a hansom cab (the cabbies' own lists)",
        14: "Shared action 14: GO TO for a hansom cab (the cabbies' own lists)",
        15: "Shared action 15: GO FURIOUSLY TO for a hansom cab (the cabbies' own lists)"}
A[0xAA71]['subs'] = [(d0, a0, n0, _lab.get((a0 - 0xAA71) // 2 + 1, l0)) if d0 == 'W' else (d0, a0, n0, l0)
                     for (d0, a0, n0, l0) in A[0xAA71]['subs']]

A[0xAA71]['desc'].append("People have action lists too, after a 00 entry in their records "
    "(see $C933): the local police man maps GO TO and GO FURIOUSLY TO to entries 1 "
    "and 2, the cabbies TAKE TO, GO TO and GO FURIOUSLY TO to 13, 14 and 15, Tricia Fender has entry 3 and "
    "Mrs Jones has entry 22 - which is how the entries no object uses are reached.")
for _i, _p in enumerate(PAGES):
    if _p[0] == 'the-case':
        PAGES[_i] = (_p[0], _p[1], _p[2].replace(
            "you win (#R$9E48 - staged and confirmed in the emulator).",
            "you win (#R$9E48 - staged in the emulator, and reached by play with the "
            "statements poked proven: see #R$E7E7).")) + tuple(_p[3:])
A[61430]['title'] = "Plan script: the German agent (actor 104) - Phipps's buyer"
A[61430]['desc'].append(
    "He waits for Phipps's signal (AWAIT), is put at Old Mill Road (room "
    "103), and from 3pm counts down like Phipps; if you turn up there "
    "($F009: IS IN you, room 103) he joins Phipps's own flight code at "
    "$EF4A - put in Main Street, the 4:55 to London, Kings Cross Road, a "
    "cab to Buckingham Palace Road and on to platform one at Victoria, "
    "where he too runs the last scene ($9E48) if he finds you there. In "
    "the winning run (see $E7E7) he was already standing on platform one "
    "at Victoria when the train came in at 6:40 - 'You can see a german "
    "agent.' - and Basil walked in two minutes later. Read from the "
    "script; the sighting is from the emulator.")
A[0xEE2B]['desc'].append(
    "The flight from $EF4A on is shared with the German agent ($EFF6), who "
    "waits at Old Mill Road too.")
C(0xC7A6, {
    0xC7A8: "7: anything at all",
    0xC7AD: "8: it must be here ($C821)",
    0xC7BB: "9: something to take - here,",
    0xC7C6: "in only one place ($C8A7),",
    0xC7CD: "not a person ($C8BE),",
    0xC7D4: "something the actor can carry ($C8C6),",
    0xC7DE: "and then whether a person holds it ($C8AF, on at $C768)",
    0xC7E4: "10: here and carried by the actor ($D275)",
    0xC7F9: "11: here and in more than one place (a door, say)",
    0xC80A: "12: a person, anywhere",
    0xC814: "13-15: a person who is here",
})
C(0xC628, {
    0xC628: "The requirement code: the low nibble of the record's byte 0; 0 needs nothing",
    0xC62F: "Pass: NZ",
    0xC632: "Refuse",
    0xC635: "Codes 5 and 6: a number",
    0xC63D: "It must be a number ($FE), its value at $A02F...",
    0xC64C: "...with bit 7 of its low byte clear for code 5 (WAIT UNTIL), set for 6 (money: PAY TO)",
    0xC654: "Refused: $A021 = 0",
    0xC660: "Codes 1 and 2: a room whose record has bit 7 of byte 0 set",
    0xC670: "Codes 1 and 3: and next door to the actor ($D471)",
    0xC682: "Codes 7-15 ($C7A6), with the object noted at $CB7A for $CB7B",
    0xC691: "Flags bit 4: then the +5 flag masks from the header ($C74E)",
    0xC6A0: "(two bytes further on when the header also has a pre-check address, bit 6)",
    0xC6B8: "The flags were wrong: $A021 = 1",
})

_EG = [
 ("11:00am Wed", "Holmes's rooms", "OPEN YOUR DOOR, WEST, DOWN, OPEN FRONT DOOR, SOUTH", "Baker Street (5)", None),
 ("11:09", "Baker Street", "HAIL CAB, CLIMB INTO HANSOM CAB, SAY TO CABBIE \"GO TO KINGS CROSS ROAD\"", "12 minutes and a fare ($9B7F, $9B25)", 0x9AF4),
 ("11:25", "Kings Cross Road", "CLIMB OUT, NORTHEAST four times", "Platform three (22), with Lestrade arriving too", None),
 ("12:17", "Platform three", "CLIMB INTO TRAIN", "The Leatherhead line, every 90 minutes", 0xF278),
 ("1:32pm", "Leatherhead platform one", "CLIMB OUT, SOUTH, SOUTH", "Main Street (50) at 1:36; the police cab is waiting", None),
 ("1:38", "Main Street", "CLIMB INTO POLICE CAB in the minute Lestrade does (his script on $EA69)", "You, Watson and Lestrade fit; Straker is left out", 0xE7E7),
 ("3:13", "Old Mill Road", "(wait)", "Phipps bolts at 3:14: 'As you enter Basil Phipps whips his horses...'", 0xEE2B),
 ("4:47", "Main Street", "CLIMB OUT, NORTH three times", "Phipps catches the 4:55 to London; Lestrade says Basil has eluded you", None),
 ("4:56", "Leatherhead platform two", "SAY TO LESTRADE \"FOLLOW ME\"", "The first moment his script is not busy", 0xEAD0),
 ("5:00", "", "SOUTH three times, CLIMB INTO POLICE CAB", "Lestrade and Watson follow you in", None),
 ("5:07", "Main Street", "SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS CROSS ROAD\"", "Verb 30: 74 minutes, not 94", 39627),
 ("6:22", "Kings Cross Road", "CLIMB OUT, NORTHEAST, NORTHEAST", "Kings Cross platform one (20)", None),
 ("6:28", "Platform one", "CLIMB INTO TRAIN", "The underground train: Paddington, then Victoria", 0xF21D),
 ("6:40", "Victoria platform one", "(wait)", "A German agent is waiting", 61430),
 ("6:42", "", "", "'Basil Phipps enters.' - and the winning ending", 0x9E48),
]
_rows = ''.join(
    f'<tr><td>{t}</td><td>{w}</td><td>{_h2.escape(c)}</td><td>{_h2.escape(n)}'
    + (f' (#R${r:04X})' if r else '') + '</td></tr>'
    for (t, w, c, n, r) in _EG)
page('the-endgame', 'The endgame, played',
     '<p>The game was won in the emulator by playing this line from Holmes\'s '
     'rooms at 11am on Wednesday (tools/experiments/chase.py, stages A B2 C2 '
     'D E F2 G3). Help it had: the case statements poked proven (the '
     'Mrs Jones marker $9993 is earnable - see The case), the two flags a player earns earlier ($9D90, Lestrade\'s '
     'introduction; $9E88, the Major - both since earned without pokes, see A playthrough without pokes) and Watson put beside you. Every '
     'command below was typed. Times are the game clock after each step.</p>'
     '<table class="disassembly"><tr><th>Time</th><th>Where</th><th>Commands</th>'
     '<th>What happens</th></tr>' + _rows + '</table>'
     '<p>Why each piece matters: Phipps only bolts if you are at Old Mill Road '
     'between 3pm and about 3:16 (#R$EE2B), and only the police cab goes there; '
     'Lestrade\'s script is busy from the moment he sets off until he stands '
     'on platform two at 4:56 (#R$E7E7); the next Leatherhead train after '
     'Phipps\'s is 90 minutes behind (#R$F278); plain GO TO in the police cab '
     'arrives at 6:42, as Basil does, and both hansom cabs are on the road '
     'then. GO FURIOUSLY TO and the underground train leave two minutes to '
     'spare. The last scene itself is #R$9E48.</p>')
C(0xA1C7, {
    0xA1C9: "HL = the block's size byte, three bytes before the node",
    0xA1CF: "Walk the free list from $9FE3 to the first block above this one",
    0xA1DB: "(end of the list: put it last)",
    0xA1EB: "Link it in: the previous link now points here,",
    0xA1F1: "its size's high byte cleared, and its own link to the next free block",
    0xA1F8: "Join it to the block after it if they touch ($A20C)...",
    0xA1FD: "...and the block before it to this one",
})
bug('in-is-visited', "The word IN is read as VISITED, so typing IN does nothing",
    "In the dictionary IN's record has bit 7 of its count byte set, which "
    "makes it a synonym: its two extra bytes point at the record to use "
    "instead, and they point at VISITED (offset $0956) - a word of class "
    "$E0, which the parser skips ($AB91). Every other synonym points at a "
    "word of its own kind (READ at EXAMINE, N at NORTH...).",
    "So whenever IN is typed it vanishes. Tried in the emulator, with the "
    "token buffer at $5B81 read after each command: PUT LAMP IN SOFA "
    "tokenises IN as $E0 $0956 and gets 'WHAT ?'; PUT LAMP INTO YOUR "
    "ARMCHAIR gets 'I DO NOT KNOW THE VERB\" PUT INTO\"' and PUT LAMP ON "
    "SOFA 'YOU CANNOT PUT ON THE SOFA', so the parser itself is fine. SIT "
    "IN YOUR ARMCHAIR works only because SIT alone does (SIT ARMCHAIR asks "
    "'WHICH ARMCHAIR ?'). The verbs that contain IN - DROP IN (17), PUT IN "
    "(38), SIT IN (40), the only verb records using a word the tokenizer "
    "replaces - can still be reached by leaving IN out, since a missing "
    "preposition is not held against a match: PUT LAMP SOFA gave 'YOU "
    "CANNOT PUT IN THE SOFA'. But PUT LAMP IN SOFA, the natural thing to "
    "type, gets 'WHAT ?'. Found with "
    "source/dictionary.py's synonym list; the link looks like a data slip "
    "in the master dictionary.")
C(0xC00C, {
    0xC00C: "am or pm?",
    0xC016: "pm: 12 noon to 12:59 counts as morning (4)",
    0xC01A: "8pm or later: night (1)",
    0xC021: "7pm: evening (2)",
    0xC028: "1pm to 6pm: afternoon (3)",
    0xC02B: "am: midnight to 5am is night (1)",
    0xC033: "6am: dawn (5)",
    0xC035: "7am to 11am: morning (4)",
})
A[0xC00C]['desc'].append("The five parts, from the code: 1 night (8pm to 5:59am), 2 the 7pm hour, "
                         "3 afternoon (1pm to 6:59pm), 4 morning (7am to 12:59pm), 5 the 6am hour. "
                         "The message codes $17, $16, $15, $14 and $0F show text only in parts 1-5 "
                         "respectively ($A68C).")
C(0xD2AD, {
    0xD2B0: "C = the limit; B = twice it (255 if that overflows)",
    0xD2B8: "Step the pointer at $A039 on through memory",
    0xD2C8: "Mix the bytes it points at into the last result ($A037)",
    0xD2D7: "Never the same number twice running",
    0xD2DE: "Halve it until it is no more than B",
    0xD2E8: "minus C",
})
C(0xC8C6, {
    0xC8C8: "B = the thing's weight (+3) plus all it holds ($D2F2)",
    0xC8D9: "The actor's +3 is how much it can carry; take off what it already carries,",
    0xC8E6: "then the thing: not enough left (carry) gives Z, no",
    0xC8EA: "NZ: it can carry it",
})
C(0xBC46, {
    0xBC4A: "A 0 on the stack marks the end of the list",
    0xBC4E: "Walk the case table; $FF ends it",
    0xBC55: "Push each statement that is waiting (bit 0) and not of the bit-5 kind",
    0xBC63: "Next statement ($BE5A)",
    0xBC68: "Then pop them one by one and try to prove each ($BCC9)",
})
A[0xD2A4]['title'] = "A random number from 0 to A"
A[0xD2A4]['desc'] = ["The size of $D2AD's result (it can be negative): |x - A|, where x is a "
                     "pseudo-random byte halved until it is no more than 2A. So 0 to A "
                     "inclusive, not 'below A'. Read from the code."]
C(0xD2A4, {0xD2A7: "Make it positive"})

# $D2A4 gives 0 to A inclusive, not 'below A': say so everywhere.
def _fixrange(t):
    return (t.replace("a random number below (iobj)", "a random number up to (iobj)")
             .replace("plus a random number below m", "plus a random number from 0 to m")
             .replace("...a random number below it", "...a random number from 0 to it")
             .replace("a random number below n ($D2A4) picks", "a random number from 1 to n ($D2A4 on n - 1, plus 1) picks"))
for _a, _r in A.items():
    if not isinstance(_r, dict):
        continue
    _r['title'] = _fixrange(_r.get('title') or '') or _r.get('title')
    _r['desc'] = [_fixrange(x) for x in _r.get('desc', [])]
    _r['comments'] = {k: _fixrange(v) for k, v in _r.get('comments', {}).items()}
    _r['subs'] = [(s0[0], s0[1], s0[2], _fixrange(s0[3])) if len(s0) > 3 and isinstance(s0[3], str) else s0
                  for s0 in _r.get('subs', [])]
A[0xD29D]['title'] = "A random number from 1 to 100"
A[0xD29D]['desc'] = [d.replace("$D2A4 with A = 99, plus one: a percentage roll.",
                               "$D2A4 with A = 99 (0 to 99), plus one: a percentage roll.") for d in A[0xD29D]['desc']]
A[0xD29D]['regs'] = ['Output:A 1-100']
for _a in list(A):
    _r = A[_a]
    if isinstance(_r, dict):
        _r['desc'] = [x.replace("30-44 minutes (30 plus a random number below 15)",
                                "30 to 45 minutes (30 plus a random number from 0 to 15)")
                       .replace("his next turn about 504 minutes later (plus a random number below \"\n     \"30",
                                "his next turn about 504 minutes later (plus a random number up to 30")
                       .replace("plus a random number below 30", "plus a random number up to 30")
                      for x in _r.get('desc', [])]
A[0x8259]['desc'] = [d.replace(
    "Bytes 6-7 are not yet decoded either (they look like rules for which object slots the phrase takes).",
    "Bytes 6-7 are a fourth word slot, laid out the same way: GO for the ten "
    "directions (so GO NORTH works), CLOSELY for verb 20 (EXAMINE CLOSELY) and "
    "FURIOUSLY for verb 30 (GO FURIOUSLY TO); the narrator prints this word first "
    "('Furiously go to the old mill road'). The high nibbles of the four slots "
    "are the record's flags, gathered by $A2BD into $A01D/$A01E. CORRECTED: "
    "bytes 6-7 were 'not yet decoded'.") for d in A[0x8259]['desc']]
A[0x8259]['desc'].append("Confirmed in the emulator: GO NORTH works like NORTH, and EXAMINE "
                         "CLOSELY LAMP is narrated 'You closely examine the oil lamp.' - the "
                         "fourth word first - and takes five minutes; EXAMINE LAMP CAREFULLY "
                         "(the adverb after the object) gets 'WHAT ?'.")
A[0x8259]['desc'].append(
    "The flag nibbles, as far as the code and the 54 records show. $A2BD "
    "packs the first two slots' nibbles into $A01D and the last two into "
    "$A01E. $A01D bit 3 (first word, nibble bit 3): the verb takes a direct "
    "object - set for every transitive verb and for none of the directions, "
    "LOOK, INVENTORY, HELLO or WAIT HERE; the narrator prints a direct "
    "object only then ($A3A5), and it is also bit 7 of the first word's "
    "reference, which is what $B39C/$A01C copy, so ALL can only be used "
    "with such verbs (in the emulator EXAMINE ALL goes through everything in "
    "the room, while KILL ALL, KILL having no flags at all, prints nothing). $A01D bit 2: the verb takes an indirect object - DROP "
    "IN, GIVE TO, PAY TO, PUT IN, PUT ON, TAKE FROM, TAKE OUT OF, TAKE TO, "
    "TELL, TELL ABOUT ($A3E9). $A01D bit 5 (second word, nibble bit 1): the "
    "phrase's second word goes before the direct object - CLIMB INTO, GET "
    "OUT OF, GO TO, LOOK THROUGH, SIT IN, TALK TO, WAIT UNTIL and others "
    "($A3A9). $A01E bit 7 (fourth word, nibble bit 3, only CLIMB OUT OF and "
    "GET OUT OF): one more word before the object in the narration ($A3AE). "
    "$A01D bit 0: the object need not be here - FOLLOW, COME WITH, the GO "
    "TOs, HAIL, TAKE OFF, TAKE TO, TELL - copied to $A038, which lets the "
    "thing search $D36A skip its is-it-here test ($B4DA, $B581). $A01D bit "
    "4: no 'You ...' narration at all ($A326 jumps over it) - LOOK, "
    "INVENTORY, HELLO, ENTER, FOLLOW, COME WITH, GO INTO, the GO TOs, TAKE "
    "TO, TELL and WAIT UNTIL, whose own code says what happens. $A01E bits "
    "2-3 both set (third word's nibble 12 or 13: WAIT UNTIL, PAY TO): the "
    "direct object is a number, requirement code 5 rather than 7 ($C4A1); "
    "$A01E bits 0-1 both set do the same for the indirect object ($C4C0), "
    "though no verb sets them. $A01E bit 4 (HAIL, CLIMB INTO): try every "
    "candidate for the second object rather than the first that fits "
    "($B190, $B2DF), and no ALL. Bits 6-7 of $A01D (bit 7: ENTER, GO INTO, "
    "the GO TOs; bit 6: TAKE TO) and bits 5-6 of $A01E were not traced to "
    "a reader.")
A[0x8259]['desc'] = [d.replace("the high 4 bits are flags not yet decoded.", "the high 4 bits are flags (see below).") for d in A[0x8259]['desc']]
C(0xD36A, {
    0xD36E: "Next thing ($D206: IX its list entry, IY its record); none left: A = $FF",
    0xD373: "Do the slot's words name it? (its name words at +7, $A4E0)",
    0xD381: "With $A038 set any match will do;",
    0xD387: "otherwise it must also be here ($C821)",
    0xD393: "A = the thing",
})
C(0xD405, {
    0xD407: "The noun (+0/+1): an article first, or note it is YOU ($A7D0)",
    0xD410: "$A028 set: the noun alone",
    0xD416: "First adjective (+2/+3), unless bit 7 marks it as not to be printed",
    0xD427: "Second adjective (+4/+5), likewise",
    0xD438: "Then the noun",
})
A[0xA2BD]['title'] = "Gather a verb record's flag nibbles into $A01D and $A01E"
A[0xA2BD]['desc'] = ["IX is a verb record ($8259): $A01D = the high nibbles of its first two "
                     "word slots (+1, +3), $A01E those of the last two (+5, +7) - the "
                     "verb's grammar flags, described at $8259 (direct object, indirect "
                     "object, preposition before the object...). Read from the code."]
C(0xAA14, {
    0xAA14: "Capital letters become small ones",
    0xAA1F: "$A025 = 0 at the start of a line: a leading space is dropped",
    0xAA31: "A carriage return starts a new line",
    0xAA3B: "A quote mark gets a space before it,",
    0xAA46: "and it, like a full stop, makes the next letter a capital ($A026)",
    0xAA51: "A letter: a capital if $A851 (all capitals, code $1B) or $A026 says so",
    0xAA6E: "Out through the screen layer ($C1E1)",
})
A[0xA852]['title'] = "Code $1B: capitals on/off"
A[0xA852]['desc'] = ["Toggles $A851. While it is set every letter is printed as a capital "
                     "($AA59) instead of the usual sentence case. It is not how the game's "
                     "refusals come out in capitals: with a breakpoint here, 'YOU CANNOT GO "
                     "WEST.' and 'I DO NOT KNOW THE WORD...' were printed without reaching "
                     "it, so they take another route to the screen. Which messages use code "
                     "$1B was not found. Read from the code."]
A[0xA851]['title'] = "Code $1B: the all-capitals flag (read at $AA59)"
A[0xAA14]['desc'] = [d.replace("(not traced past $AA46)", "(the rest: a full stop or quote mark makes the next letter a capital, and $A851 makes them all capitals)") for d in A[0xAA14]['desc']]
C(0xD182, {
    0xD182: "The room has its own text: print that ($A59F)",
    0xD187: "Otherwise the opening line ($D0DD's message at DE)...",
    0xD18C: "...as seen from inside whatever the actor is in ($C863): a cab, say",
    0xD19A: "(with THE for its name: $A2AA)",
    0xD1A2: "Then the room's name ($D1C6) and a full stop",
})
from build_skeleton import BUGS as _BUGS  # noqa: E402
for _i, (_id, _t, _body) in enumerate(_BUGS):
    if _t.startswith('Two-word verb error messages'):
        _BUGS[_i] = (_id, _t, _body + "\n\n"
            "Narrowed down on 8 November: it happens when the second word is a "
            "direction - a verb in its own right - and not with a preposition. "
            "GET UP and LOOK UP give 'UP GET' and 'UP LOOK'; PUT INTO LAMP and PUT "
            "LAMP INTO SOFA give 'PUT INTO', in order. The message ($686A, printed "
            "by $B84C) prints the typed verb's word slots in order, and the verb "
            "reader puts a direction first on purpose: in $AB91 a class-$20 word "
            "(a direction) arriving when the first slot already holds a verb "
            "moves that verb to the second slot and takes the first itself "
            "($ABE1-$ABED). That is what lets GO NORTH match the NORTH record, "
            "whose GO is an extra word; for a phrase that matches nothing it "
            "puts UP before GET in the complaint. So a cosmetic side effect "
            "rather than a fault in the message code.")
C(0xAB91, {
    0xAB9C: "Next token; $E0 words are skipped",
    0xABA3: "A verb ($30): into the first slot, if it is free",
    0xABB5: "Carry: a second word for a slot already taken",
    0xABB7: "Class $00: into the second slot",
    0xABC9: "Class $40: as a verb, without the bit-0 flag",
    0xABD1: "A direction ($20): the first slot if free...",
    0xABDD: "...otherwise it takes the first slot and the verb already there moves to the second (GO NORTH; and why GET UP is reported as 'UP GET')",
    0xABEF: "Anything else ends the verb",
})
fact('watson-connections', "Watson's connections",
     "Tell Watson something about the case and he either praises you or, by "
     "chance, wonders aloud about 'some connection between' two things, picked "
     "from the statements you have told him ($BA67, $BD06). The pairing can come "
     "out oddly. In the emulator, at the start of the game: SAY TO WATSON "
     "\"PHIPPS KILLED MRS BROWN\" got 'That is brilliant Holmes, I do not know how "
     "you do it.'; \"TRICIA FENDER KILLED MRS BROWN\" got 'Well do you think there is "
     "some connection between Basil Phipps and Tricia Fender?'; and \"MRS BROWN "
     "KILLED HERSELF\" got 'Well do you think there is some connection between "
     "Tricia Fender and Herself?'")
C(0xD4CC, {
    0xD4D2: "From the first thing, count (B) those in place A that should be listed ($D4EF)",
    0xD4E6: "A = B; Z if none",
})
C(0xF54A, {
    0xF54A: "One pixel up (E + 1) - unless that reaches y = 176 ($B0): then put it back and Z",
    0xF555: "One down (E - 1), not below 0",
    0xF55E: "One right (D + 1), not past 255",
    0xF565: "One left (D - 1), not out of the right half (bit 7 of D must stay set)",
})
C(0xF5D2, {
    0xF5D3: "HL = the pixel's screen byte, A its bit ($F5FB)",
    0xF5D8: "Find its attribute byte ($58xx)",
    0xF5E1: "Keep the paper, set the ink to the pen colour ($F60B)",
    0xF5EB: "(if the paper is that colour too, use the opposite ink)",
    0xF5F5: "Then set the pixel",
})

C(0xA20C, {
    0xA20C: "HL = the start of this block (the size word sits at IX-2)",
    0xA211: "Add its size: HL = the address just past it",
    0xA218: "DE = the link to the next free block",
    0xA21E: "No next block: return NZ (nothing to join)",
    0xA225: "Does this block end where the next one starts? If not, return NZ",
    0xA229: "Yes: HL points at the next block",
    0xA230: "DE = its size, BC = its link",
    0xA237: "Add its size to this block's",
    0xA244: "and take over its link, unhooking it from the chain",
    0xA24B: "Return Z: joined",
})
C(0xCC37, {
    0xCC37: "Clear the failure count ($CC0B)",
    0xCC3D: "Find the actor's record ($CC0E)",
    0xCC40: "Not found: $A01F = 1 and return",
    0xCC48: "Save the record address and the actor's id",
    0xCC4F: "$CC0D = 1 if an order or remark is waiting for it ($B91F), 0 if not",
    0xCC5A: "Set the actor up as the subject ($CC29, $D045)",
    0xCC60: "Output off ($5C3C = 0)...",
    0xCC64: "...unless the actor is where the player is ($C821)",
    0xCC71: "$A01F = 0",
})

# ---- The text window and the picture (traced and tried 2026-11-08) ----
# The block at $C142 held two routines; split off the boot-time screen set-up.
_c = A[0xC142]['comments']
_moved = {k: v for k, v in _c.items() if k >= 0xC14A}
for _k in _moved:
    del _c[_k]
A[0xC142]['title'] = "Text lines full width again (36 characters)"
A[0xC142]['desc'] = [
    "Clears $C128 and sets the characters-left count ($C1F5) to 36, the "
    "print position to $5020 (the start of screen row 17, where every line "
    "of text is printed before the window scrolls up) and the pixel shift "
    "to 2, by joining the end of $C129. It does not clear anything. Called "
    "by the page-wait at $C306, by the boot set-up at $C14A, and at $D71D "
    "each time the player is asked for a command - which is why a picture "
    "stays up only until the text that follows the next command scrolls it "
    "away.",
    "CORRECTED 2026-11-08: this was described as clearing the screen and "
    "resetting a line count; the routine after it ($C14A) clears the "
    "screen, and the 36 is characters to a line, not lines."]
_c.update({
    0xC142: "Not in narrow mode",
    0xC146: "36 characters to a line",
    0xC148: "Set the rest up as $C129 does",
})
_newblk(0xC14A, 0xC190, 'c', "Set up the screen at the start of the game",
    ["Clears the screen ($C10F), sets up the command window (36 "
     "characters left on its line ($C1F4), the cursor at $50E0 - the start "
     "of the bottom row - and pixel shift 2), makes the text lines full "
     "width ($C142), draws the chain strip ($C190) across screen row 18, "
     "pixel lines 1 to 6, and colours that row with attribute $78. Called "
     "once, at $A049. Read from the code."])
A[0xC14A]['comments'].update({
    0xC14A: "Clear the screen",
    0xC14D: "36 characters left on the command line",
    0xC152: "Cursor at the start of the bottom row ($50E0)",
    0xC158: "Pixel shift 2",
    0xC15D: "Text lines full width",
    0xC160: "HL = row 18, pixel line 1; DE = the chain pattern",
    0xC166: "Six pixel lines",
    0xC168: "Each is the pattern's four bytes eight times over",
    0xC179: "Next four bytes of the pattern",
    0xC17D: "Next pixel line down",
    0xC182: "Colour row 18 with attribute $78",
})

A[0xC128]['title'] = "Flag: text lines are narrow (a picture is showing)"
A[0xC128]['desc'] = [
    "1 while a room's picture is in the top right quarter of the screen "
    "and the text is kept to the left half (18 characters to a line); 0 "
    "for full-width lines. Set by $C129, cleared by $C142, read by the "
    "character printer ($C2E2) and the scroll ($C316). Confirmed in the "
    "emulator: describing the entrance hallway (room 6) sets it and the "
    "line length to 18; the next command clears it."]
A[0xC129]['title'] = "Narrow the text lines to the left half (a picture is showing)"
A[0xC129]['desc'] = [
    "Called at $A284, after the 18 newlines that clear the text window "
    "and before the room's picture is drawn in the top right quarter "
    "($F3C2). Sets $C128, the characters-left count ($C1F5) to 18, the "
    "print position to $5020 and the pixel shift to 2, and clears the "
    "page line count ($A019). From then on the scroll ($C316) moves only "
    "the left 16 bytes of each pixel line and leaves the colours alone, "
    "so the picture stays where it is while the text runs beside it.",
    "CORRECTED 2026-11-08: the 18 was read as a number of lines. "
    "Confirmed in the emulator: in room 6 the description comes out "
    "18 characters to a line ('You are in an | entrance hallway. | Above "
    "there is the | stairway...')."]
A[0xC129]['comments'].update({
    0xC129: "New page: no lines printed yet",
    0xC12D: "Narrow mode on",
    0xC131: "18 characters to a line",
    0xC133: "Characters left on this line",
    0xC136: "Print at the start of screen row 17",
    0xC13C: "Pixel shift 2",
})

C(0xC271, {
    0xC271: "Rows 20-23 of the screen...",
    0xC274: "...up one character row to rows 19-22",
    0xC27A: "For each of the eight pixel lines:",
    0xC27E: "move four character rows (128 bytes)",
    0xC285: "Next pixel line",
    0xC28A: "Clear the bottom row, row 23",
    0xC28D: "36 spaces, from pixel shift 1",
})
C(0xC29C, {
    0xC29C: "Rows 19-22 down a row, from the end backwards",
    0xC2A5: "For each of the eight pixel lines:",
    0xC2A9: "move four character rows (128 bytes)",
    0xC2B0: "Next pixel line",
    0xC2B5: "Then clear row 19 with $C271's code",
})
C(0xC2BA, {
    0xC2BA: "Pick up the print position and pixel shift",
    0xC2C6: "Not a newline: print it",
    0xC2CA: "Newline: fifteen lines since the last pause?",
    0xC2D1: "Yes: wait for a key ($C306) and start the count again",
    0xC2D6: "Count the line",
    0xC2DA: "Back to the start of row 17...",
    0xC2DD: "...and scroll everything above up a row ($C316)",
    0xC2E2: "A fresh line: 36 characters, or 18 beside a picture",
    0xC2EE: "Print the character",
    0xC2F1: "Line full? Then take a newline",
    0xC2F8: "Save the characters left, print position and pixel shift",
})
A[0xC316]['desc'] = [
    "Moves screen rows 1-17 up to rows 0-16, eight pixel lines at a time: "
    "all 32 bytes of each line in full-width mode, only the left 16 when a "
    "picture is showing ($C128 set). In full-width mode the colours of "
    "rows 1-17 move up too, and before anything moves the top row goes to "
    "the ZX Printer ($C3E4) if printing is on. Then row 17 is cleared with "
    "36 (or 18) spaces. Called by the character printer at $C2DF on every "
    "newline. Read from the code; the narrow mode confirmed in the "
    "emulator (see $C129)."]
C(0xC316, {
    0xC316: "Full width: send the top row to the printer first",
    0xC320: "From row 1 to row 0, 17 rows",
    0xC329: "32 bytes a line, or 16 beside a picture",
    0xC336: "Eight pixel lines",
    0xC33B: "Move one pixel line of the row",
    0xC341: "Next pixel line",
    0xC349: "Both pointers on a character row",
    0xC351: "Next row",
    0xC354: "Full width: move the colours of rows 1-17 up too",
    0xC363: "Clear row 17: 36 spaces, or 18",
    0xC36D: "from pixel shift 2",
})
A[0xC37D]['title'] = "Swap DE and HL, then move HL down a character row"
A[0xC37D]['desc'] = [
    "Adds 32 to L, and 8 to H when that carries - the next character row, "
    "crossing into the next third of the screen when it has to. Because it "
    "swaps first, $C316 calls it twice to move both of its pointers on "
    "and leave them the right way round.",
    "CORRECTED 2026-11-08: this was described as the next pixel line; 32 "
    "bytes on in the Spectrum's screen is the next character row."]
C(0xC37D, {
    0xC37D: "Work on the other pointer",
    0xC37E: "Down a character row",
    0xC382: "Still in the same third",
    0xC383: "Into the next third",
})
A[0xD715]['title'] = "Action record: read the typed line into a word list (RUN at $9928)"
A[0xD715]['desc'].insert(0,
    "The player's turn starts here: the page line count ($A019) is "
    "cleared and the text lines go back to full width ($C142). Then, "
    "unless '@' asked for the last command again ($D714), the typed line "
    "at $5B00 is run through the tokenizer ($D9C5) word by word into the "
    "list at $5B81: one class byte per token, followed by its two-byte "
    "value for words of class $E0, $F0 or $90 and for anything below $80; "
    "the list ends at class $C0. $D6BD is pointed at the list and the "
    "record succeeds. Read from the code.")
C(0xD715, {
    0xD719: "A fresh page count, and full-width text lines",
    0xD720: "'@': use the last word list again",
    0xD726: "Clear the 96-byte word list",
    0xD72E: "HL = the typed line, IY = the word list",
    0xD735: "Mark the end, then read the next token",
    0xD73C: "Store its class",
    0xD741: "Classes $E0, $F0, $90 and those below $80...",
    0xD751: "...are followed by their two-byte value",
    0xD75B: "Until the end of the line (class $C0)",
    0xD760: "The parser starts at the list",
    0xD766: "Succeed",
})

A[0xC306]['desc'] = [
    "Called by the character printer ($C2D1) when a newline comes after "
    "fifteen lines of text ($A019 = 15) since the player last typed a "
    "command or pressed a key. Sets FLASH on the attribute at $5A5F - the "
    "right-hand end of the chain strip on row 18 - waits for a key via "
    "the GET-KEY wrapper at $C415, turns FLASH off again and makes the "
    "text lines full width ($C142). Nothing is cleared: the text simply "
    "carries on scrolling.",
    "Confirmed in the emulator 2026-11-08: typing LOOK. LOOK in the "
    "sitting room stops here with $A019 = 15 part way through the second "
    "description, waiting for a key. CORRECTED: this was said to be "
    "triggered by $C1F5 (the characters left on the line) and to clear "
    "the screen."]
fix(0xC2BA, "advances the line counter and - once a full page has been "
    "printed (see the 15-line 'page wait' check the caller at $C306 makes) - "
    "waits for a keypress and clears the window before continuing.",
    "counts the line in $A019, waits for a key after fifteen ($C306), and "
    "scrolls the window up ($C316) to print the next line at the start of "
    "row 17. A character that fills the line (36 to a line, 18 beside a "
    "picture: $C1F5) is followed by a newline of its own.")
fix(0xC1F4, "$C1F5 is also used by the page wait (overlay 01).",
    "$C1F5 is the text window's own characters-left count, and $C1F8-$C1FA "
    "its print position and pixel shift.")

C(0xC1FC, {
    0xC200: "C = the command window's pixel shift, HL = its print position",
    0xC209: "ENTER: print a space over the cursor and start a new line",
    0xC214: "DELETE: rub the last character out ($C249)",
    0xC218: "Anything else: in capitals ($C240), printed",
    0xC21E: "Line full?",
    0xC224: "New line: back to the start of the bottom row, pixel shift 2...",
    0xC228: "...scroll the window up ($C271)...",
    0xC22B: "...and 36 characters to go",
    0xC22D: "Save the characters left, pixel shift and print position",
    0xC237: "Draw the '+' cursor after it (overwritten by the next character)",
})
A[0xC821]['title'] = "Can the current actor ($A036) see thing A?"
A[0xC821]['desc'].insert(0,
    "NZ if it can. Yes when the thing is what the actor is in or on (the "
    "root of the actor's own containment chain, $C863); no when the "
    "thing's +5 bit 7 is clear (the underground trains, objects 37-41); "
    "yes when the thing's chain ends at the actor (carried, or in "
    "something open the actor carries) or at the same holder as the "
    "actor's; and when neither is held by anything, yes if the actor's "
    "room ($A00A, set by $CC29) is one of the thing's rooms (+0 is how "
    "many, from +15 on).")
A[0xC821]['desc'].insert(1,
    "CORRECTED 2026-11-08: the test is from the current actor's point of "
    "view, not the player's. Confirmed in the emulator: during one WAIT "
    "at the start, $CC64 asks it about the player (thing 0) for every "
    "actor, and it answers yes only for Watson (actor 3, room 8) and the "
    "player himself, both in the sitting room; Mrs Hudson (actor 2, room "
    "10) and everyone else get no.")
C(0xC821, {
    0xC824: "IX = the thing's record; B = the thing",
    0xC828: "A = what the actor is in or held by, at the top ($C863)",
    0xC82E: "The thing itself: yes",
    0xC831: "+5 bit 7 clear: no",
    0xC837: "B = the actor's top; A = the thing's own top",
    0xC83E: "Held by the actor: yes",
    0xC844: "Different tops: no",
    0xC848: "The same holder (not $FF): yes",
    0xC84B: "Neither held: is the actor's room one of the thing's rooms?",
    0xC85A: "Z: no",
    0xC85D: "NZ: yes",
})

C(0xCBC2, {
    0xCBC2: "Nothing for $FF or 0",
    0xCBC7: "B = the thing; is it in the room the player is looking at ($A009)?",
    0xCBD1: "Yes: output on",
    0xCBD7: "Climb to whatever holds it at the top (a cab, say)",
    0xCBE5: "Its name is the message's subject (record + 7, on the stack)",
    0xCBEA: "For a moment make the player the current actor...",
    0xCBF7: "...and ask whether he can see that ($C821)",
    0xCBFD: "No: return (leaving $A036 as the player - it is not put back)",
    0xCC00: "Yes: back to the real actor and print message DE ($A59F)",
})

C(0xCF43, {
    0xCF43: "Bit 7: two more bytes (an address) to clear",
    0xCF4B: "Bit 4: two more",
    0xCF50: "Then by the instruction's code (bits 0-3):",
    0xCF52: "code 1: two bytes in all",
    0xCF56: "codes 2 and 5: four",
    0xCF5E: "code 7: five",
    0xCF62: "code 6: three",
    0xCF66: "code 4: five",
    0xCF6E: "code 3: three; any other: two",
    0xCF73: "Clear two bytes",
    0xCF79: "Clear one byte",
})

A[0xDDD0]['desc'].insert(1,
    "Tried in the emulator 2026-11-08, at 8:01am on Monday: WAIT UNTIL 9:00 "
    "sets the action time to 59 minutes ($89 $00 at $A02F: bit 7 marks a "
    "time); WAIT UNTIL 8 to 719 (8pm, the next 8 o'clock); WAIT UNTIL "
    "8:30PM ($88 $5E, bit 6 of the minutes) to 749; WAIT UNTIL 7AM ($C7 "
    "$00, bit 6 of the hour) to 1379, 7am the next day. WAIT UNTIL 8:30 PM, "
    "with a space, gets I DO NOT KNOW THE WORD \"PM\". All four waits are "
    "cut short at 8:34 by the news about Lestrade.")
C(0xDDD0, {
    0xDDD4: "HL = the typed time ($A02F); drop bit 7",
    0xDDDA: "Without the am/pm bits...",
    0xDDE2: "...in minutes past twelve ($DE48): the target, at $DDCD",
    0xDDE8: "The clock ($9FDF) in minutes: now, at $DDCB",
    0xDDF2: "am typed: the target is in the morning ($DDCF = 'a')",
    0xDDFB: "pm typed: in the afternoon ('p')",
    0xDE04: "Neither: the same half of the day as now ($9FE2)...",
    0xDE0E: "...unless that time has gone (or is now): then the other half",
    0xDE19: "HL = target - now",
    0xDE23: "DE = twelve hours",
    0xDE2E: "Later than now: add twelve hours if it is in the other half",
    0xDE3C: "Not later: add twelve hours, and twelve more for the same half",
    0xDE42: "That is how long the wait takes ($A01F); succeed",
    0xDE48: "HL = hours x 60 + minutes, twelve o'clock counting as 0",
    0xDE60: "Compare the target with now (carry if earlier, Z if the same)",
})

C(0xBDC2, {
    0xBDC2: "Both searches start at the top of the thing index",
    0xBDCD: "DE = the remark's verb word",
    0xBDD1: "Find it in the list of relation words at $994D (B counts from 1)",
    0xBDDA: "Not there (the list ends with 0): not a statement (Z)",
    0xBDEA: "Its position is the relation",
    0xBDEE: "The things named need not be here ($A038 = 2)",
    0xBDF3: "The first thing matching the subject words",
    0xBDF8: "None: not a statement",
    0xBDFC: "More than one: carry (which one is meant?)",
    0xBE03: "Copy the subject's entry",
    0xBE09: "The same for the object words",
    0xBE1F: "Succeed (NZ)",
    0xBE22: "HL = the thing's record",
    0xBE28: "A person (+5 bit 6) goes to $9FF6, anything else to $9FFC",
    0xBE34: "Copy six bytes",
    0xBE3A: "Carry: ambiguous",
    0xBE3C: "Next thing matching the subject slot ($B172)",
    0xBE4B: "Next thing matching the object slot ($B178)",
})

C(0xC6BE, {
    0xC6BE: "The requirement code: the low nibble of the record's byte 1; 0 needs nothing",
    0xC6C5: "Pass: NZ",
    0xC6C8: "Refuse",
    0xC6CB: "Codes 5 and 6: a number",
    0xC6D3: "It must be a number ($FE), its value at $A031...",
    0xC6DE: "...with bit 7 of its low byte clear for code 5...",
    0xC6EE: "...and set for code 6",
    0xC6F5: "Codes 1 and 2: a room whose record has bit 7 of byte 0 set",
    0xC706: "Codes 1 and 3: and next door to the actor ($D471)",
    0xC719: "Codes 7-15 ($C7A6), with the object noted at $CB7A",
    0xC727: "Flags bit 4: then the indirect object's +5 masks from the header ($C74E)",
    0xC737: "(two bytes further on when the header also has a pre-check address, bit 6)",
    0xC74B: "The flags were wrong: $A021 = 1, and refuse",
})

C(0xC74E, {
    0xC74E: "C = the object's +5 flags",
    0xC755: "First the mode in bits 2-3 of B with mask L...",
    0xC75E: "(failed: return Z)",
    0xC75F: "...then the mode in bits 0-1 with mask H",
    0xC763: "Mode 0: every mask bit must be set",
    0xC76B: "(missing: note the bits that are not)",
    0xC76D: "Mode 1: at least one (or no mask at all)",
    0xC77B: "Mode 2: none may be set",
    0xC784: "(note them, with bit 7: present but should not be)",
    0xC788: "Mode 3: not all may be set",
    0xC797: "Failed: the bits go to $CB79",
    0xC79A: "...but the failure is ignored while $A00B is clear",
    0xC7A1: "Z, with HL = the refusal that names the flag ($CB7B)",
})

A[0x8259]['desc'] = [d.replace(
    "Bits 6-7 of $A01D (bit 7: ENTER, GO INTO, "
    "the GO TOs; bit 6: TAKE TO) and bits 5-6 of $A01E were not traced to "
    "a reader.",
    "$A01E bit 5 (GIVE TO, PAY TO): with no preposition typed, the second "
    "noun phrase is the direct object ($B421) - so GIVE WATSON LAMP gives "
    "the lamp to Watson (confirmed in the emulator, 8 November). Bits 6-7 "
    "of $A01D (bit 7: ENTER, GO INTO, the GO TOs; bit 6: TAKE TO) and bit "
    "6 of $A01E (set for most transitive verbs) were not traced to a "
    "reader here; see the correction below.") for d in A[0x8259]['desc']]
A[0xB405]['desc'].append(
    "Traced in the emulator 2026-11-08 (breakpoint at $B451). TAKE LAMP: "
    "no preposition, $A01E = $40, BC = $0812 - the direct object from the "
    "node's first group (+8), the indirect from the second (+18). GIVE "
    "WATSON LAMP: no preposition, $A01E = $61 (bit 5 set), BC = $1208 - "
    "the other way round, and the game says 'You give the oil lamp to "
    "Watson.' GIVE LAMP TO WATSON: TO matches the node's first group's "
    "preposition (+14), $A01D = $0C, bit 5 flipped, BC = $0812. TALK TO "
    "WATSON: TO typed ($B188) but not attached to a group, so $A01D's bit "
    "5 ($28) is used as it is: $0812.")
C(0xB405, {
    0xB405: "A = 1: the verb record matched with its middle words swapped ($A4CD); swap $B188 and $B18A to suit",
    0xB416: "Gather the verb's flags ($A01D, $A01E)",
    0xB419: "No preposition typed ($B188 = 0)?",
    0xB421: "Then $A01E bit 5, flipped, picks the order (GIVE WATSON LAMP)",
    0xB426: "Is it the preposition of the node's first group (+14)...",
    0xB435: "...or of its second (+16)?",
    0xB440: "$A01D bit 5 - flipped if so - picks the order",
    0xB447: "Bit 5 set: B = 8 (the direct object is the first group), C = 18",
    0xB44E: "Clear: the other way round",
    0xB451: "Note the order at $B182",
    0xB457: "Copy the direct object's six bytes into $B172 (count at $B16D)",
    0xB461: "and the indirect object's into $B178 ($B16E)",
    0xB468: "HL = the node + the offset; copy six bytes",
    0xB476: "Any of them non-zero?",
    0xB480: "Then the slot is used: set bit 0 of its count",
})

C(0xAD57, {
    0xAD57: "Count the sentence ($A012) - but not a comma in mode 2 ($A01A)",
    0xAD67: "A comma: back to read another sentence ($AABD)",
    0xAD6C: "$A01B set (the line had sentences waiting)?",
    0xAD72: "Then look at the second node of the sentence list",
    0xAD79: "Has it a verb of its own?",
    0xAD83: "No: carry the verb's bit 7 into the first node...",
    0xAD95: "...and fill in the empty word slots at the first node + $A01B from the second node's words ($AE59)",
    0xADB2: "Then drop the first node of the list",
    0xADB8: "(with a verb: drop the first node of the rest of the line, $9FF2)",
    0xADBC: "IX = the list's first node; unhook it...",
    0xADD1: "...and free it ($A1C7)",
    0xADD4: "Now go through the sentences ($A012 of them) from the start",
    0xADE4: "Next sentence's node (skipping those marked by bit 6 of +1)",
    0xADE7: "A statement ($A024 = 2) whose third group (+24) is empty...",
    0xAE02: "...takes the previous sentence's",
    0xAE11: "A sentence with no verb is merged with the previous one ($AEF1)",
    0xAE1E: "Then backwards from the last node",
    0xAE2A: "Each earlier sentence with no second group (+18),",
    0xAE35: "the same verb as the later one,",
    0xAE45: "where the later one has words at +14...",
    0xAE4D: "...has words copied from it ($AF27, from +14)",
    0xAE57: "Done: Z",
    0xAE59: "Copy the word at DE to HL unless HL already holds one (Z if it was empty)",
})

A[0xAD57]['desc'].append(
    "Tried in the emulator 2026-11-08: EXAMINE LAMP AND YOUR ARMCHAIR and "
    "DROP LAMP AND YOUR MONEY each run as two commands, the verb carried to "
    "the second; but GIVE LAMP AND YOUR MONEY TO WATSON (and with a comma "
    "for AND) gets I SEE NOTHING THAT YOU CAN GIVE, and PUT LAMP AND YOUR "
    "MONEY IN YOUR ARMCHAIR gets WHAT ?, though GIVE YOUR MONEY TO WATSON "
    "on its own works. The backward pass at $AE1E, which copies words "
    "from a later sentence into an earlier one with the same verb, never "
    "compares the last pair - see the Bugs page ('and-to').")

bug('and-to', 'GIVE THE LAMP AND THE MONEY TO WATSON gives nothing',
    "When a command names two things joined by AND (or a comma) and then a "
    "second object - GIVE LAMP AND YOUR MONEY TO WATSON - the parser makes "
    "two sentences, GIVE LAMP and (GIVE) YOUR MONEY TO WATSON. The forward "
    "pass of $AD57 gives the second sentence the verb; a backward pass at "
    "$AE1E is meant to give the earlier sentences the later one's TO WATSON "
    "(it compares each sentence with the next, and when the earlier one has "
    "no second object and the same verb, copies the preposition and the "
    "object across with $AF27). It never does: the loop steps one sentence "
    "back ($AEC5) before each test, and the call at $AE22 has already "
    "stepped back once, so the last pair is never compared and the last "
    "comparison is made against the head of the list. In the emulator, "
    "carrying the lamp and the money, GIVE LAMP AND YOUR MONEY TO WATSON "
    "says I SEE NOTHING THAT YOU CAN GIVE: the first sentence is GIVE LAMP "
    "with no one to give it to (the parse nodes were dumped at $AE57: the "
    "first node has only GIVE and LAMP; the second has YOUR MONEY, TO and "
    "WATSON). GIVE YOUR MONEY TO WATSON on its own, and DROP LAMP AND YOUR "
    "MONEY, work.",
    "Taking the call at $AE22 out (three zero bytes) fixes it: the same "
    "command then prints 'You give the oil lamp to Watson.' and 'You give "
    "your money to Watson.', one minute apart. With three things the loop "
    "would then pass the object back one sentence at a time.")
C(0xAD57, {0xAE22: "One step back already - so the loop below never compares the last pair (see Bugs)"})

C(0xB39D, {
    0xB39F: "The verb word, from the node's +0",
    0xB3A5: "Its bit 7 (ALL was typed with it) goes to $B39C",
    0xB3AD: "Pattern word 1 ($B186)",
    0xB3B0: "The node's +2 (CLOSELY, FURIOUSLY, GO...) is pattern word 4 ($B18C)",
    0xB3B9: "Clear pattern words 2 and 3 ($B188, $B18A)",
    0xB3C3: "Fill them with the first two of the node's words at +4, +14, +6 and +16 that are there ($B483)",
    0xB3D9: "$A02E = 0",
    0xB3DD: "Try each 8-byte verb record from $8259",
    0xB3EB: "Does it match the pattern ($A4CD)?",
    0xB3F0: "No: next record, until the zero one at the end",
    0xB3FA: "None matched: Z",
    0xB3FD: "Matched: fill the object slots ($B405) and return NZ",
    0xB483: "No room left (B = 0): skip",
    0xB486: "Copy the word at the node + E to the pattern",
    0xB49B: "An empty one is not counted",
    0xB49C: "Otherwise one less to fill, and on to the next pattern word",
})

fix(0xC040, "($C1C0 with HL = $09A2; not checked which words)",
    "($C1C0 with HL = $09A2: the ROM's 'Start tape, then press any key.', "
    "then a key is waited for)")
C(0xC040, {
    0xC040: "'Start tape, then press any key.' (from the ROM), and wait for a key",
    0xC046: "Keep the block's length and start",
    0xC04E: "Save the 17-byte header at $C0FE (a code file, 'SHD V2.0') with the ROM's SA-BYTES",
    0xC059: "A pause of fifty frames",
    0xC05F: "Then the block itself",
    0xC06D: "'REWIND TAPE.'",
    0xC073: "', then press any key.' (the end of the ROM's message), and wait",
    0xC079: "Read the header back in VERIFY mode (LD-BYTES with carry clear)",
    0xC086: "(no match: TAPE ERROR)",
    0xC089: "Then verify the block",
    0xC097: "Matched: return with carry set",
    0xC098: "'TAPE ERROR.' and ' press any key.'",
})

A[0xD7FA]['title'] = "Action record: turn the next sentence into the player's command (RUN at $993C)"
A[0xD7FA]['desc'].insert(0,
    "Part of the player's own script (see $993C): parses the sentence at "
    "$9FF2 into a verb and objects ($B191) and copies them into the plan "
    "registers ($9FD6-$9FD8), where the script's DO picks them up. With "
    "ALL ($A01C, kept in $D6B8 between turns) the sentence is kept so that "
    "the next turn takes the next thing; otherwise its node is freed, with "
    "any BUT nodes after it. If the sentence does not parse, an ALL that "
    "has run out of things fails quietly ($DC15, with $A033 = $FF); "
    "anything else sets $D7E0 so that the rest of the line is thrown away "
    "($D7E1). Read from the code.")
C(0xD7FA, {
    0xD7FD: "Carry the ALL flag over from the last turn",
    0xD803: "IY = the sentence; where the ALL search had got to ($D6BB -> $B17E)",
    0xD80D: "Parse it into a verb and objects ($B191)",
    0xD810: "(failures now count: $A00B = 1)",
    0xD818: "Parsed: keep the ALL flag for next turn",
    0xD81E: "The next letter printed is a capital ($A026)",
    0xD823: "The verb and objects into the plan registers",
    0xD82F: "Note where the ALL search got to",
    0xD835: "ALL still going: keep the sentence",
    0xD83B: "Otherwise unhook and free its node...",
    0xD84F: "...and any nodes after it marked with bit 6 (BUT)",
    0xD858: "Succeed",
    0xD85B: "Did not parse: the ALL is over",
    0xD85F: "It was an ALL: no verb ($A033 = $FF), drop the sentence and fail quietly",
    0xD870: "Otherwise drop the rest of the line ($D7E0) and end the word list there",
})

bug('scenery-literals', "Punctuation in a room's description scrambles its scenery words",
    "To find scenery words ($B6FD) the game reads the room's description "
    "with its own small walker, $B77F, rather than the printer. The two "
    "disagree about bytes $20-$3F: the printer ($A5F2) prints them as "
    "single characters - spaces, digits, commas and full stops - but $B77F "
    "sends everything from $20 to $5F to its packed-letters code ($B7DD), "
    "which skips (A AND $1F) + 1 five-bit letters. So after the first "
    "comma or full stop the walker is reading the middle of packed text as "
    "dictionary references.",
    "Traced in the emulator 2026-11-08 by noting each word $B77F hands "
    "back. In the hansom cab (room 1, 'You are travelling the streets of "
    "London in a hansom cab, the sun shines through the windows onto your "
    "face.') it returns TRAVELL, STREET, LONDON, HANSOM and CAB, then the "
    "comma at $7DF0 sends it eleven bytes on, to two references ($9A12, "
    "$E2CC) that are really packed letters, and it stops. TAKE STREETS "
    "there gets YOU CANNOT TAKE THE STREET; TAKE WINDOWS gets I SEE NO "
    "WINDOW THAT YOU CAN TAKE. On the underground (room 3) the full stop "
    "at $7E63 is followed by six such references ($0745, $0666, ...). In "
    "the sitting room (room 8) the words that matter come first, so TAKE "
    "WINDOWS still gets YOU CANNOT TAKE THE WINDOW, though even there a "
    "space byte at $7D08 produces one false word.",
    "Making the walker step over $20-$3F (a breakpoint at $B7DD that "
    "jumps back to $B7AA) puts the cab's words after the comma back in "
    "the walk, though it then follows the night-time text (FLICKER, GAS, "
    "LAMP...) because the walker ignores the operands of the control "
    "codes below $1D as well.")
C(0xB77F, {
    0xB77F: "Finished the sub-message last time ($B77E = $FF)?",
    0xB786: "Then go back to where the last one was called from (none left: Z)",
    0xB78C: "Unhook the saved position from the list at $B6D6...",
    0xB79C: "...and free its node ($A1C7)",
    0xB7AA: "The next byte",
    0xB7B3: "A dictionary reference: DE",
    0xB7B9: "A word of class $60, $30 or $20 is the last of its message (the printer, $A647, ends there): $B77E = $FF",
    0xB7C3: "Return NZ with the word in DE",
    0xB7CD: "$00-$1F: a control code",
    0xB7D1: "$20-$5F: a run of packed letters to skip (the printer takes $20-$3F as single characters: see Bugs)",
    0xB7D5: "$60 and up: one of the common words at $67B7 ($A840); NZ, A = 0",
    0xB7DD: "(A AND $1F) + 1 letters...",
    0xB7E7: "...five bits each ($A990, C counts the half bytes)",
    0xB7F7: "Code 2: a jump - follow it",
    0xB807: "Code $0B: a call - save the position after it on the list at $B6D6...",
    0xB82E: "...and go to the sub-message",
    0xB834: "Other codes below $1D are passed over (their operands are not); $1D-$1F end the text",
})

C(0xB01C, {
    0xB01C: "BUT: only straight after ALL ($A01A = 1)",
    0xB024: "'All but' ($A01A = 2)",
    0xB029: "A new sentence node for the things after BUT, marked with bit 6 of +1",
    0xB030: "Go on parsing",
    0xB033: "ALL: only at the start of a sentence, and only once",
    0xB03D: "'All' ($A01A = 1), and bit 7 of +1 on the node",
    0xB049: "A quote mark with no verb yet (E bit 1)? Then it becomes TALK ($088B)",
    0xB058: "Add the quote's position in the word list ($A02B) to the list at $9FEC",
    0xB085: "Skip tokens up to the closing quote (class $90, no value)",
    0xB092: "Mark it as the end of a sentence (class $C0)",
    0xB09A: "PAUSE: wait for a key ($C415)",
    0xB0A3: "LOAD (and QUIT): load a saved game ($B0AC)",
})
A[0xB01C]['desc'].append(
    "Tried in the emulator 2026-11-08: a line that is only a quotation, "
    "\"HELLO\", is taken as TALK (the word at $088B): 'You talk to "
    "Watson.' and Watson's good morning, the same as SAY \"HELLO\". TO "
    "WATSON \"HELLO\" gets WHAT ?.")

C(0xF490, {
    0xF490: "The colour to fill with",
    0xF495: "A marker on the stack ($00B0: no line has E = $B0) under the seeds",
    0xF499: "From the seed, go left (D - 1) while the pixel is clear...",
    0xF4A3: "(stopped by the left edge, x = $80: start here)",
    0xF4A5: "(stopped by a set pixel: colour it and step back right)",
    0xF4AB: "Nothing seeded yet on the lines either side",
    0xF4B1: "Line E + 1 (none at the edge): a clear pixel starts a run there...",
    0xF4BF: "...and the first of each run is pushed as a seed ($F48E)",
    0xF4C9: "Back to the line",
    0xF4D0: "The same for line E - 1 ($F48F)",
    0xF4E8: "Back to the line",
    0xF4EF: "Fill this pixel and move right",
    0xF4F7: "Next pixel clear: carry on along the line",
    0xF4FC: "Set: colour it too, and the line is done",
    0xF4FF: "Take the next seed, until the marker",
    0xF505: "Restore the colour to 0",
    0xF50D: "Is the pixel at the pen set? (NZ if so)",
    0xF514: "HL 32 bytes back, unless that leaves the attribute area",
    0xF525: "HL 32 bytes on, unless that leaves the attribute area",
    0xF536: "HL one byte back, unless that leaves the attribute area",
    0xF540: "HL one byte on, unless that leaves the attribute area",
    0xF54A: "E + 1 (Z, unchanged, at $B0)",
    0xF555: "E - 1 (Z, unchanged, below 0)",
    0xF55E: "D + 1 (Z, unchanged, past 255)",
    0xF565: "D - 1 (Z, unchanged, left of $80: the picture is the right half)",
})

C(0xF56E, {
    0xF56E: "Bit 0 set: the line is mostly along E",
    0xF574: "Mostly along D: plot the point",
    0xF577: "Step along D: left with bit 2, right without",
    0xF587: "End of a run?",
    0xF58A: "Then one step along E: E - 1 with bit 1, E + 1 without",
    0xF59A: "and the run length again",
    0xF59C: "L points in all",
    0xF59F: "(or until the pen meets the edge of the picture)",
    0xF5A4: "Mostly along E: plot the point",
    0xF5A7: "Step along E: E - 1 with bit 1, E + 1 without",
    0xF5B7: "End of a run?",
    0xF5BA: "Then one step along D: left with bit 2, right without",
    0xF5CA: "and the run length again",
    0xF5CC: "L points in all",
})

C(0xB0FD, {
    0xB0FD: "THATS: E bit 3 clear - the noun phrase before it belongs to the last node",
    0xB104: "(step back to it, $AEC6)",
    0xB107: "HL = that node's first group (+8)",
    0xB10D: "Then move on to the next node, and set E bit 3",
    0xB118: "E bit 3 set: count a sentence and start a new node ($AE6A)",
    0xB11F: "Copy the first group into the new node's third group (+24)",
    0xB12E: "Back to the parser with E bits 0-2, 6 and 7 set",
    0xB135: "HE as the first word: a statement ($A024 = 2)",
    0xB13F: "HE later on: after a finished clause (E bit 3), a new node",
    0xB14B: "Mark the node: HE (+25 bit 7)",
    0xB151: "IT or THEY as the first word: a statement",
    0xB15B: "Later on: a new node after a finished clause",
    0xB167: "Mark the node: IT or THEY (+25 bit 6)",
})

C(0xAC24, {
    0xAC24: "Clear the ten-byte pattern",
    0xAC2C: "E bits 2, 4 and 5: each kind of word still allowed",
    0xAC30: "Next token",
    0xAC33: "An article ($80): once only, at the start",
    0xAC3F: "Carry: a word out of place",
    0xAC41: "Class $10 or $70: only before any adjective ($AAA7 counts them, up to three)",
    0xAC5C: "Store it in one of the two slots at $AAA8 ($AC8F; a third is out of place)",
    0xAC65: "An adjective ($60): in one of the two slots at $AAAE ($AC94); no more articles or class $10/$70 words",
    0xAC78: "The noun ($50) or a number ($F0) ends the phrase: its reference to $AAAC",
    0xAC88: "and the token after it is read",
    0xAC8B: "No carry; NZ if the phrase was empty (bit 5 still set)",
    0xAC8F: "Store BC in the first empty one of two word slots (NZ if both are full)",
})

C(0xACFB, {
    0xACFB: "A statement ($A024 = 2)?",
    0xAD02: "Only once (E bit 6)",
    0xAD0B: "Copy the first group (+8) to the third (+24)",
    0xAD20: "and parse on",
    0xAD23: "A command: with $A01B set, just parse on",
    0xAD2E: "Otherwise go back to the start of the sentence (saved by $ACCC): its token position...",
    0xAD34: "...the flags in E (D = $B0)...",
    0xAD3A: "...the sentence count...",
    0xAD40: "...and its node",
    0xAD44: "Free the nodes after it ($A1AF) and unhook them",
})

C(0xB936, {
    0xB93B: "Note the actor",
    0xB93E: "IX = its order or remark ($B90E)",
    0xB941: "A remark (+7 = 2): Watson's or Lestrade's reply ($BA20)",
    0xB949: "From a plan script's ASK (+1 = $FF)?",
    0xB950: "Words the player said: whom they are for",
    0xB956: "The ALL flag and the ALL search position, kept in the order",
    0xB966: "Parse the order's current sentence for this actor ($B191)",
    0xB96B: "Parsed: keep the ALL position and flag",
    0xB97F: "Not an ALL: drop the sentence ($B9CA)",
    0xB983: "NZ: there is a command to carry out",
    0xB98C: "An ASK: its verb and objects, resolved ($CEDE), are the command",
    0xB9A7: "Remove the order ($B9FA)",
    0xB9AC: "Unparsable: drop the order's sentences one by one...",
    0xB9B1: "...and return Z: nothing to do",
    0xB9B4: "An ALL that has run out: clear the flag, drop the sentence...",
    0xB9C7: "...and try the next one",
    0xB9CA: "Drop the order's current sentence (IY) and any BUT nodes after it",
    0xB9E5: "None left: remove the order and return Z",
    0xB9F2: "More to come: NZ",
})

fix(0xA4CD, "A = 1 and $A02E = 1 for a match on the second pair.",
    "A = 0 for a match in the order given and 1 for a match with the "
    "second and third pairs swapped (the verb lookup's $B405 then swaps "
    "$B188 and $B18A to suit); $A02E is set to 1 as soon as the first pair "
    "matches.")
C(0xA4CD, {
    0xA4D1: "The fourth pair first (six bytes on)",
    0xA4DA: "(no match: NZ)",
    0xA4E4: "$A4E0: the first pair must match",
    0xA4E9: "($A02E = 1: the first word matched)",
    0xA4EE: "Second and third pairs as they are: A = 0",
    0xA4FA: "Or swapped: the pattern's third against the words' second...",
    0xA50C: "...and its second against their third: A = 1",
})

C(0xAEF1, {
    0xAEF2: "Node IY takes IX's verb (+0, and +1 without bit 7 but keeping its own bits)",
    0xAF04: "Nothing at IX's +4: done",
    0xAF0B: "IY's +14 to +23 not all empty ($AF38): done",
    0xAF11: "Otherwise IY's first group (+8) moves to its second (+18)...",
    0xAF24: "...and IY takes IX's words from +4 to +13 ($AF52)",
    0xAF2A: "and IX's +2 too if IY has none ($AF56)",
    0xAF38: "Z if the ten bytes from IY + A are all zero",
    0xAF4E: "Copy C bytes from IX + DE to IY + DE: 6...",
    0xAF52: "...10...",
    0xAF56: "...or 2",
})

A[0xDF02]['title'] = "Action record: default for verb 26 (GIVE TO): hand the object over"
A[0xDF02]['desc'] = [
    "The pre-check ($DF24) asks whether the receiver ($A035) can carry the "
    "object as well as what it holds ($C8C6). The body makes the receiver "
    "the object's holder (+1), puts the object in the receiver's room "
    "(+15) and moves everything inside it there too ($D249). Read from the "
    "code; GIVE WATSON LAMP and GIVE YOUR MONEY TO WATSON both end with "
    "Watson holding it (emulator, 8 November)."]
C(0xDF02, {
    0xDF06: "IY = the receiver's record, IX = the object's",
    0xDF0E: "The receiver holds it now",
    0xDF14: "and it is in the receiver's room",
    0xDF1B: "with everything inside it ($D249)",
    0xDF21: "Succeed",
    0xDF24: "Pre-check: can the receiver carry it as well? ($C8C6)",
})
A[0xDF40]['desc'].insert(0,
    "The pre-check ($DF2E, shared with $E135) refuses an object that a "
    "person other than the actor holds ($C8AF). Tried in the emulator "
    "2026-11-08: Watson holds the Daily Chronicle at the start, and "
    "EXAMINE CHRONICLE gets I SEE NO CHRONICLE THAT YOU CAN EXAMINE.")
C(0xDF02, {
    0xDF2E: "Pre-check: is the object held by a person ($C8AF)?",
    0xDF36: "By someone other than the actor: refuse",
    0xDF3D: "Pass",
})

A[0xDC19]['desc'].insert(0,
    "LOOK THROUGH <door>: after the pre-check at $DC6C, finds the exit "
    "through the door ($D46C); if it leads to a room (+2), moves the actor "
    "there for a moment ($DD0B), describes the room with 'YOU CAN SEE' "
    "instead of 'YOU ARE' ($D0DC = 1, $D1B2) and moves it back. "
    "Tried in the emulator 2026-11-08: LOOK THROUGH WINDOWS gets YOU "
    "CANNOT LOOK THROUGH THE WINDOW, LOOK THROUGH DOOR asks WHICH DOOR ?. "
    "The record's first seven bytes are header and arguments, not code.")
C(0xDC19, {
    0xDC20: "Pre-check ($DC6C): fail if not a door",
    0xDC24: "A = the door; find its exit ($D46C)",
    0xDC2A: "+2: the room beyond (none: just succeed)",
    0xDC31: "Remember the current room",
    0xDC35: "'YOU CAN SEE' wording on ($D0DC)",
    0xDC3A: "Move the actor to the room beyond for a moment ($DD0B, B = the room)",
    0xDC3D: "Describe the room it is in now ($D1B2)",
    0xDC44: "Move back to the room it was in",
    0xDC48: "Wording back to normal",
})

C(0xB568, {
    0xB568: "Requirement code 5 (a number): the number is the only candidate",
    0xB56F: "Bit 7 of the slot's word count set: no more candidates (A = $FF)",
    0xB57B: "IX = where the last search stopped ($B180)",
    0xB581: "Need it be here? ($A01D bit 0 -> $A038)",
    0xB589: "Code below 5 (a room): search the rooms ($D39B)...",
    0xB594: "...otherwise the things ($D36A)",
    0xB598: "Next match; A = $FF if there is none",
    0xB59D: "Remember where it stopped",
})
C(0xD39B, {
    0xD39B: "BC = where the last search stopped (a room number in B)",
    0xD3A5: "Next room",
    0xD3A7: "$6A rooms: the end (A = $FF)",
    0xD3AE: "That room's record ($D224)...",
    0xD3B5: "...and its words (+1): do they name the slot's words? ($A4E0)",
    0xD3BC: "A match: if the room need not be next door ($A038), take it",
    0xD3C2: "Otherwise only if it is next to the actor's room ($D471)",
    0xD3CC: "Return it in A, and the search position in IX",
})

C(0xC8EF, {
    0xC8EF: "The direct object ($A034): $FE or $FF (a number, or none) has no record",
    0xC8F6: "Its requirement code ($A00F) below 5: a room ($D224)...",
    0xC905: "...otherwise a thing ($D237)",
    0xC908: "Its record to $A013",
    0xC90C: "The same for the indirect object ($A035, code $A010) into $A015",
})

C(0xC86E, {
    0xC86E: "A = the holder number so far ($FF at the start); IX = the thing",
    0xC874: "Held by nothing ($FF): stop with A = the last holder",
    0xC87C: "Otherwise A' = its holder, and IX = the holder's record ($D237)",
    0xC882: "Keep climbing only if the holder has +5 bit 7 set...",
    0xC888: "...and bit 5 or bit 3 (it lets what is inside be seen)",
    0xC894: "Return the highest holder reached",
})
C(0xD4EF, {
    0xD4EF: "Is the thing's holder (IX+1) the one this listing is for?",
    0xD4F4: "Not the actor's own record",
    0xD4FC: "And the actor can see it ($C821)",
    0xD504: "Its room count (+0) below 2: only a thing in one or no room",
    0xD50B: "Is the actor inside the thing, at any depth? ($D278: carry if so)",
    0xD516: "Not inside it: list it (carry set)",
    0xD518: "No (carry clear)",
})

C(0xA6D3, {
    0xA6D3: "The count n that follows the code",
    0xA6D8: "$A6D1 counts the elements down from n",
    0xA6DC: "A random number from 0 to n - 1 ($D2A4), plus one: the element to print ($A6D2)",
    0xA6E5: "Is this the chosen element?",
    0xA6F0: "Yes: print it (the interpreter, $A5CD)",
    0xA6F5: "Either way skip over it ($A6BB)",
    0xA6FB: "Until all n have been passed",
    0xA6FE: "Back one byte, ready for the next token",
})

C(0xA68C, {
    0xA68C: "Code $0F: the part of the day ($C00C) is 5?",
    0xA694: "Code $14: is it 4?",
    0xA69C: "Code $15: is it 3?",
    0xA6A4: "Code $16: is it 2?",
    0xA6AC: "Code $17: is it 1?",
    0xA6B2: "Not that part: skip the element that follows ($A6BB)",
    0xA6B9: "and print nothing",
})

C(0xCB43, {
    0xCB43: "Is the current actor 0, 1 or $64 ($DC6C: Z if so)? NZ (anyone else): nothing to do",
    0xCB4A: "No current actor for a moment",
    0xCB4E: "A failure ($A00B) to report? If not, skip to the hand-back",
    0xCB54: "HL = a routine to call: none, so narrate the failure ($A00C = 0, $CA76)",
    0xCB5F: "Make the first actor in the table ($9860, the player) current again",
    0xCB67: "A routine to call: with $A027 = 1, call it ($CB40), then $A027 = 0",
})

C(0xBC74, {
    0xBC74: "Walk the case table ($9965) to its $FF end; B counts",
    0xBC81: "Only statements Holmes has been told (+3 bit 0)...",
    0xBC87: "...that can now be proved ($BCC9)",
    0xBC8C: "Remember the last one found ($BA1E)",
    0xBC91: "Next record ($BE5A)",
    0xBC96: "A = how many; IX = the last of them",
})
C(0xBC9C, {
    0xBC9C: "As $BC74, but for the statements that cannot yet be proved",
    0xBCAF: "Told but not provable...",
    0xBCB4: "...the first one is remembered ($BA1E)",
    0xBCBE: "Next group of records ($BE72)",
    0xBCC4: "IX = the first unprovable statement",
})

C(0xE3B8, {
    0xE3B8: "The common checks ($E3F5): busy, already there, will it fit?",
    0xE3BC: "Keep the actor, and take the thing after the cab (its driver) as the actor...",
    0xE3C7: "...and ask $CFB6 (Z: no)",
    0xE3CC: "Actor restored",
    0xE3D0: "No driver step: allowed",
    0xE3D2: "The thing at the cab's +3 ($D237)...",
    0xE3DC: "...must share one of bits 4-6 with the actor's +4 (the AND with $70)",
    0xE3E4: "Otherwise refuse ($DC15)",
    0xE3E7: "Succeed",
})
C(0xE3F5, {
    0xE3F5: "Is the actor busy? ($CBA7)",
    0xE3F8: "Already in or on the thing? ($DCA7)",
    0xE3FC: "IX = the indirect object's record ($A017), IY = the direct's ($A013)",
    0xE404: "Will it fit in or on it? ($DEE4)",
})

C(0x9CA2, {
    0x9CA2: "Thing $55, the burning note",
    0x9CA7: "Not yet revealed (+5 bit 7 clear): nothing",
    0x9CAC: "The countdown at $9CA1: $FF means it has run out already",
    0x9CB3: "One turn less; carry on only when it reaches 0",
    0x9CB5: "Describe the note as BURNT (word $015B in +9/+10)...",
    0x9CBE: "...and clear its +13 and +14",
    0x9CC5: "Case record $99B7: clear bit 1 of +3",
})

C(0x9D95, {
    0x9D95: "Greeting for Holmes (HL = $9D91, C = 0) via $9DC6",
    0x9D9D: "'Well can you prove that ... yet, Holmes ?' via $9DD8",
    0x9DA5: "A word for Watson (C = 3) via $9CE9",
    0x9DAD: "Clear bit 0 of +3 in the three case records at $99E3, $99F1, $99A9 (those statements are not yet told)",
})

C(0x9AF4, {
    0x9AF6: "Can the cab get there from here? ($9B50)",
    0x9AF9: "The fare at 2d a step ($9B25 with DE = 2)",
    0x9AFF: "L = the table's journey time, in minutes (IX+2)",
    0x9B07: "Which is the length of the action ($A01F)",
    0x9B0A: "Clear the 'revealed' flag of the thing named at $E2C6 ($9C60)",
    0x9B12: "Then $DD0E with the same thing and B = 1",
    0x9B19: "The destination's record ($D224)",
    0x9B1C: "Clear bit 6 of its +0",
    0x9B20: "Hand the ride to the vehicle sub-script at $F3AD",
})
C(0xE2EE, {
    0xE2EE: "A = the actor, DE = the script, B and C = the objects",
    0xE2F1: "Direct and indirect objects ($A034, $A035)",
    0xE2F8: "Keep the current actor and make A the actor",
    0xE300: "Find its record ($CC0E, IY)",
    0xE303: "HL = its current script address (+1/+2)",
    0xE309: "Push it as a sub-script call frame ($CF80), so the actor returns to it afterwards",
    0xE30E: "Actor back as it was",
    0xE313: "Point the actor's record at DE: its new script",
    0xE319: "Succeed",
})

C(0xD46C, {
    0xD46C: "Entry for a door: patch the offset in the LD A,(IX+n) at $D48B to 1",
    0xD471: "Entry for a room: patch it to 2",
    0xD47B: "B = the door or room number",
    0xD47D: "IX = the actor's room record ($D33C), past its six header bytes, at its exits",
    0xD486: "Next exit ($D206): Z at the end of the list",
    0xD48B: "Its byte 1 (the door) or byte 2 (the room beyond) against B",
    0xD491: "Z: no such exit; NZ: IX = the exit",
})

C(0xBF1C, {
    0xBF1C: "The statement's subject: thing +0 ... its name words ($A4BC, +7)",
    0xBF25: "Print them ($D3E8)",
    0xBF28: "The relation word, from the table at $994D ($BF45)",
    0xBF2B: "Relation 0: print the word $005D instead",
    0xBF2D: "Print the relation word ($A887)",
    0xBF30: "The statement's object (+2): its name words",
    0xBF3C: "Done",
    0xBF45: "DE = the relation word for relation (IX+1); Z if the relation is 0",
})
C(0xC996, {
    0xC996: "Try the action record in HL ($C9BF)",
    0xC99F: "Carry: it is a script record",
    0xC9A1: "Z: failed - end the actor's go ($CB43)",
    0xC9A4: "NZ: done",
    0xC9A7: "Script record: save the actor's current script as a sub-script frame ($CF80)...",
    0xC9B3: "...and set the actor's script to the new one (HL, in +1/+2 of its record)",
    0xC9BD: "Carry: a script was started",
    0xC9BF: "Header checks: bit 5 of the record's byte 0 and $D078 (dark)...",
    0xC9CE: "...refuse with the message at $CBBB when it is too dark for that action",
    0xC9D3: "The object-requirement checks ($C628, $C6BE)",
    0xC9DD: "Bit 6: run the pre-check routine whose address follows ($CB34)",
    0xC9F2: "Any failure so far ($A00B)?",
})

C(0xE40A, {
    0xE413: "IY = the record at $A017",
    0xE417: "The direct object ($A034)...",
    0xE41A: "...becomes its holder (+1): sitting is being contained by the furniture",
    0xE41D: "Succeed",
    0xE420: "(GET OUT's pre-check, header at $E432) Is the actor busy? ($CBA7)",
    0xE423: "Is the actor inside the thing ($A034), at any depth? ($D278)",
    0xE42C: "No: refuse ($DC15)",
    0xE42F: "Yes: pass",
})
C(0xA793, {
    0xA793: "Keep the current actor in A'",
    0xA798: "$A028 = 0 (the thing is the actor); for $A7AC, 1 (a thing named by the command)",
    0xA79D: "Name them ($A82F): a thing's name words, or YOU ($080E) for $FF",
    0xA7A1: "Z (the player) leaves DE = ARE ($007A)...",
    0xA7A2: "...otherwise IS ($0485)",
    0xA7AC: "Entry for code $11: the direct object ($A034)",
    0xA7B4: "Entry for code $13: the person named in the next parameter ($A66C)",
})

C(0xE432, {
    0xE43B: "The thing the direct object is in (its +1)...",
    0xE442: "...becomes the holder of the record at $A017 (the actor)",
    0xE449: "Succeed",
})

C(0xB308, {
    0xB308: "Keep the direct object's search position ($B17E) and its number-used flag ($B4A2)",
    0xB310: "Start the search again from the top ($B34F)",
    0xB313: "Next candidate for the direct object ($B4C1)",
    0xB318: "One more: $B170 counts them",
    0xB31E: "No more: put the position and flag back",
    0xB325: "A = how many; $B170 cleared again",
    0xB32D: "The same for the indirect object: position $B180, flag $B549, count $B171",
})
C(0xACCC, {
    0xACCC: "E bit 3 clear: no clause finished yet",
    0xACCF: "Skip commas (class $A0)",
    0xACD6: "Remember where this sentence starts: the token position ($A029)...",
    0xACE0: "...the flags in E, the node (IY) and the sentence count ($A012)",
    0xACEE: "'All but' ($A01A = 2): mark the node with bit 6 of +1",
})

C(0xA990, {
    0xA990: "HL = the packed text, C = the bit position (0-7) in the byte at HL",
    0xA991: "DE = this byte and the next, big-endian",
    0xA995: "Shift left C places to bring the letter to the top...",
    0xA9A0: "Advance by five bits: C + 5, with a byte on (HL + 1) when it passes 8",
    0xA9AB: "The top five bits of D (RRCA x3, AND $1F)...",
    0xA9B2: "...plus $60: the letter's code, $60 (a) upwards",
})
C(0xA2BD, {
    0xA2BD: "IX = a verb record. +5's high nibble, brought down...",
    0xA2C7: "...plus +7's high nibble (above it) = $A01E",
    0xA2D0: "+1's high nibble, brought down...",
    0xA2DA: "...plus +3's high nibble (above it) = $A01D",
})

C(0xAEC5, {
    0xAEC5: "One sentence fewer ($A012 is kept in B)",
    0xAEC6: "IX = the node, then IY = the node before it in the list at $9FF0 ($A104)",
    0xAED6: "At the head of the list ($9FF2)? Then stop",
    0xAEE1: "Skip nodes marked with bit 6 of +1 (BUT nodes)",
    0xAEEA: "Entry for the first node: IY = 0, then as above",
})

A[0xDF40]['desc'].insert(1,
    "Body: sets $CAAE = 1, and for the actors $DC6C accepts (0, 1 and $64) "
    "prints the description ($DF5B) and a newline. Tried in the emulator "
    "2026-11-08: EXAMINE LAMP -> 'You examine the oil lamp. You see an oil "
    "lamp.' - a thing with no description message (+13/+14 empty) gets "
    "'You see' + its name + '.'.")
C(0xDF40, {
    0xDF49: "$CAAE = 1",
    0xDF4E: "Only for the actors $DC6C accepts (Z): anyone else passes without printing",
    0xDF52: "Print the description ($DF5B) and a newline ($A2A2)",
    0xDF55: "Newline",
    0xDF58: "Succeed",
    0xDF5B: "IX = the direct object's record",
    0xDF61: "Mark it as seen (+6 bit 6)",
    0xDF65: "Its description message (+13/+14): print it if there is one",
    0xDF70: "None: 'You see' ($68E1)...",
    0xDF76: "...its name ($D3D5)...",
    0xDF79: "...and a full stop",
})
A[0xE135]['desc'].insert(0,
    "EXAMINE CLOSELY. The body, for the player only (actor 0), prints the "
    "description ($DF5B) and then looks the thing up in $E16B, a table of "
    "three-byte entries (thing, message address) ended by $FF: the bed "
    "(76), the window (102), the bridge (57), the drawer (62) and the "
    "corpse (46) each have a longer text of their own. Read from the code.")
C(0xE135, {
    0xE13E: "$CAAE = 1",
    0xE143: "Only the player examines closely: anyone else passes",
    0xE148: "Print the description and the extra text ($E151)",
    0xE14B: "Newline ($A2A2)",
    0xE151: "The thing's own description ($DF5B)...",
    0xE154: "...then look for it in the table at $E16B ($D34E)",
    0xE15E: "Not there ($FF): done",
    0xE161: "Found: print its extra text",
})
A[0xE135]['desc'].append(
    "Confirmed in the emulator 2026-11-08, each in its own room: EXAMINE "
    "CLOSELY BED (room 61) -> 'The bed is unmade and one sheet is crumpled "
    "up on top. In one corner of the sheet is a very small tear.'; CORPSE "
    "(room 88) -> dried blood on the face and 'dark speckled markings that "
    "resemble powder burns' on the right hand; BRIDGE (room 88) -> 'a "
    "small chip in the stone work that is evidently quite new. It looks "
    "like a heavy metallic object has struck it.'; DRAWER (room 72, the "
    "Browns' study) -> 'the drawer has a false bottom.' These are clues "
    "the plain EXAMINE does not give.")

A[0xDC8D]['desc'].append(
    "Confirmed in the emulator 2026-11-08: TAKE LAMP sets the lamp's "
    "holder (+1) to 0, the player; DROP LAMP sets it to $FF, the holder of "
    "the actor, by copying it from the actor's record ($A017). Dropping "
    "is just being held by what holds you.")
C(0xDC8D, {
    0xDC91: "IX = the direct object's record, IY = the actor's ($A017)",
    0xDC99: "The object's holder (+1) becomes the actor's holder",
    0xDC9F: "Succeed",
    0xDCA7: "Is the actor inside the object ($D278)?",
    0xDCB0: "Yes: refuse ($DC15)",
})
C(0xDC7B, {
    0xDC7D: "Only the actors $DC6C accepts (Z); anyone else passes",
    0xDC81: "Newline",
    0xDC84: "The room the player is in ($A00A): describe it in full ($D102)",
    0xDC8A: "Succeed",
})

A[0x8259]['desc'].append(
    "CORRECTION 2026-11-08: bits 7 and 6 of $A01D are read, by $C493 and "
    "$C4B2, which set the requirement codes $A00F (direct object) and "
    "$A010 (indirect object): no direct object (bit 3 clear) -> 0; bit 7 "
    "set -> 4; both number bits of $A01E (bits 2-3) set -> 5; otherwise "
    "7. The indirect object is the same with bit 2, bit 6 and $A01E bits "
    "0-1. So bit 7 (ENTER, GO INTO, the GO TOs) and bit 6 (TAKE TO) make "
    "that object's requirement code 4 - the code $C6BE treats after the "
    "room codes - instead of an ordinary thing (7). Only bit 6 of $A01E "
    "is still unread.")
C(0xC493, {
    0xC493: "Requirement 0: no direct object",
    0xC497: "$A01D bit 3 (a direct object) clear: store 0",
    0xC49B: "Requirement 4...",
    0xC49D: "...if bit 7 is set",
    0xC4A1: "Else: both of $A01E's bits 2-3 set (a number)?",
    0xC4A8: "Yes: requirement 5",
    0xC4AC: "No: 7, an ordinary thing",
    0xC4AE: "Store at $A00F",
    0xC4B2: "The same for the indirect object: bit 2, bit 6, $A01E bits 0-1, into $A010",
})

C(0xB4A3, {
    0xB4A3: "$B4A2 = $FF means the number has not been used yet; anything else: go on to the thing search ($B4CF)",
    0xB4A9: "Used now ($B4A2 = 0)",
    0xB4AC: "The slot's first word ($B173): bit 7 set means a number",
    0xB4B3: "The direct object is $FE: a number...",
    0xB4B8: "...with its value, from the word at $B172, in $A02F",
    0xB4BE: "NZ: a candidate",
})

C(0xB54A, {
    0xB54A: "The same for the indirect object: $B549 = $FF means the number is unused; otherwise the thing search ($B576)",
    0xB550: "Used now",
    0xB553: "The slot's first word ($B179): bit 7 set means a number",
    0xB55A: "The indirect object is $FE: a number...",
    0xB55F: "...with its value, from $B178, in $A031",
    0xB565: "NZ: a candidate",
})

C(0xE003, {
    0xE007: "A = 0: the actor turns back into thing 0 ($E03A)",
    0xE00B: "The disguise (the direct object) is no longer held by anyone (+1 = 0)...",
    0xE013: "...and lies in the room the player is in (+15)",
    0xE01C: "Pre-check for TAKE OFF: the actor must be the player (A = 0)",
    0xE026: "WEAR: A = 1, the actor becomes thing 1 ($E03A)",
    0xE02B: "The disguise is taken out of the world: no holder, no room",
    0xE03A: "C = the new identity; the current actor's record ($CC0E) gets it as +0",
    0xE044: "IY = the old body ($A017), IX = the new one; $A017 now points to it",
    0xE050: "The new body takes over the old one's holder (+1) and room (+15)",
    0xE056: "The old body is held by nothing ($FF) and in no room",
    0xE064: "For everything from 1 to $6D: if the old actor holds it...",
    0xE077: "...the new body holds it",
    0xE07C: "Walk ($CFB6) the records it yields and set their +0 to C, until it returns Z",
    0xE086: "The current actor ($A036) is now the new body",
})

C(0xE1B2, {
    0xE1B4: "Is the indirect object ($A035) the bloodstained clothes ($43)?",
    0xE1BB: "Can the actor see them ($C821)?",
    0xE1C0: "No: print the refusal ($E1FC) and fail ($DC15)",
    0xE1C6: "Yes: the actor's identity becomes thing $5F, Mrs Jones ($E03A)...",
    0xE1CB: "...and the case record at $998F gets bit 1 of its +3 (Tricia Fender turns out to be Mrs Jones)",
    0xE1D3: "Succeed (also when it was not the clothes)",
})

C(0xDD61, {
    0xDD65: "IX = the exit found by the pre-check; its direction (+0) becomes the plan's direction register ($9FD7)",
    0xDD6B: "Succeed",
    0xDD6E: "Pre-check: the direct object is a room; find the exit to it next to the actor ($D471)",
    0xDD76: "No such exit: refuse ($DC15)",
    0xDD79: "Its direction must be below 11, a compass direction (not UP or DOWN...)",
    0xDD7E: "Otherwise refuse",
})
C(0xE6E6, {
    0xE6EA: "IX = the record $CFB6 yields...",
    0xE6ED: "...its +3 becomes the direct object ($A034)",
    0xE6F3: "Succeed",
    0xE6F6: "Pre-check: the actor must not be the direct object itself",
    0xE700: "And the direct object's holder (+1) must be the actor's number less 1; else refuse",
})

C(0xDF8B, {
    0xDF8D: "The burning note's countdown ($9CA1): already 0? Then nothing to change ($E000)",
    0xDF93: "Still burning: stop the countdown ($FF)...",
    0xDF98: "...and change the name word (+9/+10) of the direct object, the note, to SINGE ($07D5)",
})

C(0xA7EB, {
    0xA7EB: "Indefinite table $A24D: THE, A, AN, SOME",
    0xA7EE: "Unless $A027 or $A2AA is set...",
    0xA7F8: "...then table $A255: THE, THE, THE, SOME (a definite narration)",
    0xA7FB: "The article code is the top nibble of D; two bytes an entry",
    0xA806: "DE = the word; print it ($A887)",
})
C(0xB6AE, {
    0xB6AE: "Indirect object requirement 5 or 6 (a number): YOU CANNOT ... ($B671)",
    0xB6B9: "The indirect object slot's first word ($B179): bit 7 set (a number): the same",
    0xB6C0: "Count in $B16E: bit 0 set means a noun was typed",
    0xB6C8: "Then copy the name words at $B178 for the message ($B6F0)",
    0xB6CB: "Print the start of the message ($B62F)",
    0xB6CE: "Finish it using the indirect slot",
})

C(0xDAC6, {
    0xDAC6: "A pound sign ($60 in the game's character set): read an amount of money ($DB67)",
    0xDACB: "A digit? ($DAE8)",
    0xDACE: "Yes: read a number ($DAEF)",
    0xDAD1: "A full stop: class $B0 (end of a command)",
    0xDAD7: "A comma: class $A0",
    0xDADB: "A double quote: class $90 (starts or ends a quotation)",
    0xDADF: "Anything else: carry on with the caller (RET NZ)",
    0xDAE2: "Past the character; class in A, value 0",
    0xDAE8: "Carry clear if A is a digit ('0' to '9')",
})

C(0xACA6, {
    0xACA6: "E bit 6 (a first object is waiting to be stored)?",
    0xACAA: "Yes: clear it; the pattern goes to the node's +4 (first object)",
    0xACB2: "Otherwise E bit 7 (a second object)? If neither, return",
    0xACB5: "Clear it; the pattern goes to the node's +14",
    0xACBB: "HL = node + offset; copy the ten-byte pattern from $AAA8",
    0xACC9: "NZ: stored",
})

C(0xDC57, {
    0xDC5B: "IX = the exit through the door (pre-check $DCA8): its direction (+0)...",
    0xDC5E: "...becomes the verb ($A033): the command turns into GO <direction>",
    0xDC61: "No direct object ($A00F = 0, $A034 = $FF)",
    0xDC69: "Carry on as the movement action does ($DD07)",
})
C(0xA80E, {
    0xA80E: "Print the word's preceding space/capital handling first ($A7D0)",
    0xA813: "Class $50 (a noun) is put in the top nibble of D",
    0xA81D: "Nothing there (D and E zero apart from the class)? Return",
    0xA821: "Print the word ($A887)",
    0xA824: "Note the print state of the word's last letter ($A7EA) in $A026",
})

C(0xC0DF, {
    0xC0DF: "Keep the block's length (DE) and start (IX) at $C109/$C10B",
    0xC0E7: "Print 'PLAY SAVED GAME TAPE TO BE LOADED' ($C1CB)",
    0xC0ED: "Read a 17-byte header into $C0FE with the ROM's LD-BYTES ($0556, A = 0: a header)",
    0xC0F7: "(carry clear: no header read - try again)",
    0xC0FC: "Then read the block itself ($C089, A = $FF)",
})

C(0xE370, {
    0xE374: "Can the actor afford it? ($E34F; if not, message $683F and fail) HL = what is left",
    0xE377: "Store it as the actor's money ($E38F)",
    0xE37A: "The indirect object ($A035), the payee...",
    0xE37D: "...does it hold money? ($E619, IX = its purse; Z: no, nothing to add)",
    0xE382: "HL = its money ($E39C), DE = the sum ($E3A9)",
    0xE388: "Add and store ($E38F)",
})
C(0xE328, {
    0xE34F: "The current actor's purse ($E619); none (Z): cannot pay",
    0xE357: "HL = its money, DE = the sum in the command",
    0xE35E: "HL - DE: less than nothing? (carry): cannot pay",
    0xE365: "Message $683F and fail",
})
C(0xE5FD, {
    0xE619: "A = a holder. Look through things 1 to $6D...",
    0xE624: "...for one that this holder holds (+1)...",
    0xE62A: "...and whose name is MONEY ($0575): found with IX = the purse (NZ)",
    0xE61E: "None: Z",
})

C(0xE654, {
    0xE65B: "Pre-check: does the actor hold a purse? ($E619) No: refuse",
    0xE661: "HL = its money ($E39C)",
    0xE664: "Negative: refuse",
    0xE669: "Nothing in it: refuse",
    0xE66E: "Pass: it holds some money",
    0xE676: "(Second record, header $E66F) the same lookup...",
    0xE679: "...no purse: pass",
    0xE67B: "A purse: refuse unless it is empty",
})
C(0xEAF6, {
    0xEAF8: "The direct object's number ($A034)...",
    0xEAFB: "...becomes the holder (+1) of the indirect object's record ($A015)",
    0xEAFF: "Both are placed in room $32 (+15)",
    0xEB0E: "Succeed",
})

C(0xD5D3, {
    0xD5D3: "Table $D5C9: IN, ON, BEHIND, UNDER, TIED",
    0xD5D6: "The thing's +4 bits 0-2: how it is held (1-5)",
    0xD5DB: "Z when it is 5, TIED",
    0xD5DE: "Print the word for it ($A880)",
    0xD5E8: "Not TIED: done",
    0xD5E9: "TIED is followed by TO ($08DB)",
})
C(0xA360, {
    0xA360: "Keep the current actor; compare it with the remembered one ($A35E)",
    0xA368: "A = 0, the player: not the remembered actor - narrate as the player",
    0xA36C: "The same: forget the remembered actor ($A35E = 0)",
    0xA36D: "Either way the actor is 0 while the remembered command is narrated ($A37D)",
    0xA377: "Restore the actor; return Z",
})
C(0xBE72, {
    0xBE72: "B counts the nesting depth of the group",
    0xBE75: "C = this case record's byte 3; step IX on ($BE5A)",
    0xBE7B: "Bit 3 closes a level (not below zero)",
    0xBE84: "Bit 2 opens one",
    0xBE8B: "Until the depth is back to zero",
})

C(0xA490, {
    0xA490: "HL = the number in B (0-255)",
    0xA496: "The hundreds digit ($A480, with a leading zero suppressed)",
    0xA49C: "The tens digit",
    0xA4A2: "The units digit, always printed",
    0xA4AB: "(Next routine) HL = the address of room A's name words, +1 into its record ($D224)",
})
C(0xA51B, {
    0xA51B: "A zero word at HL ends the comparison (Z unset)",
    0xA521: "The low nibbles of the two high bytes must agree...",
    0xA529: "...and the low bytes: a 12-bit match",
    0xA52E: "Either way both pointers move on two bytes",
})
C(0xA104, {
    0xA104: "Start after the list head's own link",
    0xA108: "HL = the link (the next node's address) at IY - 2",
    0xA110: "Is it node DE? Then IY is the node before it",
    0xA114: "No: step to that node and look again",
})

C(0x9F1E, {
    0x9F1E: "Store A at HL",
    0x9F1F: "The actor's own record ($A017): its room (+15) = B...",
    0x9F26: "...and held by nothing (+1 = $FF)",
    0x9F2A: "The actor's next turn (IY+6/+7) is DE minutes later",
})
C(0x9CCE, {
    0x9CCE: "B = the room of the actor's own record ($A017)",
    0x9CD6: "IX = thing C: is it in the same room? If not, return NZ",
    0x9CDE: "Same room: can the player see it ($C821 with A = C)?",
    0x9CE2: "Not visible: NZ",
    0x9CE4: "Visible: Z",
})

C(0xC542, {
    0xC542: "No indirect object wanted ($A010 = 0): no guessing - Z",
    0xC547: "One was typed ($A035 is not $FF): no guessing - Z",
    0xC54E: "None typed: $A01D bit 1 set means the verb can do without",
    0xC555: "Otherwise NZ: guess one",
    0xC558: "Return Z",
    0xC55A: "Guess: if no guess is wanted, just run the checks ($C929)",
    0xC560: "Try each candidate in turn ($C45E, B counts from 0)...",
    0xC568: "...making it the indirect object ($A035) until the record's checks pass ($C929)",
})
C(0xBE5A, {
    0xBE5A: "Step IX four bytes on...",
    0xBE62: "...and two more if the record's last byte has bit 5 or bit 4 set (a routine address follows)",
})

C(0xB0AC, {
    0xB0AC: "The clock ($9FDD, minutes elapsed) back to 0...",
    0xB0B2: "...and the player's turn time (record at $9860, +6/+7) to 0",
    0xB0BC: "The action takes 1 minute ($A01F)",
    0xB0C0: "$A0DA = 1 (a saved game is to be loaded); NZ",
})
C(0xA1AF, {
    0xA1AF: "HL = the first node",
    0xA1B5: "HL = this node's link (IX-2)",
    0xA1BB: "Free this node ($A1C7)",
    0xA1C1: "Until the link is 0",
})

C(0xA621, {
    0xA621: "Control code A: HL = the handler from the table at $A55D, two bytes each",
    0xA62F: "Codes below $1D: call it and carry on with the same message",
    0xA633: "$1D and above end the message: call it, then Z goes on to $A5ED, NZ to $A5EA",
    0xA63A: "(Print the character in A and succeed)",
    0xA63F: "Code $1D: class $60 - end with a newline and no full stop",
    0xA643: "Code $1E: class $30 - end with a full stop and a newline",
    0xA647: "(Called for the last word of a message, class in D) print the word first ($A887)",
    0xA64A: "A = '.'",
    0xA64C: "Class bit 6 ($60): skip the full stop, newline",
    0xA650: "Class bit 4 ($30): full stop...",
    0xA655: "...and a newline ($A2A2)",
    0xA65A: "Neither: also the handler for code $1F, which does nothing",
})

C(0xDD84, {
    0xDD88: "The direct object's holder (+1) goes into plan register $9FD6",
    0xDD8E: "Succeed",
    0xDD91: "Pre-check: the direct object's holder...",
    0xDD98: "...must not be $FF (held by nothing): refuse ($DC15) if it is",
})
C(0xB4FD, {
    0xB4FD: "Next thing or room named by the direct-object slot ($B172, via $B4A0)",
    0xB503: "None left ($FF): return Z",
    0xB506: "It becomes the direct object ($A034)",
    0xB509: "Does the verb's check reject it? ($B517) Then try the next",
    0xB50E: "Accepted: A = it, and $B16D bit 1 notes that something was found",
})

C(0xDD9E, {
    0xDDA3: "Is the direct object an actor with a record ($CC0E)? A = 0 if not, 1 if so",
    0xDDAE: "Hand the quoted words on ($B86A)",
    0xDDB1: "Succeed",
    0xDDB8: "(Next record's pre-check) only if the actor is not busy ($CBA7)",
})

C(0xB387, {
    0xB387: "Does the verb take an indirect object ($A01D bit 2)? If not: Z, nothing to check",
    0xB38D: "The slot has a noun phrase ($B16E bit 0): NZ",
    0xB393: "None typed: the verb can do without ($A01D bit 1)? Z, fine",
    0xB397: "Otherwise NZ: one is missing",
})
C(0xD1C6, {
    0xD1C6: "IY = the room record + 1 (its name words)",
    0xD1D1: "$A028 = 0",
    0xD1D5: "Print the name ($D405)",
})

C(0xD898, {
    0xD898: "The time limit ($A03B) = $0BB8 = 3000",
    0xD89E: "$A027 = 1 while the line is read ($D8AD)...",
    0xD8A8: "...and 0 afterwards, keeping the result",
})
C(0xD7E1, {
    0xD7E1: "$D7E0 set (the line did not parse): clear it, throw the rest of the line away ($D88A) and fail",
    0xD7F1: "Otherwise: any sentence left ($9FF2)? NZ if so, else fail ($DC15)",
})

C(0xF1C1, {
    0xF1C1: "IX = thing A's record",
    0xF1C4: "Its state word (+9/+10) = DE",
    0xF1CA: "+8: keep the low nibble, replace the high nibble with B",
    0xF1D3: "Succeed",
})
C(0xC1A8, {
    0xC1A8: "DE = the text, HL = screen address $5041 (row 18)",
    0xC1AC: "C = pixel shift 0",
    0xC1AE: "A space first ($C388 prints a character)",
    0xC1B3: "Then B characters from DE",
    0xC1BA: "And a space after",
})

C(0xA7D0, {
    0xA7D0: "$A7EA = 0: the word is not YOU",
    0xA7D4: "Bit 7 of D clear: print the article by code ($A7EB)",
    0xA7D8: "Is the word reference $09EE (YOU)? Then print nothing",
    0xA7E4: "Otherwise note a word that is not YOU ($A7EA = 1) and return",
})
C(0xA25D, {
    0xA25D: "B = thing A",
    0xA25F: "Only when $A011 is set...",
    0xA265: "...and there is a list at $A0D8...",
    0xA270: "...look A up in it ($D34E): CP $FF gives Z if it is not there",
})
C(0xA745, {
    0xA745: "No carry (from the caller's compare): a thing - go to $A751",
    0xA747: "Carry: a room: HL = its name words ($A4AB), print them ($A7BA)",
    0xA751: "A thing: HL = its name words ($A4BC), print them ($A7C5)",
    0xA759: "Return A = 0",
})

C(0xD99E, {
    0xD99E: "Anything already typed ($A01B set)? Then '@' is an ordinary character ($D8C3)",
    0xD9A5: "$D714 = 1: use the last word list again",
    0xD9AC: "Rub out the '@' just printed: two backspaces ($08)",
})
C(0xAE6A, {
    0xAE6A: "Go to the last node of the list ($AEEA)",
    0xAE6D: "Allocate a node of $1E bytes ($A11C)",
    0xAE72: "Link it after the last: the old last node's link (IY-2)...",
    0xAE7B: "...points to it; IY = the new node",
})
C(0xB9FA, {
    0xB9FA: "Find the node before IX in the list at $9FEE ($A104)",
    0xBA04: "Unhook IX: the previous node's link = IX's link",
    0xBA10: "Free it ($A1C7)",
})

C(0xCA60, {
    0xCA60: "$CAAE = 0 (see EXAMINE: set to 1 when the action itself prints what is seen)",
    0xCA64: "Run the action's body ($CB2C), keeping its result",
    0xCA69: "Has the player's view changed? Describe the room if so ($CA7F)",
    0xCA6C: "Unless the action printed its own report ($CAAE) ...",
    0xCA70: "...give the standard report ($CAAF)",
    0xCA76: "Print a newline unless the verb has bit 7 set in $A033 ($A2E4)",
    0xCA7F: "The player's room (+15) against $A009: equal, return",
    0xCA8C: "Otherwise, as the player (the first actor, $9860), describe the room ($CA9E)",
})
C(0xA75B, {
    0xA75B: "Code $0B: IX is the control code; HL = IX + the offset in its next two bytes",
    0xA766: "Print that message ($A5C4), then move IX past the operand",
    0xA771: "Print the message whose address follows the next parameter ($A66C)",
    0xA780: "A = the current actor: $A783 gives DE = YOUR ($09F2) for the player, HIS ($0414) for anyone else",
    0xA78E: "The same for the direct object ($A034)",
})
C(0xA6BB, {
    0xA6BB: "Skip one message element. Bit 7 set: a two-byte word reference...",
    0xA6C2: "...codes 2 and $0B take two operand bytes (three in all)...",
    0xA6CE: "...any other code is a single byte",
})

C(0xF389, {
    0xF389: "IX = the direct object's record",
    0xF38D: "Its holder (+1) must be the actor's number less 1; else refuse ($DC15)",
    0xF397: "And the actor must not be the direct object itself",
    0xF39F: "Pass",
})
C(0x9ACB, {
    0x9ACD: "Work out the route's time as GO TO does ($9AA3); no route: refuse",
    0x9AD3: "Twenty minutes less: L - $14",
    0x9AD7: "The thing named at $E2C6 is $6D (109)...",
    0x9ADC: "...and the shared-action code is $69; carry on as $9B04 does",
})
C(0xA83A, {
    0xA83A: "Convert the common-word byte ($A840) and print it as a word reference ($A5EA)",
    0xA840: "Index = A - $60; the list of words is at $67B7, two bytes each",
    0xA84D: "High byte + $50: class $50, as for a noun",
})

C(0xD237, {
    0xD237: "The thing index at $8B6F: three-byte entries (id, record address)",
    0xD23B: "Find id A in it ($D34E)",
    0xD23E: "IX = that entry's record address (+1/+2)",
})
C(0xD2F2, {
    0xD2F3: "B = 0; C = 0, the running total",
    0xD2FB: "Add up everything in thing A, to any depth ($D305)",
    0xD2FE: "Return the total in A",
})
C(0xD57C, {
    0xD57C: "Next thing in the place ($D21C); Z at the end: return with carry set",
    0xD585: "Is it listable ($D4EF)? Carry: no, try the next",
    0xD58B: "Found: A = its id; Z if it is thing 0",
})

C(0xCA9E, {
    0xCA9E: "A = the room number ($DD01); HL = the room's record address ($DCFF)",
    0xCAA4: "Its +0 bit 6 (visited) set: describe it briefly ($D1B2)",
    0xCAA9: "First visit: mark it visited and describe it in full ($D102)",
})
C(0xD102, {
    0xD102: "Save the registers around the description proper ($D113)",
    0xD113: "B = the room; its record ($D224)",
    0xD11F: "The actor's top-level container ($C863): $FF - the actor is in nothing",
    0xD12F: "Otherwise message $68DD, then the way it is held ($D5D3) and its name ($D3D5) follow",
})

C(0x9D30, {
    0x9D30: "$9D90 (Lestrade has been introduced) clear: nothing to say",
    0x9D35: "Speak to thing 0 (C = 0, the player) via $9CE9 with the countdown at $9D2E",
    0x9D3D: "and to thing 3 (Watson) with the countdown at $9D2F",
    0x9D48: "(Next routine) the opposite: until $9D90 is set...",
    0x9D4D: "...tell things 0, 3 and 7 (C) that they must wait, using the countdowns at $9D45-$9D47...",
    0x9D65: "...each once: $9CF2 sets the speaker, the flag becomes 1 and message $6D9A is printed",
})
C(0x9CE9, {
    0x9CE9: "$9CF2 sets up who is being spoken to; if it returns, print message $6929",
    0x9CF2: "The thing to talk to (C) becomes the direct object ($A034)",
    0x9CF6: "Is it in the actor's room and visible to the player ($9CCE)?",
    0x9CFB: "Not so: one less on its countdown (not below zero)",
    0x9D00: "...and skip the caller's print (the stack is dropped)",
    0x9D02: "Visible: only when the countdown is 0...",
    0x9D06: "...then reset it to a random 30 to 44 ($D2A4 with range 15, plus 30)",
})
C(0x9E74, {
    0x9E74: "Output on ($5C3C = 1)",
    0x9E79: "Print the message in HL ($A59F)",
    0x9E7C: "Wait for a key ($C306)",
    0x9E7F: "Clear the text window: 18 newlines ($A296)",
    0x9E82: "Get ready to load a saved game ($B0AC)",
})

C(0xD3D5, {
    0xD3D5: "IY = the thing's record + 7: its name words",
    0xD3E1: "Print them ($D3E8)",
})
C(0xD5FB, {
    0xD5FB: "Table $D062: the words for the directions, two bytes each",
    0xD601: "A with bit 7 cleared is the direction number (1 = NORTH...)",
    0xD607: "DE = the word",
})

C(0xF5FB, {
    0xF5FB: "B = E (y), C = D (x): the ROM's pixel address routine ($22AA) gives HL = the screen byte, A = the bit position",
    0xF601: "Turn the position into a mask: one bit rotated into place",
    0xF609: "Return the screen byte in HL and the mask in A",
})
C(0xD968, {
    0xD968: "The last character typed: a full stop? Then done",
    0xD96E: "Else put one after it, count it, and echo it ($A9B7)",
    0xD976: "Step HL past the end",
})
C(0xB0C6, {
    0xB0C6: "Only at the start of a sentence ($AFE1)",
    0xB0C9: "The action takes 1 minute",
    0xB0CF: "$A0DA = 2: save the game at the end of the minute's walk",
    0xB0D4: "Carry on parsing ($B015)",
    0xB0D7: "(Load) set up the block ($B0EE) and read it from tape ($C0DF); carry clear: again",
    0xB0DF: "Restore IY from the loaded game ($9FD4)",
    0xB0E4: "(Save) keep IY at $9FD4, set up the block and write it to tape ($C040)",
})

C(0xC898, {
    0xC898: "Swap IX and IY ($C89E), climb the chain ($C86E), swap them back",
    0xC8A7: "A = byte 0 of the thing's record, less 1 (Z if it was 1)",
    0xC8AF: "IX = the thing's record ($D237)",
    0xC8B2: "Its holder (+1): $FF - held by nothing - return Z",
    0xC8B8: "Is the holder a person (+5 bit 6)? NZ: yes, return",
    0xC8BC: "Otherwise climb to the holder and ask again",
})
C(0xD770, {
    0xD770: "The next token's class (the word list pointer $D6BD)...",
    0xD776: "...is $C0 (the end of the line): fail ($DC15)",
    0xD77B: "Otherwise pass",
})
C(0xD87D, {
    0xD87D: "The sentence list ($9FF0) becomes empty; free all its nodes ($A1AF)",
    0xD88A: "The same for the rest of the line ($9FF2)",
})
C(0xC989, {
    0xC989: "Keep IX; HL = the numbered action record",
    0xC98D: "Fill in the object records ($C8EF) and run it ($C996)",
})

C(0xBF08, {
    0xBF08: "Step over the first case record ($BE5A)",
    0xBF0B: "Bit 3 (the last of the group) noted in the flags",
    0xBF10: "Is this record's evidence satisfied? ($BE91)",
    0xBF13: "Not: Z result, stop",
    0xBF18: "Satisfied: go on to the next record unless that was the last",
})
C(0xF103, {
    0xF105: "Case record $996F (Major Ffoulkes visited the opium den): bit 1 of +3 set - the statement is established",
    0xF10D: "Succeed",
})
C(0xA711, {
    0xA711: "Code $05: the case statement at the next parameter ($A66C) in IX",
    0xA719: "Print it ($BF1C)",
    0xA720: "Code $06: name the current actor ($A036) with $A028 = 0 ($A82F)",
    0xA72C: "Code $07: name the direct object ($A034) with $A028 = 1",
    0xA736: "Code $08: print the character in A",
    0xA73B: "Code $09: name the indirect object ($A035) with $A028 = 1",
    0xA751: "Name thing A (a thing: $A4BC, $A7C5)",
})

_CODES = {
    0x00: "print the thing whose address is the next parameter",
    0x01: "print the next parameter as a word",
    0x05: "print the case statement at the next parameter",
    0x06: "name the current actor",
    0x07: "name the direct object",
    0x08: "print the character in A",
    0x09: "name the indirect object",
    0x0A: "pick one of the next n elements at random",
    0x0B: "print a message at an offset from here",
    0x0C: "YOUR for the player, HIS for anyone else (the actor)",
    0x0D: "print the character in A",
    0x0E: "YOUR for the player, HIS for anyone else (the direct object)",
    0x0F: "only in part of the day 5",
    0x10: "name the actor with the verb form (ARE / IS)",
    0x11: "name the direct object with the verb form",
    0x13: "name the person in the next parameter with the verb form",
    0x14: "only in part of the day 4",
    0x15: "only in part of the day 3",
    0x16: "only in part of the day 2",
    0x17: "only in part of the day 1",
    0x18: "narrate the remembered command",
    0x19: "print the message at the next parameter",
    0x1D: "end the message, no full stop, with a newline",
    0x1E: "end the message with a full stop and a newline",
    0x1F: "does nothing",
}
A[0xA55D]['desc'].append(
    "What the handlers do, from reading them (2026-11-08; codes not "
    "listed were not worked out): " +
    "; ".join(f"${k:02X} {v}" for k, v in sorted(_CODES.items())) + ".")

C(0xA94D, {
    0xA94D: "Spell dictionary record HL: the front part first ($A95B), then a suffix if there is one ($A92F)",
    0xA95B: "IX = the spelling buffer $5C42; HL past the record's first byte",
    0xA961: "The second byte: bit 7 set means two more bytes follow (a suffix reference)",
    0xA96A: "Bits 4-6: how many letters are kept from the previous word - IX steps over them",
    0xA977: "The low nibble: how many new letters follow, five bits each ($A990)",
    0xA97C: "Unpack a letter and store it",
    0xA986: "Terminate the spelling with 0",
})
C(0xCC29, {
    0xCC29: "The current actor ($A036): its thing record ($D495)",
    0xCC2F: "Keep the record at $A017 and the room (A) at $A00A",
})

C(0xA66C, {
    0xA66C: "The message printer's parameter pointer ($A59D)",
    0xA66F: "DE = the next parameter word; the pointer moves on two bytes",
    0xA676: "NZ",
})
C(0xA0F7, {
    0xA0F7: "HL = IX's link (IX-2), the next node; A = 0 and Z at the end of the list",
    0xA100: "IX = the next node",
})
C(0xAEA9, {
    0xAEA9: "As $A0F7 but for IY: IY = the next node, Z at the end",
    0xAEB6: "Step on over nodes marked with bit 6 of +1 (BUT nodes); B is one fewer",
})
C(0xB90E, {
    0xB90E: "Find the current actor's waiting order or remark ($B91F)",
    0xB911: "Keep it ($B866)",
    0xB915: "IY = the sentence node it points to (+5/+6)",
})

C(0xD51A, {
    0xD51A: "Keep IY, DE and BC around the list ($D526)",
    0xD528: "Start at the beginning of the things in place A ($D04F)",
    0xD52C: "The next listable thing ($D57D); carry: the end of the first pass",
    0xD531: "Mark it listed (+6 bit 7), name it ($D3D9) with $A028 = 0",
    0xD53C: "One fewer to go (C): the last prints the full stop ($A414)...",
    0xD546: "...the second to last prints AND ($005D)...",
    0xD54A: "...and the rest a comma",
    0xD55B: "Second pass: for each thing that holds others ($D4CC), say how ($D590) and list what it holds (recursively, $D526)",
})
C(0xCE83, {
    0xCE83: "IY = the current plan's actor record ($9FDB); HL = IX = the current plan instruction ($9FD9)",
    0xCE8D: "A = its first byte",
})
C(0xB772, {
    0xB772: "The dictionary's class table at $5DBF: one byte per word, indexed by DE & $0FFF",
    0xB77A: "The class is its high nibble",
})
C(0xD0D0, {
    0xD0D0: "Store word HL, with bit 7 of its high byte set, big-endian at $68DE in the YOU ARE message",
})

C(0xEB19, {
    0xEB1B: "Case record $9997: is bit 1 of its +3 set (the statement is established)?",
    0xEB1F: "HL = 0; the result is NZ if it is set, Z if not",
})
C(0xE488, {
    0xE48A: "The direct object's room (+15)...",
    0xE491: "...goes into plan register $9FD6",
    0xE494: "Succeed",
})
C(0xF1F6, {
    0xF1F8: "Set bit 7 of the direct object's +5 (the bit $C821 tests for visibility)",
    0xF200: "Succeed",
})
C(0xEBD5, {
    0xEBD7: "The direct object's number plus 1...",
    0xEBDB: "...goes into plan register $9FD6",
    0xEBDE: "Succeed",
})


# --- $B191 parse a sentence: line comments (2026-11-08; read from the code,
# --- the results/messages checked against the descriptions of the helpers) ---
C(0xB191, {
 0xB191: "No direct object and no indirect object yet ($FF)",
 0xB196: "($A034 = direct, $A035 = indirect)",
 0xB199: "HL = the parser's work space ($B16D)",
 0xB19C: "17 bytes of it",
 0xB19E: "Clear them ($A2AB)",
 0xB1A1: "Match the words against the verb patterns ($B39D)",
 0xB1A4: "Matched: carry on",
 0xB1A6: "No match: the 'I do not know the verb' routine ($B84C)...",
 0xB1A9: "...and Z to say so",
 0xB1AB: "Matched: work out the verb number from IX",
 0xB1AD: "Offset of the matching pattern from $8259 (HL = IX)...",
 0xB1B0: "...",
 0xB1B3: "...",
 0xB1B5: "First record: verb 1",
 0xB1B7: "Otherwise count 8-byte steps",
 0xB1BA: "One more verb number",
 0xB1BF: "Save the verb number in $A033",
 0xB1C2: "And the pattern's address, for the questions at $B5D3",
 0xB1C6: "Verb 46 (TALK TO)?",
 0xB1CA: "If so, copy six bytes between $A002 and the object slot $B172; bit 0 of $B16D picks the direction",
 0xB1DD: "Set the requirement codes for the direct and indirect object from the verb's flags ($C493, $C4B2)",
 0xB1E3: "Did the first word carry the flag in bit 7?",
 0xB1E9: "If not, take it from the saved copy at $B39C...",
 0xB1EF: "...and restart the direct-object search ($B34F)",
 0xB1F2: "Verb flag $A01E bit 4 kept in $B190 (lets the search stop at the first candidate)",
 0xB1FA: "Set: forget the $A01C flag",
 0xB200: "Clear $A00B",
 0xB204: "Does the verb take a direct or indirect object ($A01D bits 2-3)?",
 0xB209: "Yes: go and find them",
 0xB20B: "No objects needed (or all found): check the record ($C929)",
 0xB20E: "Passed: return NZ",
 0xB20F: "Failed: hand back the 'check the record' stub ($B863)",
 0xB213: "Does the verb take an indirect object, and was one given ($B387)?",
 0xB216: "NZ: go and deal with it ($B280)",
 0xB218: "Was the direct object marked?",
 0xB21E: "If not, run the direct-object search to the end ($B308)",
 0xB221: "Found none: look at the fallbacks at $B259",
 0xB224: "Next direct-object candidate ($B4C1)",
 0xB227: "No more: finish",
 0xB229: "Is it here and fit to use ($C929)?",
 0xB22C: "No: try the next",
 0xB22E: "Yes: remember it as the one so far ($B184)",
 0xB234: "Count candidates in $B170",
 0xB238: "Stop at the first if the verb says so ($B190)",
 0xB23E: "Or if the marked-object flag is clear",
 0xB244: "Restore the first candidate into $A034",
 0xB24A: "How many candidates were there?",
 0xB24E: "None: $B259",
 0xB250: "Exactly one: the checks at $B20B",
 0xB254: "More than one: the 'too many' message ($B5E2)...",
 0xB257: "...with Z",
 0xB259: "No direct object found: verb TALK TO is the exception",
 0xB25E: "Any other verb: error $B65F",
 0xB260: "TALK TO with a marked object or words given: error too",
 0xB266: "(bit 0 of $B16D = the slot already holds words)",
 0xB26D: "TALK TO with nothing said: clear the 6-byte slots...",
 0xB270: "...at $B172,",
 0xB273: "...$B174",
 0xB276: "...and $B176",
 0xB279: "and go round again",
 0xB27B: "Error: ask what (message routine $B65F), Z",
 0xB280: "Indirect object case: was the slot marked?",
 0xB286: "If not, run the indirect search to the end ($B308)",
 0xB289: "Found none?",
 0xB28C: "...",
 0xB28F: "...",
 0xB290: "...none: ask which ($B303)",
 0xB292: "Next indirect-object candidate (the slot-2 twin of $B4C1)",
 0xB295: "No more: finish",
 0xB297: "Search for the second thing ($B2DF)",
 0xB29A: "Found exactly one second thing?",
 0xB29F: "No: look at the next",
 0xB2A1: "Remember this direct object ($B184)",
 0xB2A7: "Count it in $B170",
 0xB2AB: "Stop at the first if the verb says so",
 0xB2B1: "Or if the marked flag is clear",
 0xB2B7: "Restore the first into $A034",
 0xB2BD: "How many direct objects?",
 0xB2C1: "None: $B259",
 0xB2C3: "More than one?",
 0xB2C5: "Yes: 'too many' message",
 0xB2C7: "Exactly one: count the second things ($B2DF)",
 0xB2CD: "None: ask which ($B303)",
 0xB2D2: "Exactly one: check the record ($B20B)",
 0xB2D5: "More than one: question routine $B5D3",
 0xB2DA: "'Too many' message routine $B5E2, Z",
})
A[0xB191]['desc'] = list(A[0xB191]['desc']) + ['.', 'The line comments were written from reading the code and the descriptions of the routines it calls; the counters ($B170 direct, $B171 indirect) and the saves at $B184/$B185 are clear, but which message each failure path finally prints was not run for every path.']


# --- $A880 print a dictionary word: line comments (read from the code) ---
C(0xA880, {
 0xA880: "DE = the 2-byte word reference at HL: low 12 bits the dictionary offset...",
 0xA884: "...high nibble the flags; HL moves on past it",
 0xA887: "Output switched off ($5C3C = 0)?",
 0xA88B: "Yes: print nothing",
 0xA88C: "Remember the reference in $A022",
 0xA890: "Offset zero: no word, print nothing",
 0xA895: "Save the registers the dictionary search will use",
 0xA89A: "Print a space first ($A9B7)",
 0xA89F: "Flag nibble into C",
 0xA8A3: "Flag $70?",
 0xA8A5: "Then set $A026 to 1",
 0xA8AC: "Offset alone into HL",
 0xA8B5: "$A022 = offset with the flag nibble",
 0xA8BA: "IX = the per-letter index at $5D80 (2 bytes a letter)",
 0xA8BE: "B counts letters from 'a' (the code before 'a' is $60)",
 0xA8C1: "Find the last letter whose first record starts at or before the offset (high byte, then low)",
 0xA8D4: "Ran past 'z' ($7B)",
 0xA8DB: "Step back to the previous letter",
 0xA8E0: "DE = where that letter's records start",
 0xA8E6: "Zero means no word begins with that letter: step back again",
 0xA8EA: "Print the first letter itself ($A9B7)",
 0xA8EE: "Dictionary base $5DBF turns offsets into addresses",
 0xA8F5: "Unpack records one at a time ($A95B, front-coded) from the letter's first record up to the wanted word, leaving its spelling in $5C42",
 0xA8F9: "(compare with the wanted word's address)",
 0xA8FF: "Not there yet: next record",
 0xA901: "Restore HL, BC",
 0xA903: "The flag nibble decides whether the suffix is added ($A92F):",
 0xA904: "$50: never",
 0xA908: "$40: always",
 0xA90C: "$10: if the direct object $A034 is non-zero; any other: if the actor $A036 is",
 0xA917: "Zero: no suffix",
 0xA919: "Add the dictionary suffix ($A92F)",
 0xA91C: "Print the unpacked spelling at $5C42 up to its 0 terminator, a character at a time",
 0xA929: "Restore the registers and return",
})
A[0xA880]['desc'] = list(A[0xA880]['desc']) + ['.', 'Line comments added from reading the code; the flag-nibble rule for the suffix ($50/$40/$10) is read from the branches, not yet shown by playing.']


# --- $BA67 Watson's reply: line comments (read from the code) ---
C(0xBA67, {
 0xBA67: "A = 0 on entry: clear the two flags $BA60 (how the statement was matched) and $BA61 (remember it?)",
 0xBA6D: "Parse the next statement out of the remark into $BA19-$BA1B ($BD7E)",
 0xBA70: "Carry: nothing usable, jump to the reply code at $BBBE",
 0xBA73: "Z: try the next one",
 0xBA75: "Is it in Watson's own list ($BD4B)?",
 0xBA7A: "Yes: match kind 1",
 0xBA7C: "Record the kind in $BA60 and set $BA61 ($BB46)",
 0xBA7F: "Remember the record found, for the handler at $BB5C",
 0xBA85: "Is it in the case table ($BD51)?",
 0xBA8A: "Yes: kind 2",
 0xBA8C: "Statement flag bit 5 (the 'Tricia Fender / Phipps KILLED' ones)?",
 0xBA92: "Otherwise roll 1-100 ($D29D)...",
 0xBA95: "...",
 0xBA97: "...kind 3 if under 50",
 0xBA9B: "Else give up on this one",
 0xBA9D: "Not in either table: roll 1-100...",
 0xBAA0: "...",
 0xBAA2: "...kind 4 if under 70",
 0xBAA6: "Next word group of the remark ($AEA9); more: loop to $BA6D",
 0xBAAB: "Was anything matched?",
 0xBAAF: "No: the stock reply at $BB3F",
 0xBAB2: "Is the statement to be remembered?",
 0xBAB6: "No: skip to $BB16",
 0xBAB8: "Walk the list of remembered statements at $9FF6 ($A0F7)...",
 0xBABF: "...end of list: not there, make a node",
 0xBAC1: "...comparing the three bytes $BA62-$BA64 with each node",
 0xBAD9: "Found it already: unlink the node from the list ($A104)...",
 0xBAE5: "...closing the gap",
 0xBAF5: "Not there: get a 5-byte heap node ($A11C)",
 0xBAFA: "Fill in the node with the three bytes...",
 0xBB09: "...and put it at the head of the list $9FF4 (most recent first)",
 0xBB16: "Kind 1 (already in Watson's list)?",
 0xBB1B: "Yes: jump to its handler ($BB5C)",
 0xBB1D: "Otherwise roll 1-100",
 0xBB20: "25 or more: the stock reply",
 0xBB24: "Under 25: try to make the 'SOME CONNECTION BETWEEN' remark from the statement ($BD06)",
 0xBB2B: "Nothing to connect: the stock reply",
 0xBB2D: "Print the two things' names ($A4BC) as message parameters...",
 0xBB38: "...'SOME CONNECTION BETWEEN THE ... AND ...' ($6F62)",
 0xBB3F: "Stock reply: 'THAT IS BRILLIANT HOLMES.' ($6F54)",
 0xBB46: "Entry used at $BA7C: set $BA61 = 1 and store the kind in $BA60",
})
A[0xBA67]['desc'] = list(A[0xBA67]['desc']) + ['.', 'Line comments added from reading the code. The match kinds 1-4 stored in $BA60 are named from the branches ($BD4B hit, $BD51 hit, and the two dice rolls under 50 and 70); what $BA70 carry and $BA73 zero from $BD7E mean was not traced.']


# --- $C583 numbered action record: line comments (read from the code) ---
C(0xC583, {
 0xC583: "Record number (bit 7 dropped) into DE",
 0xC588: "Look it up in the table of 13 record addresses at $9FAB (2 bytes each)...",
 0xC58D: "...",
 0xC590: "IX = HL = the record",
 0xC594: "$A00F = requirement code of the direct object from the record's header ($C571)",
 0xC597: "$A010 = the indirect object's ($C57A)",
 0xC59A: "$A00B = 0",
 0xC59E: "Both requirement codes zero (the record takes no objects)?",
 0xC5A5: "Yes: run the record at once ($C5F4)",
 0xC5A7: "Direct object a number (code 5 or 6)?",
 0xC5B2: "Then $A034 must already hold $FE ('a number was given')...",
 0xC5B7: "...if not, give up: Z ($CB41)",
 0xC5BA: "Same test for the indirect object and $A035",
 0xC5CD: "Does the record want a direct object, and is $A034 still $FF (none named)?",
 0xC5DA: "Then guess it: try candidate B = 0, 1, 2... ($C463 says when B has run out)",
 0xC5DC: "Next candidate into A",
 0xC5DF: "Candidates exhausted: return Z",
 0xC5E0: "Make it the direct object",
 0xC5E3: "Guess the indirect object too and run the record ($C60D)",
 0xC5E6: "NZ: the record ran, finish",
 0xC5E8: "Else try the next candidate",
 0xC5EB: "Should the indirect object be guessed ($C5FC)?",
 0xC5EE: "No: run the record as it is",
 0xC5F0: "Yes: guess it and run the record ($C613)",
 0xC5F3: "Return its Z/NZ",
 0xC5F4: "Run the record: $A00B = 1...",
 0xC5F9: "...and go to $C989",
})
A[0xC583]['desc'] = list(A[0xC583]['desc']) + ['.', 'Line comments added from reading the code. CB41 is taken to be the "return Z" stub; the guessing loops only try candidates until the record runs, as the helpers at $C463/$C60D/$C613 describe.']


# --- $CAAF announce a character coming in: line comments (read from the code) ---
C(0xCAAF, {
 0xCAAF: "Actor 0, 1 or 100 ($DC6C)?",
 0xCAB2: "Yes: nothing to announce",
 0xCAB3: "The actor's room before the action ($C491)...",
 0xCAB9: "...equal to the player's room ($A009)?",
 0xCABA: "Yes: was already here, no entrance",
 0xCABB: "Where is the actor now ($D495)?",
 0xCAC4: "...the player's room?",
 0xCAC5: "No: skip the announcement",
 0xCAC7: "Print '<actor> ENTERS.' ($68ED) via $CBC2",
 0xCAD0: "Direct object has to be here (requirement code 7 or more)?",
 0xCAD5: "No: finished",
 0xCAD6: "Where is the direct object now ($D495)?",
 0xCADC: "$FF: it has no room of its own ($CAE0 onwards tries a different test)",
 0xCAE0: "Scan the bytes at IX+$0F onwards, up to the record's size, for the player's room",
 0xCAEF: "Not found: return",
 0xCAF0: "Found: save the actor in B and blank $A036",
 0xCAF9: "Switch output on ($5C3C = 1)",
 0xCAFE: "Look for an exit of the player's room ($D471)...",
 0xCB04: "...and if there is one, narrate it ($CA76)",
 0xCB09: "Switch output off again",
 0xCB0D: "Restore the actor",
 0xCB12: "Direct object has a room: was it in the player's room before the action ($C492)?",
 0xCB19: "Yes: no entrance",
 0xCB1A: "Is the object the actor itself ($A036)?",
 0xCB21: "Yes: already announced above",
 0xCB22: "Else print '<thing> ENTERS.' ($68ED)",
})
A[0xCAAF]['desc'] = list(A[0xCAAF]['desc']) + ['.', 'Line comments added from reading the code; the branch at $CADC/$CAE0 (a direct object with no room of its own) is the least certain part and was not exercised.']


# --- $D113 describe a room: line comments (read from the code) ---
C(0xD113, {
 0xD113: "B = the room number",
 0xD114: "Room record into IX ($D224)",
 0xD117: "Draw the room's picture if pictures are on ($A277)",
 0xD11B: "Save the room record, B and HL",
 0xD11F: "Is the actor inside something ($C863)? A' = the container, or $FF",
 0xD126: "$FF: not inside anything, skip",
 0xD12A: "Inside something: build 'YOU ARE IN <thing>':",
 0xD12B: "save the word at $68DE...",
 0xD12F: "...put the word for IN ($8000) into the message ($D0D0)...",
 0xD135: "...and print $68DD",
 0xD13B: "Put the old word back",
 0xD141: "Container's record ($D237)",
 0xD144: "Print how it is held (IN, ON, BEHIND...) ($D5D3)",
 0xD147: "Print its name ($D3D5)",
 0xD14C: "Count the other things in the container that should be listed ($D4CC)",
 0xD150: "None: just end the sentence ($A414)",
 0xD153: "Some: print the lead-in $09BF",
 0xD15E: "List them with commas and AND ($D51A)",
 0xD167: "Back to the room record",
 0xD16B: "HL = the room's own description word",
 0xD171: "Print it, or 'YOU ARE ON/IN ... <name>' if it has none ($D182)",
 0xD175: "The exits ($D60B)",
 0xD179: "The things here ($D68C)",
 0xD17C: "The people here ($D4A7)",
 0xD17F: "End the line ($A2A2)",
})
A[0xD113]['desc'] = list(A[0xD113]['desc']) + ['.', 'Line comments added from reading the code; the order matches what LOOK prints in the emulator.']


# --- $BF79 print the clock: line comments (read from the code) ---
C(0xBF79, {
 0xBF79: "IX = the text buffer $BF6E ('Mon 08:02am'; the space and colon are already in it)",
 0xBF7D: "Day number...",
 0xBF80: "...three letters per day from the table at $BF59 ($BFC6)",
 0xBF86: "Step over the space",
 0xBF88: "Hour: two digits ($BFB0)",
 0xBF8E: "Step over the colon",
 0xBF90: "Minute: two digits",
 0xBF96: "The a or p",
 0xBF9C: "Print the 11 characters in the status bar ($C1A8)",
 0xBFA4: "Two-digit writer: tens digit, then...",
 0xBFA7: "...the units as a digit",
 0xBFAA: "Store the character at IX and move on",
 0xBFB0: "Split A by 10 into tens (A) and units (L) ($BFBB)",
 0xBFBB: "Repeated subtraction: C counts from '0'",
 0xBFC6: "Copy three characters of day name number A (x3 into the table)",
})


# --- $BCC9 prove a statement; $BD06 find a connection (read from the code) ---
C(0xBCC9, {
 0xBCC9: "Does the statement have evidence (flags bit 2)?",
 0xBCCF: "Yes: check the evidence ($BF08)...",
 0xBCD8: "...not all there: fail, NZ ($BD03)",
 0xBCDA: "Flags bit 5 set?",
 0xBCE0: "Then only mark it as waiting (bit 0)",
 0xBCE6: "Otherwise mark it proven (bit 1 set)...",
 0xBCEA: "...and bit 0 clear",
 0xBCEE: "Bit 4 set: it has a routine...",
 0xBCF4: "...run the routine at +4/+5 ($D1DB)",
 0xBD01: "Z: proven",
 0xBD03: "NZ: not proven",
 0xBD06: "Look for a remembered statement (list at $9FF6, nodes of subject, relation, object) that shares one end with the statement at IX but differs at the other",
 0xBD0C: "IX walks the list ($A0F7)",
 0xBD13: "End of list: nothing found, NZ ($BD46)",
 0xBD15: "Compare subject with subject, subject with object, object with object, object with subject in turn...",
 0xBD3E: "...B and C then hold the two things that do not match;",
 0xBD3F: "if they are the same thing, try the next node",
 0xBD42: "Found: B and C are the pair to connect, Z",
})


# --- $A2E4 narrate a command: line comments (read from the code) ---
C(0xA2E4, {
 0xA2E4: "$A2AA = 1 while narrating",
 0xA2E9: "Save the registers",
 0xA2F0: "Save the verb and the two objects at $A35D-$A35F",
 0xA2FC: "B = $A00C (what it means was not established; $CB43 clears it before narrating)",
 0xA301: "$A027 (quoted printing) = 1 if B is zero, else 0 (so the text is quoted when B is zero)",
 0xA309: "Is it too dark to see ($D078)?",
 0xA30C: "No: carry on",
 0xA30E: "Dark, but B non-zero: carry on regardless",
 0xA312: "Dark: 'SORRY IT IS TOO DARK.' ($68D1)",
 0xA31A: "The verb's pattern record ($A2B1) into IX",
 0xA323: "Set the verb flags $A01D/$A01E ($A2BD)",
 0xA326: "Verb flag bit 4: no narration",
 0xA32B: "Set: skip to the end",
 0xA32D: "B zero?",
 0xA330: "An actor other than 0, 1 or 100?",
 0xA333: "Then start a fresh line ($A2A2)",
 0xA336: "Print the actor's name ($A724)",
 0xA339: "DE = $017F",
 0xA33D: "B zero: print the word at DE ($017F) ($A887), then narrate with the actor set to 0 = YOU ($A360)",
 0xA348: "B non-zero: narrate as it stands ($A37D)",
 0xA34B: "End the line ($A2A2)",
 0xA34E: "Clear $A2AA and $A027",
 0xA355: "Restore the registers and return",
})

A[0xA2E4]['desc'] = list(A[0xA2E4]['desc']) + ['.', 'Line comments added from reading the code. What $A00C means (the B of this routine) was not established, so the two narration paths are described by the branch, not by who is acting.']


# --- $D77E parse the next typed sentence: line comments (read from the code) ---
C(0xD77E, {
 0xD780: "Action-record body: $9FEB = 0",
 0xD784: "$A024 = 1",
 0xD788: "Keep the parser's token pointer ($D6BD) in $A02B across the parse",
 0xD78E: "Parse a sentence ($AAB2)",
 0xD792: "$A01B = 0 (flags preserved)",
 0xD797: "Put the token pointer back",
 0xD79D: "NZ: the parse failed",
 0xD79F: "Parsed: keep the rest of the line ($9FF0) as $9FF2...",
 0xD7A5: "...and empty $9FF0",
 0xD7AC: "$D6B8 = 0",
 0xD7AF: "Return NZ: success",
 0xD7B2: "Failed: free both word lists ($D87D, $D88A)",
 0xD7BA: "Parser result 2 (an action time was set)?",
 0xD7BE: "Otherwise print 'WHAT ?' ($6866) with quoted printing on...",
 0xD7C9: "...then off",
 0xD7CD: "and fail ($DC15)",
 0xD7D0: "Result 2: fail if $A01F is zero, else return NZ",
})


# --- $AB91 read a sentence's verb words: line comments (read from the code) ---
C(0xAB91, {
 0xAB91: "Statement mode ($A024 = 2)?",
 0xAB96: "Yes: the relation-word check at $ABF3",
 0xAB98: "E bits 0-2 set: ready for a verb slot (bit 1), an object-word slot (bit 2), and the direct-or-indirect choice (bit 0)",
 0xAB9C: "Next token ($AE7F): class in A, word reference in BC",
 0xAB9F: "Class $E0: skipped",
 0xABA3: "Class $30 (verb word)?",
 0xABA7: "Verb slot still free (E bit 1)?",
 0xABA9: "No: wanted twice, carry ($ABB5)",
 0xABAB: "Fill the verb slot: mark it taken...",
 0xABAD: "...and store the word reference at IY+0/+1",
 0xABB7: "Class $00 (second word)?",
 0xABBB: "Its slot (E bit 2) free?",
 0xABBF: "Mark taken and store at IY+2/+3",
 0xABC9: "Class $40: clear E bit 0, then treat as a verb word",
 0xABD1: "Class $20: goes to whichever slot is free:",
 0xABD5: "verb slot free: use it",
 0xABD9: "bit 0 still set: use the second slot",
 0xABDD: "else copy the verb word into the second slot and take the verb slot",
 0xABEF: "Any other class ends the verb: Z if the verb slot has been filled (E bit 1 clear), NZ if not",
 0xABF3: "Statement mode: next token...",
 0xABF6: "...skipping a class $80 one",
 0xABFB: "Keep the dictionary offset's high nibble out of the way",
 0xABFF: "Search the relation words at $994D (2 bytes each, 0 ends)",
 0xAC14: "Not one of them: NZ",
 0xAC17: "Found: store its reference as the verb, take the slot, read on, return Z",
})

A[0xAB91]['desc'] = list(A[0xAB91]['desc']) + ['.', 'Line comments added from reading the code; the meaning of the E register bits is inferred from how they are tested.']


# --- $CEFE skip a plan instruction: line comments (from the code and its block description) ---
C(0xCEFE, {
 0xCEFE: "Bit 7 of the opcode byte: a success address (2 bytes) follows...",
 0xCF00: "...skip it (enter the INC HL chain two from the end)",
 0xCF03: "The opcode alone",
 0xCF05: "Opcode 15: 1 byte",
 0xCF09: "Opcodes 8, 9, 1 and 13: 2 bytes",
 0xCF17: "Opcode 2: 4 bytes",
 0xCF19: "Opcodes 3 and 14: 3 bytes",
 0xCF25: "Opcodes 7 and 12: 5 bytes",
 0xCF2D: "Opcodes 11 and 10: 1 byte",
 0xCF35: "Opcode 5: 4 bytes",
 0xCF39: "Opcode 4: 5 bytes; anything else (6): 3",
 0xCF3D: "HL is advanced by 5, 4, 3, 2 or 1 depending on where the chain is entered",
 0xCF42: "Return with HL at the next instruction",
})


# --- $BB67 Lestrade's reply (first part): line comments (read from the code) ---
C(0xBB67, {
 0xBB67: "A = 0 on entry: clear $BA1D and $BA1C (the count of statements matched)",
 0xBB6D: "Parse the next statement out of the remark ($BD7E)",
 0xBB70: "Carry: no sense, reply $7243 ($BBBE)",
 0xBB73: "Look it up and try to prove it ($BC21)",
 0xBB78: "Count one more in $BA1C",
 0xBB7C: "Next part of the remark ($AEA9); more: loop",
 0xBB81: "Matched nothing at all?",
 0xBB87: "Then the stock reply $725F",
 0xBB8E: "$BA1D zero: go to the summary at $BBC9",
 0xBB94: "Otherwise IX = the last record found ($BA1E)",
 0xBB9A: "Step over it ($BE5A)...",
 0xBB9D: "...and look at what follows for records with flags bits 7-6 = 10 or bit 3 set; otherwise skip a group ($BE72)",
 0xBBB1: "Restore IX; NZ: the 'do not believe you have the evidence' reply $72A6 ($BBC4)",
 0xBBB5: "Z: reply $7295",
 0xBBB8: "Print the reply with IX as the subject",
 0xBBBE: "Reply $7243",
 0xBBC9: "Summary: try to prove every waiting statement ($BC46)",
 0xBBCC: "Find the first still unprovable one ($BC9C): B = how many",
 0xBBD1: "Some: $BBE5",
 0xBBD3: "None: count those that can now be proven ($BC74)",
 0xBBD9: "Some: reply $72BD",
 0xBBDE: "None: reply $727E",
 0xBBE5: "Print $67FF, then $72D6 unless exactly one...",
 0xBBF5: "Statement flags bit 4 clear: jump to the address at +4/+5 ($BC1A). Bit 4 set: take back the proven bit (1), print $72E1, then the message at +4/+5 (or a quote mark if that is 0)",
})
A[0xBB67]['desc'] = list(A[0xBB67]['desc']) + ['.', 'Line comments added from reading the code and cover the first part only (to $BC0E); which exact reply each address holds was not rendered.']


# --- $D60B list the exits through doors: line comments (read from the code) ---
C(0xD60B, {
 0xD60B: "Save the registers",
 0xD611: "IX = this room's exit list, BC = 3 bytes an exit ($D5EF)",
 0xD614: "IY = the first exit (direction, thing, destination)",
 0xD618: "Go to the end test",
 0xD61A: "Does the exit pass through a thing (+1 non-zero)?",
 0xD620: "Direction above 10: skip",
 0xD627: "Find the thing's record ($D237)",
 0xD62D: "Not revealed yet (+5 bit 7 clear): skip",
 0xD633: "The direction's word ($D5FB) in DE",
 0xD639: "Directions 1-8 (compass)",
 0xD63D: "9: the word $000A",
 0xD642: "10: the word $00E7",
 0xD647: "Print the lead-in $68BC ('TO THE')",
 0xD64D: "Print the direction word ($A887)",
 0xD650: "Print $68E9 ('THERE IS')",
 0xD656: "Print the door's name ($D3D5) and end the sentence ($A414)",
 0xD660: "Next exit",
 0xD664: "$FF ends the list",
 0xD66A: "Restore the registers and return",
 0xD671: "(Separate routine) walk the exits from IX: stop with Z at the $FF end...",
 0xD679: "...or return NZ at the first plain exit (no thing, a direction 1-10)",
})
A[0xD60B]['desc'] = list(A[0xD60B]['desc']) + ['.', 'Line comments added from reading the code; the exit entries are read as direction, door thing, destination, and the two non-compass directions (9, 10) were not checked by play.']


# --- candidate-search cluster ($B2DF, $B32D, $B34F, $B36B, $B5A4, $C45E, $C55A): read from the code ---
C(0xB2DF, {
 0xB2DF: "Start the indirect-object search afresh ($B36B)",
 0xB2E2: "Next indirect-object candidate ($B568)",
 0xB2E5: "None left: finish",
 0xB2E7: "Does it pass the record's checks ($C929)?",
 0xB2EA: "No: next",
 0xB2EC: "Yes: remember it in $B185...",
 0xB2F2: "...and count it in $B171",
 0xB2F6: "Stop at the first if the verb says so ($B190)",
 0xB2FC: "Put the first one found into $A035",
})
C(0xB32D, {
 0xB32D: "Save the search position $B180 (this is a counting pass that must not disturb it)",
 0xB331: "Restart the indirect-object search ($B36B)",
 0xB334: "Save the number flag $B549",
 0xB338: "Count every candidate ($B568) into $B171",
 0xB343: "Restore the flag and the position",
 0xB347: "Return the count in A",
})
C(0xB34F, {
 0xB34F: "No direct-object candidates counted yet ($B170 = 0)",
 0xB353: "Number flag $B4A2 = $FF",
 0xB358: "IX = the first thing ($D04F)",
 0xB35B: "Requirement code below 7 ($A00F): not a thing, so start at 0",
 0xB366: "Save the search position in $B17E",
})
C(0xB36B, {
 0xB36B: "No indirect-object candidates counted yet ($B171 = 0)",
 0xB36F: "Number flag $B549 = $FF",
 0xB374: "IX = the first thing ($D04F)",
 0xB377: "Requirement code below 7 ($A010): start at 0",
 0xB382: "Save the search position in $B180",
})
C(0xB5A4, {
 0xB5A4: "The indirect-object slot's words ($B178)",
 0xB5A7: "Next thing or room they name ($B4A0)",
 0xB5AA: "$FF: no more",
 0xB5AD: "Make it the indirect object ($A035)",
 0xB5B0: "Mark the slot as having a candidate (bit 1 of $B16E)",
})
C(0xC45E, {
 0xC45E: "Indirect object's requirement code ($A010)...",
 0xC463: "(or the direct object's $A00F from here)",
 0xC466: "Code below 5 means a room, otherwise a thing",
 0xC468: "A = the candidate number B",
 0xC46B: "Things: carry if B is below 110",
 0xC46E: "Rooms: carry if B is below 106",
})
C(0xC55A, {
 0xC55A: "Should the indirect object be guessed ($C542)?",
 0xC55D: "No: just run the checks ($C929)",
 0xC560: "Candidate B = 0, 1, 2...",
 0xC563: "Out of range ($C45E)?",
 0xC566: "Yes: give up (Z)",
 0xC568: "Try it as the indirect object",
 0xC56B: "Does the record's check pass ($C929)?",
 0xC56E: "No: next candidate; yes: return NZ",
})


# --- small parser/printer routines: read from the code ---
C(0xC4B2, {
 0xC4B2: "A = 0: no indirect object",
 0xC4B3: "Verb flag $A01D bit 2 (takes an indirect object)?",
 0xC4B8: "No: requirement code 0",
 0xC4BA: "Bit 6 set (TAKE TO)?: code 4",
 0xC4C0: "$A01E bits 0-1 both set (the object is a number)?: code 5",
 0xC4CB: "Otherwise code 7 (a thing that must be here)",
 0xC4CD: "Store as $A010",
})
C(0xD3E8, {
 0xD3E8: "Save A and DE",
 0xD3EA: "DE = the first name word at IY",
 0xD3F0: "Print it ($A7D0)",
 0xD3F3: "Flag in IY-2 bit 6 clear: reset $A7EA",
 0xD3FD: "Flag in IY-1 bit 5 set: continue at $D427, otherwise at $D416",
})
C(0xA92F, {
 0xA92F: "Low nibble of the record's byte picks a suffix",
 0xA932: "15: none",
 0xA935: "Times 4: an index into the table at $A85C",
 0xA93E: "Copy four letters to IX...",
 0xA949: "...and end with 0",
 0xA94D: "Entry: unpack the record at HL ($A95B), then add its suffix ($A92F)",
})
C(0xB5B6, {
 0xB5B6: "Remember A in $A01B",
 0xB5B9: "The rest of the typed line ($9FF2) becomes the current sentence ($9FF0)",
 0xB5C1: "Its link (the two bytes before it) becomes the new rest",
 0xB5CA: "Cut the sentence's own link",
})
C(0xB483, {
 0xB483: "B = 0: nothing to copy",
 0xB486: "Word pair at IY + E...",
 0xB48C: "...copied to HL, HL+1",
 0xB496: "Z if the pair was empty",
 0xB49C: "Count down B; HL on to the next pair",
})


# --- message-code handlers and record-address helpers: read from the code ---
C(0xA63F, {
 0xA63F: "Code $1D: D = $60 (end of sentence, new line)",
 0xA643: "Code $1E: D = $30 (full stop and new line)",
 0xA647: "Entry: print the word at DE ($A887), D left as it was",
 0xA64A: "A = '.'",
 0xA64C: "D bit 6 set: no full stop, straight to the new line",
 0xA650: "D bit 4 set: print the full stop ($A9B7)",
 0xA657: "Then start a new line ($A2A2) if the bit was set",
})
C(0xA780, {
 0xA780: "Code $0C: whose? A = the actor ($A036)",
 0xA783: "DE = $0414 (HIS), returned NZ when A is not zero",
 0xA788: "The player (A = 0): DE = $09F2 (YOUR), NZ",
 0xA78E: "Code $0E: the same for the direct object ($A034)",
})
C(0xA771, {
 0xA771: "Code $19: take the next message parameter ($A66C)...",
 0xA776: "...and if it is not zero, print the message it points to ($A5C4)",
 0xA77E: "Done, A = 0",
})
C(0xA4AB, {
 0xA4AB: "HL = room A's record + 1 ($D224)",
 0xA4BC: "HL = thing A's record + 7, the start of its name words ($D237)",
})


# --- after-turn routines: read from the code ---
C(0x9D13, {
 0x9D13: "Countdown at $9D10 for greeting the player (C = 0) ($9CE9)",
 0x9D1B: "Countdown at $9D11 for Inspector Lestrade (C = 2)",
 0x9D23: "Countdown at $9D12 for Chief Constable Straker (C = 4)",
 0x9D2B: "Carry on with the rest of his turn at $E691",
})
C(0x9D73, {
 0x9D73: "Lestrade already introduced ($9D90 set)?",
 0x9D77: "Yes: nothing to say",
 0x9D78: "Countdown $9D70 for the player (C = 0): 'no one is to get by' ($9D65)",
 0x9D80: "Countdown $9D71 for Watson (C = 3)",
 0x9D88: "Countdown $9D72 for the Major (C = 7)",
})


# --- $DBF7 read a number, $C249 rub out: read from the code ---
C(0xDBF7, {
 0xDBF7: "Save BC; C = the number so far, 0",
 0xDBFA: "Next character at HL: a digit ($DAE8 sets carry if not)?",
 0xDBFE: "Not a digit: finish",
 0xDC00: "Digit value into B",
 0xDC03: "C = C x 10 + digit: C x 2 in A...",
 0xDC06: "...C x 8 added...",
 0xDC0B: "...plus the digit",
 0xDC0D: "Next character",
 0xDC10: "A = the number",
})
C(0xC249, {
 0xC249: "Print a space over the last character ($C388)",
 0xC24E: "Step the cursor back twice ($C267)",
 0xC254: "Column counter $C1F4 + 1",
 0xC258: "Not yet 37: back to the input loop ($C22D)",
 0xC25C: "Otherwise move to the start of the next line ($C29C)...",
 0xC263: "...column 1, and back to the input loop",
})


# --- special-word handlers $AFE1-$B019: read from the code ---
C(0xAFE1, {
 0xAFE1: "Guard: E bit 1 set (start of a sentence)? Then return",
 0xAFE4: "Otherwise drop the caller's return address and refuse: NZ, 'not a special word' ($AF67)",
 0xAFE8: "(Second guard) E bit 1 clear: return",
 0xAFEB: "Otherwise refuse unless nothing has been read yet in this sentence ($A012, $A01B both zero)",
 0xAFF6: "Refuse ($AF67)",
})
C(0xAFFA, {
 0xAFFA: "BECAUSE / THEREFORE: D = $A0 (the comma class), continue as a comma ($ACCC)",
 0xAFFF: "PRINT: the sentence-start guard ($AFE1)",
 0xB002: "Read the printer status ($C03B)",
 0xB005: "NZ: leave $A008 alone",
 0xB007: "Printer there: $A008 = 1 (printing on)",
 0xB00B: "NOPRINT: the same guard",
 0xB00E: "Clear the text window ($A296)",
 0xB011: "$A008 = 0 (printing off)",
 0xB015: "Carry on with the sentence: D = $A02D, back into the parser ($AAC4)",
})


# --- small list helpers: read from the code ---
C(0xAF4E, {
 0xAF4E: "Copy 6 bytes ($AF4E), 10 ($AF52) or 2 ($AF56) - entry points set the count in C",
 0xAF58: "Source = IY + DE, destination = IX + DE",
 0xAF62: "BC = the count; block copy",
})
C(0xBF45, {
 0xBF45: "The statement's relation number (+1)",
 0xBF49: "0: none, return Z",
 0xBF4A: "Relation 1-11 into an index",
 0xBF4E: "Table of relation words at $994D, 2 bytes each",
 0xBF53: "DE = the word reference",
 0xBF56: "NZ: found",
})
C(0xAF38, {
 0xAF38: "Save registers",
 0xAF3B: "10 bytes at IY + A...",
 0xAF44: "...ORed together",
 0xAF49: "Restore; Z if all ten were zero (AND A also clears carry)",
})

C(0xBB67, {
 0xBBFF: "Save the statement record",
 0xBC01: "Print $72E1",
 0xBC07: "HL = the word at +4/+5",
 0xBC0F: "Non-zero: print the message it points to and finish ($A59F)",
 0xBC12: "Zero: print a quote mark (A = $22) ($A9B7)",
 0xBC17: "...and end the line ($A414)",
 0xBC1A: "Bit 4 clear: jump to the routine at +4/+5",
 0xBC21: "Look the statement up in the case table ($BD51)",
 0xBC24: "Not there: return 0",
 0xBC26: "Only if its flags bits 7-6 are 10",
 0xBC31: "Remember the record in $BA1E",
 0xBC35: "Try to prove it ($BCC9)",
 0xBC38: "Proven: return NZ",
 0xBC3A: "Not proven: $BA1D = 1...",
 0xBC3F: "...and mark it waiting (bit 0)",
 0xBC43: "Return NZ",
})


# --- $E66F action record: Watson's idle remarks (read from the code) ---
C(0xE66F, {
 0xE673: "Pre-check: A = the current actor ($A036)",
 0xE676: "Is anything held by that actor ($E619)?",
 0xE679: "None: succeed ($E683)",
 0xE67B: "Otherwise check the result ($E39C)",
 0xE67E: "HL non-zero: fail ($DC15)",
 0xE683: "Succeed, NZ",
 0xE686: "Roll 1-100 ($D29D)...",
 0xE68B: "...under 50: fail",
 0xE68E: "50 or more: NZ",
 0xE691: "Watson's after-turn remark about something already said: the 50% roll first",
 0xE694: "Failed the roll: nothing to say",
 0xE695: "Another roll 1-100 into B: how far along the list of remembered statements to go",
 0xE699: "IX = the head of the list at $9FF6",
 0xE69D: "Count B down ($E6A6 when done)",
 0xE69F: "Next node ($A0F7); at the end of the list start again",
 0xE6A6: "Is it the head itself (an empty list)?",
 0xE6B1: "No: print the question about that statement with IX as its subject ($6F80)",
 0xE6B9: "Return NZ",
})


# --- $B5D3 the parser's questions (read from the code; the descriptions of $B62F-$B65E apply) ---
C(0xB5D3, {
 0xB5D3: "Indirect-object slot holds words (bit 0 of $B16E)?",
 0xB5D8: "No: the 'THE ... WHAT ?' form at $B610",
 0xB5DA: "Yes: A = the slot's count byte ($B183), HL = the slot ($B178)",
 0xB5E0: "Join the 'WHICH' question",
 0xB5E2: "(Entry for the direct object) same test on $B16D",
 0xB5E9: "A = its count byte ($B182), HL = $B172",
 0xB5EF: "Push the slot's three words as message parameters ($B83C)",
 0xB5F2: "Move on to the next sentence of the typed line ($B5B6)",
 0xB5F5: "Print 'WHICH ... ?' ($6888)",
 0xB5FC: "Direct object with no words: push the verb's words ($B633)",
 0xB5FF: "...and the saved ($B186) word",
 0xB606: "Next sentence",
 0xB609: "Print '<word> WHAT ?' ($6880)",
 0xB610: "Neither slot: the full question: verb words ($B62F)...",
 0xB617: "...the direct object's words ($B172)...",
 0xB61B: "...and ($B633) the verb again",
 0xB625: "Next sentence",
 0xB628: "Print '<word> THE <word> WHAT ?' ($687C)",
 0xB65F: "(Entry $B65F) requirement code 5 or 6 (a number) wants...",
 0xB66A: "...or the first word of the direct-object slot has bit 7 set",
 0xB671: "Print $6855 ('DON'T BE SILLY.')",
 0xB678: "Otherwise: direct-object slot holds words?",
 0xB680: "Yes: count them ($B6DA)",
 0xB683: "Push the verb's words ($B633)",
 0xB68C: "Push the saved word ($B186)",
 0xB691: "Slot has words (bit 0)?",
 0xB695: "Yes: push them ($B83C) and use the message at $05B3",
 0xB69D: "No: three zero parameters and the message at $05DB",
 0xB6A7: "Print $6894 with those parameters",
})
A[0xB5D3]['desc'] = list(A[0xB5D3]['desc']) + ['.', 'Line comments added from reading the code; the quoted messages come from the existing notes on $6855-$6894, and the exact wording of the two variants at $05B3 and $05DB was not rendered.']


# --- case-table search and the direct-object search: read from the code ---
def CC(addr, d):
    """Like C(), but addr may be any address in the block."""
    C(max(a for a in A if a <= addr), d)


CC(0xBD4B, {
 0xBD4B: "Watson's own list ($9A7D)",
 0xBD4F: "Join the walk",
 0xBD51: "The case table ($9965)",
 0xBD55: "First byte $FF ends the table",
 0xBD5C: "Does this record match the statement ($BD69)?",
 0xBD5F: "Yes: Z, IX = the record",
 0xBD61: "Step to the next record ($BE5A)",
 0xBD66: "End of table: NZ",
 0xBD69: "Compare the relation ($BA1A) with +1...",
 0xBD70: "...then the subject ($BA19) with +0...",
 0xBD77: "...then the object ($BA1B) with +2; Z if all three agree",
})
C(0xB4C1, {
 0xB4C1: "Direct object a number (requirement code 5)?",
 0xB4C6: "Yes: the number case at $B4A3",
 0xB4C8: "First word of the direct-object slot has bit 7 set?",
 0xB4CD: "No: search for things",
 0xB4CF: "Yes: nothing to search, return A = $FF",
 0xB4D4: "Save IY; IX = the search position ($B17E)",
 0xB4DA: "Verb flag $A01D bit 0 (the object need not be here) into $A038",
 0xB4E2: "Requirement code below 5: search rooms ($D39B), otherwise things ($D36A)",
 0xB4F1: "Run the search for the next match ($B4FD)",
 0xB4F6: "Save the new position; Z/NZ: found something or not",
 0xB4FC: "Return",
})


# --- $C4D1 do a command; $CB7B refuse by naming the flag: read from the code ---
C(0xC4D1, {
 0xC4D1: "The verb number ($A033): bit 7 set means a script-only verb ($C583)",
 0xC4D9: "Its pattern record ($A2B1) into IX; set the verb flags ($A2BD)",
 0xC4E2: "Requirement codes of the two objects ($C493, $C4B2)",
 0xC4E8: "$A00B = 0",
 0xC4EC: "Verb takes no objects ($A01D bits 2-3 clear)?",
 0xC4F1: "Yes: run it as it is ($C53A)",
 0xC4F3: "Direct object a number (code 5)? Then $A034 must be $FE...",
 0xC4FF: "...else refuse (Z)",
 0xC502: "Same for the indirect object and $A035",
 0xC511: "Does the verb want a direct object, and is $A034 still $FF?",
 0xC51E: "Guess it: candidates B = 0, 1, 2... ($C463 ends the loop)",
 0xC525: "Try the candidate as the direct object",
 0xC529: "...with a guess at the indirect object ($C55A)",
 0xC52D: "Worked: run it ($C53A)",
 0xC52F: "Else the next candidate",
 0xC531: "Should the indirect object be guessed ($C542)?",
 0xC536: "Guess it ($C560)",
 0xC53A: "$A00B = 1, then find and run the action record ($C929)",
})
C(0xCB7B, {
 0xCB7B: "$CB79 = the missing or forbidden flag bits; bit 7 says which",
 0xCB80: "Needed bit missing: table at $C471...",
 0xCB85: "...forbidden bit present: table at $C481",
 0xCB88: "Mark the end of the bits with bit 7",
 0xCB8A: "Walk the table: DE = the next word, shifting the flag byte right until the lowest set bit falls out",
 0xCB91: "Word zero: nothing to say ($CB58)",
 0xCB95: "The object saved at $CB7A becomes the direct object",
 0xCB9B: "Print $6817 'THE <object> IS' (the word follows)",
})


CC(0xB05A, {
 0xB05A: "Save IY, IX",
 0xB05E: "The list headed at $9FEC...",
 0xB062: "...find its last node: the one whose link is 0 ($A104)",
 0xB068: "Get a 2-byte heap node ($A11C)",
 0xB06D: "Store the token position $A02B in it",
 0xB076: "Link it after the last node",
 0xB07F: "Restore the registers",
 0xB083: "(and DE, HL)",
})
CC(0xD6E5, {
 0xD6E5: "Quoted printing on ($A027 = 1)",
 0xD6ED: "Print the message 'I DO NOT KNOW THE WORD' ($6859)",
 0xD6F0: "Mark the word's token ($D6BD) as class $C0",
 0xD6F5: "HL = the unknown word in the typed line ($A029)",
 0xD6F8: "Print it a character at a time, a '.' as a space...",
 0xD703: "...up to the next space",
 0xD707: "Closing quote",
 0xD70C: "End the line ($A2A2)",
 0xD70F: "Quoted printing off ($A027 = 0)",
})


CC(0xEFC9, {
 0xEFC9: "The player's room ($A009): one of Basil's house (33 entrance hall to 39 yard; the seven compares run $23, $21, $22, $26, $25, $24, $27)?",
 0xEFE6: "Yes: take the other branch at $DFCC",
 0xEFE9: "No: DE = 0, B = $80, and clear then re-set bit 6 of the record's +5 ($EFBA)...",
 0xEFF1: "...so it ends with bit 6 set (the effect was not traced)",
})
CC(0xE201, {
 0xE201: "Search the thing table ($D34E) and test the result against $FF",
 0xE207: "IX = the id list at $E22A",
 0xE20B: "Compare A with each id; a match goes to $E1F9",
 0xE214: "$FE entry: go to $E1F8",
 0xE219: "$FF entry (the end): none matched, return A = 0",
 0xE21B: "Otherwise step on and search the table for the entry ($D34E)",
})


CC(0xAC94, {
 0xAC94: "The two word slots at $AAAE (2 bytes each)",
 0xAC97: "First slot empty?",
 0xAC9C: "No: second slot empty?",
 0xACA0: "Both taken: return NZ",
 0xACA1: "Store the word BC in the empty slot...",
 0xACA4: "...Z: done",
})
CC(0xADEC, {
 0xADEE: "HL = the node at IY + $18...",
 0xADF6: "...OR together its 6 bytes",
 0xADFF: "Z if all of them are zero (the slot is empty)",
})
CC(0xD919, {
 0xD91B: "Carriage return: end of line ($D949)",
 0xD91F: "A '.' ends a word ($D93C)...",
 0xD923: "...and so do ','...",
 0xD927: "...'/'...",
 0xD92B: "...the pound sign ($60)...",
 0xD92F: "...'-'...",
 0xD933: "...and ':'",
})
CC(0xAA55, {
 0xAA55: "A letter below $7B...",
 0xAA59: "...is capitalised if the capital flag $A851 is set, or $A026 (set after a full stop and by some word flags)...",
 0xAA65: "...clearing $A026,",
 0xAA69: "...and its case bit is dropped (AND $5F)",
})
CC(0xAD99, {
 0xAD99: "IY + DE: the slot",
 0xAD9E: "Fill the first word from DE unless it already has one ($AE59)",
 0xADA1: "...and the second",
 0xADA4: "Nothing to add: skip",
 0xADA6: "Else fill the pair two bytes back too",
})


CC(0xB80B, {
 0xB80B: "DE = the word pair at IX (its link)",
 0xB811: "Get a 2-byte heap node ($A11C)",
 0xB819: "Put the old link in it",
 0xB820: "Push the node on the front of the list headed at $B6D6",
})
CC(0xE0B1, {
 0xE0B1: "Player in room 88 (east side)?",
 0xE0B6: "No: nothing happens ($E0DD)",
 0xE0B8: "Day 1 (Tuesday)?",
 0xE0BF: "IX = the indirect object's record ($A015)",
 0xE0C3: "Mark it as seen and visible (+6 and +5 bit 7)",
 0xE0CB: "Move it into the player's room (+15)",
 0xE0D1: "And make the direct object its holder (+1)",
 0xE0D7: "Print the message $7B5A",
 0xE0DD: "Return NZ",
})
CC(0xE4E1, {
 0xE4E1: "Print the message in HL ($A59F)",
 0xE4E4: "HL = $9C60, a routine to run",
 0xE4E7: "Keep the current actor",
 0xE4EB: "Call (HL) ($E4FB)",
 0xE4EE: "Restore the actor",
 0xE4F0: "Reset the actor's state ($DD0E)",
 0xE4F3: "Clear bit 6 of the record at ($DCFF)",
 0xE4F8: "Return NZ",
 0xE4FC: "(Next record) the direct object ($A034): is anything held by it ($E619)?",
 0xE502: "None: fail",
})


C(0xC60D, {
 0xC60D: "Should the indirect object be guessed ($C5FC)? No: just run the record ($C989)",
 0xC613: "Guess it: candidate B = 0, 1, 2...",
 0xC616: "Out of range ($C45E)? Then give up",
 0xC61B: "Try it as the indirect object ($A035)...",
 0xC61E: "...by running the record ($C989)",
 0xC621: "NZ: it ran",
 0xC623: "Else the next candidate",
})
CC(0xB83C, {
 0xB83C: "Pop the return address into IX",
 0xB83E: "Push the three words at HL as message parameters (3 x 2 bytes)",
 0xB847: "Re-order the stack so the first word is on top...",
 0xB84A: "...and return to the caller through IX",
 0xB84C: "The 'I do not know the verb' routine: push the four saved words ($B18A, $B188, $B186, $B18C)",
})
CC(0x9DC6, {
 0x9DC6: "Greeting countdown allows it ($9CF2)?",
 0x9DCB: "Already greeted once ($9DCC non-zero): ordinary greeting ($9CEC)",
 0x9DD0: "First time: mark it greeted...",
 0x9DD2: "...and say $71ED",
})
CC(0x9DD8, {
 0x9DD8: "Greeting countdown allows it ($9CF2)? Set the flag to 1",
 0x9DDD: "Re-check the waiting statements ($BC46)",
 0x9DE0: "Find the first one that cannot be proven yet ($BC9C)",
 0x9DE3: "B non-zero: $9DF5",
 0x9DE7: "None: count those that can be proven ($BC74); none: finish",
 0x9DEC: "Print $722D 'WELL CAN YOU PROVE THAT ... YET, HOLMES ?'",
})
CC(0xCA25, {
 0xCA25: "Save the actor's room as it was before the action ($C491)",
 0xCA28: "IX = the direct object's record ($A013)",
 0xCA2C: "Save its room ($C492)",
 0xCA35: "$A00C = 1 while the action is narrated",
 0xCA3A: "Narrate it ($CA76)",
 0xCA40: "Record flag bit 7 set: return carry",
 0xCA48: "A plan's direct object slot ($9FD7) still $FF: take this action's ($A034)",
 0xCA54: "Same for the indirect object ($9FD8, $A035)",
})
CC(0xE1D8, {
 0xE1D8: "The actor ($A036)...",
 0xE1DB: "...looked up in the list at $E22A ($E207)",
 0xE1DE: "Not there: message $761D",
 0xE1E0: "Next entry: the indirect object ($A035) is searched for ($E201)",
 0xE1E8: "Not there: message $761D",
 0xE1EA: "HL = the entry's word at +1/+2",
 0xE1F2: "Print $6830 with it as a parameter",
 0xE1F9: "Return NZ",
})


CC(0xE18A, {
 0xE18A: "The indirect object ($A035): thing 16 (WHAT HAPPENED), 67 (BLOODSTAINED CLOTHES) or 17 (YOUR ALIBI)?",
 0xE197: "No: skip to $E1D3",
 0xE199: "Yes: set bit 1 of the empty statement at $9993 - set once Mrs Jones (Tricia Fender in disguise) has been asked what happened or about her alibi",
})
CC(0xE106, {
 0xE106: "$CAAE = 1 (the 'describe the room again' flag)",
 0xE10B: "Only the player ($A036 = 0) goes on",
 0xE110: "($DF5B)",
 0xE113: "IX = the direct object's record ($A013)",
 0xE117: "Already marked (+5 bit 5)? Return",
 0xE11C: "Mark it (+5 bit 5)",
})
C(0xA2B1, {
 0xA2B1: "Verb number A (1-based) times 8 into HL...",
 0xA2B8: "...added to the verb table $8259: HL = its record",
})
CC(0xA480, {
 0xA480: "One digit of the number ($A476)",
 0xA483: "Make it an ASCII digit",
 0xA485: "C = the leading-zero flag: still zero?",
 0xA489: "A '0' while leading: print nothing",
 0xA48C: "Otherwise from now on print zeros too (C = 1)",
 0xA48D: "Print the digit ($A9B7)",
})
CC(0xA65D, {
 0xA65D: "Clear $A028",
 0xA661: "Take the next message parameter ($A66C)",
 0xA667: "If it is not zero, print it ($A7BA)",
})
CC(0xC9FD, {
 0xC9FD: "The record's high nibble of byte 1...",
 0xCA00: "...rotated down four places (4 RRCAs)",
 0xCA04: "Low nibble only",
 0xCA09: "Stored in $A01F as a word",
})
CC(0xD590, {
 0xD590: "Save the registers; A = a thing",
 0xD594: "Its record ($D237)",
 0xD597: "Bit 6 of +5 (a person)?",
})
CC(0xE4CB, {
 0xE4CB: "HL = $9C56",
 0xE4CE: "The direct object ($A034)",
 0xE4D2: "Thing 2, 3 or 4 (Lestrade, Watson, Straker)? Otherwise $E4E7",
})


CC(0xE51C, {
 0xE51C: "The plan's direct object ($9FD7) = $FE (a number)",
 0xE521: "HL = the word at IX+9/+10 (an amount)",
 0xE527: "Bit 7 set: the number form",
 0xE529: "Store it at $A02F",
 0xE52C: "Return NZ",
})
CC(0xC267, {
 0xC267: "Step the print position back one character: C (the pixel column in the cell) minus 7...",
 0xC26B: "...no borrow: done",
 0xC26C: "Borrow: back to the previous cell (L = L - 1), C + 8",
})
CC(0xD1DD, {
 0xD1DD: "Keep A in D",
 0xD1DE: "E = the record's size byte + 15",
 0xD1E5: "D = 0; IX = IX + DE",
 0xD1E9: "Restore DE",
})
CC(0xA476, {
 0xA476: "Divide HL by DE by repeated subtraction: A counts from -1 (so A = the quotient)",
 0xA47E: "Add the divisor back: HL = the remainder",
})
CC(0xB0EE, {
 0xB0EE: "IX = the start of the saved-game block ($840B)",
 0xB0F2: "DE = HL - $840B... with HL = $A01F, the end",
 0xB0FB: "DE = its length",
})
CC(0xB6DA, {
 0xB6DA: "Count the words in the slot ($B6FD)",
 0xB6DD: "None: return",
 0xB6DF: "Push them as parameters ($B83C)",
 0xB6E2: "Push the verb's words ($B633)",
 0xB6E5: "And the saved word ($B186)",
})
CC(0x9AE3, {
 0x9AE3: "($9B50)",
 0x9AE6: "DE = 6 ($9B25)",
 0x9AEC: "L = the byte at IX+2 minus 2",
 0x9AF2: "Join the common ending at $9B02",
})


CC(0xD4A7, {
 0xD4A7: "Save the registers",
 0xD4AB: "Count the people here: place $FF ($D4CC)",
 0xD4B0: "None: finish",
})
CC(0xD68C, {
 0xD68C: "Save the registers",
 0xD692: "IX = room A's exits ($D5EF)",
 0xD695: "Find the first plain exit ($D671); none: finish",
})
CC(0xD95C, {
 0xD95C: "($D968)",
 0xD95F: "A closing quote mark...",
 0xD961: "...stored at HL",
 0xD962: "...and printed",
 0xD965: "HL on, B down",
})
CC(0xD9B7, {
 0xD9B7: "B bit 7 set: finished",
 0xD9BA: "Print a backspace (8) ($A9B7)",
 0xD9BF: "B up, HL back: repeat",
})
CC(0xDFB8, {
 0xDFB8: "The direct object ($A034) is thing $59?",
 0xDFBD: "No: $E000",
 0xDFC0: "And the day is Monday (0)?",
 0xDFC5: "No: $E000",
 0xDFC8: "Yes: carry on at $DFCC",
})
CC(0xDFF4, {
 0xDFF4: "A = $64 and on to $E028",
 0xDFF8: "The actor must be thing 1, else fail",
 0xE000: "Return NZ",
})
CC(0xE5C3, {
 0xE5C3: "The first actor in the table ($9860, the player)...",
 0xE5C6: "...its record ($D237): its room (+15)",
 0xE5CC: "Compare with the room of the thing at ($A017)",
 0xE5D3: "The current actor into A; on to $E5F0",
})
CC(0xE642, {
 0xE642: "Is anything held by the actor ($E619)? No: fail",
 0xE64B: "Test the result ($E39C): bit 7 of HL clear: fail",
})
CC(0xEFB5, {
 0xEFB5: "DE = $07F0, B = $10",
 0xEFBA: "The actor's record ($F1C1)",
 0xEFC0: "Clear bit 6 of +5",
 0xEFC4: "Return NZ",
})


CC(0xA296, {
 0xA296: "18 times...",
 0xA298: "...start a new line ($A2A2) and clear $A019",
})
CC(0xA5A9, {
 0xA5A9: "Save the message pointer in ($A59D)",
 0xA5AC: "Restore HL",
 0xA5AD: "$A00B set? Then skip the next store",
 0xA5B3: "Otherwise $A00C = 0",
})
CC(0xA7BA, {
 0xA7BA: "IY = HL; print the thing's name words ($D405)",
 0xA7C5: "IY = HL; print the name words at IY ($D3E8)",
})
CC(0xC240, {
 0xC240: "Lower-case letter (a-z)?",
 0xC246: "Make it upper case (AND $5F)",
})
CC(0xD21C, {
 0xD21C: "Keep A in B across the call ($D206)",
 0xD221: "Restore A",
})
CC(0xD6C1, {
 0xD6C1: "Read the player's line ($D898); nothing typed: fail",
 0xD6C7: "$D714 = 0, return NZ",
})
CC(0xD1B2, {
 0xD1B2: "Keep A in B",
 0xD1B3: "($D0DD)",
 0xD1B6: "($D187)",
 0xD1BA: "Too dark to see ($D078)? No carry: go to $D178",
})
CC(0xC3C2, {
 0xC3C2: "Shift B left, C times",
 0xC3C7: "C = A; A = B complemented",
})


CC(0xC5FC, {
 0xC5FC: "Indirect object requirement code ($A010) zero: no, Z",
 0xC601: "Indirect object still $FF (not named)?",
 0xC608: "Yes: NZ (guess it)",
 0xC60B: "No: Z",
})
CC(0xDB56, {
 0xDB56: "Full stop...",
 0xDB59: "...comma...",
 0xDB5C: "...or space: Z",
})
CC(0x9C56, {
 0x9C56: "Thing A's record ($D237)",
 0x9C59: "Set bit 7 of +5 (visible)",
 0x9C5D: "Return NZ",
 0x9C60: "(Next routine) thing A's record",
 0x9C63: "Clear bit 7 of +5 (hidden)",
 0x9C67: "Return NZ",
 0x9C6A: "The actor ($A036) looked up in the list at $9C85 ($D34E)",
 0x9C74: "$FF = not there",
})
CC(0xA2A2, {
 0xA2A2: "New line: print a carriage return (13) ($A9B7), keeping A",
 0xA2AB: "(Next routine) clear B bytes at HL",
})
CC(0xA59F, {
 0xA59F: "Print message HL: save the registers",
 0xA5A5: "HL = SP + 12: the caller's parameters",
})
CC(0xA5C4, {
 0xA5C4: "IX = the message at HL",
 0xA5C7: "Run the interpreter one step at a time ($A5CD) until it says stop",
})
CC(0xA684, {
 0xA684: "Take the next message parameter ($A66C)",
 0xA687: "IX = it (a record or word list)",
 0xA68A: "Z, A = 0",
})
CC(0xA852, {
 0xA852: "Toggle the capital flag $A851",
 0xA85A: "A = 0",
})


CC(0xC457, {
 0xC457: "Restore DE, HL, IX, IY and return",
})
CC(0xC863, {
 0xC863: "Save IX; find thing A's record ($D237)",
 0xC868: "Is it held, at any depth ($C86E)?",
 0xC86B: "Restore IX",
})
CC(0xD04F, {
 0xD04F: "IX = the thing index $8B6F...",
 0xD053: "...one 3-byte entry back (the search step adds three first)",
})
CC(0xD26C, {
 0xD26C: "Save HL; the direct object ($A034)...",
 0xD270: "...into the routine at $D275",
})
CC(0xD5EF, {
 0xD5EF: "Room A's record ($D224)",
 0xD5F2: "IX + 6 = its exits",
 0xD5F7: "BC = 3, the size of an exit",
})
CC(0xE28D, {
 0xE28D: "The actor ($A036) against the direct object ($A034)",
 0xE294: "Same: fail ($DC15)",
})
CC(0xE6BE, {
 0xE6BE: "The indirect object ($A035): is anything held by it ($E619)?",
 0xE6C4: "None: return NZ",
 0xE6C6: "DE = the word at IX+9/+10",
})
CC(0xE710, {
 0xE710: "Keep the output switch $5C3C",
 0xE714: "($CFB6)",
 0xE717: "The record's flags (+3)",
})


CC(0xA0EB, {
 0xA0EB: "Load: restore the saved game ($B0D7)...",
 0xA0EE: "...and carry on at $A040",
 0xA0F1: "Save: write the game out ($B0E4)...",
 0xA0F4: "...and carry on at $A064",
})
CC(0xA11C, {
 0xA11C: "Save IY, HL, DE, BC",
})
CC(0xA277, {
 0xA277: "Save IX, HL, BC, AF",
})
CC(0xA679, {
 0xA679: "DE = the word at IX+1/+2 (a length)",
 0xA67F: "IX moves on by that length less one",
})
CC(0xA709, {
 0xA709: "Take the next message parameter ($A66C)",
 0xA70C: "Name it ($A80E)",
 0xA70F: "Z, A = 0",
})
CC(0xA82F, {
 0xA82F: "Actor $FF?",
 0xA831: "No: name the thing ($A751)",
 0xA834: "Yes: print the word $080E ($A887)",
})
CC(0xBB5C, {
 0xBB5C: "IX = the record found ($BA65)",
 0xBB60: "HL = its handler at +3/+4",
 0xBB66: "Jump to it",
})
CC(0xC1C0, {
 0xC1C0: "($C1CB)",
 0xC1C3: "($C415)",
 0xC1C6: "Print a carriage return (13) ($C1FD)",
})
CC(0xC1FC, {
 0xC1FC: "Restore AF, then (entry $C1FD) save HL, BC, AF",
})
CC(0xC421, {
 0xC421: "Save IX, HL, DE, BC",
})


CC(0xC571, {
 0xC571: "$A00F = the record header's low nibble of byte 0",
 0xC57A: "$A010 = the low nibble of byte 1",
})
CC(0xC929, {
 0xC929: "Set up the objects' records ($C8EF)",
 0xC92C: "Direct object $FE or more (a number or nothing)? Jump to $C972",
})
CC(0xC941, {
 0xC943: "Look the verb up in the shared actions table ($D349)",
 0xC949: "$FF = no shared action",
})
CC(0xC9F5, {
 0xC9F5: "A zero: return NZ (nothing to do)",
})
CC(0xCC24, {
 0xCC26: "Restore BC, DE and return",
})
CC(0xCFEE, {
 0xCFEE: "Copy the link bytes (IX-2/-1) to IY-2/-1",
})
CC(0xD045, {
 0xD045: "The player (first actor, $9860)...",
 0xD048: "...its room ($D495)...",
 0xD04B: "...stored as the room the player sees ($A009)",
})
CC(0xD0DD, {
 0xD0DD: "Save A; room record ($D224)",
 0xD0E1: "Test the flag at $D0DC",
})
CC(0xD29D, {
 0xD29D: "Random number 0 to 99 ($D2A4)...",
 0xD2A2: "...plus one: 1 to 100",
})
CC(0xD4CC, {
 0xD4CC: "Save IX, IY, HL, BC",
})
CC(0xD6DF, {
 0xD6E0: "Unknown word: HL = $D6E5 (the routine that says so), Z",
})
CC(0xE31C, {
 0xE31C: "The direct object's record ($A013)",
 0xE320: "+6 bit 5 clear: fail ($DC15)",
})


CC(0x9EC1, {
 0x9EC1: "HL = the character's countdown byte ($9EC0)",
 0x9EC4: "C = $80, B = $4A",
 0x9EC8: "Join the common code at $9ED7",
})
CC(0xDC15, {
 0xDC15: "Fail: A = 0, HL = 0 (Z set)",
})
CC(0xDB5F, {
 0xDB5F: "Step HL back one",
 0xDB60: "Z with A = $F0 (a time was read)",
})
CC(0xC458, {
 0xC458: "(Restore the remaining registers)",
})
CC(0xC3A8, {
 0xC3A8: "Count C down; loop until zero",
})
CC(0xC3B9, {
 0xC3B9: "C = 8 - C",
})
CC(0xC1D5, {
 0xC1D5: "Jump to $C1CB",
 0xC1D8: "HL = $13C5; ($C1C0); then on to $A0EB",
})


# ---------------------------------------------------------------------
# 8 November, night: the first playthrough without pokes (partial)
# ---------------------------------------------------------------------
for _i, (_eid, _title, _body) in enumerate(FACTS):
    if _eid == 'catch-the-major':
        FACTS[_i] = (_eid, _title, _body.replace(
            "the Major's night-time trip was read from his script.",
            "CONFIRMED BY PLAY the same night, with no pokes (tools/experiments/"
            "playthrough/monday_to_major.cmds): the Major leaves his house at "
            "11:03pm on Monday, goes through Sidmouth Street's heavy oak door, "
            "upstairs and back, hails a cab to Slater Street and goes through "
            "the hidden door into the den. The hidden door is narrower than "
            "Holmes (size 85 against 96, see $DD35), so the player has to "
            "wear the china man's disguise (size 80) to follow; standing in "
            "the den as the china man the Major says nothing, but the moment "
            "the disguise is TAKEN OFF inside he says 'WELL HOLMES YOU HAVE "
            "FOUND OUT MY SHAMEFUL SECRET...' ($996F becomes $0A). Out on "
            "Slater Street, SAY TO LESTRADE \"MAJOR PERCIVAL FFOULKES VISITED "
            "OPIUM DEN\" (Lestrade turns up there by himself; the statement "
            "may be said while still in disguise) gives 'Very good Holmes, I "
            "shall return to Leather head tomorrow...' and $9E88 = 1 at "
            "12:14am on Tuesday - 46 minutes before the 1am ending at $9E85. "
            "Saying MAJOR PERCIVAL FFOULKES IS INNOCENT to Lestrade earlier "
            "(he was in Jones's library with the Major at 1:44pm) makes it "
            "wait, as the page The case says."))

fact('disguise-needs-a-trick',
     "The disguise cannot be picked up with the lamp - but WEAR then TAKE OFF carries it",
     "In Holmes's closet at the start, TAKE CHINA MANS DISGUISE answers 'I SEE NO "
     "CHINA MANS DISGUISE THAT YOU CAN TAKE' while the player carries the oil "
     "lamp and his money: the disguise (size 128) does not fit under the "
     "player's carrying limit. Dropping the lamp first lets it be taken (the "
     "capacity rule itself was not read; this is what the emulator did). WEAR CHINA MANS DISGUISE works straight from the room, though - "
     "it never has to be held - and TAKE OFF CHINA MANS DISGUISE afterwards "
     "leaves the disguise in the player's inventory next to the lamp and the "
     "money: 'You are carrying a china mans disguise, an oil lamp and your "
     "money.' Both were typed in the emulator. This is how the playthrough "
     "carried it to Slater Street (the lamp is needed in the dark). While "
     "worn, the player's actor is thing 1, the china man: LOOK says 'The china "
     "man is in...' and the harness lists the room as '0 0'. Watson follows "
     "as far as he fits; he stayed outside the hidden door.")

fact('wall-safe-trap',
     "Opening Basil's wall safe on Monday gets you shot",
     "The wall safe in Basil's library at Cobden Lane in Leatherhead (thing 89, "
     "room 58) holds the letters. Typing OPEN WALL SAFE there on Monday ends the "
     "game: 'Basil enters and says \" Holmes, your interference is becoming "
     "annoying. \" . Pulling a gun he shoots you.' (confirmed by play, 4:07pm). "
     "The check is the first record of shared action 21 ($DFB6): thing $59 and "
     "day 0 (Monday) lead on to the shooting message at $DFCC; any other day "
     "falls through to the ordinary OPEN. EXAMINE CLOSELY WALL SAFE is harmless. "
     "So the letters can only be taken from Tuesday on.")

fact('basils-london-house',
     "Basil's Camden Street house: what was observed, and the wall in the way",
     "Observed with nobody interfering and in the playthrough: the front door "
     "(thing 91) and the bedroom window (thing 79) start locked. Phipps arrives "
     "by cab at 9:35am on Tuesday, opens the front door at 9:37 and goes in; the "
     "door is shut again at 9:40 and relocked. At 10:03pm 'Someone opens the "
     "window' - he is in the bedroom (room 35) from then on, hidden (his +5 bit "
     "6 cleared), and the ripped coded note (room 38), the torn coded note (39) "
     "and the burning note (35) were all still in place at midnight (the script "
     "deletes the first two when it runs $EEC6 later that night, if both are "
     "still there; the burning note goes at 9am on Wednesday, $EF0C). Entering "
     "the bedroom through the open window while he is in it: 'Basil says \" "
     "Holmes, your interference is becoming annoying. \" . Pulling a gun he "
     "shoots you.' (tried at 12:01am). The front door's size is 32: with the "
     "door open (9:38am, straight after Phipps went through) NORTHEAST from "
     "Camden Street still says YOU CANNOT GO NORTHEAST - Holmes (96) and the "
     "china man (80) are both too big, only Lestrade (32) and the smaller "
     "characters fit. Neither door nor window can be unlocked by the player "
     "(UNLOCK FRONT DOOR: 'I SEE NO FRONT DOOR THAT YOU CAN UNLOCK'; UNLOCK ... "
     "WITH is not a verb). So the three notes that PHIPPS HAS PLANS and THE SALE "
     "LOCATION IS OLD MILL ROAD need could not be reached by the means tried. "
     "Not tried: getting Lestrade (who is small enough) to go in, which needs a "
     "moment when his script takes orders; his order handling shows 'Sorry, I "
     "cannot do that now' when busy.")

fact('large-rock-tuesday',
     "The large rock: EXAMINE CLOSELY DEEP STREAM, on Tuesday, east of the bridge",
     "(Corrected by the next fact: Lestrade must be in the room too.) Read from the code: the record at $E0AD (shared "
     "action 16, EXAMINE CLOSELY the deep stream) does nothing unless the "
     "player is in room 88 (the east side of the sandstone bridge) AND it is "
     "Tuesday (day 1). Then it marks the large rock seen and visible, moves it "
     "into the player's room and prints 'AS YOU SEARCH THE RIVER LESTRADE "
     "COMES OVER TO HELP. HE STUMBLES AND SLIDES DOWN THE BANK AND NOTICES A "
     "GLEAM IN THE WATER. REACHING IN HE PULLS OUT A GUN TIED TO A LARGE ROCK'. "
     "The rock is seen, which is all MRS BROWN KILLED HERSELF needs of it, so "
     "that statement cannot be proven on Monday. (The Monday visit to room 88, "
     "12:40-12:58pm, left the rock hidden, as expected.)")

page('the-playthrough', 'A playthrough without pokes (partial)',
     '<p>Everything on this page was typed into the emulator from a fresh boot. '
     'The commands are in <code>tools/experiments/playthrough/monday_to_major.cmds</code> '
     'and <code>tools/experiments/replay_log.py</code> replays them (the game is '
     'deterministic). It stops at <b>Tuesday 12:14am</b>: the game is not finished '
     'and the way on is blocked, see the end.</p>'
     '<table><tr><th>Clock</th><th>What happened</th></tr>'
     '<tr><td>Mon 8:02</td><td>Start in Holmes\'s sitting room. Lamp taken; WEAR CHINA MANS DISGUISE and TAKE OFF in the closet (see the fact about the disguise); SAY TO WATSON "FOLLOW ME".</td></tr>'
     '<tr><td>8:26-9:59</td><td>OPEN YOUR DOOR, WEST, DOWN, OPEN FRONT DOOR, SOUTH, HAIL CAB, CLIMB INTO HANSOM CAB, SAY TO CABBIE "GO TO KINGS CROSS ROAD"; the ride takes about 80 minutes if the cab really moves (see the stale-quotes fact); on arrival PAY 10D TO CABBIE (never GIVE MONEY).</td></tr>'
     '<tr><td>10:45-12:00</td><td>Four NORTHEAST to platform three, the steam train at 10:45, Leather Head platform one at 12:00.</td></tr>'
     '<tr><td>12:27</td><td>At Browns Front Gate Lestrade and Straker arrive and Lestrade introduces Straker ($9D90 = 1); the gate is passable from then on.</td></tr>'
     '<tr><td>12:42-12:58</td><td>Room 88: female corpse and sandstone bridge examined closely, crumpled note taken and read ("Meet me by the bridge at half past twelve... P. F.").</td></tr>'
     '<tr><td>1:25-1:51</td><td>Jones\'s house. Lestrade, Straker and the Major are in the library at 1:43; SAY TO LESTRADE "MAJOR PERCIVAL FFOULKES IS INNOCENT" makes the statement wait. Body, bookcase and the bloodstained clothes (labelled "Tricia. Fender.") examined closely.</td></tr>'
     '<tr><td>2:22-2:51</td><td>Brown\'s study: drawer, false bottom, bank account book and note examined closely.</td></tr>'
     '<tr><td>3:15-4:30</td><td>The 3:25 train from platform two, shared with Lestrade, to Kings Cross platform four.</td></tr>'
     '<tr><td>4:47-11:52pm</td><td>Hansom cab to Slater Street. (My wait loop overshot: the cab, shared with Lestrade, was at Parliament Street by 11:31pm; a second ride, 27 minutes, got to Slater Street at 11:52.)</td></tr>'
     '<tr><td>Tue 12:00-12:14</td><td>The den, the confession and Lestrade\'s "Very good Holmes": the Major is cleared ($9E88 = 1).</td></tr></table>'
     '<p>Evidence flags at the end (read from memory, only to confirm): female corpse, '
     'sandstone bridge, body, bookcase, bloodstained clothes, bank account book and note all '
     'examined; Straker introduced; Major cleared. Not yet: the large rock '
     '(Tuesday, see the fact about it), the unfinished note and folder (Tricia\'s '
     'lounge, Tuesday 8:10am-2pm), the letters (Basil\'s safe at Cobden Lane, not '
     'on Monday), the two coded notes and the burning note (Basil\'s Camden Street '
     'house), and the markers $998F and $9993.</p>'
     '<h3>What the run corrected</h3><ul>'
     '<li>The wait loop of the first attempt ran through a whole evening because its stop word was split by the line wrap: stop words must be one word that cannot wrap.</li>'
     '<li>The 4:55pm Leatherhead train does arrive at platform four at 6:00pm, as the timetable fact says.</li>'
     '<li>Lestrade rides the 3:25 train from Leatherhead to Kings Cross with the player.</li>'
     '<li>The 1am Tuesday ending (#R$9E85) really happens: waiting in Camden Street at 1:07am on a line that had not cleared the Major ended the game with Lestrade\'s "that wraps up this case".</li>'
     '<li>The opium den and the Major\'s innocence are reachable without pokes, but only with the disguise.</li></ul>'
     '<h3>Where it was blocked (since solved: see the next page)</h3>'
     '<p>PHIPPS HAS PLANS needs the ripped coded note and the torn coded note, which '
     'lie in Basil\'s Camden Street house; see the fact about that house. With the '
     'means tried (walking in, the open window, unlocking) the player cannot get '
     'at them, so THE SALE LOCATION IS OLD MILL ROAD cannot be proven and Lestrade is '
     'not sent to Old Mill Road. This is <b>not</b> a claim that the game is '
     'unwinnable: one route is untried (ordering Lestrade, who is small enough '
     'for the door, to go in) and an earlier version of these notes called a '
     'different dead end final and was wrong.</p>')

for _i, (_eid, _title, _body) in enumerate(FACTS):
    if _eid == 'the-case-table' and False:
        pass


# ---------------------------------------------------------------------
# 8 November, late: the way into Basil's Camden Street house, found (a text
# solution said to wait for the window to be opened at about 10pm)
# ---------------------------------------------------------------------
for _i, (_eid, _title, _body) in enumerate(FACTS):
    if _eid == 'basils-london-house':
        _body = _body.replace(
            "So the three notes that PHIPPS HAS PLANS and THE SALE "
            "LOCATION IS OLD MILL ROAD need could not be reached by the means "
            "tried.", "That is how it looked by walking in as Holmes.")
        FACTS[_i] = (_eid, _title, _body + "\n\n"
            "THE WAY IN, found with a hint from a published text solution (the "
            "SHERLOCK.TXT file in the World of Spectrum / ftp.icm.edu.pl game "
            "database; its page was not read in full) and then run in the emulator, "
            "no pokes: the shooting has two triggers. While Phipps counts down "
            "after opening the window (from 10:03pm on Tuesday for 55-75 minutes, "
            "$EEAF) he shoots only if the player's own actor, id 0, is in his "
            "room; the other trigger, $EFC7, shoots whoever is anywhere in rooms "
            "33-39 but is only run after the countdown, an hour or more later. "
            "So: WEAR CHINA MANS DISGUISE in Basil's front yard right after "
            "'Someone opens the window' (10:03pm), go NORTHEAST into the "
            "bedroom - Phipps is there and does nothing - through the large oak "
            "door to the hall, NORTHEAST to the passage, and the library (thick "
            "heavy door, southeast) and the yard (plain door northeast to the "
            "kitchen, back door northeast) are open. In the dark the lamp is "
            "carried. EXAMINE CLOSELY done as the china man only marks a thing "
            "SEEN (+6 bit 7, 'The china man closely examines...'); to get the "
            "EXAMINED bit (+6 bit 6) TAKE OFF the disguise first - in the "
            "library, away from Phipps, that is safe during the countdown. Done "
            "this way by 10:55pm: ripped coded note $C0 and torn coded note $40 "
            "(both examined), then WEAR again before re-entering the bedroom, "
            "SOUTHWEST out of the window at 11:07pm, still alive. The burning "
            "note is not in the fireplace at that time (TAKE BURNING NOTE: 'I SEE "
            "NO BURNT NOTE'); it is put there on Wednesday morning ($EF0C).")
page('the-playthrough-2', 'Playthrough, continued: into Basil\'s house',
     '<p>Continuing the position of A playthrough without pokes (Tuesday 12:50am), '
     'by typed commands: wait in Camden Street; Phipps arrives at 9:35am; at '
     '10:03pm the window opens; WEAR CHINA MANS DISGUISE, NORTHEAST, collect the '
     'ripped and torn coded notes as described in the fact about Basil\'s Camden '
     'Street house. That run waited through Tuesday, so it missed what Tuesday is '
     'for (Tricia on stage 8:05am-2pm; the large rock; the letters), and it is a '
     'test of the entry, not the final line. The route to try next: Monday as '
     'before but carrying the bloodstained clothes away from Jones\'s house, '
     'Tuesday morning Tricia, then Leatherhead for the rock and letters, then '
     'back to Camden Street before 10pm.</p>')

fact('stale-quotes-cabbie',
     "Quoted speech is queued: a cabbie can ignore a destination until old quotes are flushed",
     "Every quotation typed in a SAY TO is added to a list at $9FEC ($B049); "
     "the SAY that runs takes the FIRST node off it ($B86A). A SAY that fails "
     "before it gets that far (I SEE NO TRICIA FENDER THAT YOU CAN TALK TO, "
     "or a person who simply does not answer) leaves its quote behind, so "
     "every later SAY delivers the quote that was typed N commands earlier, "
     "N being the number of leftovers. Seen in the emulator: with 3-4 "
     "leftovers SAY TO CABBIE \"GO TO KINGS CROSS ROAD\" got 'You talk to "
     "the cabbie.' and nothing else, and the cabbie asked 'Well are we goin' "
     "anywhere guv'nor?' until the SAY had been typed once more than there "
     "were leftovers, when the cab set off at once (breakpoints showed shared "
     "action 14, GO TO, at $9AF6 was simply not reached before). The cure "
     "that works is TALK TO <anyone present> with no quotation, which empties "
     "the list. Earlier pages that said a cab ride 'takes 80 minutes' were "
     "wrong: that was my wait loop running on while the cab sat still.")

fact('pay-not-give-money',
     "Pay a cabbie with PAY 10D TO CABBIE, not GIVE MONEY TO CABBIE",
     "GIVE MONEY hands over the whole purse (thing 27) to the cabbie, who "
     "keeps it; after that INVENTORY shows no money, PAY says DON'T BE "
     "SILLY, and the cabbie nags 'What about me money guv'nor?'. PAY 10D TO "
     "CABBIE ($E370) takes the sum off the purse and the cabbie gives change "
     "('You pay 10d. To the cabbie. The cabbie pays 4d. To you.'), "
     "and the purse stays with Holmes. A cab that has been paid goes away at "
     "once; an unpaid one waits for you.")

fact('lestrade-cab-clash',
     "Lestrade rides the same cab: keep out of cabs at 12:20-12:45am and 7:05-7:20am",
     "Lestrade hails a cab twice in the night: Scotland Yard side at about "
     "12:20am (Slater Street to Parliament Street) and from Parliament Street "
     "at 7:05am (to Kings Cross Road, then the 7:30 train to Leatherhead, "
     "where he is at the stream, rooms 88-89, from about 9:15 to 10:05am). If "
     "the player is riding a cab then, Lestrade is left sitting in the other "
     "cab (33) at its off-stage room for the rest of the game, and "
     "everything that needs him (the rock) cannot happen.")

fact('large-rock-needs-lestrade',
     "The rock needs Lestrade in the room: Tuesday morning, east side of the bridge",
     "Corrects the fact on the rock above. Shared action 16's script runs "
     "$E0AD with Lestrade (actor 2) as direct object, and nothing happens "
     "unless he is in the room with the player. Played: arrive at the east "
     "side (room 88) by about 9:20am on Tuesday, wait for 'Inspector "
     "Lestrade enters', then EXAMINE CLOSELY DEEP STREAM; he finds the gun "
     "tied to a large rock. (The first examine, before he came in, printed "
     "only 'You see a deep stream.') He leaves at about 10:05am, and "
     "his return train is at 12:20pm. The train out to Leatherhead that "
     "reaches the station at about 9:00am is the one leaving Kings Cross "
     "platform four at 7:30am.")

fact('tuesday-ordering',
     "Tuesday's order of work that fits the clock",
     "Played without pokes: 12:55am cab to Kings Cross Road; 7:30am train; "
     "9:00 Leatherhead; 9:20 rock with Lestrade; letters from Basil's "
     "library safe by 10:05 (OPEN WALL SAFE takes 15 minutes; TAKE LETTERS "
     "then EXAMINE CLOSELY); the 10:55 train from platform two reaches Kings "
     "Cross at noon; Tricia is in her lounge until 2pm, so ask about the "
     "clothes (second SAY, the first is swallowed by the leftover quote), "
     "then Mrs Jones about her alibi, open her safe (15 minutes) and examine "
     "the unfinished note and the folder; then Scotland Yard for the "
     "statements, TALK TO LESTRADE first to flush quotes; Camden Street's "
     "window opens at 10:03pm.")


fact('burning-note-typed',
     "The burning note: TAKE NOTE FROM FIREPLACE, then drop and plain TAKE it",
     "Played without pokes on Wednesday. The note appears in the bedroom "
     "fireplace (room 35) at about 10:05am and burns away over the next "
     "15 turns. Phipps shoots anyone in the bedroom at 9:50am, even in "
     "disguise, so go in only after he has left the house (hall 10:06, street "
     "10:09, gone by 10:13); the window stays open and Basil's own chase does "
     "not start until the sale statement is proven. 'TAKE NOTE FROM FIREPLACE' "
     "works but takes the note through the plain action, so the countdown "
     "keeps running. DROP BURN NOTE then TAKE BURN NOTE runs shared action "
     "20 ($DF7E/$DF8B), which sets the countdown $9CA1 to $FF (stopped) and "
     "renames the note 'singed' ($07D5); EXAMINE CLOSELY SINGE NOTE then "
     "counts as examining the evidence and the case record $99B7 keeps its "
     "proof bit. The parser quirk that cost most of an hour: the dictionary "
     "stores BURNING and BURNT with the same first four letters, and a typed "
     "BURNING resolves to the word BURNT, so 'EXAMINE BURNING NOTE' says "
     "'I SEE NO BURNT NOTE'. 'EXAMINE BURN NOTE' (four letters) resolves to "
     "the right word, and 'SINGE NOTE' works once it is singed.")

fact('the-win-typed',
     "The winning line from Wednesday 10:53am, typed",
     "SAY TO LESTRADE \"THE SALE LOCATION IS OLD MILL ROAD\" in Scotland "
     "Yard at 10:53am (the singed note examined, PHIPPS HAS PLANS already "
     "proven) and Lestrade sets off at once. Follow him and keep behind: "
     "hansom cab (not Lestrade's) to Kings Cross Road, the 12:00 train from "
     "platform four, and get OUT at Leather Head platform one at 1:30pm "
     "(riding on to platform two loses 15 minutes and the police cab). SOUTH "
     "twice to the main street and, without a LOOK in between, CLIMB INTO "
     "POLICE CAB at 1:37pm, the minute Lestrade does: you, Watson and "
     "Lestrade fit and Straker stays out. The cab reaches Old Mill Road at "
     "3:13pm, Phipps bolts at 3:14, back in the main street at 4:47. CLIMB "
     "OUT, NORTH three times to platform two (4:54), SAY TO LESTRADE \"FOLLOW "
     "ME\" once he takes orders at 4:56, SOUTH three times, CLIMB INTO POLICE "
     "CAB and SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS CROSS ROAD\" at "
     "5:06 (no TALK TO, no extra LOOK: every minute counts), arriving 6:21. "
     "CLIMB OUT, NORTHEAST twice to platform one, CLIMB INTO TRAIN the moment "
     "it is in (6:28, before it pulls out at 6:29, so that Lestrade, who "
     "follows a turn behind, gets on), ride to Victoria platform one (6:41), "
     "CLIMB OUT and WAIT: Basil walks in at 6:42 and the game ends with "
     "'YOU TRULY DESERVE THE TITLE OF WORLDS GREATEST DETECTIVE'. Do it a "
     "minute or two later and Lestrade misses the train or Phipps leaves "
     "Victoria first. The whole run from the first command is "
     "tools/experiments/playthrough/v11_full_win.cmds (444 lines, with dead "
     "ends) and the cleaned v12_clean_win.cmds (372 lines).")

# ---- Trivia from the unpoked win (8 November, night) -------------------
fact('followers-lag-one-turn',
     "Lestrade and Watson follow one turn behind you, so a train can leave without them",
     "Seen at Kings Cross platform one on Wednesday evening. The underground "
     "train entered at 6:26 and pulled out at 6:29. Arriving in the room at "
     "6:28 and climbing in at once, the first time (one minute later than "
     "the winning run), Watson came aboard but Lestrade, who was still "
     "walking in, did not: the train left with Watson only, and the game "
     "could not be won from there. In the winning run you arrive a minute "
     "earlier, CLIMB INTO TRAIN at 6:27-6:28, and both come in before it "
     "leaves. Anyone you have told to FOLLOW ME repeats your move on the "
     "next turn, so any departure with a fixed minute (trains, the police "
     "cab) needs a spare minute.")

fact('train-goes-on-to-platform-two',
     "Riding the Leatherhead train past your stop costs the police cab",
     "The steam train from Kings Cross platform four reaches Leather Head "
     "platform one at 1:30pm (if it left at noon), and then is 'shunted "
     "between platforms' to platform two, arriving there at about 1:45pm. "
     "Staying aboard to see where it goes (waiting for the text 'platform "
     "two') put me at the wrong platform fifteen minutes late; Lestrade had "
     "already left the station in the police cab and the winning window "
     "was gone. Get out at platform one and go SOUTH twice.")

fact('police-cab-seats',
     "The police cab fits four: you, Watson, Lestrade and the constable - not Chief Constable Straker",
     "In the main street at Leather Head on Wednesday: if you climb in the "
     "minute before Lestrade, the cab holds you, Watson and the local "
     "police man and drives off without him; if you wait until he and "
     "Chief Constable Straker have climbed in, 'I SEE NO POLICE CAB THAT YOU "
     "CAN CLIMB INTO'. Climbing in in the same minute as Lestrade (at 1:37pm "
     "after arriving on the 1:30pm train and walking SOUTH twice) gives you, "
     "Watson, Lestrade and the constable, and Straker is left standing on "
     "the pavement.")

fact('ordering-the-cab-strands-lestrade',
     "Giving the police cab your own orders leaves Lestrade behind",
     "At 4:47pm, back in the main street with Lestrade, Watson and the "
     "constable aboard, SAY TO POLICE MAN \"GO FURIOUSLY TO KINGS CROSS "
     "ROAD\" made the cab leave without Lestrade: he climbed out and "
     "walked north to the station, and 'Lestrade, Watson and you' became "
     "just Watson and you. Lestrade only takes an order from about 4:56pm, "
     "on platform two ('Sorry, I cannot do that now' before then and after "
     "the first successful FOLLOW ME), so the order to the cab has to be "
     "given only after he is following you again.")

fact('phipps-shoots-the-bedroom',
     "Basil's bedroom is deadly at 9:50am on Wednesday, even in disguise",
     "Waiting in the bedroom (room 35) in the china man's disguise through "
     "9:50am on Wednesday gets you shot: the game ends. The disguise "
     "protects you from the check on your own identity, not from the shot "
     "that is fired at whoever is in the room. Phipps is in the hall at "
     "10:06, in the street at 10:09 and in his cab by 10:13; the burning "
     "note is revealed in the fireplace at about 10:05 and, unless it is "
     "taken with a plain TAKE, is ashes by about 10:23.")

fact('burn-note-parse',
     "'EXAMINE BURNING NOTE' fails but 'EXAMINE BURN NOTE' works",
     "The dictionary has BURNING and BURNT together (the first four letters "
     "are shared). Typing BURNING, BURNIN or BURNINGS is read as BURNT and "
     "the game answers 'I SEE NO BURNT NOTE THAT YOU CAN EXAMINE', even "
     "while the note is called a burning note in your inventory. BURN alone "
     "is read as the right word. Likewise NOTE alone only gets 'WHICH NOTE "
     "?' and the reply to that question goes through the same parser, so "
     "answering BURNING does not help.")

fact('cab-change-and-fares',
     "Fares seen in the run: 2d from Camden Street to Parliament Street, 6d from Parliament Street to Kings Cross Road",
     "Paying with PAY 10D TO CABBIE, the cabbie gave change each time "
     "('You pay 10d. To the cabbie. The cabbie pays 8d. To you.' after the "
     "2d ride; 4d after a 6d ride). Two hansom cabs were standing in Parliament "
     "Street at once on Wednesday, one with Lestrade in it; HAIL CAB brought "
     "the free one and CLIMB INTO HANSOM CAB boarded it.")

fact('window-exit-bedroom',
     "The bedroom window works both ways: SOUTHWEST to the front yard, WEST to Camden Street",
     "The same window you enter by on Tuesday evening (NORTHEAST from the "
     "front yard, room 102) lets you leave on Wednesday morning without "
     "passing through the house: SOUTHWEST from the bedroom puts you in "
     "Basil's front yard and WEST there in Camden Street, where a hansom "
     "cab can be hailed at once. NORTHWEST through the large oak door "
     "said YOU CANNOT GO NORTHWEST while the door was shut (I did not try "
     "opening it that time), so the window was the way out used.")

fact('train-circle-timings',
     "The underground train: Kings Cross platform one at 6:29, Victoria platform one at 6:41, Paddington at 6:43",
     "The steam trains on the underground circle run on a fixed timetable. "
     "From Kings Cross platform one the 6:29 train reaches Victoria platform "
     "one at 6:41, so you have a minute to CLIMB OUT before Basil walks "
     "onto the platform at 6:42. Missing the 6:29 and taking the next train "
     "at 6:36-6:38 reaches Paddington at 6:43 and Victoria much too late: "
     "Basil is already at Buckingham Palace Road (room 29) at 6:40 and "
     "leaves the game when he finds nobody on the platform.")

fact('replay-is-deterministic',
     "The game is deterministic: the same typed commands always give the same game",
     "The whole unpoked win, 444 typed lines starting from a fresh boot, "
     "was replayed from the file and ended in exactly the same state (clock "
     "6:43pm, room 30, end flag set) as the live run, even though the live "
     "run was assembled over several sessions out of snapshots. Nothing in "
     "the game's random numbers changes with real time; the same command "
     "text and the same earlier history always give the same result.")


# =====================================================================
# 8 November, night: deep revision after the unpoked win
# =====================================================================
def _edit_fact(fid, fn):
    for _i, (_eid, _t, _b) in enumerate(FACTS):
        if _eid == fid:
            FACTS[_i] = (_eid, _t, fn(_b)); return
    raise KeyError(fid)

def _edit_page(pid, fn=None, title=None):
    for _i, _p in enumerate(PAGES):
        if _p[0] == pid:
            PAGES[_i] = (_p[0], title or _p[1], fn(_p[2]) if fn else _p[2]) + tuple(_p[3:]); return
    raise KeyError(pid)

# Basil's house: the old "not tried" ending is wrong now
_edit_fact('basils-london-house', lambda b: b.replace(
    "Not tried: getting Lestrade (who is small enough) to go in, which needs a "
    "moment when his script takes orders; his order handling shows 'Sorry, I "
    "cannot do that now' when busy.",
    "(Superseded: the untried Lestrade idea was never needed. The disguise "
    "and the window, below, work, and the whole thing was played without "
    "pokes.)"))

# The winning line was first staged with help, later typed with none
_edit_fact('the-last-scene', lambda b: b + "\n\n"
    "UPDATE, 8 November night: everything above was first staged with "
    "statements poked proven and a minute short. It has since been played "
    "from a fresh boot with typed commands only (v11_full_win.cmds, 444 "
    "lines; transcript v11_full_win.transcript.txt). The fix to the 'minute "
    "short' problem was GO FURIOUSLY TO KINGS CROSS ROAD to the police man "
    "(74 minutes instead of 95) after ordering Lestrade to FOLLOW ME on "
    "platform two, and boarding the 6:29 underground train from Kings Cross "
    "platform one in the minute before it leaves so that Lestrade (who follows "
    "a turn behind) gets in. See 'The winning line from Wednesday 10:53am, "
    "typed'.")

_edit_page('the-endgame', lambda h: '<p><b>Update:</b> this page describes the '
    'first staged win, with help (statements poked, Watson placed). The same '
    'ending has since been reached with typed commands only from a fresh '
    'boot: see the page <a href="the-walkthrough.html">The walkthrough, '
    'Monday to the win</a> and the fact \'The winning line from Wednesday '
    '10:53am, typed\'.</p>' + h)

# playthrough pages: part numbers, and the old "blocked" paragraph replaced
_edit_page('the-playthrough', title='Walkthrough part 1: Monday to the Major (no pokes)',
    fn=lambda h: h.replace(
    'It stops at <b>Tuesday 12:14am</b>: the game is not finished '
    'and the way on is blocked, see the end.',
    'It stops at <b>Tuesday 12:14am</b>. The game was finished later: parts 2 '
    'and 3 and the full walkthrough page carry on.'))
_edit_page('the-playthrough', fn=lambda h: h.split('<h3>Where it was blocked')[0] +
    '<h3>Where it was blocked (since solved)</h3>'
    '<p>PHIPPS HAS PLANS needs the ripped and torn coded notes in Basil\'s Camden '
    'Street house. Walking in as Holmes fails; the way in is the china man\'s '
    'disguise through the window at 10:03pm on Tuesday (part 2). The idea of '
    'sending Lestrade in was never needed.</p>')
_edit_page('the-playthrough-2', title='Walkthrough part 2: Tuesday and into Basil\'s house (no pokes)')

import walkthrough_steps as _ws
page('the-walkthrough', 'The walkthrough, Monday to the win (typed commands only)',
 '<p>Two routes win the game, both from a fresh start by typing commands only. This page follows one of them from Monday 8:02am to the arrest at Victoria '
 'on Wednesday 6:43pm: %d typed lines in %d stretches, every one listed. In each table, <em>Step</em> is the line number, '
 '<em>Type</em> is exactly what is typed, <em>Clock after</em> is the game clock once the command has run, <em>Where</em> is the room you are in '
 '(&ldquo;in disguise&rdquo; while the china man\'s disguise is on) and the last column is the game\'s own reply, shortened. '
 '&times;N means the line is repeated N times until the reply shows the quoted text. The game is deterministic, so typing these lines from a fresh start gives the same result.</p>'
 '<p>The winning log is <code>v12_clean_win.cmds</code> (372 lines); <code>v13_shadow_lestrade.cmds</code> is a second route that differs from 10:53am on Wednesday '
 '(see the trivia entry about it). Replay one with '
 '<code>python3 tools/experiments/replay_log.py tools/experiments/playthrough/v12_clean_win.cmds</code> '
 '(about 20 seconds), or with <code>replay_verbose.py</code> to print every reply. The rows below were produced from a replay of that log by '
 '<code>tools/experiments/walkthrough_steps.py</code>. The log was shortened by <code>tools/experiments/minimize_cmds.py</code>, which only tried to remove '
 'LOOK, INVENTORY and error-reply lines; every line was afterwards tested on its own by <code>tools/experiments/ablate_cmds.py</code> and the results are in the last column.</p>'
 % (len(_ws.STEPS), len(_ws.PHASES))
 + _ws.body()
 + '<p>Not done: TRICIA FENDER BLACKMAILED MRS BROWN was never said (not needed). '
 'The route is one that works, not the only one.</p>')

# Bug entries confirmed during the run
bug('stale-quote-queue', "A failed SAY TO leaves its quotation behind, so later SAYs deliver old speech",
    "Every quotation typed in a SAY TO is added to a list at $9FEC ($B049) "
    "and the SAY that actually runs takes the first node ($B86A). A SAY "
    "that fails earlier (I SEE NO ... THAT YOU CAN TALK TO, or a person "
    "who does not answer) never removes its node, so every later SAY "
    "delivers the quotation typed N commands earlier, N being the number of "
    "leftovers. Seen in the emulator: SAY TO CABBIE \"GO TO KINGS CROSS "
    "ROAD\" got only 'You talk to the cabbie.' and the cab sat still until "
    "the SAY had been typed once more than there were leftovers; TALK TO "
    "<person> with no quotation empties the list. A player who waits "
    "after such a SAY (the cab 'takes' 80 minutes) loses hours.")

bug('give-money-purse', "GIVE MONEY TO CABBIE hands over the whole purse",
    "The money is a single object (thing 27), so GIVE MONEY TO CABBIE gives "
    "the cabbie everything Holmes carries: INVENTORY then shows no money, "
    "PAY says DON'T BE SILLY and the cabbie nags 'What about me money "
    "guv'nor?'. PAY 10D TO CABBIE ($E370) takes only the sum and returns "
    "change. Seen in the emulator.")

bug('burning-parses-as-burnt', "BURNING NOTE is read as BURNT NOTE, so the burning note cannot be named",
    "While the note is called a burning note in the inventory, EXAMINE "
    "BURNING NOTE, DROP BURNING NOTE and READ BURNING NOTE all answer 'I SEE "
    "NO BURNT NOTE THAT YOU CAN ...'; BURNIN and BURNINGS fail the same way. "
    "NOTE alone asks WHICH NOTE ? and answering BURNING does not help. "
    "BURN (four letters) is read as the right word, and so is SINGE once "
    "the note has been taken properly. Seen in the emulator; the cause "
    "(BURNING and BURNT share their first four letters in the dictionary, "
    "and the typed word resolves to the later one) is a reading of the "
    "word tables, not traced.")

bug('take-from-skips-the-script', "TAKE NOTE FROM FIREPLACE takes the burning note without stopping it burning",
    "Only the plain TAKE runs shared action 20 ($DF7E/$DF8B), which sets the "
    "countdown $9CA1 to $FF and renames the note 'singed'. TAKE NOTE FROM "
    "FIREPLACE moves the note into the inventory and leaves the countdown "
    "running (seen: $9CA1 still falling), so the note burns to ashes while "
    "carried and the statement that needs it can no longer be proven. The "
    "cure is DROP then a plain TAKE.")

bug('lestrade-stuck-in-cab', "Riding a cab at the wrong time leaves Lestrade stuck in the other cab for good",
    "Lestrade hails a cab at about 12:20am and again at 7:05am on Tuesday. If "
    "the player is riding a cab at those times the two scripts collide and "
    "Lestrade stays in cab 33 at its off-stage room (pc $EBC5) for the rest "
    "of the game, so everything that needs him (the large rock, the "
    "statements, the chase) cannot happen. Seen in the emulator during the "
    "first Tuesday attempts.")

# the old trivia entry on the parse quirk is now a bug
FACTS[:] = [f for f in FACTS if f[0] != 'burn-note-parse']

# Timings measured on a clean state (player outside in Camden Street)
_edit_fact('phipps-shoots-the-bedroom', lambda b: b + "\n\n"
    "Measured with the player waiting in the front yard from Tuesday 11pm: "
    "Phipps is in the bedroom (room 35) through the night, the burning note "
    "is revealed at 10:05am and its countdown runs 15 to 0 once a minute, "
    "so it is ashes at 10:24am; Phipps is in the hall (33) at 10:06, in "
    "Camden Street (32) at 10:09 and in his cab by 10:15. The earlier "
    "no-interference log (phipps_route.py) shows him back out at 9:55am. "
    "Reconciled on 9 November: at $EEE9 Phipps checks whether you (room "
    "102, Basil's front yard, or Camden Street) or the china man are "
    "outside; if so he runs the messenger scene at $EFAC ('A MESSENGER "
    "ARRIVES AT THE DOOR...') and waits 15 minutes ($DDBE) before going. "
    "phipps_route.py has you indoors in the sitting room, so he leaves at "
    "once (Camden Street at 9:55am, the street at 10:00); with you in the "
    "front yard, as in the winning route, the same script reaches the hall "
    "at about 10:06 and the street by 10:10 (logged from the route's "
    "Tuesday-night position, script $EEE9 then $EF09, 15 minutes later). "
    "Both are right; they are different conditions.")

# ---- The endings, all played by typed commands (8 November, night) ---
page('the-endings-played', 'Every ending, reached by typed commands',
 '<p>Each ending below was reached from a fresh boot by typing only, with no pokes. '
 'The command files and the replies are in <code>tools/experiments/playthrough/endings/</code> '
 '(<code>*.cmds</code>, and <code>*.transcript.txt</code> from <code>tools/experiments/replay_verbose.py</code>). '
 'The game is deterministic, so each replays exactly. The earlier trivia entry '
 '\'How the case can end\' described several of these from the code or with pokes; this page replaces that.</p>'
 '<table><tr><th>File</th><th>How</th><th>Ending text (as printed)</th></tr>'
 '<tr><td>end1_monday_3pm</td><td>Do nothing: WAIT in the sitting room to 3pm Monday (never meet Lestrade with Straker).</td><td>"I do not think you are doing too well, surely Sherlock Holmes could do a better job than you have done so far."</td></tr>'
 '<tr><td>end2_major_arrested_tuesday_1am</td><td>Meet Straker at Browns Front Gate on Monday at 12:27, then wait. Without clearing the Major the game ends at 1:04am Tuesday.</td><td>Lestrade: "Well Holmes that wraps up this case, sorry you were not of more help but you cannot solve them all you know." Despite his assurances you cannot help feeling there should be more to this case.</td></tr>'
 '<tr><td>end3a_papers_nothing_proven</td><td>Clear the Major (to 12:14am Tuesday), then wait to 10:00am Thursday.</td><td>"Not only have you failed to solve the crimes at hand but the morning papers carry a report of Mr Browns lost plans being found and sold to a foreign power... disgraced for letting this happen."</td></tr>'
 '<tr><td>end3b_papers_both_murders_proven</td><td>As the winning route to 2:12pm Tuesday (Mrs Brown and Mrs Jones statements proven, Tricia had plans), then wait in Scotland Yard to 10:00am Thursday.</td><td>"You have done extremely well to solve the case at hand but the morning papers carry a report of Mr Browns lost plans being found and sold to a foreign power..."</td></tr>'
 '<tr><td>end4a_shot_wall_safe_monday</td><td>OPEN WALL SAFE in Basil\'s library at Cobden Lane on Monday (12:15pm in this run).</td><td>Basil enters: "Holmes, your interference is becoming annoying." Pulling a gun he shoots you. Perhaps you should try again.</td></tr>'
 '<tr><td>end4b_shot_window_as_holmes</td><td>Tuesday 10:03pm, NORTHEAST through the window as Holmes (no disguise).</td><td>The same shot, as soon as you are in the bedroom with Basil.</td></tr>'
 '<tr><td>end4c_shot_bedroom_wednesday_950</td><td>Enter the bedroom in the china man\'s disguise on Wednesday morning and wait there.</td><td>The game ends at 9:50am (the shot is fired at whoever is in the room).</td></tr>'
 '<tr><td>end5_victoria_without_lestrade</td><td>The winning route, but on the 6:29 train from Kings Cross without Lestrade (he follows a turn behind and misses it).</td><td>"As Basil enters he sees you and pulls a gun. With his usual skill his first shot disposes of you. Perhaps you should try again."</td></tr>'
 '<tr><td>end6_leave_lestrade_on_platform_two</td><td>The winning route up to 4:55pm on platform two at Leatherhead, then no FOLLOW ME: just WAIT. Lestrade says "...has eluded us Holmes." at 4:56 and leaves the platform; the game runs on to Thursday.</td><td>The same morning-papers text as end3b, at 10:00am Thursday.</td></tr>'
 '<tr><td>end7_eluded_at_scotland_yard</td><td>As end6 but ride Lestrade\'s own train and cab and walk into Scotland Yard at 8:02pm, then wait.</td><td>Lestrade at 8:04pm: "I am afraid that Basil has eluded us Holmes." He goes west; at 10:00am Thursday the papers ending ("You have done extremely well...").</td></tr>'
 '<tr><td>end8_victoria_without_watson</td><td>The winning route, but SAY TO WATSON "WAIT" in place of the idle LOOK on platform two at 4:54pm.</td><td>The same death as end5: "With his usual skill his first shot disposes of you."</td></tr>'
 '<tr><td>v13_shadow_lestrade (in playthrough/)</td><td>A second winning route: after the sale-location statement at 10:53am stay with Lestrade instead of travelling alone. WEST to Parliament Street, CLIMB INTO HANSOM CAB while Lestrade is in it (10:57), Kings Cross Road 11:11, platforms one to three, the 12:15pm train from platform three with him and Watson, Leatherhead platform one 1:30pm. From there the lines are the same as v12.</td><td>The winning text, at Victoria 6:43pm (replay prints it in about twenty seconds).</td></tr>'
 '<tr><td>v11_full_win</td><td>The winning route.</td><td>"...As incredible as it may seem you have solved this case. You truly deserve the title of worlds greatest detective."</td></tr></table>'
 '<p>Watson missing, Lestrade present: <code>end8_victoria_without_watson</code>. Telling Watson to WAIT in the cab, on the Victoria train, or fifteen minutes before leaving does not leave him behind (the order lapses and he follows); at Kings Cross Road it costs the minute Lestrade needs for the 6:29 train. The order works if it replaces the idle LOOK on platform two at 4:54pm: Watson stays, Lestrade still follows and every later time is unchanged, but at Victoria the first shot from Basil kills you, so the win needs Watson as well as Lestrade (the win text has Watson push you out of the way). Before this, three attempts without that trick were recorded in <code>endings/attempt_watson_missing_victoria.transcript.txt</code>; that file is kept as history.</p>')

_edit_fact('three-endings', lambda b: b + "\n\nUPDATE, 8 November night: every ending named here (3pm Monday, the Major's arrest at 1:04am Tuesday, the morning papers at 10am Thursday in both wordings, Basil's shots, Basil at Victoria with Lestrade missing; Watson missing with Lestrade present is end8: the same shot) was reached from a fresh boot by typed commands only; see the page 'Every ending, reached by typed commands'. The 3pm and Major endings are no longer 'poked' or 'read from the code' claims.")

fact('blackmail-statement',
     "TRICIA FENDER BLACKMAILED MRS BROWN does nothing but get a shrug",
     "Said to Lestrade in Scotland Yard on Tuesday after the other statements, "
     "he answers 'I do not see the importance of that Holmes.' and the only "
     "change in the case table ($9965) is that its record at $99F1 goes from "
     "$A4 to $A6 (proven); it has no evidence group and its routine ($9A0A) "
     "only marks itself done and sets a bit in the empty record that follows. "
     "It is not needed to win. Played: v12_clean_win_with_blackmail.cmds "
     "replaces the early, unnecessary sale-location attempt on Tuesday with "
     "this statement and still ends with the winning text. Putting it in as "
     "an extra line instead costs a minute, which shifts Lestrade's Wednesday "
     "cab so that the player and he board the same hansom cab (the fare is "
     "paid in garbage, 'Lestrade pays `4 19/8') and the run no longer wins: "
     "every minute counts in this route.")

fact('early-sale-statement-unneeded',
     "Saying THE SALE LOCATION IS OLD MILL ROAD on Tuesday afternoon is not needed",
     "The first attempt at 2:13pm on Tuesday (note not yet examined) only gets "
     "'I do not believe...' and was in the route by habit. Replacing it with "
     "another statement, or removing it, still wins; the one that counts is "
     "said again on Wednesday at 10:53am after the singed note is examined.")

_edit_page('the-case', lambda h: '<p><b>Update, 8 November night:</b> the whole chain on this page - '
    'every statement proven, including THE SALE LOCATION IS OLD MILL ROAD - has since been earned by '
    'typed commands only (no evidence or markers poked), and it ends in the win: see '
    '<a href="the-walkthrough.html">The walkthrough, Monday to the win</a>. The proof of the sale '
    'location needs the burning note examined before it burns to ashes (about 10:24am on Wednesday); '
    'the cure is DROP then a plain TAKE (fact \'The burning note...\').</p>' + h)
