# encoding: utf-8
from __future__ import division
import re
from lxml import etree
import sys, time
from utils import get_full_dom_path

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

arguments = sys.argv[1:]
if len(arguments) != 1:
    import os
    print termColors['error'] + 'ERROR:' + termColors['stop'] + ' Incorrect number of arguments.'
    print 'Usage: %s inputfile'%os.path.basename(sys.argv[0])
    sys.exit()
inputFilename = arguments[0]

with open(inputFilename, 'rt') as fp:
    xml = fp.read()
dom = etree.fromstring(xml)

# Make backup
with open(inputFilename + '~', 'wt') as fp:
    fp.write(xml)

marksPattern = re.compile(r'\(\d+\)')
for valid in ['(1)', '(13)', '(1000099)']:
    assert marksPattern.match(valid).group() == valid, valid
for invalid in ['(13a)', ' (13)', '(13) ', 'a(1)', '1']:
    match = marksPattern.match(invalid)
    assert (match is None) or (match.group() != invalid), invalid

autoSaveTime = time.time()
autoSaveInterval = 60 # seconds
def auto_save(force=False):
    global dom, termColors, autoSaveTime, autoSaveInterval
    if force or (time.time()-autoSaveTime >= autoSaveInterval):
        sys.stderr.write(termColors['autosave'] + 'Auto saving...' + termColors['stop'])
        with open(inputFilename, 'wt') as fp:
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

def find_substitutions(iText, iNode=None, iPreTailTag=None, iPostTailTag=None):
    global marksPattern
    oSubstitutions = []
    for match in marksPattern.finditer(iText):
        context = [None, None]
        contextLength = 20

        start, stop = match.span()
        newStop = stop
        while (newStop < len(iText)) and (iText[newStop] in ' \n\r\t'):
            newStop += 1
        if newStop == len(iText):
            stop = newStop
            while (start > 0) and (iText[start-1] in ' \n\r\t'):
                start -= 1
        marksText = iText[start:stop]

        if iNode.tag is not None:
            context[0] = '<' + iNode.tag + '>'
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
        context[1] += '</' + iNode.tag + '>'

        if prompt_replace(marksText, '', context):
            oSubstitutions.append((start, stop))

    return oSubstitutions

def traverse(iNode):
    global termColors

    if iNode.tag in ['unit_number', 'number', 'currency', 'percentage', 'unit', 'metadata', 'shortcode', 'linked-concepts', 'marks', 'url', 'width', 'height', 'embed', 'pspicture', 'tikzpicture', 'src', '{http://www.w3.org/1998/Math/MathML}math', 'chem_compound', 'spec_note', 'nuclear_notation', 'nth', '{http://www.w3.org/2005/11/its}rules']:
        pass
    elif isinstance(iNode, etree._Comment):
        pass
    else:
        # check text for regex matches
        text = iNode.text or ''
        if len(iNode) > 0:
            postTailTag = iNode[0].tag
        else:
            postTailTag = None
        substitutions = find_substitutions(text, iNode=iNode, iPostTailTag=postTailTag)

        # traverse children (traverse before replacing to avoid double-checking text)
        for child in iNode.getchildren():
            traverse(child)

        # replace text with new elements
        for start, stop in sorted(substitutions, reverse=True):
            iNode.text = iNode.text[:start] + iNode.text[stop:]
        auto_save()

    # check tail for regex matches
    myParent = iNode.getparent()
    myIndex = myParent.index(iNode)
    text = iNode.tail or ''
    if iNode.getnext() is not None:
        postTailTag = iNode.getnext().tag
    else:
        postTailTag = None
    substitutions = find_substitutions(text, iNode=myParent, iPreTailTag=iNode.tag, iPostTailTag=postTailTag)
    for start, stop in sorted(substitutions, reverse=True):
        iNode.tail = iNode.tail[:start] + iNode.tail[stop:]
    auto_save()

for node in dom.xpath('//exercises') + dom.xpath('//activity'):
    traverse(node)
auto_save(force=True)
