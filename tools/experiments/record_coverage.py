"""Which action records does a command file run, and on which command?
usage: record_coverage.py CMDFILE OUT.json
Sets a breakpoint at the body of every block that carried a 'Not traced' label before
the 9 November pass (tools/experiments/traced_blocks.json) and logs each hit with the command typed and the game's reply."""
import re, sys, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools')); sys.path.insert(0, os.path.join(ROOT, 'source'))
from play import booted, run_with_bps, text
from plan import b
def hlen(a):
    f = b(a); return 2 + (2 if f & 0x40 else 0) + (5 if f & 0x10 else 0)
TB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced_blocks.json')))['blocks']
L = open(os.path.join(ROOT, 'source', 'game.ctl')).read().split('\n')
ROUTINES = {0xA5C4, 0xB98C, 0xBB67, 0xCC78}   # the blocks that are code entered directly, not action records
targets = {(a if a in ROUTINES else a + hlen(a)): a for a in TB}
bps = sorted(targets)
hits = {}
who = {}   # block -> {(actor, verb, dobj, iobj): [count, first command number]}
state = {'cmd': None, 'n': 0}
def on_hit(g, pc):
    mem = g.m.memory
    hits.setdefault(targets[pc], []).append(state['n'])
    k = (mem[0xA036], mem[0xA033], mem[0xA034], mem[0xA035])
    who.setdefault(targets[pc], {}).setdefault(k, [0, state['n']])[0] += 1
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted()
log = []
def run1(c):
    g.clear_output(); state['n'] = len(log)
    r = text(run_with_bps(g, ' ' + c, bps, on_hit, max_slices=6000)); log.append((c, r[:300])); return r
for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower(): break
    else: run1(c)
out = {str(a): [{'n': n, 'cmd': log[n][0], 'reply': log[n][1]} for n in sorted(set(ns))] for a, ns in hits.items()}
json.dump({'targets': sorted(set(targets.values())), 'hits': out, 'who': {str(a): [[list(k), v[0], log[v[1]][0]] for k, v in d.items()] for a, d in who.items()}}, open(sys.argv[2], 'w'), indent=1)
print(sys.argv[1], len(targets), 'targets,', len(hits), 'hit')
