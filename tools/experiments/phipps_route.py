"""Where is Phipps over the week? Logs every change of his room (entity 6,
+15) with the clock, WAITing a minute at a time. Pokes away the 3pm ending
($9D90) and the Major's ending ($9E88) so the game keeps going."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
m[0x9D90] = 1; m[0x9E88] = 1
who = int(sys.argv[1]) if len(sys.argv) > 1 else 6
DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()
last = None
for n in range(4000):
    out = run_with_bps(g, ' WAIT', [], None, max_slices=6000)
    r = m[ENT[who]['address'] + 15]
    if r != last:
        nm = RM.get(r, {}).get('name', '?') if isinstance(RM, dict) else r
        print(f"{DAYS[m[0x9FE1] % 7]} {m[0x9FE0]:2}:{m[0x9FDF]:02}{chr(m[0x9FE2])} room {r} {nm}", flush=True)
        last = r
    if 'PLAY SAVED' in text(out) or m[0x9FE1] >= 4:
        print('stop:', text(out)[-300:]); break
