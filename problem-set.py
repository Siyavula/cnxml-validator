# encoding: utf-8
from __future__ import division
import re
from lxml import etree
import sys, time
from utils import get_full_dom_path

# --- START PREAMBLE ---

'''
Some handy emacs regexes:
{\(-?[0-9]+\)}^{°} -> \1°
'''

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

autoSaveTime = time.time()
autoSaveInterval = 60 # seconds
def auto_save(force=False):
    global dom, inputFilename, termColors, autoSaveTime, autoSaveInterval
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
    global numberAndCurrencyPattern, lazyMode
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
                if (iNode.tag != 'latex') and (match is not None):
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
                        elif unitText == u'°':
                            unitText = u'°'
                        else:
                            assert unitText[:8] == r'\textrm{'
                            assert unitText[-1] == '}'
                            unitText = unitText[8:-1].strip()
                        newNode[-1].text = unitText
                        oldNumber += iText[stop:stop+len(match.group())]
                        stop += len(match.group())
                    else:
                        if lazyMode and ((iNode.tag == 'latex') or ((iNode.tag == 'correct') and ('latex' in get_full_dom_path(iNode)))):
                            # Skip unit-less numbers that are small integers and in LaTeX mode
                            try:
                                value = int(oldNumber.replace(' ','').replace(',','.'))
                                if abs(value) < 1000:
                                    continue
                            except ValueError:
                                pass
        # Check if the post-context is funny (for both currency and number)
        if postContextWarning == 0:
            offset = 0
            while (stop+offset+1 < len(iText)) and (iText[stop+offset+1] == ' '):
                offset += 1
            if (stop+offset+1 < len(iText)) and (iText[stop+offset+1] in '.,0123456789'):
                postContextWarning = min(contextLength, offset+1)
            while (postContextWarning < contextLength) and (stop+postContextWarning+1 < len(iText)) and (iText[stop+postContextWarning+1] in '.,0123456789'):
                postContextWarning += 1

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

        if prompt_replace(oldNumber, etree.tostring(newNode, encoding='utf-8').decode('utf-8'), context, (preContextWarning, postContextWarning)):
            oSubstitutions.append((start, stop, newNode))

    return oSubstitutions


def strip_namespaces(xml):
    while True:
        start = xml.find(' xmlns:')
        if start == -1:
            break
        stop = xml.find('"', start)
        assert stop != -1
        stop = xml.find('"', stop+1)
        assert stop != -1
        xml = xml[:start] + xml[stop+1:]
    return xml


for problemsetNode in dom.xpath('//problem-set'):
    print termColors['old'] + 'HEADER:' + termColors['stop']
    headerNode = problemsetNode.find('header')
    if headerNode is not None:
        output = strip_namespaces(etree.tostring(headerNode, encoding='utf-8', with_tail=True))
        start = output.find('>')+1
        stop = output.rfind('<')
        output = output[start:stop]
        print output.strip()
    entries = problemsetNode.xpath('./entry/problem')
    for i in range(min(len(entries), 3)):
        print termColors['old'] + 'ENTRY %i:'%(i+1) + termColors['stop']
        output = strip_namespaces(etree.tostring(entries[i], encoding='utf-8', with_tail=True))
        start = output.find('>')+1
        stop = output.rfind('<')
        output = output[start:stop]
        print output.strip()
    if prompt_replace('problem-set', 'multi-part'):
        # Rename
        problemsetNode.tag = 'multi-part'

        # Move shortcode out of first entry into multi-part, or delete them if they're all todo
        entries = problemsetNode.xpath('./entry')
        shortcodes = [entry.find('shortcode') for entry in entries]
        absent = [(shortcode is None) or (shortcode.text is None) or (shortcode.text.lower() == 'todo') for shortcode in shortcodes]
        if all(absent):
            for entry in entries:
                shortcode = entry.find('shortcode')
                if shortcode is not None:
                    entry.remove(shortcode)
        elif (shortcodes[0] is not None) and all(absent[1:]):
            problemsetNode.insert(0, shortcodes[0])
            for entry in entries[1:]:
                shortcode = entry.find('shortcode')
                if shortcode is not None:
                    entry.remove(shortcode)
                
        auto_save()

auto_save(force=True)
