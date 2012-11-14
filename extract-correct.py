from __future__ import division
from lxml import etree
import sys
from utils import get_full_dom_path

def remove_ampersands(iNode, iWithTail=False):
    iNode.text = (iNode.text or '').replace('&', '')
    if iWithTail:
        iNode.tail = (iNode.tail or '').replace('&', '')
    for child in iNode.getchildren():
        remove_ampersands(child, True)

def traverse(iNode):
    if (iNode.tag == 'document') or ((iNode.tag == 'content') and (iNode.getparent().tag == 'document')) or ((iNode.tag == 'section') and (iNode.getparent().tag != 'activity')):
        children = iNode.getchildren()
        for child in children:
            if not traverse(child):
                iNode.remove(child)
        return True
    elif (iNode.tag == 'title') and (iNode.getparent().tag == 'section'):
        return True
    elif iNode.tag == 'exercises':
        for correctNode in iNode.xpath('.//correct'):
            fullDomPath = get_full_dom_path(correctNode)
            if 'solution' in fullDomPath:
                correctNode.tail = ''
                entryNode = correctNode.getparent()
                while entryNode.tag != 'entry':
                    entryNode = entryNode.getparent()
                if 'latex' in fullDomPath:
                    remove_ampersands(correctNode)
                    correctNode.tag = 'latex'
                    entryNode.append(etree.Element('correct'))
                    entryNode[-1].append(correctNode)
                else:
                    entryNode.append(correctNode)
        for tag in ['header', 'footer', 'shortcode']:
            for child in iNode.xpath('.//' + tag):
                child.getparent().remove(child)
        for tag in ['problem', 'solution']:
            for child in iNode.xpath('.//' + tag):
                child.clear()
        for child in iNode.xpath('.//problem-set'):
            if child.attrib.get('{http://siyavula.com/cnxml/style/0.1}columns') is not None:
                del child.attrib['{http://siyavula.com/cnxml/style/0.1}columns']
        return True
    else:
        if len(iNode.xpath('.//exercises')) > 0:
            sys.stderr.write('WARNING: Deleting node that contains exercises.\n')
            sys.stderr.write(etree.tostring(iNode) + '\n')
        return False


filenames = sys.argv[1:]
doms = []
for filename in filenames:
    sys.stderr.write('*** ' + filename + '\n')
    xml = open(filename, 'rt').read()
    doms.append(etree.fromstring(xml))
    traverse(doms[-1])

assert (doms[0].tag == 'document') and (len(doms[0]) == 1) and (doms[0][0].tag == 'content') and (len(doms[0][0]) == 1)
for i in range(1, len(doms)):
    assert (doms[i].tag == 'document') and (len(doms[i]) == 1) and (doms[i][0].tag == 'content') and (len(doms[i][0]) == 1)
    doms[0][0].append(doms[i][0][0])
sys.stdout.write(etree.tostring(doms[0], xml_declaration=True, encoding='utf-8'))
