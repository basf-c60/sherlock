"""Hail a hansom cab in Baker Street (room 5), ask for somewhere the cab
table ($9B7F) has no journey to, then for Parliament Street (table: 20),
and time the ride. You are put in Baker Street by poking the location."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
r = 5; a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
clock = lambda: f"{m[0x9FE0]}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
def say(c):
    g.clear_output(); out = text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))
    print(f'{clock():8} you {m[0x8CC9]:3} | {c:40} | {out[-260:]}')
    return out
say('HAIL CAB')
for _ in range(10):
    if 'stops' in say('LOOK').lower() or any(m[ENT[c]['address'] + 15] == 5 for c in (30, 33)):
        break
say('CLIMB INTO CAB')
say('SAY TO CABBIE "GO TO OLD MILL ROAD"')
t0 = m[0x9FDD] | m[0x9FDE] << 8
say('SAY TO CABBIE "GO TO PARLIAMENT STREET"')
t1 = m[0x9FDD] | m[0x9FDE] << 8
for _ in range(40):
    out = say('LOOK')
    if 'parliament' in out.lower():
        break
t2 = m[0x9FDD] | m[0x9FDE] << 8
print('minutes from the order to arriving:', t2 - t1)
