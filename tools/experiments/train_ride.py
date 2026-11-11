"""Stand on Kings Cross platform four (room 23), wait for a Leatherhead train, climb in and look
once a minute: log the clock, the room you are in and what LOOK shows, until the ride is over."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
r = int(sys.argv[1]) if len(sys.argv) > 1 else 23
a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
clock = lambda: f"{m[0x9FE0]}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
def say(c):
    g.clear_output(); out = text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))
    if c != 'LOOK' or 'train' in out.lower() or m[0x8CC9] != getattr(say, 'last', None) or 'You are in' not in out:
        print(f'{clock():8} you {m[0x8CC9]:3} | {c:22} | {out[-230:]!r}')
    say.last = m[0x8CC9]
    return out
for _ in range(200):
    out = say('LOOK')
    if 'train' in out.lower():
        break
say('CLIMB INTO TRAIN')
for k in range(int(sys.argv[2]) if len(sys.argv) > 2 else 80):
    out = say('LOOK')
say('GET OUT OF TRAIN'); say('LOOK')
