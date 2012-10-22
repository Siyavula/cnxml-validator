# encoding: utf-8
from __future__ import division
import re
from lxml import etree
import sys, time

# --- START PREAMBLE ---

termColors = {
    'autosave': '\033[1m\033[34m', # bold blue
    'warning': '\033[1m\033[31m', # bold red
    'error': '\033[1m\033[31m', # bold red
    'passed': '\033[1m\033[32m', # bold green
    'failed': '\033[1m\033[31m', # bold red
    'old': '\033[1m\033[44m\033[37m', # bold white on blue
    'new': '\033[1m\033[44m\033[37m', # bold white on blue
    'context warning': '\033[1m\033[41m\033[37m', # bold white on red
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

if len(sys.argv) != 3:
    import os
    print termColors['error'] + 'ERROR:' + termColors['stop'] + ' Incorrect number of arguments.'
    print 'Usage: %s inputfile outputfile'%os.path.basename(sys.argv[0])
    sys.exit()
inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

with open(inputFilename, 'rt') as fp:
    xml = fp.read()
dom = etree.fromstring(xml)

numberAndCurrencyPattern = re.compile(r'(R ?)?[+-]?\d+( \d+)*([,\.]\d+( \d+)*)?')
for valid in ['1.3', '-1,3', '+100 000,99', '1000'] + ['R1.3', 'R-1,3', 'R +100 000,99', 'R 1000']:
    assert numberAndCurrencyPattern.match(valid).group() == valid, valid
for invalid in ['1.3a', ' 1.3', '1\n2'] + ['R1.3a', 'R  1.3', 'R 1\n2', '-R1.3']:
    match = numberAndCurrencyPattern.match(invalid)
    assert (match is None) or (match.group() != invalid), invalid
unitPattern = re.compile(r' *[a-zA-Z]{1,2}\b')
for valid in ['mm', ' cm', '  km']:
    assert unitPattern.match(valid).group() == valid, valid
for invalid in ['1mm', '1 cm']:
    match = unitPattern.match(invalid)
    assert (match is None) or (match.group() != invalid), invalid
latexUnitPattern = re.compile(r' *((\\textrm\{ *[a-zA-Z]{1,2}\})|(\\ell\b))')
for valid in [r' \textrm{ mm}', r'\textrm{  cm}', r'\textrm{km}', r'\ell', r'  \ell']:
    assert latexUnitPattern.match(valid).group() == valid, valid
for invalid in ['mm', ' cm', '  km', r'\ellb']:
    match = latexUnitPattern.match(invalid)
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

def prompt_replace(iOld, iNew, iContext=('',''), iContextWarning=(0,0)):
    print \
        termColors['bold'] + 'Replace: ' + termColors['stop'] +\
        iContext[0][:len(iContext[0])-iContextWarning[0]] +\
        termColors['context warning'] + iContext[0][len(iContext[0])-iContextWarning[0]:] + termColors['stop'] +\
        termColors['old'] + iOld + termColors['stop'] +\
        termColors['context warning'] + iContext[1][:iContextWarning[1]] + termColors['stop'] +\
        iContext[1][iContextWarning[1]:]
    print \
        termColors['bold'] + '   with: ' + termColors['stop'] +\
        iContext[0][:len(iContext[0])-iContextWarning[0]] +\
        termColors['context warning'] + iContext[0][len(iContext[0])-iContextWarning[0]:] + termColors['stop'] +\
        termColors['new'] + iNew + termColors['stop'] +\
        termColors['context warning'] + iContext[1][:iContextWarning[1]] + termColors['stop'] +\
        iContext[1][iContextWarning[1]:]
    sys.stdout.write('[y/n]? ')
    response = getch()
    if response == '\x03':
        # Catch Ctrl-C
        raise KeyboardInterrupt
    passed = response in ['y','Y']
    if passed:
        print termColors['passed'] + 'yes' + termColors['stop']
    else:
        print termColors['failed'] + 'no' + termColors['stop']
    sys.stdout.write('\n')
    return passed

def find_substitutions(iText, iNodeTag=None, iPreTailTag=None, iPostTailTag=None):
    global numberAndCurrencyPattern
    oSubstitutions = []
    for match in numberAndCurrencyPattern.finditer(iText):
        context = [None, None]
        contextLength = 20
        preContextWarning = 0
        postContextWarning = 0

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
            # Check if the pre-context is funny
            while (preContextWarning < contextLength) and (start-preContextWarning > 0) and ('a' <= iText[start-preContextWarning-1].lower() <= 'z'):
                preContextWarning += 1
        else:
            # Number
            newNode = etree.Element('number')
            newNode.text = oldNumber.replace(' ','').replace(',','.')
            # Check if the pre-context is funny
            offset = 0
            while (start-offset > 0) and (iText[start-offset-1] == ' '):
                offset += 1
            if (start-offset > 0) and (iText[start-offset-1] in '.,0123456789'):
                preContextWarning = min(contextLength, offset+1)
                while (preContextWarning < contextLength) and (start-preContextWarning > 0) and (iText[start-preContextWarning-1] in '.,0123456789'):
                    preContextWarning += 1
            # Check if the post-context is funny
            if iText[stop:stop+2] in ['st', 'nd', 'rd', 'th']:
                postContextWarning = 2
            else:
                # Check if there are units
                match = unitPattern.match(iText[stop:])
                if match is not None:
                    numberNode = newNode
                    newNode = etree.Element('unit_number')
                    newNode.append(numberNode)
                    newNode.append(etree.Element('unit'))
                    newNode[-1].text = match.group().strip()
                    oldNumber += iText[stop:stop+len(match.group())]
                    stop += len(match.group())
                else:
                    # Check if there are units in LaTeX mode
                    match = latexUnitPattern.match(iText[stop:])
                    if match is not None:
                        numberNode = newNode
                        newNode = etree.Element('unit_number')
                        newNode.append(numberNode)
                        newNode.append(etree.Element('unit'))
                        unitText = match.group().strip()
                        if unitText == r'\ell':
                            unitText = u'ℓ'
                        else:
                            assert unitText[:8] == r'\textrm{'
                            assert unitText[-1] == '}'
                            unitText = unitText[8:-1].strip()
                        newNode[-1].text = unitText
                        oldNumber += iText[stop:stop+len(match.group())]
                        stop += len(match.group())
        # Check if the post-context is funny (for both currency and number)
        if postContextWarning == 0:
            offset = 0
            while (stop+offset+1 < len(iText)) and (iText[stop+offset+1] == ' '):
                offset += 1
            if (stop+offset+1 < len(iText)) and (iText[stop+offset+1] in '.,0123456789'):
                postContextWarning = min(contextLength, offset+1)
            while (postContextWarning < contextLength) and (stop+postContextWarning+1 < len(iText)) and (iText[stop+postContextWarning+1] in '.,0123456789'):
                postContextWarning += 1

        if iNodeTag is not None:
            context[0] = '<' + iNodeTag + '>'
            if iPreTailTag is not None:
                context[0] += ' ... </' + iPreTailTag + '>'
        else:
            context[0] = ''
        if start < contextLength:
            context[0] += iText[:start]
        else:
            context[0] += ' ...' + iText[start-contextLength:start]
        if stop+contextLength > len(iText):
            context[1] = iText[stop:]
            if iPostTailTag is not None:
                context[1] += '<' + iPostTailTag + '>' + ' ... '
        else:
            context[1] = iText[stop:stop+contextLength] + '... '
        context[1] += '</' + iNodeTag + '>'

        if prompt_replace(oldNumber, etree.tostring(newNode, encoding='utf-8'), context, (preContextWarning, postContextWarning)):
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
        if len(iNode) > 0:
            postTailTag = iNode[0].tag
        else:
            postTailTag = None
        substitutions = find_substitutions(text, iNodeTag=iNode.tag, iPostTailTag=postTailTag)

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
    if iNode.getnext() is not None:
        postTailTag = iNode.getnext().tag
    else:
        postTailTag = None
    substitutions = find_substitutions(text, iNodeTag=myParent.tag, iPreTailTag=iNode.tag, iPostTailTag=postTailTag)
    for start, stop, replacement in sorted(substitutions, reverse=True):
        replacement.tail = iNode.tail[stop:]
        iNode.tail = iNode.tail[:start]
        myParent.insert(myIndex+1, replacement)
    auto_save()


# don't traverse top-level element
for child in dom.getchildren():
    traverse(child)

auto_save(force=True)
