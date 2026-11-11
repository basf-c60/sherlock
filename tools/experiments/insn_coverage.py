"""Which instructions of the blocks listed in traced_blocks.json (formerly marked 'Not traced') does a command file execute?
usage: insn_coverage.py CMDFILE OUT.json
One-shot breakpoint on every instruction address of those blocks (as listed in game.skool)."""
import re, sys, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'source'))
from play import booted, run_with_bps, text
ctl = open(os.path.join(ROOT, 'source', 'game.ctl')).read().split('\n')
tb = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced_blocks.json')))
blocks = list(tb['blocks'])
# routines that carry no 'Not traced' line but were given a 'Coverage, 9 November' note by the audit:
blocks += tb['extra_routines']
skool = open(os.path.join(ROOT, 'game.skool')).read().split('\n')
insns = {}   # block -> [addresses]
i = 0
while i < len(skool):
    m = re.match(r'^[c*b ]\$([0-9A-F]{4}) ', skool[i])
    j = i
    if m and int(m[1], 16) in blocks and skool[i][0] in 'cb':
        a0 = int(m[1], 16); insns[a0] = []
        while j < len(skool) and skool[j].strip() != '':
            mm = re.match(r'^[c*b ]\$([0-9A-F]{4}) (?!DEFB|DEFW|DEFM|DEFS)', skool[j])
            if mm: insns[a0].append(int(mm[1], 16))
            j += 1
    i = max(j, i + 1)
allad = {a: b for b, l in insns.items() for a in l}
remaining = set(allad); hit = set()
def on_hit(g, pc):
    hit.add(pc); remaining.discard(pc); g.m.clear_breakpoint(pc)
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted()
def run1(c):
    g.clear_output(); return text(run_with_bps(g, ' ' + c, sorted(remaining), on_hit, max_slices=6000))
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
json.dump({'blocks': {str(b): l for b, l in insns.items()}, 'hit': sorted(hit)}, open(sys.argv[2], 'w'))
print(sys.argv[1], len(allad), 'instructions,', len(hit), 'hit')
