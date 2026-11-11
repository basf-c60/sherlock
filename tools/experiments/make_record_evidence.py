"""Merge the outputs of record_coverage.py, record_effects.py and insn_coverage.py (one JSON per route,
in the directory given) into source/record_evidence.json, which overlay_10_traced.py reads.
usage: make_record_evidence.py DIR     (DIR holds <route>.json, fx_<route>.json and ic_<route>.json)"""
import json, glob, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'source'))
from plan import names
V, O = names()
d = sys.argv[1]
ev = {}
for f in sorted(glob.glob(os.path.join(d, '*.json'))):
    n = os.path.basename(f)[:-5]
    if n.startswith(('fx_', 'ic_', 'sc_')) or n in ('dd', 'ic_summary'): continue
    j = json.load(open(f))
    for a, lst in j.get('who', {}).items():
        e = ev.setdefault(int(a), {'runs': 0, 'routes': 0, 'actors': {}})
        e['routes'] += 1
        for k, c, cmd in lst:
            e['runs'] += c; nm = O.get(k[0], '#%d' % k[0]); e['actors'][nm] = e['actors'].get(nm, 0) + c
ic = {}; hit = set()
for f in glob.glob(os.path.join(d, 'ic_*.json')):
    if f.endswith('summary.json'): continue
    j = json.load(open(f)); hit |= set(j['hit']); ic = j['blocks']
cov = {int(b): [len(l), sum(1 for a in l if a in hit), [a for a in l if a not in hit]] for b, l in ic.items()}
out = {'records': {str(a): v for a, v in ev.items()}, 'insn_coverage': {str(b): v for b, v in cov.items()}}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'source', 'record_evidence.json'), 'w'), indent=0, sort_keys=True)
print(len(ev), 'blocks with runs;', len(cov), 'with instruction coverage')
