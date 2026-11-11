"""Play the endgame chase, in stages with snapshots (scratchpad or ./snaps).

  A: boot; 3pm/Major endings poked away; both murders and PHIPPS HAS
     PLANS poked proven; WAIT to Wednesday 11am; poke THE SALE LOCATION
     IS OLD MILL ROAD proven (Lestrade sets off on his own).
  B: wait until Lestrade reaches Leatherhead station (room 53); put you
     and Watson in Main Street (50), Watson on his follow-you loop.
  C onwards: commands, one stage at a time (see the stage functions).

    SNAPS=dir python3 tools/experiments/chase.py A B C D E F

What happened (2026-11-07): the police cab reaches Old Mill Road at
3:13pm with you, Watson and Lestrade; Phipps bolts at 3:14; the cab is
back in Main Street at 4:47; Phipps walks to platform two and boards the
train at 4:54, which leaves at 4:55 - one minute before Lestrade, still
busy saying that Basil has eluded you, can take an order. Ordered to
follow, he and Watson come on the next train (6:18), which reaches
platform four at 7:30; Phipps left the game by 6:45 (logged every 15 minutes), having found
nobody at Victoria. So the chase was lost by about a minute.

THE WIN (2026-11-08): stages A B C D E F2 G3. From platform two at 4:56,
with Lestrade ordered to follow: back to Main Street, SAY TO POLICE MAN
"GO FURIOUSLY TO KINGS CROSS ROAD" (verb 30: 74 minutes, not 94), then
Kings Cross platform one and the underground train to Victoria platform
one (6:40). Basil walks in at 6:42 and the game is won. Reproduced from a
cold start. (Stage P is the plain GO TO, 95 minutes, too slow; stage G2
tries a hansom cab, but both are on the road at 6:22.)
"""
import sys, os; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text, save, load
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
SNAP = os.environ.get('SNAPS', 'snaps'); os.makedirs(SNAP, exist_ok=True)
DAYS = 'Mon Tue Wed Thu Fri Sat Sun'.split()

def ctx(g):
    m = g.m.memory
    room = lambda e: m[ENT[e]['address'] + 15]
    clock = f"{DAYS[m[0x9FE1] % 7]} {m[0x9FE0]:2}:{m[0x9FDF]:02}{chr(m[0x9FE2])}"
    return m, room, clock

def say(g, cmd):
    m, room, clock = ctx(g)
    g.clear_output()
    out = text(run_with_bps(g, ' ' + cmd, [], None, max_slices=6000))
    m, room, clock = ctx(g)
    print(f"{clock} {cmd:40} you {room(0):3} watson {room(3):3} lestrade {room(2):3} phipps {room(6):3} pcab {room(109):3}")
    print('     ', out[-400:])
    return out

def stage_A():
    g = booted(); m, room, clock = ctx(g)
    m[0x9D90] = 1; m[0x9E88] = 1
    for x in (0x9976, 0x9984, 0x999A):
        m[x] |= 2
    h24 = lambda: m[0x9FE0] % 12 + (12 if m[0x9FE2] == ord('p') else 0)
    while not (m[0x9FE1] == 2 and h24() >= 11):
        run_with_bps(g, ' WAIT', [], None, max_slices=6000)
    m[0x99AC] |= 2
    save(g, f'{SNAP}/A.snap')

def stage_B():
    g = load(f'{SNAP}/A.snap'); m, room, clock = ctx(g)
    while room(2) != 53:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    r = 50; a = RM[r]['address']
    m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
    m[ENT[3]['address'] + 15] = r
    m[0x9871] = 0xB6; m[0x9872] = 0xE7
    for k in range(3, 8):
        m[0x9870 + k] = 0xFF if k < 6 else 0
    print(ctx(g)[2], 'Lestrade at 53; you and Watson in Main Street')
    save(g, f'{SNAP}/B.snap')

def until(g, cond, cmd='LOOK', limit=200):
    for _ in range(limit):
        if cond():
            return True
        say(g, cmd)
    return False

def stage_C():
    """Board the police cab in the minute Lestrade does (three LOOKs after
    B): then Lestrade, Watson and you fit and Chief Constable Straker does
    not. Earlier, you and Watson fill it and Lestrade is left behind; later,
    Lestrade and Straker fill it and you are refused."""
    g = load(f'{SNAP}/B.snap'); m, room, clock = ctx(g)
    for _ in range(3):
        say(g, 'LOOK')
    say(g, 'CLIMB INTO POLICE CAB')
    say(g, 'LOOK')
    while room(109) != 103:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    save(g, f'{SNAP}/C.snap')

def stage_D():
    """At Old Mill Road: Phipps bolts; ride back to Main Street with Lestrade."""
    g = load(f'{SNAP}/C.snap'); m, room, clock = ctx(g)
    for _ in range(3):
        say(g, 'LOOK')
    while room(109) != 50:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    save(g, f'{SNAP}/D.snap')

def stage_E():
    """Hurry after Phipps to platform two; then order Lestrade to follow."""
    g = load(f'{SNAP}/D.snap'); m, room, clock = ctx(g)
    for cmd in ['CLIMB OUT', 'NORTH', 'NORTH', 'NORTH'] + ['SAY TO LESTRADE "FOLLOW ME"'] * 3:
        say(g, cmd)
        print('      Lestrade script $%04X' % (m[0x9869] | m[0x986A] << 8))
    save(g, f'{SNAP}/E.snap')

def stage_F():
    """The next train, with Lestrade and Watson following, to platform four."""
    g = load(f'{SNAP}/E.snap'); m, room, clock = ctx(g)
    trains = range(36, 44)
    while not any(room(t) == 55 for t in trains):
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    say(g, 'CLIMB INTO TRAIN')
    while room(0) != 23:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
        if m[0x9FDF] % 15 == 0:
            print(ctx(g)[2], 'you', room(0), 'lestrade', room(2), 'watson', room(3), 'phipps', room(6))
    say(g, 'LOOK')


def stage_P():
    """The police-cab line: from platform two with Lestrade following,
    back to Main Street, the police cab to Kings Cross Road ($9AA3 has
    that route: 74 minutes), a hansom cab to Buckingham Palace Road, and
    on to platform one at Victoria to wait for Phipps."""
    g = load(f'{SNAP}/E.snap'); m, room, clock = ctx(g)
    for c in ['SOUTH', 'SOUTH', 'SOUTH', 'CLIMB INTO POLICE CAB', 'SAY TO POLICE MAN "GO TO KINGS CROSS ROAD"']:
        say(g, c)
    while room(109) != 18:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
        if m[0x9FDF] % 10 == 0:
            print(ctx(g)[2], 'you', room(0), 'cab', room(109), 'lestrade', room(2), 'watson', room(3), 'phipps', room(6))
    save(g, f'{SNAP}/P.snap')
    say(g, 'LOOK')

def stage_Q():
    g = load(f'{SNAP}/P.snap'); m, room, clock = ctx(g)
    say(g, 'CLIMB OUT')
    say(g, 'HAIL CAB')
    for _ in range(10):
        out = say(g, 'LOOK')
        if 'hansom' in out.lower():
            break
    say(g, 'CLIMB INTO HANSOM CAB')
    say(g, 'LOOK')
    say(g, 'SAY TO CABBIE "GO TO BUCKINGHAM PALACE ROAD"')
    for _ in range(40):
        out = say(g, 'LOOK')
        if 'buckingham' in out.lower() or 'BASIL' in out:
            break
    save(g, f'{SNAP}/Q.snap')
    for c in ['CLIMB OUT', 'EAST', 'EAST'] + ['WAIT'] * 12:
        out = say(g, c)
        if 'BASIL' in out or 'PLAY SAVED' in out:
            break


def stage_F2():
    """The furious line: GO FURIOUSLY TO is verb 30, which the police man's
    action list sends to shared action 2 ($9ACB, 20 minutes off) and a
    cabbie's to shared action 15 ($9AE1, 2 minutes off, dearer)."""
    g = load(f'{SNAP}/E.snap'); m, room, clock = ctx(g)
    for c in ['SOUTH', 'SOUTH', 'SOUTH', 'CLIMB INTO POLICE CAB',
              'SAY TO POLICE MAN "GO FURIOUSLY TO KINGS CROSS ROAD"']:
        say(g, c)
    while room(109) != 18:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
        if m[0x9FDF] % 10 == 0:
            print(ctx(g)[2], 'you', room(0), 'lestrade', room(2), 'watson', room(3), 'phipps', room(6))
    save(g, f'{SNAP}/F2.snap')
    say(g, 'LOOK')

def stage_G2():
    g = load(f'{SNAP}/F2.snap'); m, room, clock = ctx(g)
    say(g, 'CLIMB OUT')
    say(g, 'HAIL HANSOM CAB')
    for _ in range(8):
        if any(room(c) == room(0) for c in (30, 33)):
            break
        say(g, 'LOOK')
    say(g, 'CLIMB INTO HANSOM CAB')
    say(g, 'SAY TO CABBIE "GO FURIOUSLY TO BUCKINGHAM PALACE ROAD"')
    for _ in range(30):
        out = say(g, 'LOOK')
        if 'Buckingham' in out or 'BASIL' in out:
            break
    save(g, f'{SNAP}/G2.snap')
    for c in ['CLIMB OUT', 'EAST', 'EAST'] + ['WAIT'] * 10:
        out = say(g, c)
        if 'BASIL' in out.upper() or 'PLAY SAVED' in out:
            print('*****', out)
            break


def stage_G3():
    """From Kings Cross Road at 6:22 (stage F2): walk to platform one and
    take the circle train (actors 36-41: Aldergate, Kings Cross platform
    one, room 26, Victoria platform one) straight to Victoria."""
    g = load(f'{SNAP}/F2.snap'); m, room, clock = ctx(g)
    for c in ['CLIMB OUT', 'NORTHEAST', 'NORTHEAST']:
        say(g, c)
    trains = range(36, 42)
    while not any(room(t) == room(0) for t in trains):
        say(g, 'LOOK')
    say(g, 'CLIMB INTO TRAIN')
    t = [t for t in trains if True]
    for _ in range(40):
        out = say(g, 'LOOK')
        here = [x for x in trains if room(x) == 30]
        if 'platform one' in out.lower() and m[0x8CC9] == 2 and here:
            break
    save(g, f'{SNAP}/G3.snap')
    for c in ['CLIMB OUT'] + ['WAIT'] * 6:
        out = say(g, c)
        if 'BASIL' in out.upper() or 'PLAY SAVED' in out:
            print('*****', out)
            break


def stage_B2():
    """Instead of B's teleport: Watson put beside you on his follow loop
    (by Wednesday his own script has gone idle, since you never left your
    room in stage A), then the journey to Leatherhead by play - down to
    Baker Street, a cab to Kings Cross Road, platform three, the Leatherhead
    train, and on foot to Main Street."""
    g = load(f'{SNAP}/A.snap'); m, room, clock = ctx(g)
    m[ENT[3]['address'] + 15] = room(0)
    m[0x9871] = 0xB6; m[0x9872] = 0xE7
    for k in range(3, 8):
        m[0x9870 + k] = 0xFF if k < 6 else 0
    for c in ['OPEN YOUR DOOR', 'WEST', 'DOWN', 'OPEN FRONT DOOR', 'SOUTH', 'HAIL CAB']:
        say(g, c)
    for _ in range(10):
        if any(room(c) == room(0) for c in (30, 33)):
            break
        say(g, 'LOOK')
    say(g, 'CLIMB INTO HANSOM CAB')
    say(g, 'SAY TO CABBIE "GO TO KINGS CROSS ROAD"')
    for _ in range(40):
        if any(room(c) == 18 for c in (30, 33)) and room(0) != 1:
            break
        out = say(g, 'LOOK')
        if 'Kings Cross Road' in out:
            break
    for c in ['CLIMB OUT', 'NORTHEAST', 'NORTHEAST', 'NORTHEAST', 'NORTHEAST']:
        say(g, c)
    while not any(room(t) == room(0) for t in (42, 43)):
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    say(g, 'CLIMB INTO TRAIN')
    while not (any(room(t) == 54 for t in (42, 43)) and room(0) in (3, 4, 54)):
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
        if room(0) == 54:
            break
    for c in ['CLIMB OUT', 'SOUTH', 'SOUTH']:
        say(g, c)
    save(g, f'{SNAP}/B2.snap')

def stage_C2():
    """Board the police cab in the minute Lestrade will: when his script is
    on $EA69 (CLIMB INTO the police cab) at the start of your turn."""
    g = load(f'{SNAP}/B2.snap'); m, room, clock = ctx(g)
    pos = lambda: m[0x9869] | m[0x986A] << 8
    for _ in range(120):
        if pos() == 0xEA69 and room(109) == room(0):
            break
        say(g, 'LOOK')
        print('      Lestrade script $%04X' % pos())
    say(g, 'CLIMB INTO POLICE CAB')
    say(g, 'LOOK')
    while room(109) != 103:
        run_with_bps(g, ' LOOK', [], None, max_slices=6000)
    save(g, f'{SNAP}/C.snap')

if __name__ == '__main__':
    for st in sys.argv[1:]:
        globals()['stage_' + st]()
