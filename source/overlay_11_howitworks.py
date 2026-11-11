"""The high-level 'How Sherlock works' page (replaces the earlier engine summary)."""
from build_skeleton import PAGES

_MAP = [
    ('$5D80', '$5DBF', 'The dictionary index: where the words starting with each letter begin.'),
    ('$5DC0', '$67B6', 'The dictionary: 592 words, five bits to a letter.'),
    ('$67B7', '$8258', 'Every message the game prints, as bytecode.'),
    ('$8259', '$840A', 'The verb patterns: the verb number is the position in this table.'),
    ('$840B', '$8B6E', 'The room table and the 106 room records.'),
    ('$8B6F', '$956F', 'The entity index and the entity records: every person, object and door.'),
    ('$9570', '$985F', 'The node heap, 752 bytes, for the engine\'s own linked lists.'),
    ('$9860', '$9964', 'The actor table, the player\'s plan script and the case\'s relation words.'),
    ('$9965', '$9F37', 'The case table, and the routines that run when a statement is proved or a character has taken a turn.'),
    ('$9F38', '$A03F', 'The default action record for each verb, the table of script-only verbs and the game variables.'),
    ('$A040', '$A59E', 'Start-up and the main loop, the heap, the narration of commands.'),
    ('$A59F', '$AA70', 'The message interpreter, the word printer and the word-wrapping character printer.'),
    ('$AA71', '$B190', 'The shared action records and the parser.'),
    ('$B191', '$BA1F', 'Matching a typed command against the verb patterns; orders and remarks to other people.'),
    ('$BA20', '$BF78', 'Watson\'s and Lestrade\'s replies to what the player says: the case.'),
    ('$BF79', '$C492', 'The clock, saving and loading, the screen layout and the command window.'),
    ('$C493', '$CC0D', 'Carrying out a command: action records, checks and the report of what happened.'),
    ('$CC0E', '$D6BE', 'The actor\'s turn and the plan-script interpreter, the random numbers, light, and room descriptions.'),
    ('$D6BF', '$DC14', 'The player\'s turn: the line editor, the tokenizer and the number and money readers.'),
    ('$DC15', '$F3C1', 'Action records, sub-scripts and every character\'s plan script.'),
    ('$F3C2', '$F60A', 'The picture interpreter.'),
    ('$F60B', '$FFFF', 'Which rooms have a picture, and the picture data.'),
]

def _row(a, b, text):
    return ('<tr><td>#R%s</td><td>%s</td><td>%s</td></tr>' % (a, b.replace('$', '$'), text))

_HTML = (
 '<p>Sherlock (Melbourne House, 1984) is a text adventure written as one block of Z80 code and data that loads at '
 '$5D80 and starts at #R$A040. The game is a clockwork: every person, including the player, is an <i>actor</i> that '
 'runs a small program, and a single loop gives each actor a turn as the minutes go by. Almost nothing is special-cased '
 'for the player.</p>'
 '<h3>Memory map</h3>'
 '<table class="map"><tr><th>From</th><th>To</th><th>What is there</th></tr>' +
 ''.join(_row(*r) for r in _MAP) + '</table>'
 '<h3>A turn</h3>'
 '<p>The main loop (#R$A064) is one minute of game time per pass. It advances and prints the clock (#R$BFD9, #R$BF79), '
 'then walks the actor table at #R$9860 and gives a turn to every actor whose next-turn time has come. A turn begins '
 'by finding the actor (#R$CC0E) and asking whether an order or remark is waiting for it (#R$CC37, #R$B91F). If so '
 'that is dealt with first (#R$B936). Otherwise the actor\'s plan script runs one step at a time (#R$CC78) until a '
 'step takes time. The minutes it took are added to the actor\'s next-turn time and the actor\'s own after-turn '
 'routine, if it has one, runs (#R$9C77). Typing WAIT costs the player five minutes; TAKE LAMP costs one. '
 'When the game ends, #R$9E74 prints the ending and the game starts again.</p>'
 '<p>The player is actor 0. The player\'s plan script (#R$9921) reads a line from the keyboard with a time limit '
 '(#R$D898) and WAITs if nothing is typed, splits the line into words (#R$D715), parses one sentence (#R$AAB2) and '
 'carries it out. A line of several sentences is worked through one a minute. Typed words are first turned into '
 'tokens (#R$D9C5): dictionary words, numbers, clock times and old-style money such as 2/6 (#R$DB67).</p>'
 '<p>A command, typed or from a script, is a verb and up to two objects. #R$B191 matches the words against the verb '
 'patterns; #R$C4D1 finds the action record to use. A verb has a default record (#R$9F38) and an object can have '
 'its own list of shared records (#R$AA71). The record is run by #R$C9BF: it names what each object must be (here, '
 'carried, a person, a door, a number: #R$C628), tests flags on the objects, may call a pre-check routine, and then '
 'runs either a body of code or a sub-script. Afterwards #R$CA60 reports what the player sees: the command as a '
 'sentence (#R$A2E4), a new room (#R$CA7F) or someone arriving (#R$CAAF).</p>'
 '<h3>The world</h3>'
 '<p>Things, people and doors are entity records (#R$8CBA), found through an index (#R$8B6F). Each has a holder '
 '(a room, another thing, or a person), flags such as visible, a person, open, locked and seen, and a room. '
 'Rooms are records of their own (#R$84E1) with their exits. Whether the player can see is decided by #R$D078: '
 'outdoors between eight in the evening and six in the morning the player needs a light, and the oil lamp is '
 'lit from the start. #R$D0DD builds the description of the room the player is in.</p>'
 '<p>The engine also needs lists that grow and shrink while the game runs: orders and remarks waiting for '
 'actors, tokens from the typed line, countdowns, sub-script call frames. They are linked lists in a small '
 'heap (#R$9570) managed by #R$A11C and #R$A1C7.</p>'
 '<h3>The characters</h3>'
 '<p>Every character\'s behaviour is a plan script in a small bytecode that #R$CC78 interprets: DO a command, '
 'RUN an action record, ASK someone to do something, SAY or PRINT a message, SIGNAL and AWAIT another '
 'character, RETURN from a sub-script, PASS, GOTO. Each step can branch on success or failure. A step that '
 'succeeds after taking time ends the actor\'s turn; a failure moves on to the next step at once, so a step '
 'that fails to itself means "wait here until this works". Verbs from 128 up (#R$9FAB) exist only for scripts: '
 'they test where people are, the hour and chance, and move things about.</p>'
 '<p>Because characters use the same commands as the player, they can do what the player can: open doors, '
 'take cabs and trains, follow someone, and be given orders. SAY TO a person hands them what was said '
 '(#R$B86A). Some steps are marked busy, and a character on one of them refuses what the player asks '
 '(#R$CBA7). Each of nine characters also has an after-turn routine (#R$9C85) for greetings, warnings and '
 'the like. See <a href="cast.html">The cast and their scripts</a> for every script.</p>'
 '<h3>Text</h3>'
 '<p>Dictionary words are stored five bits to a letter (#R$A880 unpacks them), so a typed word is looked up '
 'through the per-letter index at #R$5D80. Messages are small programs (#R$A59F runs them): ordinary bytes '
 'are letters, bytes from $60 up stand for common words, and control codes handle things like choosing one of '
 'several phrases at random (#R$A6D3), articles (#R$A7EB), capital letters and what a character says. The '
 'parameters of a message are pushed on the stack before the call. Output goes through a word-wrapping '
 'printer (#R$A9B7) and a character routine that writes to the screen (#R$AA14); the command window echoes '
 'what is typed (#R$C1FC).</p>'
 '<h3>Pictures</h3>'
 '<p>Fourteen rooms have a picture, drawn when the player arrives from a compact list of drawing commands '
 '(#R$F3C2): move the pen, draw a line (#R$F56E), fill an area (#R$F490), colour blocks of attributes. Rooms '
 '54 and 55 share one picture. See <a href="pictures.html">The pictures</a>.</p>'
 '<h3>Chance</h3>'
 '<p>The random number generator (#R$D2AD) is seeded from the Z80 refresh register at the first keypress. '
 'It steps a pointer through memory and mixes the bytes it finds, never giving the same number twice running. '
 'Script chances (#R$F198), countdowns and the greeting delays of the after-turn routines all use it.</p>'
 '<h3>The case</h3>'
 '<p>The solution is data. #R$9965 lists statements such as MRS BROWN KILLED HERSELF, each with the evidence '
 'needed to prove it: things the player must have seen or examined, or markers that only the game can set. '
 'Telling Lestrade a statement (#R$BB67) proves it if the evidence is there and runs the statement\'s routine '
 '(#R$99FC); otherwise it waits and is proved as soon as the evidence is complete (#R$BC46). Telling Watson '
 '(#R$BA67) only makes him remember it. Lestrade must be met, with Chief Constable Straker, by three on '
 'Monday afternoon (#R$9DFF). The endings depend on what has been proved (#R$9EA2, #R$9E85) and on who is '
 'with the player when Basil arrives (#R$9E48). See <a href="the-case.html">The case</a> for every statement '
 'and its evidence.</p>'
 '<h3>Saving</h3>'
 '<p>The game state is one block of 7,188 bytes from #R$840B to $A01F: the room and entity records, the heap, the '
 'actor table, the case table and the game variables. SAVE (#R$B0C6) sets a flag, and at the end of that minute the '
 'main loop writes the block to tape (#R$B0E4, #R$C040) and checks it. LOAD, and a game that has ended, read '
 'the block back (#R$B0D7) and start again from #R$A040.</p>'
)

for i, (pid, title, html) in enumerate(PAGES):
    if pid == 'how-it-works':
        PAGES[i] = (pid, 'How Sherlock works', _HTML)
