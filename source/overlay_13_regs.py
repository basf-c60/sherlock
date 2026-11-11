"""Register notes for the code blocks (Input:/Output: lines) and short step lists."""
from build_skeleton import A


SKIPPED = []


def R(addr, *regs):
    if addr not in A:
        SKIPPED.append(addr)      # an entry point inside another block: its notes live in that block
        return
    A[addr]['regs'] = list(regs)


def S(addr, *steps):
    if addr not in A:
        SKIPPED.append(addr)
        return
    d = A[addr].setdefault('desc', [])
    d.append('How it works:')
    d.extend('%d. %s' % (i + 1, s) for i, s in enumerate(steps))


R(0x99FC, 'Input:IX The action record being run (each routine is entered at its own address)', 'Output:F Prints a message, then returns through $A59F')
R(0x9A80, 'Output:F NZ (success)', '$A027 1 if the actor is you, 0 if someone else')
R(0x9A99, 'Input:IX The action record', 'Output:F Z when the route is refused; otherwise continues at $9AD7')
R(0x9AA3, 'Input:A The current room ($A00A); $A034 holds the destination', 'Output:F Z not a route; NZ a route', 'L The journey time in minutes')
R(0x9ACB, 'Input:IX The action record', 'Output:F Z when the route is refused; otherwise continues at $9B04')
R(0x9AE1, 'Input:IX The action record (a cabbie\'s GO FURIOUSLY TO)', 'Output:F From the ride routine at $9B02')
R(0x9AF4, 'Input:IX The action record (a cabbie\'s GO TO)', 'Output:HL $F3AD, the vehicle sub-script', 'F Carry set')
R(0x9B25, 'Input:IX The journey entry (+2 holds the minutes)', 'DE The fare for each five minutes', 'Output:DE The fare', 'IX Unchanged')
R(0x9B50, 'Input:IX The cabbie\'s record (found from $A036)', 'Output:F Z when a journey exists; otherwise the caller is abandoned after the apology is printed')
R(0x9C41, 'Input:$A017 The actor\'s container, the vehicle', '$A034 The destination room', 'Output:F From the move at $DD0E')
R(0x9C56, 'Input:A The thing number', 'Output:IX The thing\'s record', 'F NZ')
R(0x9C60, 'Input:A The thing number', 'Output:IX The thing\'s record', 'F NZ')

R(0x9C6A, 'Input:$A036 The actor', 'Output:F Z if the actor has no after-turn routine; NZ if it has', 'IX The actor\'s entry in the table at $9C85')
R(0x9C77, 'Input:$A036 The actor', 'Output:F Unchanged from the actor\'s own routine, or the caller continues if there is none')
R(0x9CA2, 'Output:F Z until the note has burnt; no registers are returned')
R(0x9CCE, 'Input:C The thing number', 'Output:F Z if the thing is in the actor\'s room and the player can see it; NZ if not', 'B The room of the actor ($A017)', 'IX The thing\'s record')
R(0x9CE9, 'Input:HL The greeting countdown', 'C The thing to greet', 'Output:F From $A59F when the greeting is printed')
R(0x9CF2, 'Input:HL The greeting countdown', 'C The thing to speak to', 'Output:F Z when the greeting should be said now; if not, the caller\'s return is dropped and the countdown moves on', 'HL Unchanged', '$A034 The thing to speak to')
R(0x9D13, 'Output:F From the rest of his turn at $E691')
R(0x9D30, 'Output:F From the second greeting')
R(0x9D65, 'Input:HL The flag for this person', 'C The person to tell (via $9CF2)', 'Output:F From $A59F when the message is printed')
R(0x9DC6, 'Input:HL The greeting flag of Lestrade ($9D91; its countdown is the next byte)', 'C The person to greet', 'Output:F From $A59F')
R(0x9DD8, 'Input:HL The countdown for the question', 'C The person asked', 'Output:F From $A59F when it is printed; nothing is printed if no statement waits')
R(0x9DFF, 'Output:F From $9D95 or $A59F')

R(0x9D48, 'Output:F From $9D65', 'HL, C Set for each of the three people told in turn')
R(0x9D73, 'Output:F From $9D65')
R(0x9D95, 'Output:F None used')
R(0x9E48, 'Output:F The game ends through $9E74')
R(0x9E6A, 'Output:F NZ and nothing printed once Lestrade has been introduced; otherwise the game ends through $9E74')
R(0x9E74, 'Input:HL The message to print', 'Output:F None: the game restarts through $B0AC')
R(0x9E85, 'Output:F NZ and nothing printed once $9E88 is non-zero; otherwise the game ends through $9E74')
R(0x9EA2, 'Output:F The game ends through $9E74 with the failure or success message')
R(0x9EC1, 'Input:IY The actor\'s entry in the actor table', 'Output:F None used')
R(0x9ECB, 'Input:IY The actor\'s entry in the actor table', 'Output:F None used')
R(0x9ED1, 'Input:IY The actor\'s entry in the actor table', 'Output:F None used')
R(0x9F1E, 'Input:A The value to store', 'HL Where to store it', 'B The room to put the actor in', 'DE The minutes until its next turn', 'IY The actor\'s entry in the actor table', 'Output:IX The actor\'s own record ($A017)')
R(0x9FC5, 'Output:HL $9FCE, the routine that prints the refusal', 'A 0 (refused)')
R(0xA040, 'Output:F None: this routine never returns, it falls into the main loop')
R(0xA064, 'Output:F None: the loop never ends by itself; $A0DA stops it')
R(0xA0DB, 'Input:HL The minute counter', 'IY The actor\'s entry in the actor table', 'Output:F Z/NC when the actor\'s time has come; C when it has not', 'DE The actor\'s next-turn time')
S(0x9EC1, "Each of the three characters has a state byte (the room he left), which is 0 while he is about.",
  "If the state byte is non-zero he is away: put him back in that room with no container, clear the state byte, give him no state word and set bit 6 of +5 so he is a person to talk to again.",
  "Otherwise, if it is am, do nothing. If it is not 9 o'clock in the evening, do nothing.",
  "At 9pm: store the room he is in, move him to B (0 for the cook and gardener, room 74 for Strachan), and set his next turn 504 plus a random 0 to 30 minutes on. Only the low byte takes the random part, so from 8 up the carry is lost.",
  "Give him the state word SLEEPING ($07F0) and clear bit 6 of +5.")
S(0xA064, "Clear the ending flag $A0DA. If it is set on a later pass, go to the ending code at $A0E7.",
  "Move the clock on one minute ($BFD9) and print it ($BF79).",
  "If the player is waiting until a time (plan verb 50) and ENTER is held down, make the player's next turn now.",
  "Walk the actor table from $9860 in 8-byte steps until the $FF marker. For each actor whose time has come ($A0DB): start its turn ($CC37), then run plan steps ($CC78) until one takes time ($A01F non-zero).",
  "Add that time to the actor's next-turn time and run the actor's after-turn routine ($9C77).",
  "At the end of the table, loop for the next minute. When the ending flag is 2 the game is saved ($B0E4) and the loop continues; otherwise it is loaded ($B0D7) and the game restarts at $A040.")

R(0xA0F7, 'Input:IX A node of a list', 'Output:IX The next node', 'F Z at the end of the list (A = 0)')
R(0xA104, 'Input:IY The list head', 'DE The node to find', 'Output:IY The node (or list head) whose link points at DE')
R(0xA11C, 'Input:A The number of data bytes wanted (3 more are used for the header)', 'Output:IX The cleared block', 'F NZ on success; out of memory ends in $C1D8')
R(0xA1AF, 'Input:IX The first node of the list', 'Output:The whole list is freed')
R(0xA25D, 'Input:A The thing number', 'Output:F Z when $A011 is 0, there is no list, or the thing is not in it; NZ if it is', 'IX The list at ($A0D8) when there is one')
R(0xA277, 'Input:IX The record whose picture is wanted (+1/+2 point to the picture data)', 'Output:All registers kept')
R(0xA296, 'Output:A, B Changed')
R(0xA2A2, 'Output:A Kept')
R(0xA2BD, 'Input:IX A verb record', 'Output:$A01D The high nibbles of +1 and +3', '$A01E The high nibbles of +5 and +7')
R(0xA2E4, 'Input:$A033 The verb', '$A034 The first object, $A035 the second', '$A036 The actor', 'Output:All registers kept')
R(0xA360, 'Output:F Z', 'IX Changed')
R(0xA419, 'Input:HL A sum of money in the parser\'s packed form', 'Output:The sum printed as pounds, shillings and pence')
R(0xA476, 'Input:HL The number to divide', 'DE The divisor', 'Output:A The quotient', 'HL The remainder')
R(0xA480, 'Input:HL The number', 'DE The place value (100 or 10)', 'C 0 while still skipping leading zeros', 'Output:HL The remainder', 'C Non-zero once a digit has been printed')
R(0xA490, 'Input:B The number, 0 to 255', 'Output:The number printed in decimal; HL, DE kept')
R(0xA4AB, 'Input:A The room number', 'Output:HL The room\'s record + 1')
R(0xA4BC, 'Input:A The thing number', 'Output:HL The thing\'s record + 7, the start of its name words')
S(0xA11C, "C = the number of bytes wanted + 3 (the size field and the link).",
  "Walk the free list from $9FE3. Each free block begins with its size and a link. Blocks that are too small are passed over.",
  "Of those that are big enough, remember the smallest (best fit), and the link that points to it.",
  "If none fits, go to the out-of-memory routine at $C1D8.",
  "If the chosen block would leave 4 bytes or more, split it: the free block keeps the front part and the end is handed out. Otherwise the whole block is taken and unhooked from the free list.",
  "Store the size before the block, clear its data and return NZ with IX at the block.")
S(0xA419, "Take away the marker bit and convert the packed sum to pence, then print a space.",
  "Pounds = pence / 240. If there are any, print the pound sign and the number. Stop if nothing is left; otherwise print a space.",
  "Shillings = what is left / 12. If there are none, print the pence and 'D.' (as in '6D.').",
  "Otherwise print the shillings, a stroke, and the pence, or '-' for none, as in '2/6' or '1/-'.")
S(0xA2E4, "Set $A2AA to 1 while narrating, and keep the verb and both objects at $A35D to $A35F.",
  "Work out whether the text is printed as quoted ($A027 is 1 when $A00C is 0).",
  "If it is too dark to see ($D078) and the actor is the player, print 'SORRY IT IS TOO DARK.' and finish.",
  "Find the verb's record and gather its flags ($A2BD). If bit 4 of $A01D is set the verb is never narrated.",
  "Start a fresh line if the actor is a character other than the player, Watson or Lestrade's usual set ($DC6C), and print the actor's name ($A724).",
  "If the actor was the player print the word YOU and narrate the command ($A360); otherwise narrate it as it stands ($A37D). End the line, clear $A2AA and $A027.")

R(0xA4CD, 'Input:HL The words of a command (four pairs)', 'IY The pattern words', 'Output:F Z when the pattern names the words', 'A 0 when the second and third pairs matched as they stand; 1 when they matched swapped', 'Registers HL, IY, DE kept')
R(0xA51B, 'Input:HL A word reference of the command (0 matches anything)', 'IY A word reference of the pattern', 'Output:F Z when they match', 'HL, IY Both moved on two bytes')
R(0xA536, 'Output:A The key pressed (0 if none)', 'F Z when nothing was typed in time')
R(0xA59F, 'Input:HL The message', '(SP+) Any parameters the caller pushed, dropped on return', 'Output:All registers kept')
R(0xA5C4, 'Input:HL The message', 'Output:F From the last element')
R(0xA5CD, 'Input:IX The message position', 'Output:F NZ to go on with the next element; Z when the message has ended', 'IX Moved on')
R(0xA621, 'Input:A The control code (below $20)', 'IX The message position', 'Output:F Z to stop or NZ to go on, from the handler')
R(0xA63A, 'Input:A The code to print', 'Output:F Z (XOR A)')
R(0xA63F, 'Input:D Bit 6: no full stop; bit 4: full stop and new line', 'Output:F From the new line', 'A Changed')
R(0xA65D, 'Input:(message parameters) The next word: the thing to name', 'Output:F Z', 'A 0')
R(0xA66C, 'Input:$A59D The parameter pointer', 'Output:DE The next parameter word', 'HL The pointer, moved on two', 'F NZ')
R(0xA679, 'Input:IX The position of the code', 'Output:IX Moved on by the offset')
S(0xA4CD, "A4CD tries the fourth pair of the pattern first, six bytes on; if it fails, the whole match fails.",
  "A4E0 then needs the first pair to match ($A51B; an empty pattern word matches anything) and notes that in $A02E.",
  "The second and third pairs are tried as they stand (A = 0).",
  "If that fails they are tried swapped, the pattern's third against the command's second and its second against their third (A = 1).")
S(0xA5CD, "Bit 7 set: a two-byte dictionary reference. Classes $20, $30 and $60 are the sentence-ending words ($A647); any other is printed ($A887).",
  "Codes $20 to $3F: a single literal character. $40 to $5F: a run of (code AND $1F) + 1 letters packed five bits each ($A990), each printed as it is unpacked.",
  "$60 and above: one of the common words ($A83A).",
  "Below $20: a control code, which is looked up in the handler table at $A55D and called. Codes below $1D carry on; $1D and above end the message.")
S(0xA59F, "Save the registers and take the address of the caller's parameters (stack pointer plus 12) for $A59D.",
  "Clear $A00C unless $A00B is set.",
  "Run the interpreter over the message ($A5C4).",
  "Restore the registers, drop the parameters from the stack and return.")

R(0xA65A, 'Output:A 0', 'F Z (stop)')
R(0xA65C, 'Output:No registers changed')
R(0xA682, 'Output:A 0', 'F Z')
R(0xA684, 'Input:(message parameters) The next word: the new message', 'Output:IX The new message position', 'A 0', 'F Z')
R(0xA68C, 'Input:IX The position of the code', 'Output:F Z; the next element is printed only in the code\'s own part of the day, otherwise it is skipped', 'A 0 when skipped')
R(0xA6BB, 'Input:IX An element of a message', 'Output:IX The next element')
R(0xA6D3, 'Input:IX The position of the code (the byte after it is n)', 'Output:IX At the end of the n elements', 'A 0', 'F Z')
R(0xA702, 'Output:DE The word reference at $A00D', 'F NZ')
R(0xA709, 'Input:(message parameters) The next word', 'Output:A 0', 'F Z')
R(0xA711, 'Input:(message parameters) The next word: a case statement', 'Output:A 0', 'F Z')
R(0xA720, 'Output:A 0', 'F Z')
R(0xA72C, 'Output:A 0', 'F Z')
R(0xA736, 'Input:A The code to print', 'Output:A 0', 'F Z')
R(0xA73B, 'Output:A 0', 'F Z')
R(0xA745, 'Input:A The room or thing number', 'F Carry set for a room, clear for a thing', 'Output:A 0', 'HL Kept')

R(0xA75B, 'Input:IX The position of the code ($0B), followed by a 16-bit offset', 'Output:IX Past the offset', 'A 0', 'F Z')
R(0xA771, 'Input:(message parameters) The next word: a message, or 0', 'Output:A 0', 'F Z')
R(0xA780, 'Input:$A036 The actor (code $0C); $A034 the direct object (code $0E)', 'Output:DE $09F2 (YOUR) for the player, $0414 (HIS) for anyone else', 'F NZ')
R(0xA793, 'Input:$A036 The actor (code $10); $A034 the direct object (code $11); the next parameter (code $13)', 'Output:DE ARE ($007A) for the player, IS ($0485) otherwise', 'F NZ for the player; the flags of the compare otherwise')
R(0xA7BA, 'Input:HL A thing\'s name words', 'Output:The name printed ($D405); IY kept')
R(0xA7C5, 'Input:HL A thing\'s name words', 'Output:The name printed ($D3E8); IY kept')
R(0xA7D0, 'Input:DE A word reference or an article code', 'Output:$A7EA 1 unless the word is YOU', 'F Z if the word is YOU')
R(0xA7EB, 'Input:D The article code in its top nibble', 'Output:The article (THE, A, AN or SOME) printed', 'DE Kept')
R(0xA80E, 'Input:DE A word reference', 'Output:The word printed, as a noun ($A887)', '$A026 Marked if the word is not YOU')
R(0xA82F, 'Input:A The actor number ($FF is SOMEONE)', 'Output:The name printed')
R(0xA83A, 'Input:A The byte, $60 or more', 'Output:The common word printed', 'F NZ')
R(0xA840, 'Input:A The byte, $60 or more', 'Output:DE The word reference (class $50)')
R(0xA852, 'Output:A 0', '$A851 Toggled')
R(0xA880, 'Input:HL A word reference (two bytes)', 'Output:HL Past the reference', 'The word printed')
R(0xA92F, 'Input:HL A dictionary record', 'IX The end of the spelling', 'Output:IX At the end of the suffix, ended with 0')
R(0xA94D, 'Input:HL A dictionary record', 'Output:The spelling at $5C42', 'HL, IX Kept')
R(0xA95B, 'Input:HL A dictionary record', 'Output:The record\'s spelling at $5C42, ended with 0', 'HL Past the record')
R(0xA990, 'Input:HL The packed text', 'C The bit position (0 to 7)', 'Output:A The letter code ($60 + n)', 'HL, C Moved on five bits')
R(0xA9B7, 'Input:A The character to print', 'Output:All registers kept')
R(0xAB91, 'Input:IY The sentence node', 'E Slot flags (bit 0, 1, 2)', 'Output:F Z if the verb slot was filled; NZ if not; carry set for a second word in a slot already taken', 'E Updated')
S(0xA880, "Take the 12-bit offset and the flag nibble from the two bytes at HL; print nothing if output is off ($5C3C) or the offset is 0.",
  "Print a space, then find the letter whose records contain the offset by searching the per-letter index at $5D80.",
  "From that letter's first record, spell each record ($A95B) until the offset is reached; the spelling is built at $5C42 from its kept letters, new packed letters and suffix.",
  "Print the spelling a letter at a time through the word-wrap printer, applying capitals and the flag nibble's rules.")
S(0xA9B7, "If quoted printing is on ($A027), send the character straight out ($C1E1).",
  "A space, carriage return or quote ends a word. Any other character is added to the word buffer at $5C0B; a delete removes the last letter.",
  "When a word ends: if it does not fit on the rest of the line ($C1F5), start a new line first. Then print the word, and then the character that ended it.")
S(0xAB91, "In statement mode ($A024 = 2) the words are matched against the relation words at $994D instead ($ABF3).",
  "Otherwise take tokens ($AE7F). A class $30 token goes in the verb slot (IY+0/+1), a class $00 token in the second word slot (IY+2/+3).",
  "A class $40 token clears E bit 0 and is treated as a verb; a class $20 token goes to whichever slot is free.",
  "A word for a slot already taken returns carry set. Any other class ends the verb: return Z if the verb slot has been filled.")

R(0xAC24, 'Input:E Flags for the kinds of word still allowed (bits 2, 4, 5)', 'Output:F Carry set for a word out of place', 'E Updated', 'The ten-byte pattern at $AAA8')
R(0xAC8F, 'Input:BC The word', 'Output:F Z when stored in one of the two slots at $AAA8; NZ when both are taken')
R(0xAC94, 'Input:BC The word', 'Output:F Z when stored in one of the two slots at $AAAE; NZ when both are taken')
R(0xACA6, 'Input:E Bit 6: first object waiting; bit 7: second object', 'IY The sentence node', 'Output:F NZ when stored; Z when neither was waiting', 'E The bit cleared')
R(0xACCC, 'Input:E Flags', 'IY The sentence node', 'Output:The start of the sentence saved at $AAA1 to $AAA6')
R(0xAE59, 'Input:HL A word reference slot', 'DE The word to copy in', 'Output:HL, DE Both moved on two bytes')
R(0xAE6A, 'Output:IY The new 30-byte node, linked after the last')
R(0xAE7F, 'Input:D The previous class', 'Output:A, D The class of the token', 'BC The word reference (for classes with one)', '$A029 Where this token started', '$A02B The position after it')
R(0xAEA9, 'Input:IY A node', 'Output:IY The next node', 'F Z at the end of the list')
R(0xAEB6, 'Input:IY A node', 'B The sentence count', 'Output:IY The next node not marked BUT', 'IX The node before', 'B One fewer')
R(0xAEC5, 'Input:IY A node', 'B The sentence count', 'Output:IY The node before it, skipping nodes marked BUT', 'IX The node given', 'B One fewer')
R(0xAEEA, 'Output:IY The last node of the sentence list')
R(0xAEF1, 'Input:IX The node to merge', 'IY The node to merge it into', 'Output:IY Updated')
R(0xAF38, 'Input:IY A node', 'A The offset into it', 'Output:F Z if the ten bytes at IY + A are all zero', 'Registers kept')
R(0xAF4E, 'Input:DE The offset', 'IX, IY The two nodes', 'Output:6 bytes copied (entry $AF52 copies 10, $AF56 copies 2)')
R(0xAF67, 'Output:F NZ', 'A 1')
R(0xAFE1, 'Input:E Parse flags', 'Output:F Returns if E bit 1 is set; otherwise the caller is abandoned with NZ')
R(0xAFFA, 'Input:E Parse flags', 'Output:Carries on in the parser')
R(0xB01C, 'Input:E Parse flags', 'IY The sentence node', 'Output:Carries on in the parser, or NZ if out of place')
R(0xB0AC, 'Output:F NZ', 'HL 1')
R(0xB0C6, 'Output:Carries on in the parser at $B015')
S(0xAC24, "Clear the ten bytes of the noun-phrase pattern at $AAA8 and set E bits 2, 4 and 5.",
  "Take tokens. An article ($80) is allowed once, at the start; a second one returns carry.",
  "Up to three words of class $10 or $70 (adjectives and prepositions) are counted in $AAA7 and stored by $AC8F or $AC94.",
  "A noun ends the phrase. The pattern is then copied into the node as the first or second object ($ACA6).")
S(0xAE7F, "Remember where the token starts ($A029) and the class of the one before ($A02D).",
  "The class is the first byte. Classes $E0, $F0, $90 and those below $80 have a two-byte word after them, which is returned in BC.",
  "Save the position after the token and return the class in A.")
S(0xAEF1, "IY takes IX's verb: the low byte at +0 and the other flag bits from +1 (without bit 7).",
  "If IX has no words at +4 and +5 there is nothing more to do.",
  "If IY already has words at +14 to +23 stop. Otherwise move IY's first group up to the second group and copy IX's words from +4.",
  "Copy IX's second word in as well if IY has none.")

R(0xB0D7, 'Output:IY Restored as saved', 'The saved game loaded over $840B onwards')
R(0xB0EE, 'Output:IX $840B, the start of the saved block', 'DE Its length ($A01F - $840B)', 'HL $A01F - $840B before the swap')
R(0xB0FD, 'Input:E Parse flags (bit 3: a clause has finished)', 'IY The sentence node', 'Output:E Bits 0 to 2, 6 and 7 set', 'IY The node that took the pronoun\'s words')
R(0xB191, 'Input:IY The first parse node', 'Output:F Z with HL = $B84C when no verb matches; NZ when one does', '$A033 The verb number', '$A034 The direct object, $A035 the indirect object', 'IX The verb record that matched')
R(0xB2DF, 'Output:$A035 The first indirect object that passes the record\'s checks', '$B171 How many pass')
R(0xB303, 'Output:HL $B6AE, the routine that asks which one', 'F Z')
R(0xB308, 'Output:A The number of candidates for the direct object', 'Search state kept')
R(0xB32D, 'Output:A The number of candidates for the indirect object', 'Search state kept')
R(0xB34F, 'Output:$B17E The first thing to search, or 0 for a room', '$B170 0, $B4A2 $FF')
R(0xB36B, 'Output:$B180 The first thing to search, or 0 for a room', '$B171 0, $B549 $FF')
R(0xB387, 'Input:$A01D The verb\'s flags', 'Output:F Z if nothing is needed or none is missing; NZ if the slot has words or one is missing')
R(0xB405, 'Input:A 1 if the pattern matched with its middle words swapped, 0 if not', 'IY The parse node', 'Output:The two object slots filled in the verb\'s order')
R(0xB483, 'Input:HL Where to copy to', 'IY A node', 'E The offset of the word pair', 'B The number of pairs still wanted', 'Output:F Z if the pair was empty or B was 0', 'B One fewer if the pair was not empty', 'HL Moved on two bytes if copied')
R(0xB4A0, 'Input:HL The slot\'s words', 'IY The search routine ($D36A or $D39B)', 'Output:A The thing or room, or $FF', 'IX The search position')
R(0xB4A3, 'Output:F NZ with $A034 = $FE and $A02F the number the first time; Z otherwise', 'A $FF if there is nothing to search')
R(0xB4C1, 'Output:A The next candidate for the direct object ($A034); $FF if none', 'F Z when none', 'IX Saved at $B17E')
R(0xB4FD, 'Output:A The next thing or room, $FF if none', 'F Z when none', '$A034 The candidate', '$B16D bit 1 set when found')
R(0xB517, 'Input:$A034 The candidate', 'Output:F NZ if the candidate is one of the BUT things; Z if not', 'Registers kept')
R(0xB54A, 'Output:F NZ with $A035 = $FE and $A031 the number the first time', 'A $FF if there is nothing to search')
R(0xB568, 'Output:A The next candidate for the indirect object ($A035); $FF if none', 'F Z when none', 'IX Saved at $B180')
R(0xB5A4, 'Output:A The next thing or room, $FF if none', 'F Z when none', '$A035 The candidate', '$B16E bit 1 set when found')
S(0xB191, "Set both object numbers ($A034, $A035) to $FF and clear the 17 bytes of the parser's work space at $B16D.",
  "Match the parsed words against the verb patterns ($B39D). If none matches, return Z with HL = $B84C, the routine that says the verb is not known.",
  "Turn the matching record's address into a verb number (records are 8 bytes from $8259, counting from 1) and keep it in $A033, with the record's address at $B18E.",
  "For verb 46 (TALK TO) swap the six bytes between $A002 and the object slot, as bit 0 of $B16D says.",
  "Copy the typed objects into the two slots in the verb's order ($B405), and count the candidates for each ($B308, $B32D).",
  "Ask which one is meant ($B6AE) if there are too many, or none if there are too few; otherwise choose the direct and indirect objects and return NZ.")
S(0xB405, "If the pattern matched with its middle words swapped (A = 1), swap the two prepositions at $B188 and $B18A.",
  "Gather the verb's flags ($A2BD).",
  "With no preposition typed, bit 5 of $A01E decides the order of the two noun phrases (GIVE WATSON LAMP).",
  "Otherwise see which of the node's two groups the preposition belongs to (+14 or +16) and put each group in the matching slot.")
S(0xB4C1, "If the requirement code ($A00F) is 5, the candidate is a number: use it once ($B4A3).",
  "If the slot's first word has bit 7 set, there is nothing to search: return $FF.",
  "Otherwise search the rooms ($D39B, for codes below 5) or the things ($D36A) from the saved position ($B17E), skipping those the BUT list rejects ($B517), and save the new position.")

R(0xB5B6, 'Input:A The value for $A01B', 'Output:$9FF0 The rest of the typed line as the current sentence', '$9FF2 What follows it', 'IX The new sentence node')
R(0xB5D3, 'Input:$B16D, $B16E Flags telling which slots hold words', 'Output:A question printed ($A59F); the player\'s own words are the message parameters')
R(0xB6AE, 'Input:$A010 The indirect object\'s requirement code', 'Output:A message printed ($A59F)')
R(0xB6DA, 'Input:HL The slot\'s words', 'Output:F Z if the words do not name scenery; otherwise YOU CANNOT ... THE ... is printed and the caller is abandoned (entry $B6F0 does the same for the second slot)')
R(0xB6FD, 'Input:HL The slot\'s words', 'Output:F Z if the words do not name some scenery of the room; NZ if they do')
R(0xB772, 'Input:DE A dictionary word reference', 'Output:A The class: $50 noun, $60 adjective')
R(0xB83C, 'Input:HL Three word references', 'Output:The three words pushed as message parameters under the return address')
R(0xB84C, 'Output:The message "I DO NOT KNOW THE VERB" printed with the typed verb')
R(0xB863, 'Output:As $C929')
R(0xB86A, 'Input:A 1 if the person spoken to has a plan script; 0 if not', 'Output:The quoted sentence handed over or used up')
R(0xB90E, 'Input:$A036 The actor', 'Output:IX The waiting node, kept at $B866', 'IY The sentence node it points to', 'F Z if found')
R(0xB91F, 'Input:$A036 The actor', 'Output:F Z with IX the waiting node; NZ if none', 'IX Changed')
R(0xB936, 'Input:A The actor', 'Output:F From the order or remark')
R(0xB98C, 'Input:IX The ASK order', 'Output:$A033 The verb', '$A034 The direct object, $A035 the indirect object')
R(0xB9FA, 'Input:IX The node to remove', 'Output:The node unlinked from $9FEE and freed')
R(0xBA20, 'Input:$A036 The person spoken to (2 Lestrade, 3 Watson)', 'IX The remark node', 'Output:F Carry set (the turn is used)', 'A 1')
R(0xBA67, 'Input:IY The remark\'s sentence node', 'A 0', 'Output:F From the reply')
R(0xBB46, 'Input:A The kind of match', 'Output:$BA60 The kind', '$BA61 1', '$BA62 The three bytes from $BA19')
R(0xBB5C, 'Input:$BA65 The record found', 'Output:Continues at the record\'s handler (+3/+4)')
R(0xBB67, 'Input:IY The remark\'s sentence node', 'A 0', 'Output:A reply printed')
R(0xBC46, 'Output:Each waiting statement of the case table checked and, if provable, marked')
S(0xB936, "Find the node waiting for this actor ($B90E). If its +7 is 2 it is a remark: give Watson's or Lestrade's reply ($BA20).",
  "If its +1 is $FF it came from a plan script's ASK: turn it into a command ($B98C).",
  "Otherwise it is words the player said: restore the ALL flag and search position from the node, and parse the current sentence for this actor ($B191).",
  "If parsing fails, drop the sentences one by one and return Z. Otherwise keep the ALL position, drop the sentence unless it is an ALL, and return with the command to run.")
S(0xB86A, "Take the next quoted sentence from the list at $9FEC and unlink it.",
  "If the person has a plan script (A = 1), parse the words as a sentence of their own ($B8AA) and put them on the order and remark list at $9FEE as an 8-byte node.",
  "Otherwise skip the words to the end of the line and mark it with a $90 token.")
S(0xBC46, "Push every statement of the case table at $9965 that is waiting (bit 0 of +3 set) and is not one of the bit-5 kind, ending the list with a 0.",
  "Pop them one at a time and try to prove each ($BCC9).")

R(0xBC74, 'Output:A, B How many waiting statements can now be proven', 'IX The last of them ($BA1E)')
R(0xBC9C, 'Output:B How many waiting statements cannot be proven yet', 'IX The first of them ($BA1E)')
R(0xBE5A, 'Input:IX A case record', 'Output:IX The next case record (4 bytes on, or 6 if a routine address follows)', 'AF Kept')
R(0xBE72, 'Input:IX The first record of a group', 'Output:IX The first record after the group', 'AF Kept')
R(0xBF08, 'Input:IX A case record', 'Output:F Z if a piece of evidence fails; NZ if all are satisfied', 'IX Moved on')
R(0xBF1C, 'Input:IX A statement record of the case table', 'Output:The statement printed: thing, relation, thing')
R(0xBF45, 'Input:IX A statement record', 'Output:DE The relation\'s words', 'F NZ if there is one; Z if the relation is 0')
R(0xBF79, 'Output:The clock printed in the status bar ($C1A8)')
R(0xBFD9, 'Output:The minute counter, the minute, hour, am/pm and day moved on by one minute')
R(0xC00C, 'Output:A The part of the day: 1 night, 2 evening, 3 afternoon, 4 morning, 5 dawn')
R(0xC03B, 'Output:A Bit 6 set if the printer is not ready (the ZX Printer status)', 'F NZ in that case')
R(0xC040, 'Input:IX The start of the block', 'DE Its length', 'Output:The block saved to tape and verified')
R(0xC0DF, 'Input:IX The start of the block', 'DE Its length', 'Output:F Carry set when the block loaded correctly')
R(0xC10F, 'Output:The screen cleared, the attributes black on white and the border white')
R(0xC129, 'Output:$C1F5 18 characters to a line', '$C1F8 The print position', '$C128 1')
R(0xC142, 'Output:$C1F5 36 characters to a line', '$C128 0')
R(0xC14A, 'Output:The screen cleared and the command window set up')
R(0xC1A8, 'Input:HL The text', 'B The number of characters', 'Output:The text printed at the status bar')
R(0xC1C0, 'Input:HL A message ending with bit 7 set', 'Output:The message printed, a key waited for and a new line started')
R(0xC1CB, 'Input:HL A message whose last byte has bit 7 set', 'Output:The message printed', 'HL At the last byte')
R(0xC1E1, 'Input:A The character', 'Output:The character printed in the command window or the text window, as the flags $5C3C and $A027 say')
S(0xC00C, "In the morning (am), 12 midnight to 5:59 is night (1), 6am is dawn (5) and 7 to 11am is morning (4).",
  "In the afternoon (pm), 12 noon is morning (4), 1 to 6pm is afternoon (3), 7pm is evening (2) and 8pm onwards is night (1).")
S(0xBFD9, "Count the minute since the start ($9FDD) and add one to the minute ($9FDF).",
  "At 60, the minute becomes 0 and the hour ($9FE0) goes up; 13 becomes 1.",
  "When the hour reaches 12, am and pm swap; going to am starts the next day ($9FE1).")

R(0xC1FC, 'Input:A The character typed (ENTER $0D, DELETE $08, anything else)', 'Output:All registers kept', 'The character shown in the command window')
R(0xC240, 'Input:A A character', 'Output:A The character, in capitals if it was a lower-case letter')
R(0xC249, 'Input:C Pixel shift', 'HL Print position', 'Output:Control joins the input loop at $C22D')
R(0xC267, 'Input:C The pixel shift in the cell', 'L The cell', 'Output:C, L Stepped back one 7-pixel character')
R(0xC271, 'Output:The command window scrolled up one line and its bottom row cleared', 'HL, DE, BC Kept')
R(0xC29C, 'Output:Part of the command window moved down one row and the gap cleared', 'HL, DE, BC Kept')
R(0xC2BA, 'Input:A The character (or $0D for a new line)', 'Output:The character printed at the text cursor; registers kept')
R(0xC306, 'Output:A key waited for, the window cleared; HL kept')
R(0xC316, 'Input:HL The print position', 'C The pixel shift', 'Output:The text rows moved up one line; the top row sent to the printer first when at full width')
R(0xC37D, 'Input:DE, HL Two screen addresses', 'Output:HL The other pointer moved down one character row', 'DE The pointer that was HL')
R(0xC388, 'Input:A The character', 'HL The screen address', 'C The pixel shift', 'Output:The glyph drawn; all registers kept')
R(0xC3E4, 'Input:$A008 Non-zero when printing is on', 'Output:The top character row sent to the ZX Printer; registers kept')
R(0xC400, 'Output:HL, DE restored')
R(0xC403, 'Input:B The pixel line number', 'HL The screen address of the line', 'Output:The line sent to the printer through the ROM at $0F12')
R(0xC415, 'Output:A The key pressed (bit 7 cleared)')
R(0xC41F, 'Output:A The key with bit 7 set, or 0 if none', 'All other registers kept')
R(0xC45E, 'Input:B The candidate number', 'Output:F Carry when it is within the allowed range (below 106 for a room, 110 for a thing)')
R(0xC493, 'Input:$A01D, $A01E The verb\'s flags', 'Output:$A00F The direct object\'s requirement: 0 none, 4, 5 a number or 7 an ordinary thing')
R(0xC4B2, 'Input:$A01D, $A01E The verb\'s flags', 'Output:$A010 The indirect object\'s requirement: 0 none, 4, 5 a number or 7 an ordinary thing')
S(0xC1FC, "ENTER prints a space over the cursor and starts a new line; DELETE rubs the last character out ($C249).",
  "Anything else is shown in capitals ($C240) and printed ($C388).",
  "When the line is full, or after ENTER, the window scrolls up ($C271) and 36 characters are available again.",
  "Save the characters left, pixel shift and print position. Draw a '+' cursor after the character.")
S(0xC2BA, "Pick up the text print position ($C1F8) and pixel shift ($C1FA).",
  "A character other than ENTER is printed ($C388); if the line is then full a new line is started.",
  "A new line after fifteen lines of text ($A019) waits for a key ($C306) first. Scroll the text up a row ($C316), and start the new line with 36 characters (18 beside a picture).")
S(0xC316, "At full width, send the top row to the printer ($C3E4) if printing is on.",
  "Move text rows 1 to 17 up to rows 0 to 16, eight pixel lines each, 32 bytes a line (16 beside a picture).",
  "Clear the bottom text row.")
S(0xC41F, "Save the registers and point IY at the system variables.",
  "Allow one interrupt (EI, HALT) so the keyboard is scanned.",
  "If no new key is flagged, return 0. Otherwise take the key from $5C08, turn the ROM's editing codes into backspace and '[', and put it in capitals.",
  "Set bit 7 to say a key was pressed.")

R(0xC4D1, 'Input:$A033 The verb', '$A034 The direct object, $A035 the indirect object', '$A036 The actor', 'Output:F Z if refused; NZ if the action was done')
R(0xC542, 'Input:$A010, $A035, $A01D', 'Output:F NZ when an indirect object should be guessed; Z when not')
R(0xC55A, 'Output:F NZ when a candidate indirect object let the record\'s checks pass; Z when none did', '$A035 The candidate that passed')
R(0xC571, 'Input:IX An action record', 'Output:$A00F The direct object\'s requirement code (the low nibble of byte 0)')
R(0xC57A, 'Input:IX An action record', 'Output:$A010 The indirect object\'s requirement code (the low nibble of byte 1)')
R(0xC583, 'Input:A A record number with bit 7 set', 'Output:F Z if refused; NZ if the record ran')
R(0xC5FC, 'Input:$A010, $A035', 'Output:F NZ when the indirect object should be guessed; Z when not')
R(0xC60D, 'Output:F NZ when a candidate made the record run; Z when none did', '$A035 The candidate')
R(0xC628, 'Input:IY The action record', 'Output:F NZ if the direct object meets the record\'s requirement; otherwise the command is refused through $DC15')
R(0xC74E, 'Input:C An object', 'B Two modes (bits 2-3 for mask L, bits 0-1 for mask H)', 'L, H The masks', 'Output:F NZ if the object\'s +5 flags pass both tests; Z if not')
R(0xC821, 'Input:A A thing number', 'Output:F NZ if the actor ($A036) can see it; Z if not')
R(0xC863, 'Input:A A thing number', 'Output:A The top of its containment chain', 'IX Kept')
R(0xC86E, 'Input:IX A thing\'s record', 'Output:A The highest holder reached, $FF if none', 'IX Kept')
R(0xC898, 'Input:IY A thing\'s record', 'Output:A The highest holder reached', 'IX, IY Kept')
R(0xC8A7, 'Input:A A thing number', 'Output:F Z if the thing has exactly one location', 'A Its location count less 1')
R(0xC8AF, 'Input:A A thing number', 'Output:F NZ if some person holds it at any depth; Z if not')
R(0xC8BE, 'Input:A A thing number', 'Output:F NZ if it is a person (+5 bit 6)')
R(0xC8C6, 'Input:A The actor', 'B The thing', 'Output:F NZ if the actor can carry the thing as well as what it holds; Z if not', 'BC Kept')
R(0xC8EF, 'Input:$A034, $A035 The objects', 'Output:$A013 The direct object\'s record', '$A015 The indirect object\'s record')
S(0xC4D1, "A verb number with bit 7 set is a script-only verb: use the numbered record ($C583).",
  "Otherwise find the verb's pattern record ($A2B1), gather its flags ($A2BD), and set the two objects' requirement codes ($C493, $C4B2).",
  "If a number is required, the object must be $FE. If a required direct object is still $FF, ask for it.",
  "Guess the indirect object when it is missing and the verb allows ($C542, $C55A), then check the record ($C929) and carry it out.")
S(0xC583, "The record number (bit 7 dropped) indexes the 13 record addresses at $9FAB.",
  "Set both requirement codes from the record's header ($C571, $C57A).",
  "If the record takes no objects, run it at once ($C5F4). If the direct object must be a number, $A034 must be $FE or the command is refused.",
  "Guess a missing indirect object ($C60D) and run the record.")
S(0xC86E, "Start with the thing's holder (+1). If it is $FF nothing holds it, and the answer is the last holder reached.",
  "Otherwise move up to the holder's record, but only climb further when the holder's +5 bit 7 is set and it also has bit 5 or bit 3 set (it lets what is inside be seen).",
  "Return the highest holder reached.")
S(0xC821, "The thing is seen if it is what the actor is in or on, or the actor's own container.",
  "A thing with +5 bit 7 clear cannot be seen.",
  "Things held by the actor, or with the same top-level holder, can be seen; things with different holders cannot.",
  "If neither is held, the thing can be seen when it is in the actor's room.")

R(0xC929, 'Input:$A033 The verb', '$A034, $A035 The objects', 'Output:F Z if refused; NZ if the action ran')
R(0xC933, 'Input:$A017 The actor\'s record', '$A033 The verb', 'Output:The action record chosen and run through $C996')
R(0xC960, 'Input:IX A record whose +1 is a number', 'Output:HL The action record at entry (number - 1) of the table at $AA71')
R(0xC989, 'Input:IX A numbered action record', 'Output:F From the record', 'IX Kept')
R(0xC996, 'Input:HL An action record', 'Output:F Carry set if a script was started as the actor\'s plan; Z if refused; NZ if done')
R(0xC9BF, 'Input:HL An action record', 'Output:F Z with HL = the refusal handler if refused; NZ if the record\'s checks pass; carry set if it is a script')
R(0xCA60, 'Output:HL, AF The result of the action\'s body')
R(0xCA76, 'Input:$A033 The verb', 'Output:The action narrated unless the verb is script-only')
R(0xCA7F, 'Output:The room described if the player\'s view has changed')
R(0xCA9E, 'Input:$DD01 The room number', '$DCFF Its record', 'Output:The room described in full the first time, briefly after')
R(0xCAAF, 'Input:$A036 The actor', 'Output:An entrance announced, or the direct object\'s arrival noted')
R(0xCB2C, 'Input:HL The handler', 'Output:F, HL From the handler', '$CB28, $CB2A The IX and IY the handler left')
R(0xCB40, 'Input:HL The address to jump to')
R(0xCB41, 'Output:A 0', 'F Z')
R(0xCB43, 'Input:HL The failure routine to call, or 0', 'Output:A 0', 'F Z', '$A036 The player again')
R(0xCB7B, 'Input:$CB79 The flag bits that failed', '$CB7A The object', 'Output:A message like "THE ... IS <word>" printed')
R(0xCBA7, 'Input:$B934 The guard flag', 'Output:Returns if bit 6 is clear; otherwise the message is printed and the caller is abandoned through $DC15')
R(0xCBBB, 'Output:HL The message printed')
R(0xCC0E, 'Input:A An actor number', 'Output:IY The actor\'s record, or the $FF end marker if there is none', 'BC, DE Kept')
S(0xC933, "If the actor is a person (+5 bit 6) and lists this verb in its own actions ($D1DC), look the verb up in the shared actions table ($D349); a shared action that is found is run.",
  "If the direct object needs to be a thing (requirement code 7 or more) and lists this verb in its own actions, use that.",
  "Otherwise look the verb up in the default-action table at $9F38; with no default the command fails ($DC15).")
S(0xC9BF, "Refuse if it is too dark ($D078) and the record cares about that.",
  "Check the direct object ($C628) and the indirect object ($C6BE) against the record.",
  "If bit 6 of the record is set, run its pre-check routine; if that refuses, stop.",
  "Otherwise take the high nibble of byte 1 as the action's length ($A01F) and run the body, narrating the action first and describing any change.")
S(0xCB43, "If the actor is the player, Watson or the police cab (actors 0, 1 or $64), do nothing.",
  "Otherwise note a failure ($A00B): either call the failure routine given in HL or narrate that the action failed ($CA76).",
  "Make the player the current actor again.")

R(0xCC29, 'Input:$A036 The actor', 'Output:$A017 The actor\'s record', '$A00A The actor\'s room', 'IX The record')
R(0xCC37, 'Input:A The actor number', 'Output:$A01F 0 (or 1 if the actor is not in the table)', 'IY The actor\'s record', '$A036 The actor', '$5C3C Output on only when the actor is seen by the player')
R(0xCC78, 'Input:A The actor number', 'Output:$A01F The minutes the step took (0 if none)')
R(0xCD24, 'Input:IX The instruction (+1 the actor signalled)', 'Output:The token left on the list at $9FE7; the step succeeds')
R(0xCD47, 'Input:IX The instruction (+1 the actor the token must come from)', 'Output:The step succeeds if the token was there (and is removed), otherwise it fails')
R(0xCD82, 'Output:$A01F 1')
R(0xCD95, 'Input:IX The instruction (+1/+2 the message)', 'Output:The step succeeds')
R(0xCDA1, 'Input:IX The instruction (+1 the person, +2/+3 the message)', 'Output:The step succeeds')
R(0xCDBF, 'Input:IX The instruction (+1 the person, +2 verb, +3 and +4 objects)', 'Output:The order queued at $9FEE; the step succeeds')
R(0xCE18, 'Input:IX The instruction', 'Output:The command or record run; the step succeeds, fails or starts a sub-script')
R(0xCE83, 'Output:IY The actor\'s record', 'HL, IX The current instruction', 'A Its first byte')
R(0xCE8F, 'Output:The script position moved on and the turn ended ($CD91)')
R(0xCEB8, 'Output:The failure counted and the script position moved on')
R(0xCEDE, 'Input:A An argument byte', 'Output:A The value it stands for')
R(0xCEFE, 'Input:A The opcode byte', 'HL The instruction', 'Output:HL Past the instruction (CF03 skips the opcode and operands only)')
R(0xCF43, 'Input:IX A spent one-shot instruction', 'Output:The instruction and its addresses overwritten with zeros')
R(0xD008, 'Input:IY The actor\'s record', 'Output:$9FD6 The plan\'s verb', '$9FD7 Its objects')
R(0xD045, 'Output:$A009 The room the player is in')
R(0xD04F, 'Output:IX One entry before the thing index at $8B6F')
S(0xCC37, "Clear the failure count ($CC0B). Find the actor's record ($CC0E); if there is none, make the action take 1 minute and stop.",
  "Keep the record address ($9FDB) and the actor ($A036), and note whether an order or remark is waiting ($B91F).",
  "Set up the actor ($CC29) and note the player's room ($D045).",
  "Switch output on only when the player can see the actor ($C821). Clear $A01F.")
S(0xCC78, "Set up the actor ($CC5A) and load its plan registers ($D008). Take its script position from its record.",
  "If ten steps have failed this turn, give up until next turn ($CD8B). Skip any zero bytes (spent one-shot instructions).",
  "The opcode is the low nibble of the first byte. Codes of 10 and up are control flow ($CCF3); the others are actions. If an order was given this turn, turn it into a command ($B936) and carry it out first.",
  "Run the instruction. It succeeds ($CE8F), moving to its success address, or fails ($CEB8), moving to its failure address, and a one-shot instruction is erased ($CF43).")
S(0xCEB8, "Count the failure in $CC0B.",
  "Skip the instruction and any success address. If the instruction has a failure address (bit 4), go there.",
  "If the new position is the same instruction, wait there until next turn ($CD8B); otherwise try the next one now.")

R(0xD078, 'Input:$A017 The actor\'s record', 'Output:F Carry when it is too dark for the actor to see; NC when not', 'Registers kept')
R(0xD0D0, 'Input:HL A word reference', 'Output:The word written into the YOU ARE message at $68DE', 'DE Kept')
R(0xD0DD, 'Input:A A room number', 'Output:HL The message to start the description with', 'AF Kept')
R(0xD102, 'Input:A A room number', 'Output:The room described in full; registers kept')
R(0xD113, 'Input:A A room number', 'HL The opening message', 'Output:The room described, with its picture if shown')
R(0xD182, 'Input:HL The room\'s own text, or 0', 'DE The opening message', 'Output:The description printed')
R(0xD1B2, 'Input:A A room number', 'Output:The name line and, if it is not dark, the rest')
R(0xD1C6, 'Input:IX A room\'s record', 'Output:The room\'s name printed with no article')
R(0xD1DB, 'Input:HL The address to jump to')
R(0xD1DC, 'Input:IX An entity record', 'A A verb number', 'Output:F Carry set with IX on the verb\'s pair if listed; carry clear if not')
R(0xD21C, 'Input:A Kept across the call', 'Output:As $D206')
R(0xD237, 'Input:A A thing number', 'Output:IX The thing\'s record')
R(0xD26C, 'Input:$A034 The direct object', 'Output:F Carry set if the actor carries it')
R(0xD2A4, 'Input:A The limit', 'Output:A A random number from 0 to the limit')
R(0xD305, 'Input:A A thing', 'B 0 for weights (all the way down); non-zero for sizes (one level)', 'C The running total', 'Output:C The total, $FF if it overflows')
R(0xD349, 'Input:IX A table of two-byte entries', 'A The id', 'Output:IX The entry found', 'F Z if found; NZ if the $FF end marker was reached')
R(0xD34E, 'Input:IX A table of three-byte entries', 'A The id', 'Output:IX The entry found', 'A The id, or $FF at the end marker', 'F Z if found')
R(0xD36A, 'Input:HL A word slot of the parse', 'IX The last thing found', 'Output:A The next matching thing, $FF if none', 'IX Its list entry')
R(0xD39B, 'Input:HL A word slot of the parse', 'IX The search position (a room number in B)', 'Output:A The next matching room, $FF if none', 'IX The search position')
R(0xD3D5, 'Input:IX A thing\'s record', 'Output:The thing\'s name printed; IY kept')
R(0xD3E8, 'Input:IY A thing\'s name words', 'Output:The name printed; A and DE kept')
S(0xD078, "Only actors with +4 bit 7 set (the player, and some others) can be in the dark.",
  "Follow the actor's containment chain ($C86E). A room with its light bit (+0 bit 7) is never dark; nor is anywhere by day (anything but night, $C00C).",
  "At night in an unlit room, look through all the things for a light: one that is in the actor's reach, alight (+5 passes the test) and shining (+4 bit 7). If one is found it is not dark.",
  "Otherwise return with carry set.")
S(0xD113, "Draw the room's picture if pictures are on and the room has one ($A277).",
  "If the actor is inside something (a cab, say), print 'YOU ARE IN' and how it is held ($D5D3) and its name ($D3D5).",
  "Print the room's own description ($D182), then list what can be seen.")
S(0xD36A, "Take the next thing from the index ($D206); when there are none left, return $FF.",
  "See whether the slot's words name it ($A4E0 against its name words at +7); if not, take the next.",
  "With $A038 set any match will do; otherwise it must also be visible to the actor ($C821).")

R(0xD405, 'Input:IY A thing\'s name words', 'Output:The name printed with its adjectives; A and DE kept')
R(0xD46C, 'Input:A A door number (entry $D46C) or a room number (entry $D471)', 'Output:F NZ with IX the exit if there is one; Z if not', 'BC, IY Kept')
R(0xD495, 'Input:A An actor number', 'Output:A The actor\'s room, or $FF if it is not an actor', 'IX The actor\'s record')
R(0xD4A7, 'Output:"YOU CAN SEE" and the people here listed; registers kept')
R(0xD4CC, 'Input:A A place', 'Output:A, B The number of things there to be listed', 'F Z if none')
R(0xD4EF, 'Input:A A place', 'IX A thing\'s list entry', 'IY Its record', 'Output:F Carry set if it should be listed')
R(0xD51A, 'Input:A A place', 'B, C As for $D526', 'Output:The things in the place listed; IY, DE, BC kept')
R(0xD526, 'Input:A A place', 'C The number of things to name', 'Output:The things named with commas and AND, each marked seen (+6 bit 7)')
R(0xD57C, 'Input:A A place', 'Output:A The next thing\'s id', 'F Carry set at the end; Z if it is thing 0')
R(0xD590, 'Input:A A thing', 'C How many things it holds', 'Output:"IS CARRYING" or IS/ARE with how it holds them printed')
R(0xD5D3, 'Input:IX The container\'s record', 'Output:The word IN, ON, BEHIND, UNDER or TIED TO printed', 'F Z if TIED')
R(0xD5EF, 'Input:A A room number', 'Output:IX The room\'s exits', 'BC 3, the size of an exit')
R(0xD5FB, 'Input:A A direction number (bit 7 ignored)', 'Output:DE The direction\'s word')
R(0xD60B, 'Output:The exits through revealed things described; registers kept')
R(0xD671, 'Input:IX An exit', 'BC 3', 'Output:IX The next plain exit', 'F Z at the end; NZ if found')
R(0xD68C, 'Input:A A room number', 'Output:"VISIBLE EXITS ARE" and the plain exits listed; registers kept')
R(0xD6BF, 'Output:F NZ if a line was typed; the turn fails if nothing was')
R(0xD6CE, 'Output:A The class byte', 'F NZ for a verb; Z with HL = $D6E5 for an unknown word')
R(0xD6E5, 'Output:The message "I DO NOT KNOW THE WORD" printed with the word')
R(0xD715, 'Output:The typed line split into a word list at $5B81')
R(0xD769, 'Output:F NZ')
S(0xD526, "First pass: name each listable thing in the place ($D57D), marking it as seen (+6 bit 7).",
  "After each name put a comma, but AND before the last two and a full stop after the last.",
  "Second pass: for each thing that holds others, say how it holds them ($D590) and list what it holds in the same way, going down the levels.")
S(0xD715, "Clear the page line count and put the text at full width ($C142). If '@' was typed, use the last word list again.",
  "Otherwise clear the 96-byte word list at $5B81 and read tokens from the typed line ($D9C5).",
  "Store each token's class; classes $E0, $F0, $90 and those below $80 are followed by a two-byte value.",
  "Continue until the end marker.")

R(0xD770, 'Input:$D6BD The next token', 'Output:F NZ if it is not the end of the line; otherwise the turn fails through $DC15')
R(0xD77E, 'Output:F NZ if a sentence parsed; Z if not', '$9FF2 The rest of the line')
R(0xD7D9, 'Output:F NZ')
R(0xD7E1, 'Output:F NZ if another sentence is waiting; otherwise the turn fails through $DC15')
R(0xD7FA, 'Input:$9FF2 The sentence', 'Output:$9FD6 The verb', '$9FD7 The objects', 'F Z if the sentence could not be made into a command')
R(0xD87D, 'Output:$9FF0 Empty; its nodes freed')
R(0xD88A, 'Output:$9FF2 Empty; its nodes freed')
R(0xD898, 'Output:F Z if nothing was typed in time; NZ if a line was typed')
R(0xD95C, 'Input:HL The end of the line buffer', 'B The count', 'Output:HL Past the closing quote', 'B One fewer')
R(0xD968, 'Input:HL Past the last character typed', 'B The count', 'Output:HL Past the end', 'B One fewer if a full stop was added')
R(0xD978, 'Input:A The key', 'HL The line buffer', 'Output:A $0D (ENTER) with N, E, S or W typed for a cursor key; the key itself for any other', 'HL Moved on', 'B One fewer')
R(0xD99E, 'Output:F NZ with $D714 set to 1, unless something has already been typed', 'A The key')
R(0xD9B7, 'Input:HL The line end', 'B The count (bit 7 set means finished)', 'Output:HL Back to the start', 'B Up to $80')
R(0xD9C5, 'Input:HL The typed line', 'Output:A, D The token class ($C0 end of line, $D0 not understood, $F0 number, and so on)', 'BC The token\'s value', 'HL Past the word', '$A029 Where the word started')
R(0xDA34, 'Input:HL The word', 'Output:DE The first dictionary record for the letter', '$DA32 Where its words end', 'F Z if there are none')
R(0xDA7D, 'Input:$5C0B The typed word', '$5C42 The candidate word', 'Output:The best match so far updated ($DC14)')
R(0xDAC6, 'Input:A The first character of the word', 'HL The word', 'Output:A The token class; BC its value; HL past it, for money, a number, full stop, comma or quote', 'F NZ for any other character')
R(0xDAE8, 'Input:A A character', 'Output:F Carry clear if it is a digit')
R(0xDAEF, 'Input:HL The number', 'Output:A $F0 (a number) or $D0 (not understood)', 'B, C The time, or 0', 'HL Past it')
R(0xDB56, 'Input:A A character', 'Output:F Z if it is a full stop, comma or space')
R(0xDB5F, 'Output:HL Back one', 'A $F0', 'F Z')
S(0xD9C5, "Skip spaces and remember where the word starts ($A029).",
  "A carriage return gives an end-of-line token ($C0).",
  "Characters that are not letters (the pound sign, digits, full stop, comma, quote) are read as their own tokens ($DAC6).",
  "Otherwise look up the dictionary words under the first letter ($DA34), spell each one out ($A94D) and compare it with the typed word ($DA7D), keeping the best match.",
  "A word that matches returns its class and word reference; no match gives a $D0 token.")
S(0xDA34, "The first letter (A = 1 to Z = 26) indexes the table of offsets at $5D80.",
  "DE is where that letter's words start in the dictionary. The next letter that has words marks where they end ($DA32).",
  "Return Z if there are no words under the letter.")
S(0xD7FA, "Carry the ALL flag over from the last turn and take the sentence at $9FF2.",
  "Parse it into a verb and objects ($B191). If that fails, set the failure flag and finish.",
  "Put the verb and objects in the plan registers ($9FD6, $9FD7), and note where the ALL search got to.",
  "If ALL is still going keep the sentence; otherwise unhook and free its node.")

R(0xDB67, 'Input:HL The text at the pound sign', 'Output:A $F0 (an amount) or $D0 (not understood)', 'BC The sum in the packed form', 'HL Past the amount')
R(0xDBF7, 'Input:HL A decimal number', 'Output:A The number', 'HL Past it', 'BC Kept')
R(0xDC15, 'Output:A 0', 'HL 0', 'F Z (failed)')
R(0xDC19, 'Input:$A034 The door', 'Output:F NZ (done); the room beyond described as seen through the door')
R(0xDC57, 'Input:IX The exit through the door', 'Output:The command turned into a movement; F From $DD07')
R(0xDC6C, 'Input:$A036 The actor', 'Output:F Z if the actor is 0, 1 or $64 (the player, Watson or the police cab); NZ for anyone else')
R(0xDC7B, 'Output:F NZ; the room described in full ($D102) when the actor is accepted by $DC6C')
R(0xDC8D, 'Input:$A013 The direct object\'s record', '$A017 The actor\'s record', 'Output:F NZ; the object\'s holder is now the actor\'s holder')
R(0xDCBB, 'Output:HL The message printed ($A59F)')
R(0xDCC1, 'Input:$A013 The target\'s record', '$A036 The actor', 'Output:F NZ; the target is now held by the actor')
R(0xDCD2, 'Input:$A033 The direction verb', 'Output:F NZ if the actor can go; otherwise the move is refused through $DC15', 'IX The exit')
R(0xDD03, 'Input:IX The exit found by the pre-check', 'Output:F NZ; the actor is in the new room')
R(0xDD61, 'Input:IX The exit found by the pre-check', 'Output:$9FD7 The exit\'s direction', 'F NZ')
R(0xDD84, 'Input:$A013 The direct object\'s record', 'Output:$9FD6 Its holder', 'F NZ; the pre-check refuses if it is held by nothing')
R(0xDD9E, 'Input:$A034 The person spoken to', 'Output:F NZ')
R(0xDDB4, 'Output:F NZ')
R(0xDDBE, 'Input:$A034 The number of minutes', 'Output:$A01F The minutes', 'F NZ')
R(0xDDD0, 'Input:$A02F The time typed', 'Output:$A01F The minutes to wait', 'F NZ')
R(0xDE6F, 'Input:$A036 The actor', 'Output:F NZ; "YOU ARE CARRYING" and the list, or NOTHING, printed')
R(0xDE9D, 'Input:$A013 The target\'s record', 'Output:F NZ; the target is open (+5 bit 5 set)')
R(0xDEAF, 'Input:$A013 The target\'s record', 'Output:F NZ; the target is closed (+5 bit 5 clear)')
R(0xDEC1, 'Input:IX The thing being moved', 'IY The container', 'Output:F NZ; the thing is in the container\'s room and held by it')
S(0xDD03, "The pre-check ($DCD2) finds the exit in the direction (the verb number), and refuses if there is none, the actor is inside something, the destination is 0 or the thing in the way will not let the actor through.",
  "The body sets the displayed room if the actor is the one followed, remembers the room entered ($DD01) and its record ($DCFF).",
  "The actor's own location (+15) becomes the new room, and the things it holds are updated ($D249).")
S(0xDDD0, "Take the time typed ($A02F) and work out the minutes past twelve for it ($DE48) and for the clock now.",
  "If am or pm was typed, the target is in that half of the day; otherwise it is in the same half as now, or the next.",
  "The difference is how long the action takes ($A01F).")

R(0xDED9, 'Input:$A013 The thing being put', '$A015 The container', '$A035 The container\'s id', 'Output:IX The thing', 'IY The container', 'F NZ if it fits; Z if it will not')
R(0xDF02, 'Input:$A013 The object\'s record', '$A015 The receiver\'s record', 'Output:F NZ; the receiver holds the object, in the receiver\'s room')
R(0xDF40, 'Input:$A034 The direct object', 'Output:F NZ; $CAAE 1; the description printed')
R(0xDF5B, 'Input:$A034 The direct object', 'Output:The thing marked seen (+6 bit 6) and its description, or "You see" and its name, printed')
R(0xDF8B, 'Output:F From $E000 (NZ)')
R(0xDFB6, 'Input:$A034 The direct object', 'Output:Continues at $E000, or at $DFCC on Monday for the wall safe')
R(0xDFCA, 'Output:The game ends through $9E74 with Basil\'s message')
R(0xDFEA, 'Output:F From $E007')
R(0xDFF0, 'Output:F From $E028')
R(0xE003, 'Output:F NZ; the actor is itself again and the disguise lies in the player\'s room')
R(0xE022, 'Output:F NZ; the actor is in disguise and the disguise is out of the world')
R(0xE03A, 'Input:A 1 to wear, 0 to take off', 'Output:$A017 The actor\'s new record', 'IX That record')
R(0xE0AD, 'Input:$A034 The direct object', '$A015 The indirect object\'s record', 'Output:F NZ; the rock revealed in room 88 on Tuesday')
R(0xE0EB, 'Output:F NZ; the torn note revealed ($9C56)')
R(0xE0FD, 'Output:F NZ; the false bottom revealed ($9C56)')
R(0xE104, 'Input:$A013 The bookcase\'s record', 'Output:F NZ; the bookcase swung away the first time')
R(0xE135, 'Input:$A034 The direct object', 'Output:F NZ; its description and any extra text printed')
R(0xE188, 'Input:$A035 The topic', 'Output:The statement at $9993 marked when the topic is the right one')
R(0xE1B2, 'Input:$A035 The topic', 'Output:F NZ; Tricia Fender becomes Mrs Jones if the topic is the clothes and they can be seen; otherwise $DC15')
R(0xE1D6, 'Input:$A036 The actor', '$A035 The topic', 'Output:F NZ; the answer printed, or the refusal if there is none')
R(0xE28D, 'Output:F Fails ($DC15) when the actor is the direct object')
R(0xE298, 'Input:$A034 The cab', 'Output:F NZ if the cab can be hailed here; otherwise refused ($DC15)')
R(0xE2C7, 'Input:$A034 The cab hailed', 'Output:F NZ; the cab moved to the player and the cabbie started on its fare script')
R(0xE2EE, 'Input:A The actor', 'DE The script', 'B, C The two objects', 'Output:F NZ; the actor\'s old script is kept as a sub-script and the new one started')

R(0xE31C, 'Input:$A013 The direct object\'s record', 'Output:F NZ if it can be counted (+6 bit 5); otherwise refused ($DC15)')
R(0xE328, 'Input:$A013 The money thing\'s record', 'Output:F NZ; "IT TOTALS" and the sum printed')
R(0xE36A, 'Output:HL The message printed ($A59F)')
R(0xE370, 'Input:$A036 The payer', '$A035 The payee', 'Output:F NZ; the payer\'s money reduced and the payee\'s increased by the sum')
R(0xE3B8, 'Input:$A034 The cab', 'Output:F NZ if the actor may get in; Z or $DC15 if not')
R(0xE3EA, 'Output:F NZ; the actor is held by the thing as for SIT IN')
R(0xE3F5, 'Input:$A034 The thing', 'Output:F NZ if the actor can sit on or get into it; Z if not')
R(0xE40A, 'Input:$A034 The thing', 'Output:F NZ; the thing is now the actor\'s holder')
R(0xE432, 'Input:$A013 The thing the actor is in', 'Output:F NZ; the actor is held by what held the thing')
R(0xE488, 'Input:$A013 The direct object\'s record', 'Output:$9FD6 The direct object\'s room', 'F NZ')
R(0xE497, 'Input:$A034 The thing', '$A035 The room', 'Output:F NZ; the thing is in the room, held by nothing')
R(0xE4C9, 'Input:$A034 The room number', 'Output:F NZ; the train moved there and the room\'s visited bit cleared')
R(0xE518, 'Input:IX The purse', 'Output:$9FD7 $FE', '$A02F The amount in the number form', 'F NZ')
R(0xE52F, 'Input:$A034 The fixed part', '$A035 The random part ($FF for none)', 'Output:F NZ; a countdown node (actor, n plus random) on the list at $9FE5')
R(0xE57A, 'Output:F NZ while the countdown runs; $DC15 when it runs out and is removed')
R(0xE588, 'Input:IX The actor\'s countdown node', 'Output:F NZ; the node unlinked and freed')
R(0xE5A8, 'Output:F NZ')
R(0xE5AD, 'Input:$A034 The thing', '$A035 The room', 'Output:F NZ if the thing is in that room; otherwise $DC15')
R(0xE5C1, 'Input:$A017 The thing to compare with', 'Output:F From $E5F0: NZ if the player is in the same room')
R(0xE5D8, 'Input:$A034, $A035 Two things', 'Output:F NZ if they are in the same room and are different; otherwise $DC15')
R(0xE5FD, 'Input:$A034 The direct object', 'Output:F NZ if it is with the actor; otherwise $DC15')
R(0xE63E, 'Output:F NZ if the cabbie holds a purse with a negative balance (a fare is owed); otherwise $DC15')
R(0xE654, 'Output:F NZ if the cabbie\'s purse holds a positive sum; otherwise $DC15')
R(0xE66F, 'Output:F NZ if the cabbie has no purse or its balance is zero; otherwise $DC15')
R(0xE6BC, 'Input:$A035 The cabbie', 'Output:F NZ; the fare named')
S(0xE3B8, "Run the checks for sitting on or getting into things ($E3F5: not busy, not already in it, will it fit).",
  "With the actor temporarily the thing after the cab (its driver), see whether the driver has a step in progress ($CFB6).",
  "If so, the thing at the cab's +3 and the actor must share one of bits 4 to 6 of +4, or the move is refused.")
S(0xE4C9, "The direct object is a room number. If it is Lestrade, Watson or Straker (things 2, 3, 4), print 'THE TRAIN PULLS OUT OF THE STATION.' and use the routine that clears the revealed flag ($9C60); otherwise the one that sets it ($9C56).",
  "Run that routine on the train, move the train to the room ($DD0E) and clear the visited bit of the room's record.")

R(0xE6E6, 'Input:$A034 The passenger', 'Output:F NZ; the cab\'s step record\'s +3 is the passenger', 'IX That record')
R(0xE70E, 'Output:F NZ; the cabbie\'s shout printed, if the player can see it')
R(0xE7E2, 'Output:F NZ')
R(0xEAF6, 'Input:$A034 The police cab', '$A015 The indirect object\'s record', 'Output:F NZ; the policeman is held by the cab and both are in room $32')
R(0xEB11, 'Output:F NZ if the statement at $99A9 is proven; Z if not', 'HL 0')
R(0xEB19, 'Output:F NZ if the statement at $9997 is proven; Z if not', 'HL 0')
R(0xEBD5, 'Input:$A034 The cab', 'Output:$9FD6 The cab\'s number plus 1', 'F NZ')
R(0xED39, 'Output:F NZ; the policeman revived (+5 bit 6 set)', 'IX The policeman\'s record')
R(0xEF9C, 'Output:F NZ; the message printed')
R(0xEFAC, 'Output:F NZ; the message printed')
R(0xEFB3, 'Input:$A036 The actor', 'Output:F NZ; the actor asleep, no longer a person to talk to')
R(0xEFC7, 'Input:$A009 The player\'s room', 'Output:F NZ; Phipps wakes, or shoots the player if the player is in Basil\'s house')
R(0xF103, 'Output:F NZ; the statement at $996F is established')
R(0xF198, 'Input:$A034 n', 'Output:F NZ when a random number from 1 to 99 is not above n; otherwise $DC15')
R(0xF1A8, 'Output:F NZ; the policeman knocked out')
R(0xF1C1, 'Input:A A thing number', 'DE The state word (0 for none)', 'B The high nibble for +8', 'Output:IX The thing\'s record', 'F NZ')
R(0xF1D6, 'Input:$A034 The hour, 1 to 24', 'Output:F NZ if the clock shows it; otherwise $DC15')
R(0xF1F6, 'Input:$A013 The direct object\'s record', 'Output:F NZ; the object visible (+5 bit 7 set)')
R(0xF203, 'Input:$A013 The thing\'s record', 'Output:F NZ; the thing unlocked')
R(0xF210, 'Input:$A013 The thing\'s record', 'Output:F NZ; the thing locked')
R(0xF389, 'Input:$A013 The direct object\'s record', 'Output:F NZ if it is held by the actor\'s number less 1 and is not the actor; otherwise $DC15')
R(0xF3C2, 'Input:HL The picture\'s bytecode', 'Output:The picture drawn; registers kept')
R(0xF490, 'Input:A The colour', 'DE The seed point', 'Output:The area around the seed filled; DE, HL kept')
R(0xF50D, 'Input:D, E The pen position', 'Output:F NZ if the pixel is set', 'HL Kept')
R(0xF54A, 'Input:E The pen\'s y', 'Output:E One more unless it would reach 176', 'F Z at the edge')
R(0xF555, 'Input:E The pen\'s y', 'Output:E One less unless it would go below 0', 'F Z at the edge')
R(0xF55E, 'Input:D The pen\'s x', 'Output:D One more', 'F Z at the edge')
R(0xF565, 'Input:D The pen\'s x', 'Output:D One less', 'F Z at the left edge')
R(0xF56E, 'Input:L The number of steps', 'B The run length before a step on the other axis', 'C The direction bits', 'D, E The pen', 'Output:D, E The pen after the line', 'BC, HL Kept')
R(0xF5FB, 'Input:D, E The pen position', 'Output:HL The screen byte', 'A The bit mask', 'BC Kept')
S(0xF3C2, "The pen starts at (127, 63). Take the next command; 0 ends the picture.",
  "$08 moves the pen to the (x, y) in the next two bytes (x always has bit 7 set, so the pen stays in the right half of the screen).",
  "A command with bit 7 set draws a line ($F56E): its low three bits give the direction, and the rest the number of steps and run lengths.",
  "Other commands set the colour, fill an area ($F490) or draw other shapes; each is followed by its operands.")
S(0xF490, "Keep the colour at $F60B and put a marker on the stack.",
  "From the seed, go left until the pixel is set or the edge is reached, colouring as it goes.",
  "Work along the lines above and below: the first clear pixel of each run of clear pixels is pushed as a seed for later.",
  "Pop seeds and repeat until the marker is reached.")
