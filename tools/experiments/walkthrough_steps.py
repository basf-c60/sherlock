"""Replay a winning command file and record, for every command, the clock and place before and
after it, how many times an '(until ...)' line had to be repeated, and the game's reply.
usage: walkthrough_steps.py CMDFILE OUT.json   (about 20 seconds)"""
import re, sys, json
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
g = booted(); m = g.m.memory
def clk():
    return {'day': m[0x9FE1], 'h': m[0x9FE0], 'm': m[0x9FDF], 'ap': chr(m[0x9FE2]), 'room': m[0x8CC9]}
def run1(c):
    g.clear_output(); return text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))
out = []
for i, c in enumerate(cmds, 1):
    before = clk(); n = 1; replies = []
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        n = 0
        for _ in range(80):
            n += 1; r = run1(mm.group(2)); replies.append(r)
            if mm.group(1).lower() in r.lower(): break
        cmd, until = mm.group(2), mm.group(1)
    else:
        replies.append(run1(c)); cmd, until = c, None
    out.append({'i': i, 'cmd': cmd, 'until': until, 'n': n, 'before': before, 'after': clk(),
                'reply': ' '.join(replies[-1].split()), 'first': ' '.join(replies[0].split())})
json.dump({'steps': out, 'end': m[0xA0DA]}, open(sys.argv[2], 'w'), indent=0)
print(len(out), 'steps; end flag', m[0xA0DA])
