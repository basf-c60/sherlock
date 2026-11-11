"""Find every little-endian reference to an address in p.bin:
python3 tools/refs.py ADDR [ADDR...]  - shows the 4 bytes before each hit
and names CALL/JP/LD forms when the byte before is a known opcode."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = open(os.path.join(ROOT, 'p.bin'), 'rb').read(); B = 0x5D80
OPS = {0xCD: 'CALL', 0xC3: 'JP', 0x21: 'LD HL', 0x11: 'LD DE', 0x01: 'LD BC',
       0x2A: 'LD HL,()', 0x22: 'LD (),HL', 0x32: 'LD (),A', 0x3A: 'LD A,()',
       0xCA: 'JP Z', 0xC2: 'JP NZ', 0xDA: 'JP C', 0xD2: 'JP NC', 0xCC: 'CALL Z',
       0xC4: 'CALL NZ', 0xDC: 'CALL C', 0xD4: 'CALL NC', 0xF2: 'JP P', 0xFA: 'JP M'}
for a in sys.argv[1:]:
    t = int(a, 16); pat = bytes([t & 255, t >> 8]); i = P.find(pat); hits = []
    while i >= 0:
        op = P[i - 1] if i else None
        name = OPS.get(op, '')
        if op in (0x21, 0x2A, 0x22) and i >= 2 and P[i - 2] in (0xDD, 0xFD):
            name = ('IX ' if P[i - 2] == 0xDD else 'IY ') + name
        hits.append(f'${B + i:04X} [{P[max(0, i - 4):i].hex(" ")}] {name}')
        i = P.find(pat, i + 1)
    print(f'${t:04X}: {len(hits)} refs'); [print('   ', h) for h in hits]
