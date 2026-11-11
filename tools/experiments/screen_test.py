"""Play with the real ROM loaded and pictures drawn, and save the screen.
Moves the player to Baker Street (room 5), LOOKs, and writes screen.png."""
import sys, os; sys.path.insert(0, 'tools'); sys.path.insert(0, 'source')
import skoolkit
from play import P, S, run_with_bps, text
from harness import Game, PICTURE_ENTRY
import rooms as RMOD, draw_pictures as DP
RM = RMOD.rooms()
ROM = open(os.path.join(os.path.dirname(skoolkit.__file__), 'resources', '48.rom'), 'rb').read()
g = Game(P, S)
g.m.set_memory_block(0, ROM)
g.m.clear_breakpoint(PICTURE_ENTRY)
g.run(max_slices=60)
for _ in range(4):
    g.queue('\r'); g.run(max_slices=400)
mem = g.m.memory
r = 5; a = RM[r]['address']
mem[0x8CC9] = r; mem[0xA00A] = r; mem[0xDCFF] = a & 255; mem[0xDD00] = a >> 8; mem[0xDD01] = r; mem[0x8CBA + 1] = 0xFF
out = run_with_bps(g, 'LOOK', [], None, max_slices=4000)
print(text(out)[-300:])
print('pictures skipped by the harness:', g.pictures)
DP.to_png(g.m, sys.argv[1] if len(sys.argv) > 1 else 'screen.png')
