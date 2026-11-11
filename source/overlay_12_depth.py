"""Depth pass (9 November): step-by-step explanations and register notes for the larger routines.
Each entry says what the routine takes, what it gives back, and walks through the logic in the order the
code does it. Steps are read from the instructions at the addresses given."""
from build_skeleton import A


def deepen(addr, steps, regs=None, intro=None):
    a = A[addr]
    d = a.setdefault('desc', [])
    new = []
    if intro:
        new.append(intro)
    new.append('How it works:')
    new.extend('%d. %s' % (i + 1, s) for i, s in enumerate(steps))
    d.extend(new)
    if regs is not None:
        a['regs'] = regs


deepen(0xA1C7, [
    "Save HL and DE, and work out where the freed block starts: three bytes before the node in IX.",
    "Walk the list of free blocks from its head at $9FE3. The list is kept in address order, so stop at the first free "
    "block that lies above this one, or at the end of the list.",
    "Link the block in at that point: the previous link now points at it, and its own link points at the block that came after.",
    "Try to join it to the free block that follows it ($A20C). If the freed block joined onto the one before it instead, "
    "step back to that block and try again to join it to what follows."],
    ['Input:IX The node to free', 'IX is not preserved'])

deepen(0xA20C, [
    "Work out the address just past this free block: its start plus the size held in its first two bytes.",
    "Read the link to the next free block. If there is none, return NZ.",
    "If the next free block does not start at exactly that address, return NZ: there is a gap between them.",
    "Otherwise add the next block's size to this one's and take over the next block's link, which unhooks it from the "
    "list, and return Z."],
    ['Input:IX The link field of a free block (its size is the word before it)',
     'Output:F Z if the next free block was joined on, NZ if not'])

deepen(0xC6BE, [
    "Take the indirect object's requirement code from the low nibble of byte 1 of the record. Zero means no requirement: pass.",
    "Codes 5 and 6 want a number (the parser's number marker is $FE, the value in $A031): code 5 needs bit 7 of the "
    "value clear, code 6 needs it set.",
    "Codes 1 and 2 want a room whose record has bit 7 of its first byte set; codes 1 and 3 also want the room to be "
    "next door to the actor ($D471).",
    "Codes 7 to 15 are handed to $C7A6 along with the object's id, which is also stored at $CB7A so that a refusal can name it.",
    "If the record's flags have bit 4 set, the objects' +5 flag bytes are then tested against the masks in the record's "
    "header ($C74E). A failure there sets $A021 and refuses."],
    ['Input:IY The action record', 'Output:F NZ if the indirect object is acceptable, Z if refused (the refusal is printed by $DC15)'])

deepen(0xC7A6, [
    "Mask the code to its low nibble. Codes 7 to 15 split into six groups; each ends by jumping to the pass at $C62F or "
    "the refusal at $C632.",
    "Code 7: anything will do. Code 8: the object must be in the actor's room ($C821).",
    "Code 9 (TAKE): in the room; in exactly one place ($C8A7), so doors and the like are out; not a person ($C8BE); of a "
    "size the actor can carry ($C8C6); and not already held by a person ($C8AF).",
    "Code 10: in the room and held by the actor ($D275). Code 11: in the room and in more than one place, which is what "
    "a door is. Code 12: a person anywhere. Codes 13 to 15: a person who is in the room."],
    ['Input:A The requirement code (7-15)', 'C The object\'s id', 'IY The action record',
     'Output:F NZ if the object passes, Z if it is refused'])

deepen(0xBE91, [
    "If the evidence is already marked done (bit 1 of its flags), it holds: finish.",
    "The top two bits of the flags give the kind. Kind 0: both things named in the record must have been seen by the "
    "player (bit 7 of their +6 flags); if so it holds. Kind $80 is a marker that only some other routine can set, "
    "so it never holds by itself.",
    "Kind $40: both things must have been examined (bit 6 of +6). Then, as for kind $C0 (which has no test of its own), "
    "it holds only if it has no children, or if all of its children hold ($BF08).",
    "When it holds, mark it done (bit 1 set, bit 0 clear) and return NZ."],
    ['Input:IX An evidence record in the case table', 'Output:F NZ if it holds, Z if not'])

deepen(0xD2AD, [
    "Set the limit C to A and work out B, twice the limit (255 if that overflows).",
    "Step the pointer at $A039 on through memory and fetch the byte it points at.",
    "Mix that byte, and the byte after it, into the last result at $A037. If the answer equals the last result, step on and try again, "
    "so the same number never comes up twice running.",
    "Halve the answer until it is no larger than B, then subtract C. The result is a signed number from -C to +C."],
    ['Input:A The limit', 'Output:A A pseudo-random number from -limit to +limit (as a signed byte)'])

deepen(0xF514, [
    "Each of the four entry points moves HL, the address of an attribute byte, one cell: $F514 up a row, $F525 down a row, "
    "$F536 left and $F540 right.",
    "A row is 32 bytes. After the move the high byte is checked against the edges of the attribute area ($5800 to $59FF): "
    "if the move left it, it is undone, so the address never leaves the screen."],
    ['Input:HL An attribute address', 'Output:HL The address one cell on, or unchanged at the edge', 'AF is preserved'])

deepen(0xF5D2, [
    "Find the screen byte and bit for the pixel at (D, E) ($F5FB).",
    "Work out the attribute byte for that character cell.",
    "Keep the cell's paper and set its ink to the pen colour at $F60B. If the paper is already that colour, use the opposite ink so the pixel shows.",
    "Set the pixel itself."],
    ['Input:D X coordinate', 'E Y coordinate', 'HL is preserved; A and F are not'])

deepen(0xBD51, [
    "Start at the first record of the case table ($9965), or - from $BD4B - at Watson's own list ($9A7D).",
    "A first byte of $FF ends the table: return NZ.",
    "Compare the record with the statement being looked for: its relation ($BA1A) with byte +1, then its subject "
    "($BA19) with +0, then its object ($BA1B) with +2. All three must match.",
    "On a match return Z with IX at the record; otherwise step to the next record ($BE5A), skipping any evidence records "
    "that belong to this one, and repeat."],
    ['Input:$BA19 The statement\'s subject', '$BA1A Its relation', '$BA1B Its object',
     'Output:F Z if found, NZ if not', 'IX The record, if found'])

deepen(0xBCC9, [
    "If the statement has evidence (flags bit 2), check all of it ($BF08). If any is missing, return NZ: not proved.",
    "If flags bit 5 is set, the statement is only marked as waiting (bit 0 set) and Z is returned. It will be settled later by $BC46.",
    "Otherwise mark it proved (bit 1 set, bit 0 clear). If bit 4 is set, run its routine at +4/+5 ($D1DB): the routines "
    "from $99FC on, which print what Lestrade or Watson says and may set a marker.",
    "Return Z: proved."],
    ['Input:IX The statement record', 'Output:F Z if proved (or marked as waiting), NZ if the evidence is not all there'])

deepen(0xAA14, [
    "A capital letter becomes lower case; everything else is passed on as it is.",
    "A space at the start of a line is dropped ($A025 is zero until the first real character of the line).",
    "A carriage return starts a new line. A quote mark gets a space put in front of it. A quote mark or a full stop sets $A026, "
    "so the next letter will be a capital.",
    "A lower-case letter becomes a capital if the all-capitals flag $A851 is set or $A026 is set; $A026 is cleared as it is used.",
    "Pass the character to the screen layer ($C1E1)."],
    ['Input:A The character'])

deepen(0xAFB3, [
    "Pick the table: the twelve special words at $AF6B, or - when the parser is reading speech ($A024 = 2) - only the "
    "last six, from $AF9B.",
    "Each entry is four bytes: a dictionary word reference followed by the address of a handler. Compare the word in BC with "
    "each entry in turn.",
    "No match: return NZ, and the word is an ordinary one.",
    "A match: take the handler's address and jump to it. The handler does the work and returns to the parser's caller."],
    ['Input:BC The word reference', 'Output:F NZ if the word is not special (otherwise the handler runs)'])

deepen(0xCBC2, [
    "Do nothing if the thing is $FF or 0 (nobody).",
    "Find which room the thing is in ($D495). If it is not the room the player is looking at ($A009), do nothing.",
    "Otherwise switch printing on and climb from the thing to whatever holds it at the top, a cab for example, so that the "
    "message is about the outermost holder.",
    "Make the player the current actor for a moment and ask whether the player can see that holder ($C821). If not, return "
    "without printing.",
    "If so, put the real actor back and print message DE with the holder's name as its subject ($A59F)."],
    ['Input:A The thing', 'DE The message', 'Output:Nothing is printed unless the player can see the thing'])

deepen(0xCF80, [
    "Allocate a seven-byte node from the heap ($A11C).",
    "Fill it in: the actor ($A036); HL, where the script should carry on after the sub-script; the command's two objects "
    "($A034, $A035); B; and the plan's verb ($9FD6).",
    "Link the node in at the head of the list of call frames at $9FE9.",
    "The same block has two more entry points. $CFB6 finds the current actor's frame by walking the list: NZ with IX at the "
    "frame, or Z if there is none. $CFCF is the return: it finds the frame, sets the actor's script position back to the "
    "calling instruction, unlinks and frees the frame ($A1C7), reloads the plan registers ($D008) and returns the saved byte "
    "in A."],
    ['Input:HL Where to come back to', 'B A byte to keep (returned in A by $CFCF)'])

deepen(0xBF79, [
    "Write the three-letter day name into the buffer at $BF6E, choosing it from the table at $BF59 by the day number ($9FE1).",
    "Write the hour ($9FE0) and the minute ($9FDF) as two digits each, found by repeated subtraction of ten ($BFBB), with the "
    "space and colon already in the buffer.",
    "Write the letter a or p ($9FE2) and print the eleven characters, for example 'Mon 08:02am', in the status bar ($C1A8)."],
    ['No registers are used on entry'])

deepen(0xAAB2, [
    "Clear the sentence count and start with every kind of word allowed (E = $FF).",
    "Decide the sentence's mode ($A024). If a line of sentences is still being worked through it is an ordinary command "
    "(mode 1). Otherwise try to read a noun phrase first ($AC24): a sentence that opens with one and has no preposition is "
    "a statement such as MRS JONES KILLED TRICIA FENDER (mode 2, subject kept in the parse node); anything else is a "
    "command (mode 1) and reading starts again from the beginning.",
    "Read the verb and its particles ($AB91). Carry means the words make no sense.",
    "A special word (token class $90) goes to $AFB3. A comma ($A0) starts another sentence ($ACCC).",
    "Read the objects: each noun phrase ($AC24) is filed in the parse node ($ACA6), and this repeats as long as noun phrases follow.",
    "A full stop ($B0) completes the sentence ($AD57). In a statement, any other word must be a relation word ($ABF3), which "
    "ends the subject and carries on with the object.",
    "Anything else makes no sense: return NZ ($AF67)."],
    ['Input:IY The parse node for the sentence', 'Output:F NZ if the sentence makes no sense (A = 2 for a stray full stop)'])

deepen(0xBDC2, [
    "Start both searches at the top of the thing index ($D04F).",
    "Look the remark's verb word up in the list of relation words at $994D. Its position in that list (counting from 1) is "
    "the statement's relation. If it is not there the remark is not a statement: return Z.",
    "Allow things that are not in the room to be named ($A038 = 2).",
    "Find the thing that matches the subject words ($BE3C). None means it is not a statement. A second match means the "
    "subject is ambiguous: return carry. Otherwise remember it and copy its six-byte entry to $9FF6 if it is a person or "
    "$9FFC if not ($BE22), so that HE, IT and THEY can refer to it later.",
    "Do the same for the object words ($BE4B).",
    "Return NZ: the statement's subject, relation and object are in $BA19, $BA1A and $BA1B."],
    ['Input:$BA17 The remark\'s verb word', 'Output:F NZ if it made a statement, Z if it is not one', 'Carry set if a name was ambiguous'])

deepen(0xB39D, [
    "Take the verb's word reference from the parse node. Bit 7 of it says ALL was typed with the verb; keep that in $B39C and clear it.",
    "Build the pattern to match at $B186-$B18D: the verb word, the particle at node +2 (CLOSELY, FURIOUSLY, a direction), "
    "and up to two more words from the node's other slots ($B483).",
    "Walk the eight-byte verb records from $8259, comparing each with the pattern ($A4CD).",
    "On a match, fill the object slots ($B405) and return NZ. If the zero record that ends the table is reached, return Z."],
    ['Input:IY The parse node', 'Output:F NZ if a verb record matched, Z if none did'])

deepen(0xD8AD, [
    "Print the prompt '> ' and set up the buffer at $5B00; B counts down from 128, with bit 7 set while nothing has been typed.",
    "Wait for a key with the time limit ($A536). If time runs out, give up: the player will wait.",
    "On an empty line, '@' repeats the last command ($D99E). The first key of a line may be a cursor key, which is turned "
    "into a one-key move ($D978).",
    "Rub-out ($18) clears the whole line; DELETE removes one character, and removing a quote mark flips the inside-quotes flag.",
    "Letters are taken. A quote mark flips the flag (closing a quotation first ends it with a full stop). Space, full stop, comma, "
    "slash, the pound sign, hyphen, colon and digits are taken. Anything else is ignored.",
    "ENTER closes any open quotation, ends the line with a full stop ($D968) and a carriage return, and returns NZ."],
    ['Output:F NZ if a line was typed, Z if the wait timed out', 'HL The end of the line in the buffer at $5B00'])

deepen(0xA37D, [
    "Look up the remembered command's verb record and flags ($A2B1, $A2BD, $C493, $C4B2).",
    "Print the verb's words: the pair at +6 of the record, then the pair at +0 ($A880).",
    "If the verb takes a direct object (flags bit 3): print any word that goes before it, then the object itself - a number or "
    "sum of money ($A419) if it is one, ME if it is the actor, or its name ($A745).",
    "If there is an indirect object and the flags allow one: print its preposition, then the object the same three ways.",
    "End with a full stop. The result is a sentence such as 'You pay 2/6 to Watson.'"],
    ['Input:$A35D The remembered command: verb, direct object, indirect object'])

deepen(0xACFB, [
    "In statement mode ($A024 = 2), do this once only: copy the node's first group of six bytes (+8) to the third group (+24), "
    "so the subject can be shared, and read on for the object ($AB4C).",
    "In command mode, if $A01B is set (a line of sentences is being worked through), just read on.",
    "Otherwise go back to the start of the sentence, whose position, flags, sentence count and node were saved by $ACCC, "
    "free the nodes that were made after it ($A1AF) and unhook them, ready to read the sentence again."],
    ['Input:E The flags for what may come next', 'IY The parse node'])

deepen(0xAD57, [
    "Count the sentence in $A012, except for a comma in statement mode.",
    "A comma ($A0) goes back to read another sentence ($AABD).",
    "If a line of several sentences is being worked through ($A01B set): if the second node has no verb of its own, carry its "
    "verb flag into the first node and fill the first node's empty word slots from the second ($AE59). Then drop the first node "
    "of the list.",
    "Go through the sentences from the start. In a statement whose third group is empty, take the previous sentence's group. "
    "A sentence with no verb is merged into the previous one ($AEF1).",
    "Then go backwards from the last sentence: where an earlier sentence has the same verb as a later one and no second group of "
    "its own, copy the later sentence's second group into it ($AF27). So EXAMINE LAMP AND YOUR ARMCHAIR is understood as two commands "
    "with the same verb. The loop never compares the last pair; see the Bugs page.",
    "Return Z: done."],
    ['Input:D The token class last read', 'E Flags', 'Output:F Z when the sentences have been tidied'])

A[0xB77F]['desc'] = [
    "Fetch the next word of a message for $B6FD's name match. $B77E is $FF once the last word of the message has been given out.",
    "How it works:",
    "1. If $B77E is $FF, the message is finished: take the most recent saved call position from the list headed at $B6D6 "
    "(none left: return Z), unhook it, free its node ($A1C7) and carry on reading just after the call.",
    "2. Read the next byte. If bit 7 is set it starts a two-byte dictionary reference, which is put in DE. If its class "
    "($70 bits) is $60, $30 or $20 it is the last word of the message, so $B77E is set to $FF. Return NZ with the word in DE.",
    "3. Below $20 is a control code. Code 2 is a jump: add the 16-bit offset to the position and carry on. Code $0B is a call: "
    "make a 2-byte node holding the position after the call, put it on the front of the list at $B6D6 and go to the sub-message. "
    "Codes $1D to $1F end the text. Other codes are skipped.",
    "4. $20 to $5F is a run of packed letters, (byte AND $1F) + 1 of them at five bits each ($A990); they are stepped over, "
    "not returned.",
    "5. $60 and above is one of the common words ($A840): return NZ with A = 0."]
A[0xB77F]['regs'] = ['Input:IX The message position', 'Output:F Z when no words are left; NZ when a word was found',
                     'DE The dictionary reference when A is not 0', 'IX The position after the word']
