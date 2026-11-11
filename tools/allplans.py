"""Find every plan script in the game and every action record they use.
Prints a summary; importable as collect()."""
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # appended so tools/dis.py never shadows the stdlib dis
from plan import b, w, decode, walk

def hlen(a):
    f = b(a); return 2 + (2 if f & 0x40 else 0) + (5 if f & 0x10 else 0)

def records():
    recs = {}
    a = 0x9F38
    while b(a) != 0xFF:
        recs.setdefault(w(a + 1), set()).add(f'default for verb {b(a)}'); a += 3
    i = 0
    while w(0xAA71 + 2 * i):
        recs.setdefault(w(0xAA71 + 2 * i), set()).add(f'shared {i+1}'); i += 1
    for n in range(13):
        recs.setdefault(w(0x9FAB + 2 * n), set()).add(f'internal verb {128+n}')
    return recs

def collect():
    recs = records()
    starts = {}
    a = 0x9860
    while b(a) != 0xFF:
        starts.setdefault(w(a + 1), set()).add(f'actor {b(a)}'); a += 8
    # Scripts that code switches an actor onto (found by searching for
    # LD rr,nn into the script area): the HAIL record gives the cabbie
    # the script at $F2B6 ($E2E2 LD DE,$F2B6).
    starts.setdefault(0xF2B6, set()).add('given to a hailed cabbie by $E2E2')
    instrs = {}
    done = set()
    changed = True
    while changed:
        changed = False
        for r, why in list(recs.items()):
            if b(r) & 0x80 and r not in done:
                starts.setdefault(r + hlen(r), set()).add(f'body of record ${r:04X}')
        todo = [s for s in starts if s not in done]
        for s in todo:
            done.add(s)
            got = walk([s])
            instrs.update(got)
            for ia, ins in got.items():
                t = ins.get('target')
                if t is not None and t not in recs:
                    recs[t] = {f'RUN at ${ia:04X}'}; changed = True
                elif t is not None:
                    recs[t].add(f'RUN at ${ia:04X}')
            changed = changed or bool(todo)
        for r in recs:
            if b(r) & 0x80 and (r + hlen(r)) not in starts:
                changed = True
    return recs, starts, instrs

if __name__ == '__main__':
    recs, starts, instrs = collect()
    print(len(recs), 'records,', len(starts), 'script entry points,', len(instrs), 'instructions')
    for r in sorted(recs):
        print(f'${r:04X} {b(r):02X} {b(r+1):02X} {"SCRIPT" if b(r)&0x80 else "code  "} ' + '; '.join(sorted(recs[r]))[:150])
