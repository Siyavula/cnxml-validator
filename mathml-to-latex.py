# encoding: utf-8
from __future__ import division
import utils
from lxml import etree
import sys

arguments = sys.argv[1:]
if len(arguments) != 2:
    import os
    print 'ERROR: Incorrect number of arguments.'
    print 'Usage: %s inputfile outputfile'%os.path.basename(sys.argv[0])
    sys.exit()
inputFilename = arguments[0]
outputFilename = arguments[1]

with open(inputFilename, 'rt') as fp:
    xml = fp.read()
dom = etree.fromstring(xml)

mathml_transform = utils.MmlTex()
for mathNode in dom.xpath('//m:math', namespaces={'m': 'http://www.w3.org/1998/Math/MathML'}):
    tex = mathml_transform(mathNode)
    tex = unicode(tex).replace('$', '')
    if tex.count(r'\left') != tex.count(r'\right'):
        tex = tex.replace(r'\left', '').replace(r'\right', '')

    # replace the stackrel{^} with hat
    tex = tex.replace(r'\stackrel{^}', r'\hat')

    # fix the \times symbol
    tex = tex.replace(u'×', r'\times ')

    # fix the trig functions too
    for func in ['sin', 'cos', 'tan', 'cot']:
        tex = tex.replace(' ' + func, '\\' + func + ' ')

    latexNode = etree.Element('latex')
    latexNode.text = tex
    replaceNode = mathNode
    if mathNode.getparent().tag == 'equation':
        replaceNode = mathNode.getparent()
    latexNode.tail = replaceNode.tail
    replaceNode.getparent().replace(replaceNode, latexNode)

with open(outputFilename, 'wt') as fp:
    fp.write(etree.tostring(dom, xml_declaration=True, encoding='utf-8'))
