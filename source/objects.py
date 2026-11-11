"""
Decode Sherlock's entity (actor/object/room) records from the game's own
data, using the layout established by the code that reads it:

  $8B6F  index: 3-byte records (id, record address), $FF-terminated
         (searched by $D34E, resolved by $D237)
  record byte 0      n: number of variable bytes (see $D1DC: the action
                     list starts at record + 15 + n)
  record +1          id of the thing that contains this one
                     ($FF = nothing; followed by $C86E, written by the
                     shared GET INTO / GET OUT actions)
  record +2          size (also capacity for containers - see the fit
                     check at $DEE4, confirmed by poking it)
  record +4          bits 0-2 nonzero: can hold things ($DEE4)
  record +5          bit 5: open (set/cleared by shared OPEN/CLOSE)
  record +7..        word slots: 2 bytes each, low 12 bits = dictionary
                     offset of a word (noun first, then adjectives),
                     a zero word ends the list. (Confirmed for the
                     player = YOU, Watson = WATSON, the armchairs =
                     ARMCHAIR + YOUR / WATSONS.)
  record +15..+14+n  the n LOCATIONS (room numbers) this thing is in. Most
                     things have one (n=1, so $D495's "room at +$0F"); a
                     door lists every room it connects (the plain door
                     between the sitting room (8) and closet (9) lists
                     ten rooms, 8 and 9 among them).
  record + n + 15    the object's own (verb, shared action) list,
                     $FF/$00-terminated ($D1DC)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dictionary as D

INDEX = 0x8B6F
b, w = D.byte, D.word16


def entities():
    words = D.by_offset()
    out = []
    a = INDEX
    while b(a) != 0xFF:
        oid, rec = b(a), w(a + 1)
        n = b(rec)
        names = []
        p = rec + 7
        while p < rec + 15 + n - 2:
            v = w(p)
            if v & 0x0FFF == 0:
                break
            wd = words.get(v & 0x0FFF)
            # A few slots point into the middle of a dictionary record
            # (e.g. $960, inside WAITS) - not resolved; shown as '?'.
            names.append((wd['stem'] if p == rec + 7 else wd['word']) if wd else f'?{v & 0xFFF:03x}')
            p += 2
        lst = rec + n + 15
        actions = []
        while b(lst) not in (0xFF, 0x00):
            actions.append((b(lst), b(lst + 1)))
            lst += 2
        out.append(dict(id=oid, address=rec, n=n, container=b(rec + 1),
                        size=b(rec + 2), flags4=b(rec + 4), flags5=b(rec + 5),
                        names=names, room=b(rec + 15),
                        locations=[b(rec + 15 + i) for i in range(n)],
                        actions=actions,
                        end=lst + 1))
        a += 3
    return out


def display_name(e):
    """Adjectives then noun, as the game prints them ('watsons armchair')."""
    if not e['names']:
        return '(unnamed)'
    return ' '.join(e['names'][1:] + e['names'][:1]).lower()


if __name__ == '__main__':
    for e in entities():
        print(f"{e['id']:3d} @{e['address']:#06x} {display_name(e):28s} "
              f"in={e['container']:3d} locs={e['locations']} size={e['size']:3d} "
              f"f4={e['flags4']:02x} f5={e['flags5']:02x} acts={e['actions']}")
