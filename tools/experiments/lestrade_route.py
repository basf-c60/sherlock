"""Where is Lestrade, and where is his script, over the week, with both
murders, PHIPPS HAS PLANS and THE SALE LOCATION IS OLD MILL ROAD poked
proven? Logs changes of room (entity 2, +15) and script position ($9869)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e for e in O.entities()}
g = booted(); m = g.m.memory
m[0x9D90] = 1; m[0x9E88] = 1
for x in (0x9976, 0x9984, 0x999A, 0x99AC):
    m[x] |= 2
DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()
last = None
for n in range(4000):
    out = run_with_bps(g, ' WAIT', [], None, max_slices=6000)
    r = m[ENT[2]['address'] + 15]; pc = m[0x9869] | m[0x986A] << 8
    if (r, pc) != last:
        print(f"{DAYS[m[0x9FE1] % 7]} {m[0x9FE0]:2}:{m[0x9FDF]:02}{chr(m[0x9FE2])} room {r} script ${pc:04X}", flush=True)
        last = (r, pc)
    if 'PLAY SAVED' in text(out) or (m[0x9FE1] >= 2 and m[0x9FE0] == 4 and m[0x9FE2] == ord('p')):
        print('stop:', text(out)[-300:]); break
