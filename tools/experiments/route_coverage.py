"""Which routines does a command file execute? usage: route_coverage.py CMDFILE OUT.json
Sets a one-shot breakpoint at the first address of every code block and entry point
(lines starting 'c$', '*$' or ' $' after a 'c' header are NOT used - only 'c$'/'*$' labels
in game.skool) and records the ones hit while the commands are typed from a fresh boot.
Only entries are seen: a block entered in the middle, or a data record read by the plan
interpreter, shows as not hit even if its bytes were used."""
import re, sys, json
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
addrs = set()
for l in open('game.skool'):
    mm = re.match(r'[c*]\$([0-9A-F]{4}) (?!DEFB|DEFW|DEFM|DEFS)', l)
    if mm: addrs.add(int(mm.group(1), 16))
remaining = set(addrs); hit = set()
def on_hit(g, pc):
    hit.add(pc); remaining.discard(pc); g.m.clear_breakpoint(pc)
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted()
def run1(c):
    g.clear_output()
    r = text(run_with_bps(g, ' ' + c, sorted(remaining), on_hit, max_slices=6000)); run1.last = r; return r
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else:
        run1(c)
print('last reply:', run1.last[-200:] if hasattr(run1,'last') else '')
json.dump({'checked': sorted(addrs), 'hit': sorted(hit)}, open(sys.argv[2], 'w'))
print(len(addrs), 'entry points checked,', len(hit), 'hit')
