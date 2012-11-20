# encoding: utf-8
from __future__ import division
import re
from lxml import etree
import sys, time
from utils import get_full_dom_path

OPTIONS = {
    'blanketIgnore': [],#['exercises'],
    'checkPictureCode': True,
}

# --- START PREAMBLE ---

termColors = {
    'autosave': '\033[1m\033[34m', # bold blue
    'warning': '\033[1m\033[31m', # bold red
    'error': '\033[1m\033[31m', # bold red
    'passed': '\033[1m\033[32m', # bold green
    'failed': '\033[1m\033[31m', # bold red
    'old': '\033[1m\033[41m\033[37m', # bold white on red
    'new': '\033[1m\033[44m\033[37m', # bold white on blue
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
    print termColors['error'] + 'ERROR:' + termColors['reset'] + ' Incorrect number of arguments.'
    print 'Usage: %s fromfilename tofilename'%os.path.basename(sys.argv[0])
    sys.exit()
filenames = arguments
xmls = [open(filename, 'rt').read() for filename in filenames]
doms = [etree.fromstring(xml) for xml in xmls]

autoSaveTime = time.time()
autoSaveInterval = 60 # seconds
def auto_save(force=False):
    global dom, inputFilename, termColors, autoSaveTime, autoSaveInterval
    if force or (time.time()-autoSaveTime >= autoSaveInterval):
        sys.stderr.write(termColors['autosave'] + 'Auto saving...' + termColors['reset'])
        with open(inputFilename, 'wt') as fp:
            fp.write(etree.tostring(dom, xml_declaration=True, encoding='utf-8'))
        sys.stderr.write(termColors['autosave'] + ' done.\n' + termColors['reset'])
        autoSaveTime = time.time()

nodeLists = [dom.xpath('//*') for dom in doms]

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


for nodeList in nodeLists:
    i = 0
    while i < len(nodeList):
        if False:#nodeList[i].tag in ['shortcode']:
            del nodeList[i]
        else:
            node = nodeList[i]
            while node is not None:
                if node.attrib.get('ignore') is not None:
                    del nodeList[i]
                    break
                node = node.getparent()
            else:
                for tag in OPTIONS['blanketIgnore']:
                    if ('/' + tag + '[') in build_absolute_xpath(nodeList[i]):
                        del nodeList[i]
                        break
                else:
                    i += 1


for i in range(2):
    with open('xpaths%i'%(i+1),'wt') as fp:
        for node in nodeLists[i]:
            fp.write(build_absolute_xpath(node) + '\n')

for listIndex in range(len(nodeLists[0])):
    if nodeLists[0][listIndex].tag == 'multi-part' and nodeLists[1][listIndex].tag == 'problem-set':
        nodeLists[1][listIndex].tag = 'multi-part'
    xpaths = [build_absolute_xpath(nodeList[listIndex]) for nodeList in nodeLists]
    if (xpaths[0] != xpaths[1]) or (nodeLists[0][listIndex].attrib != nodeLists[1][listIndex].attrib):
        print '====================='
        for i in range(2):
            print termColors['bold'] + xpaths[i] + termColors['reset']
            print strip_namespaces(etree.tostring(nodeLists[i][listIndex-1]))
            print termColors[['old','new'][i]] + strip_namespaces(etree.tostring(nodeLists[i][listIndex])) + termColors['reset']
            print strip_namespaces(etree.tostring(nodeLists[i][listIndex+1]))
            print '====================='
        sys.exit()

if OPTIONS['checkPictureCode']:
    codeList = ['code']
else:
    codeList = []
for listIndex in range(len(nodeLists[0])):
    if nodeLists[0][listIndex].tag in ['number', 'unit_number', 'url', 'width', 'height', 'embed', 'usepackage', 'src', 'type', 'currency', 'unit', 'percentage', 'chem_compound', 'spec_note', 'nuclear_notation', 'nth', 'link'] + codeList:
        if ''.join(etree.tostring(nodeLists[0][listIndex], with_tail=False).split()) != ''.join(etree.tostring(nodeLists[1][listIndex], with_tail=False).split()):
            for i in range(2):
                print termColors[['old','new'][i]] + strip_namespaces(etree.tostring(nodeLists[i][listIndex])) + termColors['reset']

'''
for listIndex in range(len(nodeLists[0])):
    if nodeLists[0][listIndex].tag == 'latex':
        latex1 = ''.join(etree.tostring(nodeLists[0][listIndex], with_tail=False).split())
        latex2 = ''.join(etree.tostring(nodeLists[1][listIndex], with_tail=False).split())
        if latex1 != latex2:
            for i in range(2):
                print termColors[['old','new'][i]] + strip_namespaces(etree.tostring(nodeLists[i][listIndex])) + termColors['reset']
'''

with open(filenames[1], 'wt') as fp:
    fp.write(etree.tostring(doms[1], xml_declaration="True", encoding="utf-8") + '\n')
