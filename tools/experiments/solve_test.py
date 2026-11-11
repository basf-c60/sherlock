"""Every true statement, told to Lestrade with all evidence poked in
(including the $9993 marker the game never sets - see the Bugs page)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
r = m[ENT[2]['address'] + 15]; a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r; m[0x8CBA + 1] = 0xFF
# Keep Lestrade where he is: point his script at the idle loop at $F05C
# (RUN $E5A8 / GOTO $F05C), so he still takes turns and answers remarks.
m[0x9869] = 0x5C; m[0x986A] = 0xF0
for t in (46, 57, 72, 66, 67, 87, 88, 90, 83, 81, 85, 64, 65, 93):
    m[ENT[t]['address'] + 6] |= 0xC0
for x in (0x9992, 0x9996, 0x9972):
    m[x] |= 2
STATE = [0x9968, 0x9976, 0x9984, 0x999A, 0x99AC, 0x99E6, 0x99F4]
for st in ('MRS BROWN KILLED HERSELF', 'MRS JONES KILLED TRICIA FENDER', 'PHIPPS HAS PLANS',
           'THE SALE LOCATION IS OLD MILL ROAD', 'TRICIA FENDER HAD PLANS',
           'TRICIA FENDER BLACKMAILED MRS BROWN', 'MAJOR FFOULKES VISITED THE OPIUM DEN'):
    out = run_with_bps(g, f' SAY TO LESTRADE "{st}"', [], None, max_slices=4000)
    t = text(out); i = t.rfind('You talk to')
    print(st, '|', ' '.join('%02X' % m[x] for x in STATE), '|', t[i:i + 260] if i >= 0 else t[-200:])
