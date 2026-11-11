"""
Scriptable Z80 harness for Sherlock (Beam Software/Melbourne House, 1984).

Memory layout, confirmed by tracing the tape's own custom loader
(see source/loader_notes.md):

    0x4000-0x5AFF  loading screen (display file), loaded from the "s" block
    0x5B00-0x5BFF  relocated loader stub (irrelevant once the game starts)
    0x5D80-0xFFFF  the main "p" block: all game code + data. Load address
                   0x5D80, entry point 0xA040 (17,088 bytes into the block).
                   The game sets SP=0x5D80 itself in its own init code,
                   reusing the freed loader/stub space as stack.

    (The "SHD V2.0" block, header address 0x840B-0xA01F, is entirely
    inside the "p" block's range and is loaded *before* "p", so it is
    completely overwritten before the game ever runs - see
    source/loader_notes.md for how this was confirmed.)

Two hooks make headless play possible without a real ROM:

GET-KEY ($C41F) - Keyboard input does not go through raw port reads (zero
`IN A,($FE)` / `IN A,(C)` instructions anywhere in the 41,600-byte "p"
block). Instead the game calls its own routine at $C41F, which does
`EI; HALT; DI` to let the ROM's interrupt handler scan the keyboard into
the standard system variables, then reads FLAGS ($5C3B bit 5, "key
available") and LAST-K ($5C08, decoded ASCII), remaps a couple of ROM
edit-key codes, and returns:
    A = 0                        -> no key was waiting
    A = ord(char) | 0x80 (bit 7) -> a key was waiting, this is its code
Called from three places, all genuine CALL instructions ($A080, $A53B,
$C416). We bypass the whole routine at a breakpoint on entry and jump
straight back to the caller, so we never need real interrupts/ROM at
all - but we must also set the flags an immediate `or a` on the result
would give, because the caller's next instruction almost certainly
branches on them and the real routine's last instruction before RET
(`xor a` or `set 7,a`) would have set them (see _or_a_flags).

PRINT-CHAR ($C388) - the low-level "plot one character's glyph" routine.
It computes screen_font_address = A*8 + 0x3C00 (matches the real ROM
font layout: space=32 -> 0x3D00) and draws 8 pixel rows, so A holds the
literal ASCII code being printed at the moment this is called - we don't
need real ROM glyph bitmaps to recover the text, just to hook here and
read A. (Confirmed: this recovers legible game text, e.g. the opening
"Mon 08:00am ... The sun streams in..." description - see
source/loader_notes.md.)
"""

import z80

LOAD_ADDR = 0x5D80
ENTRY_PC = 0xA040
GET_KEY_ENTRY = 0xC41F
PRINT_CHAR_ENTRY = 0xC388
# The location-picture interpreter: draws vector pictures with the 48K ROM's
# graphics routines (it calls PIXEL-ADD at $22AA). There is no ROM here, so
# the harness skips the whole call - it only draws, it changes no game
# state. Without this, entering a room with a picture (the entrance
# hallway, room 6) ran off into empty memory. See harness_notes.md.
PICTURE_ENTRY = 0xF3C2

SCREEN_START, SCREEN_END = 0x4000, 0x5B00


def _parity_even(x: int) -> bool:
    x ^= x >> 4
    x ^= x >> 2
    x ^= x >> 1
    return (x & 1) == 0


def _or_a_flags(a: int) -> int:
    """F value a plain `or a` on this A would leave: S/Z from the
    result, H=0, PV=parity, N=0, C=0, bits 5/3 mirror the result."""
    a &= 0xFF
    s = 0x80 if a & 0x80 else 0
    z = 0x40 if a == 0 else 0
    f5 = a & 0x20
    f3 = a & 0x08
    pv = 0x04 if _parity_even(a) else 0
    return s | z | f5 | f3 | pv


class Game:
    def __init__(self, p_block: bytes, screen_block: bytes | None = None,
                 track_pc_coverage: bool = False):
        self.m = z80.Z80Machine()
        mem = bytearray(65536)
        if screen_block is not None:
            mem[0x4000:0x4000 + len(screen_block)] = screen_block
        mem[LOAD_ADDR:LOAD_ADDR + len(p_block)] = p_block
        self.m.set_memory_block(0, bytes(mem))
        self.m.set_breakpoint(GET_KEY_ENTRY)
        self.m.set_breakpoint(PRINT_CHAR_ENTRY)
        self.m.set_breakpoint(PICTURE_ENTRY)
        self.pictures = 0
        self.m.pc = ENTRY_PC
        self.m.sp = LOAD_ADDR
        self.q: list[str] = []          # queued input characters
        self.printed: list[str] = []    # characters seen at PRINT-CHAR
        self.pc_coverage: set[int] | None = set() if track_pc_coverage else None
        self._mem = mem
        if self.pc_coverage is not None:
            # Read-mark only the "p" block's own range. We only care
            # about which addresses *inside our own code* get touched
            # (that's the whole Phase-1 code/data question); ROM/stack/
            # screen reads are irrelevant noise for that purpose, and
            # marking the full 64K turned out to make every address
            # register as "covered" immediately (some interaction with
            # how the emulator applies marks over such a large range),
            # so keep this to the region we actually need answered.
            self.m.mark_addrs(LOAD_ADDR, 0x10000 - LOAD_ADDR,
                               z80.Z80Machine.READ_MARK)

            def on_read(addr):
                self.pc_coverage.add(addr)
                return self._mem[addr]
            self.m.set_read_callback(on_read)
            # Writes to this marked range still need to land somewhere:
            # without a write callback, marked-for-read bytes would
            # otherwise not update on write. Keep it a plain passthrough.
            self.m.mark_addrs(LOAD_ADDR, 0x10000 - LOAD_ADDR,
                               z80.Z80Machine.WRITE_MARK)

            def on_write(addr, value):
                self._mem[addr] = value
            self.m.set_write_callback(on_write)

    def queue(self, text: str):
        """Queue characters to feed to GET-KEY, one per call, in order.
        '\\r' is ENTER; append it yourself after each command."""
        self.q.extend(text)

    def _handle_get_key(self):
        ret_addr = self.m.memory[self.m.sp] | (self.m.memory[self.m.sp + 1] << 8)
        self.m.sp = (self.m.sp + 2) & 0xFFFF
        if self.q:
            a = ord(self.q.pop(0)) | 0x80
        else:
            a = 0
        self.m.a = a
        self.m.f = _or_a_flags(a)
        self.m.pc = ret_addr

    def _skip_picture(self):
        ret_addr = self.m.memory[self.m.sp] | (self.m.memory[self.m.sp + 1] << 8)
        self.m.sp = (self.m.sp + 2) & 0xFFFF
        self.m.pc = ret_addr
        self.pictures += 1

    def _handle_print_char(self):
        a = self.m.a
        self.printed.append(chr(a) if 32 <= a < 127 else f'[{a:#04x}]')
        self.m.step_over_breakpoint()

    def run(self, ticks_per_slice=2_000_000, max_slices=400,
            idle_after=40):
        """Run until the input queue is exhausted and GET-KEY has been
        polled with nothing queued `idle_after` times in a row (the game
        is idle, waiting for a key), or the slice budget runs out.
        Returns (reason, slices_used).
        """
        idle_polls = 0
        for s in range(max_slices):
            self.m.ticks_to_stop = ticks_per_slice
            self.m.run()
            if self.m.pc == GET_KEY_ENTRY:
                if not self.q:
                    idle_polls += 1
                    if idle_polls > idle_after:
                        return ('idle', s)
                else:
                    idle_polls = 0
                self._handle_get_key()
            elif self.m.pc == PRINT_CHAR_ENTRY:
                self._handle_print_char()
            elif self.m.pc == PICTURE_ENTRY:
                self._skip_picture()
        return ('slice_budget', max_slices)

    def output(self) -> str:
        return ''.join(self.printed)

    def clear_output(self):
        self.printed.clear()
