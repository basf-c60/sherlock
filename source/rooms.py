"""
Decode Sherlock's rooms from the game's own data, following the code
that reads it ($D113 describes a room, $D224 finds its record, $D5EF/
$D60B walk its exits):

  $840B  room table: one 2-byte record address per room number (107)
  record byte 0    flags (bits 1-3 index a table at $D05A, not decoded)
  record +1..+6    up to three word slots naming the room (low 12 bits =
                   dictionary offset, as for entities; the noun's top
                   nibble is its article: 1 'a', 2 'an', 8 none)
  record +7/+8     address of the room's description message (0 = none);
                   $D16B prints it with the message interpreter
  record +9...     exits, 3 bytes each: direction (1 N, 2 S, 3 E, 4 W,
                   5 NE, 6 NW, 7 SE, 8 SW, 9 U, 10 D - the verb numbers),
                   the door/passage object in the way (0 = none), and
                   the destination room; ended by $FF.

Checked against play: room 8 (the sitting room) has north through the
plain door (object 50) to room 9, the closet the player walked into; room
9 has south through the same door back to 8.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dictionary as D

b, w = D.byte, D.word16
ROOM_TABLE = 0x840B
DIRS = {1: 'N', 2: 'S', 3: 'E', 4: 'W', 5: 'NE', 6: 'NW', 7: 'SE', 8: 'SW',
        9: 'U', 10: 'D'}


ROOM_RECORDS_END = 0x8B6F   # the last table entry points here: not a room


def room_addresses():
    out = []
    r = 0
    while True:
        p = w(ROOM_TABLE + 2 * r)
        if p == ROOM_RECORDS_END or not (0x8400 <= p < 0xA000):
            return out
        out.append(p)
        r += 1


def rooms():
    words = D.by_offset()
    out = {}
    for r, rec in enumerate(room_addresses()):
        names = []
        article = None
        for k in range(3):
            v = w(rec + 1 + 2 * k)
            if v & 0x0FFF:
                wd = words.get(v & 0x0FFF)
                if k == 0:
                    article = {1: 'a', 2: 'an'}.get(v >> 12)
                # As the game prints them: the noun without its suffix,
                # adjectives with it ("disgusting opium den").
                txt = (wd['stem'] if k == 0 else wd['word']) if wd else f'?{v & 0xFFF:03x}'
                names.append(txt.lower())
        exits = []
        p = rec + 9
        while b(p) != 0xFF and len(exits) < 12:
            exits.append((b(p), b(p + 1), b(p + 2)))
            p += 3
        out[r] = dict(number=r, address=rec, flags=b(rec), names=names, article=article,
                      description=w(rec + 7), exits=exits, end=p + 1)
    return out


def room_name(room):
    n = room['names']
    return ' '.join(n[1:] + n[:1]) if n else f"room {room['number']}"


if __name__ == '__main__':
    for r, room in rooms().items():
        ex = ' '.join(f"{DIRS.get(d, d)}->{dest}" + (f"[{door}]" if door else '')
                      for d, door, dest in room['exits'])
        print(f"{r:3d} @{room['address']:#06x} f={room['flags']:02x} "
              f"{room_name(room):28s} desc={room['description']:#06x}  {ex}")
