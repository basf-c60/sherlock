"""Wait through the game day with the player doing nothing, and log every move of the two hansom
cabs (things 30, 33) and the eight steam trains (things 36-43): a record is written whenever the
room in a vehicle's +15 changes."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e for e in O.entities()}
g = booted(); m = g.m.memory
ids = [30, 33] + list(range(36, 44))
clock = lambda: f"{m[0x9FE0]}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
last = {i: None for i in ids}
n = int(sys.argv[1]) if len(sys.argv) > 1 else 120
for k in range(n):
    g.clear_output(); run_with_bps(g, ' ' + (sys.argv[2] if len(sys.argv) > 2 else 'WAIT'), [], None, max_slices=6000)
    for i in ids:
        r = m[ENT[i]['address'] + 15]
        if r != last[i]:
            print(f'{clock():8} thing {i:2} room {last[i]} -> {r}')
            last[i] = r
