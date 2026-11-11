# Discovering an unknown table or record format

Every Spectrum game invents its own binary formats for its world data -
there's no standard to look up. The technique below is general and was
used repeatedly (dictionary, object records, room records, the action
table, the character table, timer entries) in the worked example.

## The core method: anchor, cross-reference, generalise

1. **Find one thing you're already sure of.** Something you know from
   playing the game or from the very first bytes of execution: the
   player's starting room number, a word you're confident is in the
   vocabulary, an object you know the game starts with. This is your
   *anchor*.

2. **Find that anchor's bytes in memory**, and look at what's around it.
   A room number you know is 1 might appear as a single byte inside a
   larger structure; the surrounding bytes are probably other fields of
   the same record. A word you know ("TAKE", "NORTH") lets you work out
   the letter encoding (compare the bytes to the ASCII/expected letters
   and look for an offset, a 5-bit pack, or a lookup table).

3. **Find the table that indexes these records.** Search for a run of
   2-byte or 3-byte values that look like they could be addresses inside
   the data area you're studying (values consistently inside the right
   memory range, at a consistent stride). This is very often a flat array
   of `(key, address)` or `(key, value_lo, value_hi)` triples terminated
   by a sentinel byte (`0xFF` is common).

4. **Compare several records side by side.** Once you can extract three or
   four records of the same kind, line them up. Fields that vary in a way
   that matches something you can observe in-game (this room is bigger,
   this object is heavier) are easy to name. Fields that are *always* the
   same value across every record you've found are probably flags or
   padding - note them as "unknown, always 0" rather than guessing, until
   you find a record where they differ.

5. **Confirm by cross-reference, not by reading alone.** Search the whole
   binary for the byte pattern of a specific record's address (as raw
   little-endian bytes) to find every place that *points at it*. This
   tells you what kind of thing references records of this kind (e.g. "an
   action-number byte immediately precedes this address, so this is one
   entry in an object's own list of action handlers") far more reliably
   than assuming from context. Two real mistakes in the worked example
   came from *not* doing this and assuming a nearby routine or table entry
   was the trigger, when the actual reference was somewhere else entirely
   (a chained handler attached to a specific action on a specific object,
   not the routine that merely happened to be textually adjacent).

   ```python
   import re
   addr = 0xA631                      # some routine's address, little-endian
   pattern = bytes([addr & 0xFF, addr >> 8])
   for m in re.finditer(re.escape(pattern), binary):
       print(hex(load_addr + m.start()), "preceding byte:", binary[m.start()-1])
   ```

   If you get more than one hit, or a hit whose preceding byte doesn't make
   sense as whatever key type you expected (an action number, a room
   number), don't force an interpretation - go look at the actual bytes
   around each hit and reconsider.

6. **Verify field meanings in the emulator**, not just by inspection. Once
   you have a hypothesis for what a byte means ("bit 6 = alive"), poke a
   record's byte directly and observe the game's behaviour changing (or
   not) as predicted. This is fast with the harness from
   `emulator-harness.md` and catches wrong bit-position guesses immediately.

## Specific formats that showed up in the worked example

These are common enough in Spectrum text adventures that they're worth
checking for early, though verify independently rather than assuming they
transfer exactly:

- **Packed 5-bit letters** (A=1..Z=26) with a continuation bit (usually the
  top bit) marking the end of a word, sometimes with the first byte or two
  of a word repurposing spare high bits as a word-class or synonym flag.
- **A per-letter index into the dictionary** (26 entries, one per letter)
  so lookups don't need a linear scan.
- **Synonyms**: a bit marking "this word means the same as that other
  word", with the real word's offset following - discovering this explains
  why several verbs that "shouldn't" work in the parser actually do (or
  conversely, why a verb you'd expect to work doesn't, because it's a
  synonym for something unexpected).
- **Object/room records as a fixed header + variable trailing data**: fixed
  fields (size, weight, flags, a handful of "word slot" references for
  name/adjectives), followed by a variable number of location bytes and
  then a variable list of the object's *own* small routines for specific
  actions, terminated by a sentinel.
- **A generic "N-byte table, sentinel-terminated" search routine**, reused
  for many different tables in the game (the object index, a room's exits,
  a character's reaction table, and so on) - once you've found and
  understood it once, recognise its calling convention elsewhere rather
  than re-deriving it.
- **A message/text bytecode interpreter** - see `message-rendering.md`.
- **A turn-based scheduler**: an array of fixed-size timer records (reload
  value, current count, an "expire" routine address, and often a
  "tick" routine that runs for the last few counts before expiry) processed
  once per turn.

## When you get stuck

- Grep for the value in *multiple* representations (as a raw byte, as a
  little-endian word, as a big-endian word, offset by a plausible base
  address) - it's easy to lose an hour to an endianness or off-by-one-base
  mismatch.
- Render a screen or dump a memory region as an image (pixels as literal
  bits) even for tables you don't think are graphical - sometimes a
  "mysterious" table turns out to be exactly that.
- If a routine's purpose is unclear from static reading, single-step it in
  the emulator with concrete, known inputs and watch what changes.
