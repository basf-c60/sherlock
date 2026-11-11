"""Do the staff go to bed at 9pm? Pokes $9D90 (introduced to Lestrade) so
the 3pm ending does not happen, then WAITs until after 9pm, watching the
cook (9), the gardener (8) and Strachan (5)."""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e for e in O.entities()}
g = booted(); mem = g.m.memory
mem[0x9D90] = 1
def st(i):
    a = ENT[i]['address']
    return f"room {mem[a+15]:3} +5 {mem[a+5]:02X} +9/10 {mem[a+9]|mem[a+10]<<8:04X}"
for n in range(200):
    out = run_with_bps(g, 'WAIT', [], None, max_slices=6000)
    t = text(out)
    h, ap = mem[0x9FE0], chr(mem[0x9FE2])
    if n % 20 == 0 or (ap == 'p' and h in (8, 9)):
        print(f'{h:2}:{mem[0x9FDF]:02}{ap} cook {st(9)} | gardener {st(8)} | strachan {st(5)}')
    if 'Perhaps you should' in t or 'PLAY SAVED' in t:
        print('game over:', t[-200:]); break
    if ap == 'p' and h == 9 and mem[0x9FDF] > 10:
        break
