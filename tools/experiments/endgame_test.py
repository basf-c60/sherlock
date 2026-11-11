"""The last scene, staged: you (and, unless left out, Watson and Lestrade)
wait on platform one at Victoria (room 30) while Phipps walks in from
Buckingham Palace Road (room 28) - his script pointed at $EF7F (EAST,
EAST, IS WITH you?, RUN $9E48). Watson and Lestrade are parked on the idle
loop at $F05C so they stay put.

    python3 tools/experiments/endgame_test.py [--no-lestrade] [--no-watson] [--absent]
"""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
m[0x9D90] = 1; m[0x9E88] = 1

def put(ent, r):
    m[ENT[ent]['address'] + 15] = r

def park(actor_entry):
    m[actor_entry + 1] = 0x5C; m[actor_entry + 2] = 0xF0

r = 31 if '--absent' in sys.argv else 30
a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
for ent, entry, flag in ((3, 0x9870, '--no-watson'), (2, 0x9868, '--no-lestrade')):
    park(entry)
    put(ent, 30 if flag not in sys.argv else 11)
put(6, 28)
m[0x9889] = 0x7F; m[0x988A] = 0xEF
g.clear_output()
for n in range(6):
    out = text(run_with_bps(g, ' WAIT', [], None, max_slices=6000))
    if 'BASIL' in out or 'PLAY SAVED' in out:
        i = out.find('AS BASIL'); print(out[i:i + 600] if i >= 0 else out[-600:]); break
else:
    print('nothing after 6 WAITs; Phipps in room', m[ENT[6]['address'] + 15], '|', out[-300:])
