from __future__ import division
from lxml import etree
import sys

xml = sys.stdin.read()
dom = etree.fromstring(xml)

from utils import get_full_dom_path

def traverse(iNode):
    if (iNode.tag == 'document') or ((iNode.tag == 'content') and (iNode.getparent().tag == 'document')) or (iNode.tag == 'metadata') or ((iNode.tag == 'section') and (iNode.getparent().tag != 'activity')):
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
        if len(iNode.xpath('.//exercises')):
            sys.stderr.write('WARNING: Deleting node that contains exercises.\n')
            sys.stderr.write(etree.tostring(iNode) + '\n')
        return False

traverse(dom)
sys.stdout.write(etree.tostring(dom, xml_declaration=True, encoding='utf-8'))

'''

\section{TITLE}
\begin{Exercises}{TITLE}
\begin{enumerate}
\item
\end{enumerate}
\end{Exercises}
'''
