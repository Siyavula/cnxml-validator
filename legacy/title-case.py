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

for titleNode in dom.xpath('//title'):
    if len(titleNode) > 0:
        oldText = (titleNode.text or '').lstrip()
        newText = oldText.capitalize()
        for child in titleNode:
            if child.tag in ['latex', 'number']:
                addText = strip_namespaces(etree.tostring(child, with_tail=False))
                oldText += addText
                newText += addText
                oldText += child.tail or ''
                newText += (child.tail or '').lower()
            else:
                print 'ERROR', etree.tostring(titleNode)
        if oldText != newText:
            print termColors['warning'] + "WARNING: " + termColors['stop'] + "I can't fix this one, but it looks funny. Maybe you should fix it in the CNXML+."
            start = 0
            while oldText[start] == newText[start]:
                start += 1
            stop = len(oldText)
            while oldText[stop-1] == newText[stop-1]:
                stop -= 1
            print oldText[:start] + termColors['old'] + oldText[start:stop] + termColors['stop'] + oldText[stop:]
            print newText[:start] + termColors['new'] + newText[start:stop] + termColors['stop'] + newText[stop:]
    else:
        oldText = (titleNode.text or '').strip()
        newText = oldText.capitalize()
        if oldText != newText:
            start = 0
            while oldText[start] == newText[start]:
                start += 1
            stop = len(oldText)
            while oldText[stop-1] == newText[stop-1]:
                stop -= 1
            if prompt_replace(oldText[start:stop], newText[start:stop], (oldText[:start], oldText[stop:])):
                titleNode.text = newText
                auto_save()

auto_save(force=True)
