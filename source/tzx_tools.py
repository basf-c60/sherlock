"""
TZX/TAP block extraction and rebuild-with-patch helpers.
See references/tape-formats.md for the format details this implements.
"""


def parse_tzx(data):
    """Return a list of (payload_start_offset, payload_length) for every
    standard-speed data block (id 0x10) in a TZX file, in file order.
    `payload` includes the flag byte and the trailing checksum byte.
    """
    i = 10  # 8-byte "ZXTape!" + 0x1A signature, + 2-byte version
    blocks = []
    while i < len(data):
        block_id = data[i]
        i += 1
        if block_id == 0x10:
            length = data[i + 2] | data[i + 3] << 8
            blocks.append((i + 4, length))
            i += 4 + length
        elif block_id == 0x30:
            i += 1 + data[i]
        elif block_id == 0x32:
            length = data[i] | data[i + 1] << 8
            i += 2 + length
        elif block_id == 0x20:
            i += 2
        elif block_id == 0x33:
            # "hardware type" block: 1-byte count, then 3 bytes per entry
            # (type, id, info) - informational only, safe to skip.
            n = data[i]
            i += 1 + 3 * n
        else:
            raise ValueError(
                f"unhandled TZX block id {block_id:#04x} at offset {i-1:#x} - "
                "inspect this tape by hand, it may use a turbo/protected loader")
    return blocks


def parse_tap(data):
    """Return a list of (payload_start_offset, payload_length) for every
    block in a TAP file. Same payload convention as parse_tzx.
    """
    i = 0
    blocks = []
    while i < len(data):
        length = data[i] | data[i + 1] << 8
        blocks.append((i + 2, length))
        i += 2 + length
    return blocks


def extract_block(data, start, length):
    """Return (flag, body, checksum) for one payload; body excludes the
    flag byte and the checksum byte. flag 0x00=header, 0xFF=data (usual
    convention; some tapes use other flag values for custom loaders).
    """
    payload = data[start:start + length]
    return payload[0], payload[1:-1], payload[-1]


def recompute_checksum(payload):
    """XOR every byte except the last (existing/stale checksum byte),
    return the payload with a freshly computed final byte.
    """
    x = 0
    for b in payload[:-1]:
        x ^= b
    return payload[:-1] + bytes([x])


def patch_tape(tape_bytes, block_start, block_length, new_body, flag=0xFF):
    """Return a new tape byte string with one block's body replaced.

    new_body must be exactly `block_length - 2` bytes (same size as the
    original body, i.e. same size as the code/data it replaces - Spectrum
    tape headers declare a fixed length, so a patch can't grow or shrink
    a block without also editing the corresponding header block, which is
    usually not worth attempting; keep patches equal-length).
    """
    assert len(new_body) == block_length - 2, (
        f"replacement body must be exactly {block_length - 2} bytes, "
        f"got {len(new_body)} - equal-length patches only")
    payload = bytes([flag]) + new_body + bytes([0])   # placeholder checksum
    payload = recompute_checksum(payload)
    out = bytearray(tape_bytes)
    out[block_start:block_start + block_length] = payload
    return bytes(out)


def verify_all_checksums(tape_bytes, blocks):
    """Raise if any block's stored checksum doesn't match a fresh XOR of
    its own bytes - a good sanity check after any patch.

    The checksum byte is defined so that XORing it together with every
    preceding byte (flag + body) cancels to zero - so the check is an XOR
    of the *whole* payload including that last byte, not of everything
    except it. (This function's own first draft got that backwards and
    was caught only by running it against a real tape file - see
    references/verification.md for why that habit matters generally.)
    """
    for start, length in blocks:
        payload = tape_bytes[start:start + length]
        x = 0
        for b in payload:          # the whole payload, checksum byte included
            x ^= b
        assert x == 0, (
            f"checksum mismatch in block at offset {start:#x} "
            f"(expected XOR of the whole payload, checksum included, to be 0)")


def write_tap_from_blocks(tape_bytes, blocks, out_path):
    """Build a plain .tap file from the same (start, length) blocks
    extracted from a TZX - useful for emulators/hardware that don't
    support TZX, or just as a simpler format to keep around.
    """
    out = bytearray()
    for start, length in blocks:
        out += bytes([length & 0xFF, length >> 8])
        out += tape_bytes[start:start + length]
    open(out_path, 'wb').write(bytes(out))
