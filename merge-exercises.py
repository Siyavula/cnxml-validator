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
    'old': '\033[1m\033[41m\033[37m', # bold white on red
    'new': '\033[1m\033[41m\033[37m', # bold white on red
    'context warning': '\033[1m\033[41m\033[37m', # bold white on red
    'bold': '\033[1m',
    'reset': '\033[0m',
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
if len(arguments) != 2:
    import os
    print termColors['error'] + 'ERROR:' + termColors['stop'] + ' Incorrect number of arguments.'
    print 'Usage: %s tofilename fromfilename'%os.path.basename(sys.argv[0])
    sys.exit()
filenames = arguments
xmls = [open(filename, 'rt').read() for filename in filenames]
doms = [etree.fromstring(xml) for xml in xmls]

autoSaveTime = time.time()
autoSaveInterval = 60 # seconds
def auto_save(force=False):
    global doms, filenames, termColors, autoSaveTime, autoSaveInterval
    if force or (time.time()-autoSaveTime >= autoSaveInterval):
        sys.stderr.write(termColors['autosave'] + 'Auto saving...' + termColors['reset'])
        with open(filenames[0], 'wt') as fp:
            fp.write(etree.tostring(doms[0], xml_declaration=True, encoding="utf-8") + '\n')
        sys.stderr.write(termColors['autosave'] + ' done.\n' + termColors['reset'])
        autoSaveTime = time.time()

def xpath_with_namespaces(iNode, iXpath):
    namespaces = {}
    reverseMap = {}
    while True:
        start = iXpath.find('{')
        if start == -1:
            break
        stop = iXpath.find('}')
        assert stop > start
        url = iXpath[start+1:stop]
        prefix = reverseMap.get(url)
        if prefix is None:
            prefix = chr(len(namespaces) + ord('a'))
            namespaces[prefix] = url
            reverseMap[url] = prefix
        iXpath = iXpath[:start] + prefix + ':' + iXpath[stop+1:]
    return iNode.xpath(iXpath, namespaces=namespaces)

def build_absolute_xpath(iNode):
    myTag = iNode.tag
    parent = iNode.getparent()
    if parent is None:
        return '/' + myTag
    else:
        count = xpath_with_namespaces(parent, './' + myTag).index(iNode) + 1
        xpath = '/' + myTag + '[' + str(count) + ']'
        return build_absolute_xpath(parent) + xpath

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

import StringMatcher

nodeLists = [dom.xpath('//exercises//problem-set/entry | //exercises//multi-part/entry') for dom in doms]
assert len(nodeLists[0]) == len(nodeLists[1])

for tagName in ['solution','correct']:
    for nodeIndex in range(len(nodeLists[0])):
        entries = [nodeList[nodeIndex] for nodeList in nodeLists]
        solutions = [entry.find(tagName) for entry in entries]
        solutionStrings = []
        for solution in solutions:
            if solution is None:
                solutionStrings.append('')
            else:
                solutionStrings.append(strip_namespaces(etree.tostring(solution, with_tail=False)))
        if solutionStrings[0] != solutionStrings[1]:
            blocks = StringMatcher.matching_blocks(StringMatcher.editops(solutionStrings[0], solutionStrings[1]), solutionStrings[0], solutionStrings[1])
            if sum([block[2] for block in blocks])/max(len(solutionStrings[0]), len(solutionStrings[1])) < 0.1:
                blocks = []
            for i, col in [(0,'old'), (1,'new')]:
                pos = 0
                output = ''
                for block in blocks:
                    if block[i] > pos:
                        output += termColors[col] + solutionStrings[i][pos:block[i]] + termColors['reset']
                    output += solutionStrings[i][block[i]:block[i]+block[2]]
                    pos = block[i]+block[2]
                if pos < len(solutionStrings[i]):
                    output += termColors[col] + solutionStrings[i][pos:] + termColors['reset']
                print '===', col.upper(), '===================================================='
                print output
            print '============================================================'

            sys.stdout.write('[y/n]? ')
            response = getch()
            if response == '\x03':
                # Catch Ctrl-C
                raise KeyboardInterrupt
            passed = response in ['y','Y']
            if passed:
                print termColors['passed'] + 'yes' + termColors['reset']
            else:
                print termColors['failed'] + 'no' + termColors['reset']
            sys.stdout.write('\n')

            if passed:
                if (tagName == 'correct') and (solutions[0] is None):
                    entries[0].append(solutions[1])
                else:
                    entries[0].replace(solutions[0], solutions[1])
                auto_save()

auto_save(True)
