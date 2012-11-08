# encoding: utf-8
from __future__ import division
import re
from lxml import etree
import sys, time
from utils import get_full_dom_path

arguments = sys.argv[1:]
if len(arguments) != 1:
    import os
    print 'ERROR: Incorrect number of arguments.'
    print 'Usage: %s inputfile'%os.path.basename(sys.argv[0])
    sys.exit()
inputFilename = arguments[0]

with open(inputFilename, 'rt') as fp:
    xml = fp.read()
dom = etree.fromstring(xml)

for exercisesNode in dom.xpath('//exercises'):
    problemsetCount = len(exercisesNode.xpath('./problem-set'))
    entryCount = len(exercisesNode.xpath('./entry'))
    multipartCount = len(exercisesNode.xpath('./multi-part'))

    if (problemsetCount == 1) and (entryCount == 0) and (multipartCount == 0):
        for problemsetNode in exercisesNode.find('problem-set').xpath('.//problem-set'):
            problemsetNode.tag = 'multi-part'
    else:
        for problemsetNode in exercisesNode.xpath('.//problem-set'):
            problemsetNode.tag = 'multi-part'

with open(inputFilename, 'wt') as fp:
    fp.write(etree.tostring(dom, xml_declaration=True, encoding='utf-8'))
