# Tape formats: TZX and TAP

## TAP (simple)

A flat sequence of blocks, each: a 2-byte little-endian length `L`,
followed by `L` bytes of data, where the first data byte is a flag
(`0x00` = header, `0xFF` = data) and the last data byte is a checksum
(XOR of every byte from the flag to the byte before the checksum,
inclusive).

```python
def parse_tap(data):
    i = 0
    blocks = []
    while i < len(data):
        length = data[i] | data[i+1] << 8
        blocks.append(data[i+2:i+2+length])
        i += 2 + length
    return blocks
```

A standard ROM header block (19 bytes of payload) encodes: type (0=BASIC
program, 3=code block, others exist), a 10-character name, a length, and
two parameter words whose meaning depends on the type (for a code block:
load address and an unused/second value).

## TZX (richer container)

Starts with an 8-byte signature `"ZXTape!"` + `0x1A`, then a 2-byte
version, then a sequence of blocks, each starting with a 1-byte ID:

- `0x10` "standard speed data": 2-byte pause, 2-byte length, then the same
  flag+data+checksum payload as a TAP block.
- `0x11` "turbo speed data": as above but with explicit pulse timings first
  (rare for ordinary loaders; more common for copy-protected loaders).
- `0x20` pause block (2 bytes).
- `0x30` text description (1-byte length + ASCII) - informational only,
  safe to skip.
- `0x32` archive info - informational, safe to skip.
- Others exist for turbo loaders, generalized data blocks, etc.; skip
  unrecognised IDs by reading their own length field if present, or stop
  and inspect by hand if not (most adventure-game tapes use only the
  handful above).

```python
def parse_tzx(data):
    i = 10  # skip signature + version
    blocks = []
    while i < len(data):
        block_id = data[i]; i += 1
        if block_id == 0x10:
            length = data[i+2] | data[i+3] << 8
            blocks.append(data[i+4:i+4+length])
            i += 4 + length
        elif block_id == 0x30:
            i += 1 + data[i]
        elif block_id == 0x32:
            length = data[i] | data[i+1] << 8
            i += 2 + length
        elif block_id == 0x20:
            i += 2
        else:
            raise ValueError(f"unhandled TZX block {block_id:#x} at {i:#x} - "
                              "inspect by hand, this may be a turbo loader")
    return blocks
```

## Finding the loader, the load address, and the entry point

A game tape is usually: BASIC loader block, then one or more code/data
blocks it loads. Read the BASIC loader's tokenised bytes (or just note its
approximate size and skip past it) to find the final `RANDOMIZE USR n`
line - `n` is the entry point. The header block immediately before each
code block states its own load address and length, so you don't need to
infer those.

If there's a loading-screen block loaded to an odd address (e.g. `40000`)
and then `LDIR`-ed onto the display file, that's cosmetic; the block you
actually want to disassemble is the last (usually largest) code block.

## Rebuilding a tape after a patch

1. Copy the *entire* original tape file.
2. Find the byte offset of the patched block's payload within it (track
   this when you originally extracted the block - store `(offset, length)`
   pairs alongside each extracted binary).
3. Overwrite that slice with your patched bytes (same length!).
4. Recompute that block's own checksum (XOR of flag+data bytes) and write
   it into the last byte of the block's payload.
5. Verify every block's checksum in the whole file still holds (a good
   sanity check that you haven't shifted anything or miscounted an offset).

```python
def recompute_checksum(payload_with_stale_checksum):
    x = 0
    for b in payload_with_stale_checksum[:-1]:
        x ^= b
    return payload_with_stale_checksum[:-1] + bytes([x])
```

If you also want a `.tap` for emulators/hardware that don't read TZX,
build one directly from the same extracted blocks: for each block, write
its 2-byte length followed by the payload bytes (TAP has no separate pause
or ID bytes to worry about).
