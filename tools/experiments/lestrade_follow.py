"""Lestrade on platform two at Leatherhead (room 55) in his wait-for-a-
train loop ($EAD0), you beside him. Does an order take him off the
platform, and does he then follow you (verb 134, $EAE2)?

    python3 tools/experiments/lestrade_follow.py 'SAY TO LESTRADE "FOLLOW ME"'
"""
import sys; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
from play import booted, run_with_bps, text
import objects as O, rooms as RMOD
ENT = {e['id']: e for e in O.entities()}; RM = RMOD.rooms()
g = booted(); m = g.m.memory
m[0x9D90] = 1; m[0x9E88] = 1
r = 55; a = RM[r]['address']
m[0x8CC9] = r; m[0xA00A] = r; m[0xDCFF] = a & 255; m[0xDD00] = a >> 8; m[0xDD01] = r
m[ENT[2]['address'] + 15] = 55
m[0x9869] = 0xD0; m[0x986A] = 0xEA
m[ENT[3]['address'] + 15] = 11; m[0x9871] = 0x5C; m[0x9872] = 0xF0   # Watson out of the way
lr = lambda: (m[ENT[2]['address'] + 15], '$%04X' % (m[0x9869] | m[0x986A] << 8))
g.clear_output()
for cmd in [sys.argv[1] if len(sys.argv) > 1 else 'SAY TO LESTRADE "FOLLOW ME"', 'SOUTH', 'SOUTH', 'SOUTH', 'WEST', 'EAST']:
    g.clear_output()
    out = text(run_with_bps(g, ' ' + cmd, [], None, max_slices=6000))
    print(f'{cmd:32} you {m[0x8CC9]:3}  lestrade', lr(), '|', out[-220:])
