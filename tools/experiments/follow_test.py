import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'source')
from play import booted, run_with_bps, text
import objects as O
ENT={e['id']:e for e in O.entities()}
g=booted()
mem=g.m.memory
def cont(i): return mem[ENT[i]['address']+1]
def room(i): return mem[ENT[i]['address']+15]
print('before: player in', cont(0), 'room', room(0), '| watson in', cont(3), 'room', room(3))
for c in ['FOLLOW WATSON','LOOK','GET OUT','INVENTORY']:
    g.clear_output(); out=run_with_bps(g,c,[],None,max_slices=4000)
    print(f'{c!r}: {text(out)[:400]}')
    print('   player in', cont(0), 'room', room(0), '| watson in', cont(3), 'room', room(3))
print('24 =', O.display_name(ENT[24]), '; 23 =', O.display_name(ENT[23]))
