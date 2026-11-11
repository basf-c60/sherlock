"""Shared helpers for emulator experiments (restored-session version).
Boots the game to the first command prompt and provides run_with_bps()."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'source'))
sys.path.insert(0, ROOT)   # in the packaged zip, source/ is the project root
from harness import Game, _or_a_flags, GET_KEY_ENTRY, PRINT_CHAR_ENTRY, PICTURE_ENTRY

def _bin(n):
    for d in ('', 'extracted_binaries', os.path.join('source', 'extracted_binaries')):
        f = os.path.join(ROOT, d, n)
        if os.path.exists(f): return open(f, 'rb').read()
    raise FileNotFoundError(n)
P = _bin('p.bin')
S = _bin('s.bin')

def booted():
    g = Game(P, S)
    g.run(max_slices=60)
    for _ in range(4):
        g.queue('\r'); g.run(max_slices=400)
    g.clear_output()
    return g

def run_with_bps(g, cmd, bps, on_hit, max_slices=3000, idle_after=40):
    """Queue cmd+ENTER and run until idle; call on_hit(g, pc) at each of bps."""
    for bp in bps:
        g.m.set_breakpoint(bp)
    if cmd is not None:
        g.queue(cmd + '\r')
    idle = 0
    for _ in range(max_slices):
        g.m.ticks_to_stop = 2_000_000
        g.m.run()
        pc = g.m.pc
        if pc == GET_KEY_ENTRY:
            if not g.q:
                idle += 1
                if idle > idle_after:
                    break
            else:
                idle = 0
            g._handle_get_key()
        elif pc == PRINT_CHAR_ENTRY:
            g._handle_print_char()
        elif pc == PICTURE_ENTRY:
            g._skip_picture()
        elif pc in bps:
            on_hit(g, pc)
            g.m.step_over_breakpoint()
    for bp in bps:
        g.m.clear_breakpoint(bp)
    return g.output()

def text(out):
    """Strip the '+' echo markers and squash the 37-column padding."""
    import re
    return re.sub(r' {2,}', ' | ', out.replace('+', '')).strip()

REGS = ['af', 'bc', 'de', 'hl', 'ix', 'iy', 'sp', 'pc', 'alt_af', 'alt_bc',
        'alt_de', 'alt_hl', 'ir', 'iff1', 'iff2', 'int_mode' if False else 'iff1']

def save(g, path):
    """Snapshot the machine between commands (memory and registers)."""
    import pickle
    st = {r: getattr(g.m, r) for r in REGS}
    pickle.dump((bytes(g.m.memory), st), open(path, 'wb'))

def load(path):
    """A booted Game with a snapshot from save() put back."""
    import pickle
    mem, st = pickle.load(open(path, 'rb'))
    g = booted()
    g.m.set_memory_block(0, mem)
    for r, v in st.items():
        setattr(g.m, r, v)
    g.clear_output()
    return g
