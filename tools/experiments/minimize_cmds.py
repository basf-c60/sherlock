"""Shorten a winning command file by removing lines that turn out not to matter.

usage: python3 tools/experiments/minimize_cmds.py IN.cmds OUT.cmds [EARLIER.cmds]

Candidates are plain LOOK and INVENTORY lines and lines whose reply was an
error ('I SEE NO', 'YOU CANNOT', 'I DO NOT KNOW', 'WHICH ...'). A removal is
kept only if the whole file, replayed from a fresh boot, still ends with the
winning text ('worlds greatest detective' in the last reply). Removal sets are tried by bisection (ddmin style).
"""
import re, sys
sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text

def replay(cmds):
    g = booted(); m = g.m.memory
    last = ''
    for c in cmds:
        mm = re.match(r'\(until (.*?)\) (.*)', c)
        if mm:
            for _ in range(80):
                g.clear_output()
                last = text(run_with_bps(g, ' ' + mm.group(2), [], None, max_slices=6000))
                if mm.group(1).lower() in last.lower(): break
        else:
            g.clear_output()
            last = text(run_with_bps(g, ' ' + c, [], None, max_slices=6000))
        if m[0xA0DA]:            # game over: stop replaying
            break
    # the WINNING text, not just any game over in room 30 at 6:43 (the same
    # place and time also gives the 'disposes of you' ending without Lestrade)
    t = ' '.join(last.upper().replace('|', ' ').split())
    return m[0xA0DA] == 1 and 'WORLDS' in t and 'GREATEST DETECTIVE' in t

def errors(cmds):
    """indices of lines whose reply was an error or that are plain LOOK/INVENTORY"""
    g = booted(); m = g.m.memory; bad = []
    for i, c in enumerate(cmds):
        mm = re.match(r'\(until (.*?)\) (.*)', c)
        if mm:
            for _ in range(80):
                g.clear_output()
                r = text(run_with_bps(g, ' ' + mm.group(2), [], None, max_slices=6000))
                if mm.group(1).lower() in r.lower(): break
            continue
        g.clear_output()
        r = text(run_with_bps(g, ' ' + c, [], None, max_slices=6000)).upper()
        if c in ('LOOK', 'INVENTORY') or any(k in r for k in ('I SEE NO', 'YOU CANNOT', 'I DO NOT KNOW', 'WHICH ')):
            bad.append(i)
        if m[0xA0DA]: break
    return bad

def main():
    cmds = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
    cand = errors(cmds)
    if len(sys.argv) > 3:      # only try lines that an earlier (flawed) pass removed
        import difflib
        earlier = [l.rstrip('\n') for l in open(sys.argv[3]) if l.strip()]
        sm = difflib.SequenceMatcher(None, cmds, earlier, autojunk=False)
        gone = set()
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ('delete', 'replace'): gone |= set(range(i1, i2))
        cand = [i for i in cand if i in gone]
    print('candidates', len(cand), flush=True)
    keep = set(cand)          # candidates still kept in the file
    def try_remove(S):
        trial = [c for i, c in enumerate(cmds) if i not in (set(cand) - keep) | set(S)]
        return replay(trial)
    # ddmin over the candidate list in chunks
    n = 2
    todo = [i for i in cand]
    chunk = max(1, len(todo) // 2)
    while chunk >= 1:
        for start in range(0, len(todo), chunk):
            S = [i for i in todo[start:start + chunk] if i in keep]
            if not S: continue
            if try_remove(S):
                keep -= set(S)
                print('removed', len(S), 'remaining candidates kept', len(keep), flush=True)
        if chunk == 1: break
        chunk //= 2
    final = [c for i, c in enumerate(cmds) if i not in (set(cand) - keep)]
    assert replay(final)
    open(sys.argv[2], 'w').write('\n'.join(final) + '\n')
    print('wrote', sys.argv[2], len(cmds), '->', len(final))

main()
