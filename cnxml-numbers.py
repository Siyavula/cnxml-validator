from __future__ import division
import re
from lxml import etree
import sys, time

# --- START PREAMBLE ---

termColors = {
    'autosave': '\033[1m\033[34m', # bold blue
    'warning': '\033[1m\033[31m', # bold red
    'passed': '\033[1m\033[32m', # bold red
    'failed': '\033[1m\033[31m', # bold red
    'old': '\033[47m\033[30m', # inverted black/white
    'new': '\033[47m\033[30m', # inverted black/white
    'bold': '\033[1m',
    'stop': '\033[0m',
}

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

# --- END PREAMBLE ---

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

with open(inputFilename, 'rt') as fp:
    xml = fp.read()
dom = etree.fromstring(xml)

numberAndCurrencyPattern = re.compile(r'(R ?)?[+-]?\d+( \d+)*([,\.]\d+( \d+)*)?')
for valid in ['1.3', '-1,3', '+100 000,99', '1000'] + ['R1.3', 'R-1,3', 'R +100 000,99', 'R 1000']:
    assert numberAndCurrencyPattern.match(valid).group() == valid
for invalid in ['1.3a', ' 1.3', '1\n2'] + ['R1.3a', 'R  1.3', 'R 1\n2', '-R1.3']:
    match = numberAndCurrencyPattern.match(invalid)
    assert (match is None) or (match.group() != invalid), invalid

autoSaveTime = time.time()
autoSaveInterval = 60 # seconds
def auto_save(force=False):
    global dom, outputFilename, termColors, autoSaveTime, autoSaveInterval
    if force or (time.time()-autoSaveTime >= autoSaveInterval):
        sys.stderr.write(termColors['autosave'] + 'Auto saving...' + termColors['stop'])
        with open(outputFilename, 'wt') as fp:
            fp.write(etree.tostring(dom, xml_declaration=True, encoding='utf-8'))
        sys.stderr.write(termColors['autosave'] + ' done.\n' + termColors['stop'])
        autoSaveTime = time.time()

def prompt_replace(old, new, context=('','')):
    print termColors['bold'] + 'Replace: ' + termColors['stop'] + context[0] + termColors['old'] + old + termColors['stop'] + context[1]
    print termColors['bold'] + '   with: ' + termColors['stop'] + context[0] + termColors['new'] + new + termColors['stop'] + context[1]
    sys.stdout.write('? ')
    response = getch()
    if response == '\x03':
        # Catch Ctrl-C
        raise KeyboardInterrupt
    sys.stdout.write('\n')
    passed = response in ['y','Y']
    if passed:
        print termColors['passed'] + 'yes' + termColors['stop']
    else:
        print termColors['failed'] + 'no' + termColors['stop']
    return passed

def find_substitutions(iText, iNodeTag=None, iTailTag=None):
    global numberAndCurrencyPattern
    oSubstitutions = []
    for match in numberAndCurrencyPattern.finditer(iText):
        start, stop = match.span()
        oldNumber = iText[start:stop]
        if oldNumber[0] == 'R':
            # Currency
            newNode = etree.Element('currency')
            newNode.append(etree.Element('number'))
            newNode[0].text = oldNumber[1:].replace(' ','').replace(',','.')
            # Check whether we need to use a non-default precision
            pos = newNode[0].text.find('.')
            if (pos != -1) and (pos < len(newNode[0].text)-3):
                newNode.attrib['precision'] = str(len(newNode[0].text) - pos - 1)
        else:
            # Number
            newNode = etree.Element('number')
            newNode.text = oldNumber.replace(' ','').replace(',','.')
            pass

        # TODO: also find units

        context = [None, None]
        contextLength = 20
        if iNodeTag is not None:
            context[0] = '<' + iNodeTag + '>'
            if iTailTag is not None:
                context[0] += ' ... </' + iTailTag + '>'
        else:
            context[0] = ''
        if start < contextLength:
            context[0] += iText[:start]
        else:
            context[0] += ' ...' + iText[start-contextLength:start]
        if stop+contextLength > len(iText):
            context[1] = iText[stop:]
        else:
            context[1] = iText[stop:stop+contextLength] + '... '
        context[1] += '</' + iNodeTag + '>'

        if prompt_replace(oldNumber, etree.tostring(newNode), context):
            oSubstitutions.append((start, stop, newNode))

    return oSubstitutions

mathmlWarningIssued = False
def traverse(iNode):
    global mathmlWarningIssued, termColors

    if iNode.tag in ['unit_number', 'number', 'currency', 'percentage', 'unit', 'metadata', 'shortcode', 'linked-concepts', 'marks', 'url', 'width', 'height', 'embed', 'pspicture', 'tikzpicture', 'src', '{http://www.w3.org/1998/Math/MathML}math', 'chem_compound', 'spec_note', 'nuclear_notation', 'nth', '{http://www.w3.org/2005/11/its}rules']:
        if (not mathmlWarningIssued) and (iNode.tag == '{http://www.w3.org/1998/Math/MathML}math'):
            sys.stderr.write(termColors['warning'] + 'WARNING: Found (and ignored) MathML\n' + termColors['stop'])
            mathmlWarningIssued = True
    else:
        # check text for regex matches
        text = iNode.text or ''
        substitutions = find_substitutions(text, iNode.tag)

        # traverse children (traverse before replacing to avoid double-checking text)
        for child in iNode.getchildren():
            traverse(child)

        # replace text with new elements
        for start, stop, replacement in sorted(substitutions, reverse=True):
            replacement.tail = iNode.text[stop:]
            iNode.text = iNode.text[:start]
            iNode.insert(0, replacement)
        auto_save()

    # check tail for regex matches
    myParent = iNode.getparent()
    myIndex = myParent.index(iNode)
    text = iNode.tail or ''
    substitutions = find_substitutions(text, iNodeTag = myParent.tag, iTailTag = iNode.tag)
    for start, stop, replacement in sorted(substitutions, reverse=True):
        replacement.tail = iNode.tail[stop:]
        iNode.tail = iNode.tail[:start]
        myParent.insert(myIndex+1, replacement)
    auto_save()


# don't traverse top-level element
for child in dom.getchildren():
    traverse(child)

auto_save(force=True)
