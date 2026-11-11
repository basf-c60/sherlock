"""Targeted tests for action records that no stored route runs (9 November, 'Not traced' pass).
usage: untraced_tests.py   - prints what typed commands did, with breakpoints at the record bodies."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'source'))
from play import booted, run_with_bps, text
import objects as O, rooms as R
ENT = {e['id']: e for e in O.entities()}; RM = R.rooms()
def goto(g, r):
    mem = g.m.memory; a = RM[r]['address']
    mem[0x8CC9] = r; mem[0xA00A] = r; mem[0xDCFF] = a & 255; mem[0xDD00] = a >> 8; mem[0xDD01] = r
def cmd(g, c, bps):
    hits = []
    g.clear_output()
    out = run_with_bps(g, ' ' + c, bps, lambda g, pc: hits.append(pc), max_slices=6000)
    print('  %-28s -> %s' % (c, text(out)[:230])); print('      hit:', ['$%04X' % h for h in hits[:6]])
g = booted()
print('A. LOOK THROUGH (body $DC20), in the sitting room')
for c in ['LOOK THROUGH WINDOW', 'LOOK THROUGH YOUR DOOR', 'OPEN YOUR DOOR', 'LOOK THROUGH YOUR DOOR']:
    cmd(g, c, [0xDC20])
print('B. closet (room 9): the old and china men disguises')
g = booted(); goto(g, 9)
for c in ['LOOK', 'WEAR OLD MANS DISGUISE', 'INVENTORY', 'TAKE OFF OLD MANS DISGUISE', 'WEAR OLD MANS DISGUISE', 'LOOK']:
    cmd(g, c, [0xDFF4, 0xDFEE, 0xDFF8, 0xE007, 0xE028])
print('C. COUNT')
g = booted()
for c in ['INVENTORY', 'COUNT MONEY', 'COUNT YOUR MONEY']:
    cmd(g, c, [0xE32C])
print('D. input and inventory edge cases (bodies of $D77E, $D7FA, $DE6F, $E370)')
g = booted()
BPS = [0xD7D0, 0xD7D3, 0xD84F, 0xD865, 0xDE86, 0xE365, 0xE1C0]
for c in ['TAKE ALL', 'INVENTORY', 'DROP ALL', 'INVENTORY', 'TAKE', 'BLAH', 'PAY 100D TO WATSON', 'TAKE ALL BUT LAMP', 'DROP ALL BUT LAMP', 'GO BLAH']:
    cmd(g, c, BPS)

print('E. the first messenger scene ($EF9C): replay the winning route to Tuesday 12:30pm, then put the player in Camden Street')
print('   (the room number is written into memory - the only poke in this pass) and WAIT')
import re
cmds_ = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'tools/experiments/playthrough/v12_clean_win.cmds')) if l.strip()][:215]
g = booted(); mem = g.m.memory
def run1(c, bps=()):
    g.clear_output(); return text(run_with_bps(g, ' ' + c, list(bps), lambda g, pc: None, max_slices=6000))
for c in cmds_:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
goto(g, 32)
for i in range(60):
    r = run1('WAIT')
    if 'MESSENGER' in r.upper():
        print('  ', r[-200:]); break
print('F. GO THROUGH as the player (body $DC5B)')
g = booted()
for c in ['GO THROUGH YOUR DOOR', 'OPEN YOUR DOOR', 'GO THROUGH YOUR DOOR']:
    cmd(g, c, [0xDC5B])
