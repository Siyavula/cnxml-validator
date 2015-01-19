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
if '--extension' in arguments:
    index = arguments.index('--extension')
    requiredExtension = arguments[index+1]
    del arguments[index]
    del arguments[index]
else:
    requiredExtension = 'png'
if len(arguments) != 1:
    import os
    print termColors['error'] + 'ERROR:' + termColors['stop'] + ' Incorrect number of arguments.'
    print "Usage: %s [--extension ext] inputfile"%os.path.basename(sys.argv[0])
    print "       If specified, ext should not contain a dot. The default extension is 'png'."
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

for srcNode in dom.xpath('//image/src'):
    filename = (srcNode.text or '').strip()
    pos = filename.rfind('.')
    if pos == -1:
        continue
    pos += 1
    extension = filename[pos:]
    if extension != requiredExtension:
        if prompt_replace(extension, requiredExtension, (filename[:pos], '')):
            srcNode.text = filename[:pos] + requiredExtension
            auto_save()

auto_save(force=True)
