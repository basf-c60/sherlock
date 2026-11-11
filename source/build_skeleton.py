"""
Skeleton for the "overlay" annotation pattern used throughout this skill.

The idea: never hand-edit the generated .skool file, and never hand-edit
a giant .ctl file either once it grows past a first draft. Instead keep a
single Python dict, `A`, keyed by address, holding everything you know
about that address (title, prose description, register doc, line-by-line
comments, sub-block breakdown for data tables). Populate it from any
number of small "overlay" modules - one per work session or one per
subsystem is a good default - each of which just imports this module and
calls `blk()` / `C()` to add or extend entries. A single `build.py` then
walks the whole dict once and emits the .ctl file that sna2skool.py reads.

This is what makes a project with hundreds of annotated routines tractable
to maintain and correct: fixing a wrong claim is a one-line edit to a
dict value in whichever overlay file introduced it, and the next build
picks it up everywhere the address is referenced (comments, tables of
contents, cross-references).

Usage sketch:

    # overlay.py  (this file, shared state + helpers)
    # overlay_01_startup.py
    #     from overlay import blk, C
    #     blk(0x8000, 'c', 'Clear the screen', ["Fills the display file with zeroes."])
    # overlay_02_parser.py
    #     from overlay import A, blk, C
    #     blk(0x8100, 'c', 'Tokenise a line of input', [...])
    #     C(0x8100, {0x8100: 'HL = the input buffer', 0x8103: 'B = its length', ...})
    # build.py
    #     import overlay_01_startup, overlay_02_parser   # side-effecting imports
    #     from overlay import A
    #     ... walk A, emit game.ctl ...
"""

A = {}   # address -> record, shared mutable state all overlay modules write into


def blk(addr, kind, title, desc=(), regs=(), comments=None, subs=(), mid=None):
    """Create or overwrite the top-level record for `addr`.

    kind: 'c' code, 'b' bytes/data, 't' text, 'w' words (16-bit table), 'g' game
          status buffer, 'u' unused - whatever your toolchain's directive letters are.
    title: one-line summary, shown as the routine/block's heading.
    desc: list of prose paragraphs explaining what this is for and how it works.
    regs: list of 'Input:X ...' / 'Output:Y ...' strings documenting the calling
          convention, if this is a routine other code calls into.
    comments: optional {instruction_address: line_comment} to seed immediately
              (usually you add these later via C(), once you're sure of them).
    subs: for data blocks, a list of (directive, address, length, label) tuples
          describing a table's sub-entries (e.g. one row per object/room/word).
    mid: optional {address: text} for a longer aside attached at a specific
          point inside a block, distinct from a line comment.
    """
    A[addr] = dict(t=kind, title=title, desc=list(desc), regs=list(regs),
                    comments=dict(comments or {}), subs=list(subs), mid=dict(mid or {}))


def C(addr, line_comments):
    """Add or update line-by-line comments on an existing block at `addr`.

    Call this from a *later* overlay module once you've traced a routine's
    logic and are confident in the per-instruction explanations - keeps the
    "what is this for" prose (written early, from blk()) separate from the
    "here is exactly how" detail (written once you're sure, from C()),
    which in practice is how the work actually proceeds: understand the
    purpose first, verify and narrate the mechanism second.
    """
    A[addr]['comments'].update(line_comments)


def fix(addr, old_substring, new_substring):
    """Find-and-replace inside a block's prose description.

    Use this from a later overlay to correct an earlier claim without
    duplicating the whole description - keeps the diff small and the
    correction visible in version control / review.
    """
    desc = A[addr]['desc']
    hit = False
    for i, para in enumerate(desc):
        if old_substring in para:
            desc[i] = para.replace(old_substring, new_substring)
            hit = True
    assert hit, f"pattern not found in {hex(addr)}: {old_substring!r}"


# --- Trivia / Bugs page entries -------------------------------------------
# Keep these as parallel lists so a small script can render them into
# whatever "extra pages" feature your toolchain supports (SkoolKit's ref
# files, or a plain extra HTML page you template yourself).

BUGS = []
FACTS = []


def bug(entry_id, title, *paragraphs):
    BUGS.append((entry_id, title, '\n\n'.join(paragraphs)))


def fact(entry_id, title, *paragraphs):
    FACTS.append((entry_id, title, '\n\n'.join(paragraphs)))


# --- build.py sketch --------------------------------------------------------
#
# import re
# import overlay_01_startup, overlay_02_parser, ...   # populate A, BUGS, FACTS
# from overlay import A, BUGS, FACTS
#
# lines = ['@ $<load_addr> start', '@ $<load_addr> org']
# for addr in sorted(A):
#     d = A[addr]
#     lines.append(f"{d['t']} ${addr:04X} {d['title']}".rstrip())
#     for para in d['desc']:
#         lines.append(f"D ${addr:04X} {para}")
#     for reg in d['regs']:
#         lines.append(f"R ${addr:04X} {reg}")
#     for (directive, sub_addr, length, label) in d['subs']:
#         lines.append(f"{directive} ${sub_addr:04X},{length} {label}".rstrip())
#     for line_addr, comment in sorted(d['comments'].items()):
#         if comment:
#             lines.append(f"C ${line_addr:04X} {comment}")
# lines.append('i $<end_of_code_address>')
# open('game.ctl', 'w').write('\n'.join(lines) + '\n')
#
# Then, as a completely separate step, render BUGS/FACTS into whatever
# "extra pages" mechanism your HTML generator supports.


# --- Site notes --------------------------------------------------------------
# A line comment for an address inside a block nobody has annotated yet
# (e.g. every LD HL,<message> in the game gets the message's text). build.py
# emits each note under whichever code block contains the address; an
# annotated block's own comment at the same address takes priority.

NOTES = {}


PAGES = []   # (page_id, title, html) - generated reference pages


def page(page_id, title, html):
    """A generated reference page (map, room list...), added to the site's
    index next to the notes pages. The html may use skool macros (#R)."""
    PAGES.append((page_id, title, html))


RESOURCES = {}   # file name -> path: extra files copied into the site


def note(addr, text):
    NOTES[addr] = text
