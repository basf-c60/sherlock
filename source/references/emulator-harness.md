# Building a scriptable Z80 test harness

This is the single most valuable piece of infrastructure to build early.
Everything from the initial code/data split, through discovering the
dictionary format, to catching your own documentation mistakes at the end,
goes faster and is more trustworthy with a working harness than without one.

Use the `z80` Python package (`pip install z80 --break-system-packages`).
It's a plain register-level emulator: you set memory, set registers, tell
it to run for so many T-states or until a breakpoint, and read the result
back. It knows nothing about the Spectrum ROM, screen layout, or keyboard -
you provide all of that by hooking `set_input_callback` (port reads) and by
placing breakpoints at addresses *inside the game* where you know
characters get printed or keys get read (found during Phase 1/3).

## Minimal harness

```python
import z80

class Game:
    def __init__(self, code, load_addr, entry_pc, sp=0x5EF0,
                 print_bp=None, key_read_bp=None):
        self.m = z80.Z80Machine()
        mem = bytearray(65536)
        mem[0x38] = 0xFB; mem[0x39] = 0xC9   # RST 38 -> harmless RET, in case anything strays there
        mem[load_addr:load_addr+len(code)] = code
        self.m.set_memory_block(0, bytes(mem))
        self.nin = 0
        self.m.set_input_callback(self._port_in)
        self.m.pc = entry_pc
        self.m.sp = sp
        self.print_bp = print_bp
        self.key_read_bp = key_read_bp
        self.q = []      # queued keystrokes
        self.gap = 0     # turns of "no key" to insert between characters, if the game debounces
        self.out = []

    def _port_in(self, port):
        # A cheap default: never report a key pressed via raw port reads.
        # Real games are usually driven through their OWN "read a key"
        # routine (hooked as a breakpoint below), not raw port polling,
        # so this rarely needs to be cleverer than "no key".
        return 0xFF

    def run(self, cmd=None, max_iterations=200000):
        if cmd is not None:
            self.q += list(cmd.upper()) + ['\r']   # adjust case/terminator per game
        self.out = []
        polls_with_nothing_queued = 0
        for _ in range(max_iterations):
            self.m.ticks_to_stop = 1_000_000
            self.m.run()
            pc = self.m.pc
            if pc == self.print_bp:
                self.out.append(chr(self.m.a))
                self.m.step_over_breakpoint()
            elif pc == self.key_read_bp:
                if self.gap > 0:
                    self.gap -= 1
                    self.m.a = 0
                elif self.q:
                    self.m.a = ord(self.q.pop(0))
                    self.gap = 2          # crude debounce; tune per game
                else:
                    polls_with_nothing_queued += 1
                    self.m.a = 0
                    if polls_with_nothing_queued > 50:
                        return ''.join(self.out)
                self.m.step_over_breakpoint()
        return ''.join(self.out)
```

Set `self.m.set_breakpoint(addr)` for both `print_bp` and `key_read_bp`
before calling `run`. Finding these two addresses is usually one of the
first things worth doing once you have a rough code/data split: search for
the routine that does `IN A,($FE)` (reads the keyboard half-rows) - that's
your key-read hook - and the routine that writes a pixel glyph to the
display file - that's your print hook, or hook the one *character-level*
print routine just above it if word-wrap/paging logic lives below it.

## Patterns that pay off repeatedly

**A `scen.py`-style test-scenario helper.** Once you know the object/room
record layout, wrap `Game` in a subclass with `setobj(number, offset,
value)`, `goto(room)`, and a `run()` that also seeds any RNG-state bytes
from a `seed` parameter, so you can:

```python
g = Game(seed=3)
g.setobj(SWORD, HOLDER_OFFSET, PLAYER_OBJECT_NUMBER)   # force an item into the player's hands
g.goto(SOME_ROOM)
print(g.run('take sword'))
```

This turns "I think this routine does X" into a five-line, rerunnable
check, and it's how most of the confirmed bugs and corrected claims in the
worked example were actually found.

**Call a routine directly**, bypassing the parser/game-command layer
entirely, when you want to test one routine's logic in isolation (e.g. "is
the found/not-found flag Z-set or NZ?"). Set up registers, set `m.pc` to
the routine's address, run until it returns to a `HALT` you've planted at
the return address, then read back registers/flags:

```python
def call_routine(binary, load_addr, routine_pc, **regs):
    m = z80.Z80Machine()
    mem = bytearray(65536)
    mem[load_addr:load_addr+len(binary)] = binary
    mem[0x4000] = 0x76                      # HALT as a "stop here" marker
    m.set_memory_block(0, bytes(mem))
    m.sp = 0x5EF0
    mem2 = bytearray(m.memory); mem2[0x5EF0] = 0x00; mem2[0x5EF1] = 0x40
    m.set_memory_block(0, bytes(mem2))      # return address -> the HALT
    for k, v in regs.items(): setattr(m, k, v)
    m.pc = routine_pc
    for _ in range(2000):
        m.ticks_to_stop = 1
        m.run()
        if m.pc == 0x4000: break
    return {'a': m.a, 'f': m.f, 'ix': m.ix, ...}
```

This is exactly how a genuinely wrong assumption about a "found/not-found"
flag convention (Z meant the opposite of what several routines' own
documentation claimed) was caught: read the code, form a hypothesis, then
actually call the routine with a key that exists and one that doesn't, and
read the flags back, instead of trusting the re-reading.

**Profile before optimising.** If asked to speed something up, single-step
(`ticks_to_stop = 1` each iteration) while tallying a `Counter` of visited
PC values over a representative run, then look at where the time actually
goes before proposing a change. Verify any optimisation by comparing full
output (e.g. a full screen buffer, or every line of text over a scripted
session) between the original and patched binaries - not just "it looks
right".

**Watch your own step budget.** Printing many lines of text can cost far
more emulated cycles than expected (word-wrap, per-glyph rendering, a
"pause for a keypress" busy-loop the game itself implements). If a test's
output looks truncated, increase the iteration budget substantially before
concluding something is broken - more than one false alarm in the worked
example turned out to be the *test harness* running out of patience, not
the game.
