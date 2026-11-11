"""Remove whole blocks of lines (given as FIRST-LAST, 1-based) from a winning command file, one block at a time, and report whether the game still wins.
usage: ablate_blocks.py CMDFILE OUT.json PART NPARTS SPEC [SPEC ...]   (SPEC = FIRST-LAST or N or comma-joined list of those)"""
import sys, json, os, time
sys.argv, args = sys.argv[:5], sys.argv[5:]
exec(open('tools/experiments/ablate_cmds.py').read().split("# order:")[0].split("part, nparts")[0])
part, nparts = int(sys.argv[3]), int(sys.argv[4])
g = booted(); snaps = []
for c in cmds:
    snaps.append(snap(g)); run_line(g, c)
res = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else {}
for n, blk in enumerate(args):
    if n % nparts != part or blk in res: continue
    S = set()
    for part_ in blk.split(','):
        a, b = (list(map(int, part_.split('-'))) + [None])[:2]
        S |= set(range(a, (b or a) + 1))
    a = min(S)
    t0 = time.time()
    win, flag, clk, tail = finish(restore(snaps[a - 1]), [c for i, c in enumerate(cmds[a - 1:], a) if i not in S], limit=300)
    res[blk] = {'win': win, 'flag': flag, 'clock': clk, 'tail': tail}
    json.dump(res, open(sys.argv[2], 'w'))
    print(blk, 'WIN' if win else 'no', clk, '%.0fs' % (time.time() - t0), flush=True)
