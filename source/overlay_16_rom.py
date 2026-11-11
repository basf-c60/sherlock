"""The ROM and system-variable addresses that descriptions mention, on one page (link target)."""
from build_skeleton import page

_ROWS = [
 (0x04C2, 'SA-BYTES', 'ROM', 'The ROM routine that writes a block of bytes to tape. The save routine uses it for the saved game.'),
 (0x0556, 'LD-BYTES', 'ROM', 'The ROM routine that reads a block of bytes from tape (the game load and the header read).'),
 (0x0F12, 'COPY-LINE code', 'ROM', 'The part of the ROM printer routine that prints one pixel line; the screen-copy routine joins it here.'),
 (0x22AA, 'PIXEL-ADDRESS', 'ROM', 'The ROM routine that turns pixel coordinates (B = y, C = x) into the screen byte address in HL and the bit position in A.'),
 (0x4000, 'Display file', 'Screen', 'The start of the screen bitmap: 6,144 bytes, eight pixel lines per character row.'),
 (0x5800, 'Attribute file', 'Screen', 'The start of the colour attributes: 768 bytes, one per character cell ($5800 to $5AFF).'),
 (0x5B00, 'Typed line', 'Workspace', 'Where the line the player types is kept before it is split into words.'),
 (0x5B81, 'Token list', 'Workspace', 'The list of words made from the typed line. A repeated command reuses the one from the previous command.'),
 (0x5C08, 'LAST_K', 'System variable', 'The last key pressed. The keyboard routine takes a new key from here.'),
 (0x5C0B, 'Line buffer', 'System variable area', 'Used by the game as the buffer where typed characters are collected, and as the tape header workspace.'),
 (0x5C3A, 'ERR_NR', 'System variable', 'The error-number byte; the start of the standard system-variable area that IY is pointed at.'),
 (0x5C3B, 'FLAGS', 'System variable', 'A set of ROM flag bits.'),
 (0x5C3C, 'TV_FLAG', 'System variable', 'The ROM\'s output flags. The game stores a value here to switch printing to the screen on or off for a message.'),
 (0x5C42, 'Spelling buffer', 'System variable area', 'Used by the game as the buffer where a dictionary word is spelled out from its kept letters, new letters and suffix.'),
]
_h = ['<p>The game uses a few places outside its own code: ROM routines, screen memory and the system-variable area. '
      'Descriptions link here when they mention one of them.</p>',
      '<table class="rom"><tr><th>Address</th><th>Name</th><th>Kind</th><th>What the game uses it for</th></tr>']
for a, n, k, d in _ROWS:
    _h.append('<tr id="a%04X"><td><a id="a%04X"></a>$%04X</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (a, a, a, n, k, d))
_h.append('</table>')
page('rom_symbols', 'ROM and system variables', '\n'.join(_h))
