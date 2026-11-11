"""
Overlay 05: every message the game prints from a fixed address, as
rendered by the game's own interpreter in the emulator
(render_messages.py -> messages.json). Each message gets a data block
titled with its text, and every LD HL,<message> site gets the text as
its line comment, so the comments can never drift from a re-render.
"""

import json
import os
import sys
sys.path.insert(0, '.')
from build_skeleton import A, blk, note, fact

HERE = os.path.dirname(os.path.abspath(__file__))
MESSAGES = json.load(open(os.path.join(HERE, 'messages.json')))


def short(text, n=60):
    text = ' '.join(text.split())
    return text if len(text) <= n else text[:n - 3].rstrip() + '...'


blk(0x67B7, 'b', 'Message bytecode: everything the game prints',
    ["From the end of the dictionary ($67B7) up to the verb patterns at "
     "$8259, this is text in the message interpreter's bytecode ($A59F): "
     "a byte with bit 7 set starts a two-byte dictionary reference, $00-"
     "$1C are control codes (jump table at $A55D), $20-$3F are literal "
     "characters, $40-$5F introduce a run of packed 5-bit letters, and "
     "$60 and above are handled at $A83A.",
     "CORRECTED: the automatic code/data split had 23 'code' blocks in "
     "here, mostly starting on page boundaries ($6D00, $7000, ...). None "
     "of them is called or jumped to from anywhere; they came from this "
     "project's coverage map, which counted the printer's data reads as "
     "executed bytes. Two of them collided with message starts and broke "
     "the round trip, which is how this was found.",
     f"{len(MESSAGES)} messages are split out below: those printed by an "
     "LD HL shortly before a printer call, those loaded into HL or DE "
     "anywhere in code, those printed or said by plan scripts (PRINT "
     "and SAY TO, see $CC78), those only a room or thing record points "
     "to (room descriptions, for instance), and the rest, found by walking "
     "the bytecode from $67FF message by message. The 72 bytes before $67FF "
     "(this block) are not an ordinary message."])
A[0x67B7]['end'] = 0x8259

import rooms as _R
import objects as _O
_ROOMS = sorted(_R.rooms().items(), key=lambda kv: kv[1]['address'])
_ENTS = sorted(_O.entities(), key=lambda e: e['address'])


def _owner(p):
    """What record the 16-bit pointer at address p sits in."""
    if 0x840B <= p < 0x8B6F:
        best = None
        for r, room in _ROOMS:
            if room['address'] <= p:
                best = (r, room)
        if best:
            r, room = best
            return f'room {r} ({_R.room_name(room)}), whose record #R${room["address"]:04X} points to it at byte +{p - room["address"]}'
    best = None
    for e in _ENTS:
        if e['address'] <= p:
            best = e
    if best and p < 0x9570:
        return f'thing {best["id"]} ({_O.display_name(best)}), byte +{p - best["address"]} of its record #R${best["address"]:04X}'
    return None


for key, m in sorted(MESSAGES.items()):
    addr = int(key, 16)
    text = ' '.join(m['text'].split())
    _stop = {0x6830: ('$19', '$6833', 'prints the words the player typed inside the quotation marks'),
             0x6F62: ('$00', '$6F7C', 'prints words of the player\'s own command')}
    partial_note = ''
    if m['status'] == 'ok':
        status = ''
    elif addr in _stop:
        c, at, what = _stop[addr]
        status = ''
        partial_note = (f' The text shown stops at control code {c} at {at}, which {what}; '
                        'what follows depends on a real typed command, so only the part before it is given.')
        if text.endswith(' W'):
            text = text[:-2]
    else:
        status = ' (rendering stopped early: it needs a parameter the renderer does not supply)'
    used = ['$' + s for s in m['sites']] + [f'${s} (plan script)' for s in m.get('script_sites', [])]
    ptr = []
    for pa in m.get('table_pointers', []):
        o = _owner(int(pa, 16))
        ptr.append(f'the description of {o}' if o else f'a pointer at ${pa}')
    c0b = [f'${r.split()[1]}' for r in m.get('message_refs', []) if r.startswith('0B')]
    c02 = [f'${r.split()[1]}' for r in m.get('message_refs', []) if r.startswith('02')]
    mr = []
    if c0b:
        mr.append('called as a sub-message (control code $0B) at ' + ', '.join(c0b))
    if c02:
        mr.append('jumped into by control code $02 at ' + ', '.join(c02))
    mr_text = (' It is ' + ' and '.join(mr) + '.') if mr else ''
    rr = []
    own = {int(x, 16) + k for x in m.get('script_sites', []) for k in range(6)}
    for ra in m.get('record_refs', []):
        if int(ra, 16) in own:
            continue
        o = _owner(int(ra, 16)) if int(ra, 16) < 0x9570 else None
        rr.append(f'the word at ${ra}' + (f', in the record of {o.split(", whose")[0].split(", byte")[0]}' if o else ''))
    if rr:
        mr_text += ' Its address is stored as ' + '; '.join(rr) + '.'
    if used:
        where = 'Printed from: ' + ', '.join(used) + ('; also ' + '; '.join(ptr) if ptr else '') + '.' + mr_text
    elif ptr:
        where = 'No instruction loads it; it is ' + '; '.join(ptr) + '.' + mr_text
    elif m.get('found_by') == 'sub-message':
        where = 'No instruction loads it.' + (mr_text or ' Another message calls it as a sub-message.')
    elif m.get('found_by') == 'record pointer':
        where = 'No instruction loads it directly.' + mr_text
    elif addr == 0x7DC1:
        where = ('No instruction loads it.' + mr_text + ' It is the night-time half of the hansom cab description '
                 '(#R$7DE1): after "...IN A HANSOM CAB," control code $17 ($A6AC) asks #R$C00C whether it is night; '
                 'if so the next element, the $02 jump, runs and lands here, otherwise the jump is skipped and the '
                 'daytime sentence about the sun follows.')
    elif m['text'].strip() == 'WHAT' and not mr_text:
        where = ('Only the two bytes $7D $1D: the dictionary word WHAT, then an end-of-message code. No instruction, '
                 'record or other message points to it, and it sits right after the end of the message before it. '
                 'Why it is there is not known.')
    elif mr_text:
        where = 'No instruction loads it.' + mr_text
    else:
        where = ('No instruction or record was found that loads it directly. It follows the message '
                 'before it in the message area, and may be reached from another message by an offset '
                 '(codes $02 and $0B) or through a pointer worked out at run time.')
    where += partial_note
    blk(addr, 'b', f'Message: "{short(text, 70)}"',
        [f'Rendered by running the game\'s own message interpreter ($A59F) in '
         f'the emulator{status}: "{text}"',
         'Placeholders: the actor is "you", the direct object "the oil lamp", '
         'and ‹word› marks a word of the player\'s own command (control code '
         '$01), which needs parser state that no longer exists when rendering.',
         where])
    for site in m['sites']:
        note(int(site, 16), f'"{short(text)}"')

fact('messages-rendered',
     "Every fixed message, rendered by the game itself",
     "The message printer at $A59F is a bytecode interpreter: dictionary "
     "word references, packed 5-bit letters, literal punctuation and 29 "
     "control codes. Rather than decode that by hand, each of the "
     f"{len(MESSAGES)} messages found (in code, in the characters' plan "
     "scripts, as room descriptions, and by walking the message area) was rendered by running the interpreter in the emulator; "
     f"{sum(1 for v in MESSAGES.values() if v['status'] == 'ok')} render completely. They include "
     "the parser's complaints, Watson's and Lestrade's lines (\"SO MRS "
     "BROWN KILLED HERSELF, EXCELLENT HOLMES, ANOTHER BRILLIANT "
     "CONCLUSION.\"), and story events (\"AS YOU RUN YOUR HANDS OVER THE "
     "BOOKS YOU TOUCH A HIDDEN SPRING...\"). One of the game's own "
     "spelling slips survives in the data: a messenger \"DISSAPEARS DOWN "
     "THE STREET\".")
