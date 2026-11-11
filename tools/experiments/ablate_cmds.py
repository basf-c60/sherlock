"""Remove each line of a winning command file in turn and replay: does the game still end with the winning text?
A snapshot of the machine is taken before every line, so a trial only replays the lines after the removed one.
usage: ablate_cmds.py CMDFILE OUT.json PART NPARTS [CHECK]   (lines i with i % NPARTS == PART; CHECK = validate snapshots first)"""
import re, sys, json, time
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text

REGS = ['af', 'bc', 'de', 'hl', 'ix', 'iy', 'sp', 'pc', 'alt_af', 'alt_bc', 'alt_de', 'alt_hl', 'ir', 'iff1', 'iff2', 'halted', 'int_disabled']

def snap(g):
    return (bytes(g.m.memory), {r: getattr(g.m, r) for r in REGS}, list(g.q), list(g.printed), g.pictures)

def restore(s):
    g = booted()      # fresh Game object with its breakpoints set; then overwrite its state
    mem, regs, q, printed, pics = s
    g.m.set_memory_block(0, mem)
    for r, v in regs.items():
        try: setattr(g.m, r, v)
        except AttributeError: pass
    g.q = list(q); g.printed = list(printed); g.pictures = pics
    return g

class Timeout(Exception): pass
DEADLINE = [None]

def run_line(g, c):
    if DEADLINE[0] and time.time() > DEADLINE[0]: raise Timeout
    mm = re.match(r'\(until (.*?)\) (.*)', c)
    if mm:
        last = ''
        for _ in range(80):
            if DEADLINE[0] and time.time() > DEADLINE[0]: raise Timeout
            g.clear_output()
            last = text(run_with_bps(g, ' ' + mm.group(2), [], None, max_slices=6000))
            if mm.group(1).lower() in last.lower(): break
        return last
    g.clear_output()
    return text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))

def verdict(g, last):
    m = g.m.memory
    t = ' '.join(last.upper().replace('|', ' ').split())
    win = m[0xA0DA] == 1 and 'WORLDS' in t and 'GREATEST DETECTIVE' in t
    return win, m[0xA0DA], '%d %d:%02d%s r%d' % (m[0x9FE1], m[0x9FE0], m[0x9FDF], chr(m[0x9FE2]), m[0x8CC9]), t[-160:]

def finish(g, cmds, last='', limit=None):
    m = g.m.memory
    DEADLINE[0] = time.time() + limit if limit else None
    try:
        stuck = 0
        for c in cmds:
            if m[0xA0DA]: break
            t0 = time.time(); c0 = (m[0x9FE1], m[0x9FE0], m[0x9FDF], m[0x9FE2])
            last = run_line(g, c)
            # a command that burns its whole slice budget without the clock moving: the game is waiting for a key that never comes
            stuck = stuck + 1 if (time.time() - t0 > 0.5 and c0 == (m[0x9FE1], m[0x9FE0], m[0x9FDF], m[0x9FE2])) else 0
            if stuck >= 4:
                return (False, -2, 'stuck at %d %d:%02d%s r%d' % (m[0x9FE1], m[0x9FE0], m[0x9FDF], chr(m[0x9FE2]), m[0x8CC9]), ' '.join(last.upper().replace('|', ' ').split())[-160:])
    except Timeout:
        return (False, -1, 'timeout at %d %d:%02d%s r%d' % (m[0x9FE1], m[0x9FE0], m[0x9FDF], chr(m[0x9FE2]), m[0x8CC9]), '')
    finally:
        DEADLINE[0] = None
    return verdict(g, last)

cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
part, nparts = int(sys.argv[3]), int(sys.argv[4])
# snapshots before every line (the whole file replayed once)
g = booted(); snaps = []; base = ''
for c in cmds:
    snaps.append(snap(g)); base = run_line(g, c)
print('baseline', verdict(g, base)[:3], flush=True)
if len(sys.argv) > 5:           # validate: restoring a snapshot and finishing must give the same verdict
    for k in (50, 200):
        print('check', k, finish(restore(snaps[k]), cmds[k:])[:3], flush=True)
    sys.exit()
# order: lines of the kinds the old minimiser never tried first
def kind(c): return 0 if re.match(r'(\(until .*?\) )?(WAIT|LOOK|INVENTORY)$', c) else 1
order = sorted(range(len(cmds)), key=lambda i: (kind(cmds[i]), i))
import os
res = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}
for n, i in enumerate(order):
    if n % nparts != part or str(i + 1) in res: continue
    t0 = time.time()
    win, flag, clk, tail = finish(restore(snaps[i]), cmds[i + 1:], limit=300)
    res[i + 1] = {'cmd': cmds[i], 'win': win, 'flag': flag, 'clock': clk, 'tail': tail}
    json.dump(res, open(sys.argv[2], 'w'))
    print(i + 1, cmds[i][:40], 'WIN' if win else 'no', clk, '%.0fs' % (time.time() - t0), flush=True)
