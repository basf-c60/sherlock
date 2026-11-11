"""
Merge the sna2ctl-generated baseline control file with our own verified
overlay annotations (see overlay_*.py) into the final game.ctl that
sna2skool.py reads.

Approach: parse the baseline's block-start lines into an ordered list of
(address, type) covering the whole address space. For every address our
overlay describes (the `A` dict from build_skeleton.py), force a block
boundary there with our own type (always 'c' so far - everything we've
annotated is confirmed code) and splice the following prose/comment
directives straight after it. Everywhere we haven't touched, the
original automatic block boundary and type are kept exactly as
sna2ctl produced them - this is still a rough first pass there, as
verification.md and the SKILL itself expect.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import overlay_01_boot          # noqa: F401  (populates A / BUGS / FACTS by import)
import overlay_02_world_model   # noqa: F401
import overlay_03_dictionary    # noqa: F401
import overlay_04_actions       # noqa: F401
import overlay_05_messages      # noqa: F401
import overlay_06_rooms         # noqa: F401
import overlay_07_code_fixes    # noqa: F401
import overlay_08_plans         # noqa: F401
import overlay_09_audit         # noqa: F401
import overlay_10_traced        # noqa: F401
import overlay_11_howitworks    # noqa: F401
import overlay_12_depth         # noqa: F401
import overlay_13_regs
import overlay_14_statebits
import overlay_15_lines
import overlay_16_rom
import overlay_17_vehicles
import linkify
from build_skeleton import A, BUGS, FACTS, NOTES

BASELINE = os.path.join(ROOT, 'game.ctl.baseline')
OUTPUT = os.path.join(ROOT, 'game.ctl')


def parse_baseline(path):
    header = []
    blocks = []  # (address:int, type:str)
    with open(path) as f:
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('@'):
                header.append(line)
                continue
            m = re.match(r'^([bcgistuw])\s+(\d+)\s*$', line)
            if m:
                blocks.append((int(m.group(2)), m.group(1)))
    return header, blocks


def main():
    header, blocks = parse_baseline(BASELINE)
    block_addrs = {addr for addr, _ in blocks}

    # Splice in every overlay address as a forced 'c' block boundary.
    for addr in A:
        block_addrs.add(addr)

    # Drop stale baseline boundaries that fall strictly between two of
    # our own confirmed instruction-start addresses (a block's title
    # address plus its comment keys) - the baseline's automatic guess
    # sometimes slices a real, now-confirmed instruction in half (e.g.
    # a 3-byte LD A,(nn) starting at a comment address, with the
    # baseline having independently guessed a data block starting on
    # the operand byte). Since we've confirmed the instruction actually
    # starts earlier and doesn't end until the next confirmed address,
    # any baseline boundary strictly inside that gap is necessarily
    # wrong and must be removed, or sna2skool errors on the overlap.
    # A block's span runs from its own address to its last comment or
    # the end of its last sub-block; any baseline boundary inside that
    # span (other than another overlay block) would split it.
    for rec_addr, rec in A.items():
        known = {rec_addr} | set(rec['comments'])
        if rec.get('end'):
            known.add(rec['end'])   # an explicit end for a plain data span
        for (_d, sub_addr, length, _l) in rec['subs']:
            known.add(sub_addr)
            known.add(sub_addr + length)
        lo, hi = min(known), max(known)
        for addr in list(block_addrs):
            if lo < addr < hi and addr not in A:
                block_addrs.discard(addr)

    merged = []
    for addr in sorted(block_addrs):
        if addr in A:
            # BUG FIX: this used to append 'c' unconditionally, so every
            # overlay block was disassembled as code even when its blk()
            # call said 'b' (data) - e.g. the $9927 table. Use the type
            # the overlay actually declared.
            merged.append((addr, A[addr]['t']))
        else:
            # keep whatever type the baseline had at/just-before this
            # address (find the nearest preceding baseline block-start)
            btype = 'c'
            for baddr, bt in blocks:
                if baddr <= addr:
                    btype = bt
                else:
                    break
            merged.append((addr, btype))

    lines = list(header)
    starts = [a for a, _ in merged]
    import bisect
    notes_by_block = {}
    for naddr, text in NOTES.items():
        k = bisect.bisect_right(starts, naddr) - 1
        if k >= 0 and merged[k][1] == 'c':
            notes_by_block.setdefault(merged[k][0], {})[naddr] = text
    for addr, btype in merged:
        rec = A.get(addr)
        extra = notes_by_block.get(addr, {})
        if rec:
            title = rec['title']
            lines.append(f'{btype} {addr} {title}'.rstrip())
            for para in rec['desc']:
                lines.append(f'D {addr} {para}')
            for reg in rec['regs']:
                lines.append(f'R {addr} {reg}')
            # Line comments ('C addr text') and sub-block directives
            # ('B addr,len text' etc.) are both sub-block directives to
            # SkoolKit; emit them together in address order. Sub-blocks
            # let a code block contain data (e.g. an action record's
            # header bytes in front of its executable body).
            subdirs = []
            for line_addr, text in extra.items():
                if line_addr not in rec['comments']:
                    subdirs.append((line_addr, f'C {line_addr} {text}'))
            for line_addr, comment in rec['comments'].items():
                if btype == 'c':
                    subdirs.append((line_addr, f'C {line_addr} {comment}'.rstrip()))
            for (d, sub_addr, length, label) in rec['subs']:
                subdirs.append((sub_addr, f'{d} {sub_addr},{length} {label}'.rstrip()))
            for _, line in sorted(subdirs):
                lines.append(line)
        else:
            lines.append(f'{btype} {addr}')
            for line_addr, text in sorted(extra.items()):
                lines.append(f'C {line_addr} {text}')

    lines = overlay_15_lines.apply(lines)
    lines = linkify.link_ctl(lines)
    with open(OUTPUT, 'w') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'Wrote {OUTPUT}: {len(merged)} blocks, '
          f'{len(A)} of them with verified annotations '
          f'({sum(1 for r in A.values() for _ in r["comments"])} line comments)')

    # Render BUGS/FACTS/notes as a real SkoolKit ref file: [Bug:*] and
    # [Fact:*] sections give native Bugs/Trivia pages (linked from the
    # index, styled like the rest of the site), and [Page:*] sections
    # turn our supplementary write-ups (loader_notes.md etc.) into real
    # pages instead of separate .md files sitting outside the site.
    import re as _re

    def slug(text):
        return _re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

    def safe_title(text):
        # ':' is the ref-file section-name field separator
        # ([Bug:anchor:title]) - avoid relying on how a stray one in the
        # title itself would be parsed.
        import re as _r2
        text = _r2.sub(r'(\d):(\d)', r'\1.\2', text)   # times such as 10:53am
        return text.replace(':', ' -')

    def render_body(text):
        # Box-page sections get no Markdown processing (unlike the
        # custom notes pages below, which go through the markdown
        # library), so convert `code`-style backtick spans to <code>
        # tags ourselves for readability.
        return _re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    import sitegen
    FACTS_ORDERED = sitegen.reorder_facts(list(FACTS))
    ref_lines = [
        '[Game]',
        'Game=Sherlock (1984): annotated disassembly',
        'Logo=Sherlock: annotated disassembly',
        'StyleSheet=skoolkit.css;sherlock.css',
        '',
    ]
    for entry_id, title, body in BUGS:
        ref_lines.append(f'[Bug:{slug(entry_id)}:{safe_title(title)}]')
        ref_lines.append(render_body(body))
        ref_lines.append('')
    for entry_id, title, body in FACTS_ORDERED:
        ref_lines.append(f'[Fact:{slug(entry_id)}:{safe_title(title)}]')
        ref_lines.append(render_body(body))
        ref_lines.append('')

    # Supplementary notes as custom pages, converted from Markdown.
    import markdown as _markdown
    notes_pages = [
        ('loader-notes', 'Loader notes (Phase 0)', 'loader_notes.md'),
        ('harness-notes', 'Harness notes (Phase 1)', 'harness_notes.md'),
        ('dictionary-notes', 'Dictionary notes (Phase 3)', 'dictionary_notes.md'),
        ('world-model-notes', 'World-model notes (Phase 3)', 'world_model_notes.md'),
    ]
    index_page_ids = []
    titles_lines = ['[Titles]']
    headers_lines = ['[PageHeaders]']
    links_lines = ['[Links]']
    for page_id, title, fname in notes_pages:
        src = os.path.join(os.path.dirname(__file__), fname)
        if not os.path.exists(src):
            continue
        with open(src) as f:
            md_text = f.read()
        html_body = _markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
        ref_lines.append(f'[Page:{page_id}]')
        ref_lines.append(f'PageContent=#INCLUDE({page_id}-content)')
        ref_lines.append('')
        ref_lines.append(f'[{page_id}-content]')
        ref_lines.append(html_body)
        ref_lines.append('')
        title = sitegen.NICE_TITLES.get(page_id, title)
        titles_lines.append(f'{page_id}={title}')
        headers_lines.append(f'{page_id}={title}')
        links_lines.append(f'{page_id}={title}')
        index_page_ids.append(page_id)

    # Generated reference pages (map, rooms, objects, vocabulary).
    from build_skeleton import PAGES, RESOURCES
    PAGES = list(PAGES) + [('trivia-by-theme', 'Trivia by theme', sitegen.themes_page(FACTS_ORDERED))]
    for page_id, title, html_body in PAGES:
        ref_lines.append(f'[Page:{page_id}]')
        ref_lines.append(f'PageContent=#INCLUDE({page_id}-content)')
        ref_lines.append('')
        ref_lines.append(f'[{page_id}-content]')
        ref_lines.append(html_body)
        ref_lines.append('')
        title = sitegen.NICE_TITLES.get(page_id, title)
        titles_lines.append(f'{page_id}={title}')
        headers_lines.append(f'{page_id}={title}')
        links_lines.append(f'{page_id}={title}')
        index_page_ids.append(page_id)
    if RESOURCES:
        ref_lines.append('[Resources]')
        for name in RESOURCES:
            ref_lines.append(f'{name}=images')
        ref_lines.append('sherlock.css=.')
        ref_lines.append('')

    # Accumulate all pages' titles/headers/links into single sections -
    # repeating a [Titles]-style section name overwrites the previous
    # one rather than merging with it, so every page must be listed in
    # the same section or all but the last would fall back to their
    # raw page ID as link text.
    if index_page_ids:
        ref_lines.append('\n'.join(titles_lines))
        ref_lines.append('')
        ref_lines.append('\n'.join(headers_lines))
        ref_lines.append('')
        ref_lines.append('\n'.join(links_lines))
        ref_lines.append('')

    # Link the custom pages from the index page, under their own group.
    # NOTE: [Index+] (the documented "append" syntax) did not behave as
    # expected when tested (it caused every other default index group -
    # Memory maps, Reference, etc. - to disappear entirely, not just
    # fail to gain our addition). Sidestepped by declaring the full
    # [Index] section explicitly: the default group order (confirmed by
    # running `skool2html.py -r 'Index$'`) plus our own group appended.
    if index_page_ids:
        ref_lines.extend(sitegen.index_lines(index_page_ids))
    ref_lines.extend(sitegen.extra_ref_sections(index_page_ids, FACTS_ORDERED))
    import shutil
    shutil.copy(os.path.join(os.path.dirname(__file__), 'sherlock.css'), os.path.join(ROOT, 'sherlock.css'))

    ref_path = os.path.join(ROOT, 'game.ref')
    with open(ref_path, 'w') as f:
        _n = sum(1 for l in lines if _re.match(r'^C \d+ \S', l))
        ref_lines = [_re.sub(r'<li><b>[\d,]+</b><span>line comments</span>',
                             '<li><b>{:,}</b><span>line comments</span>'.format(_n), l) for l in ref_lines]
        f.write('\n'.join(linkify.link_ref(ref_lines)) + '\n')
    print(f'Wrote {ref_path}: {len(BUGS)} bugs, {len(FACTS)} facts, '
          f'{len(index_page_ids)} project-notes pages')

    # Also keep a plain Markdown copy of BUGS/FACTS for anyone browsing
    # the source/ folder directly without building the HTML site.
    with open(os.path.join(ROOT, 'trivia.md'), 'w') as f:
        f.write('# Trivia and verified findings\n\n')
        for entry_id, title, body in FACTS:
            f.write(f'## {title}\n\n{body}\n\n')
        if BUGS:
            f.write('# Bugs\n\n')
            for entry_id, title, body in BUGS:
                f.write(f'## {title}\n\n{body}\n\n')


if __name__ == '__main__':
    main()
