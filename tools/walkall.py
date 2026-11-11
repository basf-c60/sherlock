"""Verify every decoded exit by playing it: for each room and exit, put the
player in the room (location byte $8CC9 and displayed room $A00A), open
the door in the way (record +5 bit 5, as shared OPEN does), type the
direction and read back where the player ended up."""
import sys, json
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import rooms as R, objects as O
from harness import Game

WORDS = {1: 'NORTH', 2: 'SOUTH', 3: 'EAST', 4: 'WEST', 5: 'NORTHEAST', 6: 'NORTHWEST',
         7: 'SOUTHEAST', 8: 'SOUTHWEST', 9: 'UP', 10: 'DOWN'}
RM = R.rooms()
ENT = {e['id']: e for e in O.entities()}
g0 = booted()
snap = bytes(g0.m.memory)
results = []
for r, room in RM.items():
    for d, door, dest in room['exits']:
        g = g0
        g.m.set_memory_block(0, snap)
        mem = g.m.memory
        mem[0x8CC9] = r; mem[0xA00A] = r
        # the room record of the last room anyone moved into ($DD24)
        a = room['address']; mem[0xDCFF] = a & 255; mem[0xDD00] = a >> 8; mem[0xDD01] = r
        if door:
            a = ENT[door]['address'] + 5
            mem[a] |= 0x20
        g.clear_output()
        out = run_with_bps(g, WORDS[d], [], None, max_slices=2500)
        now = mem[0x8CC9]
        results.append(dict(room=r, dir=WORDS[d], door=door, dest=dest, got=now,
                            ok=now == dest, out=text(out)[:120]))
        g.clear_output()
for x in results:
    if x['ok']:
        continue
    g.m.set_memory_block(0, snap); mem = g.m.memory
    r = x['room']; a = RM[r]['address']
    mem[0x8CC9] = r; mem[0xA00A] = r; mem[0xDCFF] = a & 255; mem[0xDD00] = a >> 8; mem[0xDD01] = r
    mem[0x8CBA + 2] = 8      # the player's size: 96 -> 8
    if x['door']:
        mem[ENT[x['door']]['address'] + 5] |= 0x20
    g.clear_output()
    run_with_bps(g, x['dir'], [], None, max_slices=2500)
    x['got_when_small'] = mem[0x8CC9]
    g.clear_output()
bad = [x for x in results if not x['ok']]
print(len(results), 'exits,', len(results) - len(bad), 'confirmed')
for x in bad:
    print('  ', x)
json.dump(results, open('source/exits_checked.json', 'w'), indent=0)
