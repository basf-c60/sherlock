"""Quick look-up disassembler: python3 tools/dis.py START [END]
Disassembles p.bin (loaded at $5D80) from START to END (default START+0x40)
by driving sna2skool.py with a throwaway control file. Replaces z80dasm,
which isn't available in this environment."""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, 'source', 'extracted_binaries', 'p.bin')
start = int(sys.argv[1], 16)
end = int(sys.argv[2], 16) if len(sys.argv) > 2 else start + 0x40
with tempfile.TemporaryDirectory() as d:
    ctl = os.path.join(d, 'x.ctl')
    open(ctl, 'w').write(f'c {start}\ni {end}\n')
    out = subprocess.run(['sna2skool.py', '-H', '-o', '0x5d80', '-c', ctl, BIN],
                         capture_output=True, text=True).stdout
for line in out.splitlines():
    if line[:1] in 'c*' or line.startswith(' $'):
        print(line)
