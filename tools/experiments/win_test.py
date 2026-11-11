"""Try for the winning ending. Pokes both murders and PHIPPS HAS PLANS
proven (and the 3pm/Major endings out of the way), WAITs until START
(default Wed 11am), puts you and Watson next to Lestrade, pokes THE SALE
LOCATION IS OLD MILL ROAD proven, and from then on simply follows whoever
is named by FOLLOW (Lestrade, then Phipps once he has fled): walking
through the exit that leads to his room, climbing into the vehicle he is
in, climbing out when he does. Logs everyone's rooms and prints the end.

    python3 tools/experiments/win_test.py [START_HOUR_24] [--no-watson]
"""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
import overlay_04_actions as o4
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
VEH_ROOM = {1: 'HANSOM CAB', 2: 'TRAIN', 3: 'TRAIN', 4: 'TRAIN', 105: 'POLICE CAB'}
g = booted(); m = g.m.memory
room = lambda e: m[ENT[e]['address'] + 15]
DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()
clock = lambda: f"{DAYS[m[0x9FE1] % 7]} {m[0x9FE0]:2}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
hour24 = lambda: m[0x9FE0] % 12 + (12 if m[0x9FE2] == ord('p') else 0)
VERBOSE = '-v' in sys.argv
start = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 11

m[0x9D90] = 1; m[0x9E88] = 1
for x in (0x9976, 0x9984, 0x999A):
    m[x] |= 2
while not (m[0x9FE1] == 2 and hour24() >= start):
    run_with_bps(g, ' WAIT', [], None, max_slices=6000)
L = room(2)
print(clock(), 'Lestrade in room', L, 'script $%04X' % (m[0x9869] | m[0x986A] << 8))

def teleport(r):
    a = RM[r]['address']
    m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
    if '--no-watson' not in sys.argv:
        # Watson too, with his script pointed at his follow-you loop ($E7B6);
        # by Wednesday his own script has long since gone idle in this run
        # because you never left your room.
        m[ENT[3]['address'] + 15] = r
        m[0x9871] = 0xB6; m[0x9872] = 0xE7
teleport(L)
g.clear_output()
print(text(run_with_bps(g, ' LOOK', [], None, max_slices=6000))[-300:])
m[0x99AC] |= 2

def first_step(a, b):
    from collections import deque
    seen = {a: None}; q = deque([a])
    while q:
        r = q.popleft()
        if r == b:
            break
        for d, _, dest in (RM[r]['exits'] if RM.get(r) else []):
            if dest not in seen and dest not in VEH_ROOM:
                seen[dest] = (r, d); q.append(dest)
    if b not in seen or a == b:
        return None
    while seen[b][0] != a:
        b = seen[b][0]
    return seen[b][1]

target = 2
last = None
for n in range(1500):
    me, it = room(0), room(target)
    if target == 2 and room(6) == me and hour24() >= 15:
        pass
    if me == it:
        cmd = ' LOOK'
    else:
        step = first_step(me, it)
        if step:
            cmd = ' ' + o4.VERBS[step]
        elif it in VEH_ROOM:
            cmd = ' CLIMB INTO ' + VEH_ROOM[it]
        elif me in VEH_ROOM:
            cmd = ' CLIMB OUT'
        else:
            cmd = ' LOOK'
    out = text(run_with_bps(g, cmd, [], None, max_slices=6000))
    state = (room(0), room(3), room(2), room(6), target)
    if state != last or 'PLAY SAVED' in out:
        print(clock(), cmd.strip(), '| you', state[0], 'watson', state[1], 'lestrade', state[2], 'phipps', state[3])
        last = state
    if cmd != ' LOOK' and VERBOSE:
        print('      ', out[-240:])
    for key in ('ELUDED', 'WHIPS', 'BASIL', 'SPEEDS'):
        if key in out:
            i = out.find(key); print('   >>', out[max(0, i - 150):i + 250]); break
    if target == 2 and 'WHIPS' in out:
        target = 6
        print('   now following Phipps')
    if 'PLAY SAVED' in out:
        print('END:', out[-900:]); break
    if m[0x9FE1] >= 4:
        print('gave up'); break
