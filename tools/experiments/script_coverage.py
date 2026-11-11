"""Which plan-script instructions does a command file execute? usage: script_coverage.py CMDFILE OUT.json
Breakpoint at $CC9B (the interpreter has just fetched an instruction; HL is its address)."""
import re, sys, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'source'))
from play import booted, run_with_bps, text
seen = {}
def on_hit(g, pc):
    a = g.m.hl; seen[a] = seen.get(a, 0) + 1
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted()
def run1(c):
    g.clear_output(); return text(run_with_bps(g, ' ' + c, [0xCC9B], on_hit, max_slices=6000))
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
json.dump(seen, open(sys.argv[2], 'w'))
print(sys.argv[1], len(seen), 'instruction addresses executed')
