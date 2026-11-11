"""What does each still-untraced action record change? usage: record_effects.py CMDFILE OUT.json
At the body of every block in traced_blocks.json (not the player's own input records), takes a copy of
memory $8000-$A0FF when it is entered, and compares it with memory when the record returns to
the interpreter. Samples at most 3 runs for each (actor, verb, direct, indirect) combination.
Each changed byte is reported as the entity and field it belongs to, when it lies in a thing record."""
import re, sys, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'source'))
from play import booted, run_with_bps, text
from plan import b
import objects as O
ENT = sorted((e['address'], e['id']) for e in O.entities())
def where(a):
    prev = None
    for ad, i in ENT:
        if ad > a: break
        prev = (ad, i)
    if prev and a - prev[0] < 26 and 0x8CBA <= a < ENT[-1][0] + 26: return 'thing %d +%d' % (prev[1], a - prev[0])
    return '$%04X' % a
def hlen(a):
    f = b(a); return 2 + (2 if f & 0x40 else 0) + (5 if f & 0x10 else 0)
TB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced_blocks.json')))['blocks']
L = open(os.path.join(ROOT, 'source', 'game.ctl')).read().split('\n')
ROUTINES = {0xA5C4, 0xB98C, 0xBB67, 0xCC78}   # the blocks that are code entered directly, not action records
targets = {(a if a in ROUTINES else a + hlen(a)): a for a in TB if not (0xD6BF <= a <= 0xD7FA)}
bps = sorted(targets)
W = lambda mem, a: mem[a] | mem[a + 1] << 8
pend = {}; seen = {}; res = {}
def on_hit(g, pc):
    mem = g.m.memory
    if pc in targets:
        blk = targets[pc]
        k = (blk, mem[0xA036], mem[0xA033], mem[0xA034], mem[0xA035])
        if seen.get(k, 0) >= 3: return
        seen[k] = seen.get(k, 0) + 1
        ret = W(mem, g.m.sp)
        pend.setdefault(ret, []).append((blk, k, bytes(mem[0x8000:0xA100]), g.m.sp))
        g.m.set_breakpoint(ret)
        if ret not in bps: bps.append(ret)
    elif pc in pend:
        blk, k, snap, sp = pend[pc].pop()
        if not pend[pc]: del pend[pc]; g.m.clear_breakpoint(pc); bps.remove(pc)
        now = mem[0x8000:0xA100]
        d = [(0x8000 + i, snap[i], now[i]) for i in range(len(snap)) if snap[i] != now[i]]
        r = res.setdefault(blk, {})
        key = tuple(sorted((where(a), x, y) for a, x, y in d if not (0xA000 <= a < 0xA040) and a not in (0x9FE1,)))
        e = r.setdefault(json.dumps([key]), [0, k, None]); e[0] += 1
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted()
log = []
def run1(c):
    g.clear_output()
    r = text(run_with_bps(g, ' ' + c, bps, on_hit, max_slices=6000)); log.append(c); return r
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
json.dump({str(a): [[json.loads(k)[0], v[0], v[1]] for k, v in d.items()] for a, d in res.items()}, open(sys.argv[2], 'w'))
print(sys.argv[1], len(res), 'blocks with effects')
