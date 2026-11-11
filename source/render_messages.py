"""
Render game messages by running the game's own message interpreter
($A59F) in the emulator and capturing what it prints - the approach in
references/message-rendering.md, rather than hand-decoding bytecode.

Each message is rendered in a copy of a game booted to its first command
prompt, with fixed placeholder parameters so substitutions read
naturally and consistently:
    actor ($A036)            = 0  (you)
    direct object ($A034)    = 22 (the oil lamp)
    indirect object ($A035)  = 24 (watsons armchair)
so "You take the oil lamp."-style output means "<actor> ... <object>".
Parser messages that quote the player's command are rendered after the
command EXAMINE LAMP, so its words appear where the command goes.

Characters are captured at $A9B7, the interpreter's character-output
primitive, rather than at PLOT-CHAR: below $A9B7 the screen code adds a
cursor glyph after every character and wraps lines mid-word, which
would have to be undone again.

Usage: python3 render_messages.py  -> writes messages.json
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.append(os.path.join(ROOT, 'tools'))   # appended: tools/dis.py must not shadow the stdlib dis
from harness import Game, _or_a_flags, GET_KEY_ENTRY, PRINT_CHAR_ENTRY, PICTURE_ENTRY  # noqa: E402

P = open(os.path.join(ROOT, 'p.bin'), 'rb').read()
S = open(os.path.join(ROOT, 's.bin'), 'rb').read()
BASE = 0x5D80
PRINTER = 0xA59F
TRAP = 0x5BF0          # return address; free loader-stub RAM
LINES_LEFT = 0xC1F5    # page-wait counter (see overlay_01_boot.py)

ACTOR, DOBJ, IOBJ = 0, 22, 24


CONTEXT_COMMAND = 'EXAMINE LAMP'
CHAR_OUT = 0xA9B7      # the interpreter's character-output primitive
CONTROL = 0xA621       # control-code dispatch (A = code 0-$1C)
NEXT_BYTE = 0xA5ED     # "move on to the next message byte"
WORD_OF_COMMAND = 0x01 # control code: print a word of the parsed command
PLACEHOLDER = ' \u2039word\u203a'


def booted_snapshot():
    """A game booted to its first prompt, after one real command has
    been parsed - the parser error messages print words of the current
    command (via the matched verb pattern saved at $B18E), which is
    garbage until something has been parsed."""
    g = Game(P, S)
    g.run(max_slices=60)
    for _ in range(4):
        g.queue('\r')
        g.run(max_slices=400)
    g.queue(CONTEXT_COMMAND + '\r')
    g.run(max_slices=1500)
    return bytes(g.m.memory)


def message_sites():
    """{message address: [call sites]} for every LD HL,nn shortly before
    a CALL/JP (or conditional) to the printer."""
    sites = {}
    for m in re.finditer(re.escape(bytes([PRINTER & 0xFF, PRINTER >> 8])), P):
        i = m.start() - 1
        if P[i] not in (0xCD, 0xC3, 0xC4, 0xCC, 0xC2, 0xCA, 0xD4, 0xDC,
                        0xD2, 0xDA):
            continue
        for back in range(3, 14):
            j = i - back
            if j >= 0 and P[j] == 0x21:
                addr = P[j + 1] | P[j + 2] << 8
                if BASE <= addr < 0x10000:
                    sites.setdefault(addr, []).append(BASE + j)
                break
    return sites


MSG_LO, MSG_HI = 0x67B7, 0x8259   # the message bytecode area (overlay 05)


def code_load_sites():
    """{message address: [sites]} for every LD HL,nn or LD DE,nn inside a
    code block of the current game.skool whose operand is in the message
    area - wider than message_sites(), which only finds LD HL shortly
    before a printer call. The DE form feeds $CBC2."""
    sites = {}
    skool = os.path.join(ROOT, 'game.skool')
    kind = None
    for line in open(skool):
        if line[:1] in 'bcgistuw' and line[1:2] == '$':
            kind = line[0]
        m = re.match(r'^[ *bc]\$([0-9A-F]{4}) LD (HL|DE),\$([0-9A-F]{4})\b', line)
        if m and kind == 'c':
            v = int(m.group(3), 16)
            if MSG_LO <= v < MSG_HI:
                sites.setdefault(v, []).append(int(m.group(1), 16))
    return sites


def script_sites():
    """{message address: [instruction addresses]} for every PRINT and
    SAY TO instruction in the plan scripts (tools/allplans.py)."""
    import allplans
    _recs, _starts, ins = allplans.collect()
    sites = {}
    for a, r in ins.items():
        if r.get('msg') is not None:
            sites.setdefault(r['msg'], []).append(a)
    return sites


class Renderer:
    def __init__(self):
        self.snap = booted_snapshot()

    def render(self, addr, max_slices=20000):
        g = Game(P, S)
        g.m.set_memory_block(0, self.snap)
        mem = g.m.memory
        mem[0xA036], mem[0xA034], mem[0xA035] = ACTOR, DOBJ, IOBJ
        mem[LINES_LEFT] = 0xFF
        sp = 0x5D40
        mem[sp], mem[sp + 1] = TRAP & 0xFF, TRAP >> 8
        g.m.sp = sp
        g.m.hl = addr
        g.m.pc = PRINTER
        g.m.set_breakpoint(TRAP)
        g.m.set_breakpoint(CHAR_OUT)
        g.m.set_breakpoint(CONTROL)
        chars = []
        keys = 0
        for _ in range(max_slices):
            g.m.ticks_to_stop = 500_000
            g.m.run()
            pc = g.m.pc
            if pc == TRAP:
                return apply_screen_case(''.join(chars), ''.join(g.printed)), 'ok'
            if pc == GET_KEY_ENTRY:
                # A page-wait or a "press a key": answer with ENTER.
                keys += 1
                if keys > 20:
                    return ''.join(chars), 'waits-for-input'
                g.queue('\r')
                g._handle_get_key()
            elif pc == CHAR_OUT:
                a = g.m.a
                if a == 8:
                    # Delete: suffixes like "-ING" on RIDE are stored as
                    # backspace + "ING" (see the suffix table at $A85C).
                    if chars and chars[-1] != PLACEHOLDER:
                        chars.pop()
                    g.m.step_over_breakpoint()
                    continue
                chars.append(chr(a) if 32 <= a < 127 else ('\n' if a == 13 else f'[{a:02X}]'))
                g.m.step_over_breakpoint()
            elif pc == CONTROL and g.m.a == WORD_OF_COMMAND:
                # Needs the parser's working state, which is gone by
                # the time we render: show a placeholder and skip it.
                if not chars or chars[-1] != PLACEHOLDER:
                    chars.append(PLACEHOLDER)
                g.m.pc = NEXT_BYTE
            elif pc == CONTROL:
                g.m.step_over_breakpoint()
            elif pc == PRINT_CHAR_ENTRY:
                g._handle_print_char()
            elif pc == PICTURE_ENTRY:
                g._skip_picture()
        return apply_screen_case(''.join(chars), ''.join(g.printed)), 'partial'


def apply_screen_case(clean, screen):
    """Take each character's case from what the screen layer actually
    displayed: walk the clean stream and find each letter, in order, in
    the screen stream (which also contains cursor glyphs and padding)."""
    out, j = [], 0
    low = screen.lower()
    clean = clean.replace(PLACEHOLDER, '\x00')
    for ch in clean:
        if ch == '\x00':
            out.append(PLACEHOLDER)
            continue
        if ch.isalpha():
            k = low.find(ch.lower(), j)
            if k >= 0:
                out.append(screen[k]); j = k + 1
                continue
        out.append(ch)
    return ''.join(out)


def parsed_starts(lo=0x67FF, hi=0x8258):
    """Start addresses of every message in the area, found by walking the bytecode: a word
    reference whose first byte is $A_, $B_ or $E_ ends a sentence and so the message, as do codes
    $1A, $1D, $1E and $1F; $02 and $0B take a two-byte offset; $0A a count; $40-$5F a run of
    packed letters. (Walked from $67FF: the 72 bytes before it are not an ordinary message.)"""
    d, cur, out = P, lo, []
    while cur < hi:
        out.append(cur)
        while cur < hi:
            b = d[cur - BASE]
            if b & 0x80:
                cur += 2
                if (b & 0x70) in (0x20, 0x30, 0x60):
                    break
            elif b < 0x20:
                if b in (0x02, 0x0B):
                    cur += 3
                elif b == 0x0A:
                    cur += 2
                else:
                    cur += 1
                    if b in (0x1A, 0x1D, 0x1E, 0x1F):
                        break
            elif 0x40 <= b <= 0x5F:
                cur += 1 + (5 * ((b & 0x1F) + 1) + 7) // 8
            else:
                cur += 1
    return out


def submessage_targets(starts, lo=0x67FF, hi=0x8258):
    """Targets of control code $0B (print a message at an offset from here: HL = the address of the
    code plus its two-byte offset) found in the messages that start at `starts`."""
    st = sorted(starts)
    out = set()
    for i, a in enumerate(st):
        e = st[i + 1] if i + 1 < len(st) else hi
        cur = a
        while cur < e:
            b = P[cur - BASE]
            if b & 0x80:
                cur += 2
            elif b in (0x02, 0x0B):
                off = P[cur + 1 - BASE] | P[cur + 2 - BASE] << 8
                if off & 0x8000:
                    off -= 0x10000
                if b == 0x0B and 0x67B7 <= cur + off < hi:
                    out.add(cur + off)
                cur += 3
            elif b == 0x0A:
                cur += 2
            elif 0x40 <= b <= 0x5F:
                cur += 1 + (5 * ((b & 0x1F) + 1) + 7) // 8
            else:
                cur += 1
    return out


def message_refs(lo=0x67FF, hi=0x8258):
    """{target: [(code, address of the code)]}: every control code $0B (print the message at an
    offset from here) and $02 (jump within the message) in the area. Both land on the address of
    the code plus its signed two-byte offset."""
    refs, cur = {}, lo
    while cur < hi:
        b = P[cur - BASE]
        if b & 0x80:
            cur += 2
        elif b in (0x02, 0x0B):
            off = P[cur + 1 - BASE] | P[cur + 2 - BASE] << 8
            if off & 0x8000:
                off -= 0x10000
            refs.setdefault(cur + off, []).append((b, cur))
            cur += 3
        elif b == 0x0A:
            cur += 2
        elif 0x40 <= b <= 0x5F:
            cur += 1 + (5 * ((b & 0x1F) + 1) + 7) // 8
        else:
            cur += 1
    return refs


def record_refs(starts, skip):
    """{message address: [addresses of 16-bit values equal to it]} in the entity records and the
    action-record/script area, where messages are named as data. `skip` holds operand addresses
    of instructions already found (LD HL,nn and the like)."""
    res = {}
    for lo, hi in ((0x8CBA, 0x9570), (0xDC15, 0xF3C2)):
        for a in range(lo, hi - 1):
            v = P[a - BASE] | P[a + 1 - BASE] << 8
            if v in starts and a not in skip:
                res.setdefault(v, []).append(a)
    return res


def pointers(starts):
    """{message address: [addresses of the 16-bit description pointers (room record +7) to it]}"""
    import rooms as _rooms
    res = {}
    for rm in _rooms.rooms().values():
        pa = rm['address'] + 7
        v = P[pa - BASE] | P[pa + 1 - BASE] << 8
        if v in starts and v == rm['description']:
            res.setdefault(v, []).append(pa)
    return res


def tidy(text):
    return text.strip()


if __name__ == '__main__':
    r = Renderer()
    sites = message_sites()
    loads = code_load_sites()
    scripts = script_sites()
    out = {}
    import rooms as _rooms
    walked = set(parsed_starts()) | {rm['description'] for rm in _rooms.rooms().values()
                                     if MSG_LO <= (rm['description'] or 0) < MSG_HI}
    subs = submessage_targets(walked | set(sites) | set(loads) | set(scripts))
    walked |= subs
    mrefs = message_refs()
    skip = set()
    for dct in (sites, loads):
        for lst in dct.values():
            skip.update(x + 1 for x in lst)
    rrefs = record_refs(walked | set(sites) | set(loads) | set(scripts), skip)
    ptrs = pointers(walked | set(sites) | set(loads) | set(scripts))
    for addr in sorted(set(sites) | set(loads) | set(scripts) | walked):
        text, status = r.render(addr)
        code = sorted(set(sites.get(addr, [])) | set(loads.get(addr, [])))
        out[f'{addr:04X}'] = dict(text=tidy(text), status=status,
                                  sites=[f'{s:04X}' for s in code],
                                  script_sites=[f'{s:04X}' for s in sorted(scripts.get(addr, []))],
                                  message_refs=[f'{c:02X} {a:04X}' for c, a in sorted(mrefs.get(addr, []), key=lambda x: x[1])],
                                  record_refs=[f'{a:04X}' for a in rrefs.get(addr, [])],
                                  table_pointers=[f'{s:04X}' for s in ptrs.get(addr, [])],
                                  found_by=('printer call' if addr in sites else
                                            'LD in code' if addr in loads else
                                            'plan script' if addr in scripts else
                                            'pointer in a record' if addr in ptrs else 'record pointer' if addr in rrefs else 'sub-message' if addr in subs else 'walk'))
    # A load into the message area is not always a message: drop renders
    # of a character or two found only that way ($67B7 'Z', $8000 'Z' and
    # $8078 '.' were pointer arithmetic, not messages).
    out = {k: v for k, v in out.items()
           if not (v['found_by'] == 'LD in code' and len(v['text']) < 3)}
    print(len(out), 'messages')
    json.dump(out, open(os.path.join(HERE, 'messages.json'), 'w'), indent=1)
    for k, v in out.items():
        print(k, v['status'], repr(v['text'][:90]))
