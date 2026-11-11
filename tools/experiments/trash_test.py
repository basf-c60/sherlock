import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O, rooms as R
ENT={e['id']:e for e in O.entities()}; RM=R.rooms()
def goto(g, r):
    mem=g.m.memory; a=RM[r]['address']
    mem[0x8CC9]=r; mem[0xA00A]=r; mem[0xDCFF]=a&255; mem[0xDD00]=a>>8; mem[0xDD01]=r
def flags5(g,i): return g.m.memory[ENT[i]['address']+5]
for room, target, hidden, cmds in [(39,80,81,['EXAMINE CLOSELY TRASH PILE','CLOSELY EXAMINE TRASH PILE','EXAMINE CLOSELY THE TRASH PILE','LOOK','TAKE NOTE']),
                                   ]:
    g=booted(); goto(g,room)
    print(f'== room {room} ({RM[room].get("name")}); hidden {hidden} {O.display_name(ENT[hidden])} +5={flags5(g,hidden):02X}')
    for c in cmds:
        g.clear_output(); out=run_with_bps(g,c,[0xE0E0,0xE0F2,0xE0EB,0xE0FD],lambda g,pc: print('    hit',hex(pc),'A=',g.m.a),max_slices=3000)
        print(f'  {c!r}: {text(out)[:260]}')
        print(f'     hidden +5={flags5(g,hidden):02X}')
