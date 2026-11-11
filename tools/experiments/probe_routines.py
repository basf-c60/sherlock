"""Check the stated postconditions of a few small routines while a command file is typed.
Each routine is checked every time it runs: $A2B1 (verb record address), $A2AB (zero fill),
$AEA9 (next node link), $A11C (allocation zeroed, NZ), $9CCE (Z implies same room)."""
import re, sys
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O
ENT = {e['id']: e['address'] for e in O.entities()}
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()][:int(sys.argv[2])]
g = booted(); m = g.m
mem = m.memory
bps = [0xA2B1, 0xA2AB, 0xAEA9, 0xA11C, 0x9CCE]
pend = {}   # return address -> list of (routine, entry data)
stats = {r: [0, 0] for r in bps}   # checks, failures
fails = []
def w(a): return mem[a] | mem[(a + 1) & 0xFFFF] << 8
def on_hit(g, pc):
    if pc in stats and pc not in pend.get('_ret', ()):
        sp = m.sp; ret = w(sp)
        ent = dict(A=m.a, B=m.b, C=m.c, HL=m.hl, IY=m.iy, pc=pc)
        if pc == 0xAEA9: ent['link'] = w((m.iy - 2) & 0xFFFF)
        if pc == 0x9CCE: ent['actor_room'] = mem[w(0xA017) + 15]
        pend.setdefault(ret, []).append(ent); m.set_breakpoint(ret)
        if ret not in bps: bps.append(ret)
    else:
        lst = pend.get(pc)
        if not lst: return
        ent = lst.pop()
        if not lst: m.clear_breakpoint(pc); bps.remove(pc); del pend[pc]
        r = ent['pc']; ok = True
        if r == 0xA2B1: ok = m.hl == 0x8259 + 8 * (ent['A'] - 1)
        elif r == 0xA2AB: ok = all(mem[(ent['HL'] + i) & 0xFFFF] == 0 for i in range(ent['B'] or 256))
        elif r == 0xAEA9: ok = m.iy == ent['link']
        elif r == 0xA11C: ok = m.ix != 0 and all(mem[(m.ix - 2 + i) & 0xFFFF] == 0 for i in range(ent['A'] + 2) if i != 0 or True) and mem[(m.ix - 3) & 0xFFFF] == ent['A'] + 3
        elif r == 0x9CCE:
            if not (m.f & 0x40): ok = True    # NZ: nothing to check
            else: ok = mem[ENT[ent['C']] + 15] == ent['actor_room']
        stats[r][0] += 1
        if not ok: stats[r][1] += 1; fails.append((hex(r), ent))
def run1(c):
    g.clear_output()
    return text(run_with_bps(g, ' ' + c, bps, on_hit, max_slices=6000))
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
for r, (n, f) in stats.items(): print('$%04X: %d checks, %d failures' % (r, n, f))
print(fails[:5])
