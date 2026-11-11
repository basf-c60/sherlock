"""Greedy shortening of a winning command file: try dropping each candidate line (by original line number) from the current route;
keep the drop only if the whole route, replayed from a fresh boot, still ends with the winning text.
usage: greedy_min.py CMDFILE OUT.json N [N ...]   (N = 1-based original line numbers to try, in the order given)"""
import sys, json, time
args = sys.argv[3:]
sys.argv = sys.argv[:3] + ['0', '1']
exec(open('tools/experiments/ablate_cmds.py').read().split("# order:")[0].replace("part, nparts = int(sys.argv[3]), int(sys.argv[4])", ""))
out = sys.argv[2]
ids = list(range(1, len(cmds) + 1)); cur = list(cmds)
def snaps_of(c):
    g = booted(); ss = []
    for x in c:
        ss.append(snap(g)); run_line(g, x)
    return ss
ss = snaps_of(cur)
log = []
for n in map(int, args):
    if n not in ids: continue
    pos = ids.index(n); t0 = time.time()
    r = finish(restore(ss[pos]), cur[pos + 1:], limit=300)
    ok = r[0]
    log.append({'line': n, 'cmd': cmds[n - 1], 'dropped': ok, 'clock': r[2]})
    print(n, cmds[n - 1][:40], 'DROPPED' if ok else 'kept', r[2], '%.0fs' % (time.time() - t0), flush=True)
    if ok:
        del cur[pos]; del ids[pos]; ss = snaps_of(cur)
    json.dump({'log': log, 'kept_ids': ids}, open(out, 'w'))
open(out.replace('.json', '.cmds'), 'w').write('\n'.join(cur) + '\n')
