"""Replay a list of typed commands from a fresh boot and report the result.

usage (from the project's top folder):
    python3 tools/experiments/replay_log.py tools/experiments/playthrough/monday_to_major.cmds [N]

One command per line, run exactly as typed (with the leading space the
harness needs). A line '(until TEXT) CMD' repeats CMD, up to 80 times,
until TEXT appears in the game's reply - NOTE that room text wraps in the
narrow window, so choose TEXT that cannot be split across lines (a single
word). The game is deterministic: the same commands always give the same
run. Stops after the first N commands if N is given; prints the clock, the
player's room, and the markers $996F (Major's confession), $9E88 (Major
cleared), $9D90 (Straker introduced). Saves the position to
/tmp/replay_log.snap.
"""
import re
import sys
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text, save

cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
if len(sys.argv) > 2:
    cmds = cmds[:int(sys.argv[2])]
g = booted(); m = g.m.memory

def run1(c):
    g.clear_output()
    return text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))

for c in cmds:
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        for _ in range(80):
            if mm.group(1).lower() in run1(mm.group(2)).lower():
                break
    else:
        run1(c)
save(g, '/tmp/replay_log.snap')
print('after %d commands: day %d %d:%02d%s, room %d; $996F=%02X $9E88=%d $9D90=%d' % (
    len(cmds), m[0x9FE1], m[0x9FE0], m[0x9FDF], chr(m[0x9FE2]), m[0x8CC9],
    m[0x9972], m[0x9E88], m[0x9D90]))
