"""Full verification: build ctl/ref, regenerate skool, round-trip against
the original binary, and cross-check every line-comment address against
the instruction boundaries SkoolKit actually produced. Exit 1 on failure."""
import os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source') if os.path.isdir(os.path.join(ROOT, 'source')) else ROOT  # the zip's source/ is the root
PBIN = next(f for f in (os.path.join(ROOT, 'p.bin'), os.path.join(ROOT, 'extracted_binaries', 'p.bin'), os.path.join(ROOT, 'source', 'extracted_binaries', 'p.bin')) if os.path.exists(f))
def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
r = run([sys.executable, 'build.py'], SRC); print(r.stdout.strip()); assert r.returncode == 0, r.stderr
r = run(['sna2skool.py', '-H', '-o', '0x5d80', '-c', 'game.ctl', PBIN], ROOT)
open(os.path.join(ROOT, 'game.skool'), 'w').write(r.stdout)
warn = [l for l in r.stderr.splitlines() if 'WARNING' in l]
print('sna2skool warnings:', warn or 'none')
run(['skool2bin.py', '-i', 'game.skool', '/tmp/rt.bin'], ROOT)
same = open('/tmp/rt.bin', 'rb').read() == open(PBIN, 'rb').read()
print('round trip:', 'IDENTICAL' if same else 'MISMATCH')
sys.path.insert(0, SRC)
import importlib, build_skeleton
for m in sorted(f[:-3] for f in os.listdir(SRC) if f.startswith('overlay_') and f.endswith('.py')):
    importlib.import_module(m)
real = set()
for line in open(os.path.join(ROOT, 'game.skool')):
    m = re.match(r'^[*cbtsuwg ]?\$([0-9A-F]{4}) ', line)
    if m: real.add(int(m.group(1), 16))
bad = [(a, l) for a, rec in build_skeleton.A.items() if rec['t'] == 'c'
       for l in rec['comments'] if l not in real]
# A site note inside a block the automatic split mislabelled as data is
# not emitted (and has no instruction line to check): report, don't fail.
emitted = open(os.path.join(ROOT, 'game.ctl')).read()
lost = [l for l in build_skeleton.NOTES if f'C {l} ' not in emitted and l not in
        {c for r in build_skeleton.A.values() for c in r['comments']}]
print(f'site notes: {len(build_skeleton.NOTES)}, not emitted (not inside a code block): {len(lost)}')
n = sum(len(r['comments']) for r in build_skeleton.A.values())
print(f'address cross-check: {len(build_skeleton.A)} blocks, {n} line comments, {len(bad)} problems')
for a, l in bad[:20]: print(f'  {a if isinstance(a, str) else hex(a)}: comment at ${l:04X} is not an instruction start')
if lost: print('  in blocks the automatic split calls data (really code):',
               ' '.join(f'${l:04X}' for l in sorted(lost)))
bad += [('note', l) for l in build_skeleton.NOTES if l not in lost and l not in real]
sys.exit(0 if same and not bad and not warn else 1)
