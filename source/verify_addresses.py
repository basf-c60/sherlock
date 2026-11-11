"""
Cross-check every line-comment address against the real instruction stream.

Run this after every batch of annotation work. It catches: a typo'd hex
digit in a comment's key, a comment accidentally attached under the wrong
routine's block, and a comment address that used to be a valid instruction
boundary but no longer is after a control-file change shifted where code
and data begin.

Adapt the two "TODO" functions to your own toolchain - the shape is:
  1. get the real list of instruction-start addresses for every code block
     (from a disassembly listing, or by re-disassembling with a Z80
     disassembler and parsing its output)
  2. get every (block_address -> {line_address: comment}) mapping your
     overlay modules have built up
  3. report any line_address that isn't a genuine instruction start inside
     that specific block.

This is a completeness/typo check, not a correctness check - a comment can
be attached to a perfectly real instruction and still say something wrong.
See references/verification.md for how to check *that*.
"""

import re


def get_real_instruction_addresses(disassembly_listing_path):
    """Parse a flat 'ADDR  MNEMONIC ...' disassembly listing (e.g. the
    output of z80dasm -a) into {block_start_guess: set(instruction_addrs)}.

    Simplify by returning one flat set of all instruction-start addresses
    if your control file already tells you block boundaries some other
    way; the important thing is having a ground-truth set of "yes, an
    instruction genuinely starts here" addresses to check comments against.
    """
    addrs = set()
    for line in open(disassembly_listing_path):
        m = re.match(r'^([0-9a-fA-F]{4})\s', line)
        if m:
            addrs.add(int(m.group(1), 16))
    return addrs


def get_comment_addresses(overlay_module_A_dict):
    """Return {block_addr: set(line_addrs_with_comments)} from your `A` dict
    (see build_skeleton.py) - only for blocks of your 'code' kind, since
    line comments only make sense there.
    """
    out = {}
    for addr, rec in overlay_module_A_dict.items():
        if rec.get('t') == 'c' and rec.get('comments'):
            out[addr] = set(rec['comments'].keys())
    return out


def check(real_instruction_addrs, comment_addrs_by_block):
    """Return a list of (block_addr, bad_line_addr) problems, empty if clean."""
    bad = []
    for block_addr, line_addrs in comment_addrs_by_block.items():
        for line_addr in line_addrs:
            if line_addr not in real_instruction_addrs:
                bad.append((block_addr, line_addr))
    return bad


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    # TODO: import every overlay module here so `A` is fully populated,
    # e.g.  import overlay_01_startup, overlay_02_parser, ...
    from build_skeleton import A   # replace with your real shared-state module

    real = get_real_instruction_addresses('game_disassembly_listing.txt')
    comments = get_comment_addresses(A)
    problems = check(real, comments)

    print(f"{len(problems)} problem(s) found")
    for block_addr, bad_addr in problems:
        print(f"  block {block_addr:#06x}: comment at {bad_addr:#06x} "
              f"is not a real instruction start in that block")
    sys.exit(1 if problems else 0)
