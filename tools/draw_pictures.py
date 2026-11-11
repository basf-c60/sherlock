"""Draw every room picture by running the game's own picture interpreter
($F3C2) in the emulator, with the Spectrum ROM that SkoolKit ships
loaded at $0000 (the interpreter plots through PIXEL-ADD at $22AA).

    python3 tools/draw_pictures.py OUTDIR

Writes one PNG per picture (pic-XXXX.png: the top right quarter of the
screen, where every picture is drawn, at 2x) and prints a summary.
tools/package.sh runs this into html/game/pictures for the Pictures page.
"""
import os, sys
import z80
import skoolkit
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = open(os.path.join(ROOT, 'p.bin'), 'rb').read()
ROM = open(os.path.join(os.path.dirname(skoolkit.__file__), 'resources', '48.rom'), 'rb').read()
COLS = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205)]
BRIGHT = [(0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]
SENTINEL = 0x5CF0


def draw(addr, max_ticks=3_000_000_000):
    m = z80.Z80Machine()
    mem = bytearray(65536)
    mem[0:0x4000] = ROM
    mem[0x5800:0x5B00] = bytes([0x38]) * 0x300      # white paper, black ink
    mem[0x5D80:0x5D80 + len(P)] = P
    m.set_memory_block(0, bytes(mem))
    m.sp = 0x5D00
    m.sp -= 2
    m.memory[m.sp] = SENTINEL & 0xFF
    m.memory[m.sp + 1] = SENTINEL >> 8
    m.hl = addr
    m.iy = 0x5C3A
    m.pc = 0xF3C2
    m.set_breakpoint(SENTINEL)
    used = 0
    while m.pc != SENTINEL and used < max_ticks:
        m.ticks_to_stop = 1_000_000
        m.run()
        used += 1_000_000
    return m, m.pc == SENTINEL


def to_png(m, path, crop=False):
    img = Image.new('RGB', (256, 192))
    px = img.load()
    mem = m.memory
    for y in range(192):
        row = 0x4000 | ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2)
        for xb in range(32):
            byte = mem[row + xb]
            attr = mem[0x5800 + (y // 8) * 32 + xb]
            pal = BRIGHT if attr & 0x40 else COLS
            ink, paper = pal[attr & 7], pal[(attr >> 3) & 7]
            for bit in range(8):
                px[xb * 8 + bit, y] = ink if byte & (0x80 >> bit) else paper
    if crop:   # every picture is drawn in the top right quarter
        img = img.crop((128, 0, 256, 128))
    img.resize((img.width * 2, img.height * 2), Image.NEAREST).save(path)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'pictures'
    os.makedirs(out, exist_ok=True)
    w = lambda a: P[a - 0x5D80] | P[a - 0x5D80 + 1] << 8
    a = w(0xA0D8)
    seen = {}
    while P[a - 0x5D80] != 0xFF:
        room, pic = P[a - 0x5D80], w(a + 1)
        seen.setdefault(pic, []).append(room)
        a += 3
    for pic, rooms in sorted(seen.items()):
        m, ok = draw(pic)
        path = os.path.join(out, f'pic-{pic:04X}.png')
        to_png(m, path, crop=True)
        ink = sum(1 for i in range(0x4000, 0x5800) if m.memory[i])
        print(f'${pic:04X} rooms {rooms}: {"returned" if ok else "DID NOT RETURN"}, {ink} non-empty screen bytes -> {path}')
