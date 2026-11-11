"""Ride a hansom cab from Baker Street to Parliament Street and do not pay; log what the cabbie
does, then try walking away, to see the consequences."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
walk = len(sys.argv) > 1 and sys.argv[1] == 'walk'
g = booted(); m = g.m.memory
r = 5; a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
clock = lambda: f"{m[0x9FE0]}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
def say(c):
    g.clear_output(); out = text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))
    print(f'{clock():8} you {m[0x8CC9]:3} cab30@{m[ENT[30]["address"]+15]:3} | {c:30} | {out[-230:]}')
    return out
say('HAIL CAB')
for _ in range(10):
    say('LOOK')
    if m[ENT[30]['address'] + 15] == 5 or m[ENT[33]['address'] + 15] == 5: break
say('CLIMB INTO CAB')
say('SAY TO CABBIE "GO TO PARLIAMENT STREET"')
for _ in range(40):
    out = say('LOOK')
    if 'that will be' in out.lower(): break
if walk:
    say('GET OUT OF CAB'); say('EAST')
for _ in range(14):
    say('LOOK')
