#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lxml import etree


if __name__ == "__main__":
    spec = open('spec.xml', 'r').read()
    specxml = etree.XML(spec)
    print 'learner    teacher    correct    Xpath'
    for entry in specxml:
        xpath = entry.find('xpath')
        if xpath is not None:
            latex_callback = {'learner':False, 'teacher':False, 'correct':False}
            html_callback = {'learner':False, 'teacher':False, 'correct':False}

            callbacks = entry.findall('.//conversion-callback')
            for cb in callbacks:
                for audience in ['learner', 'teacher', 'correct']:
                    if ('latex' in cb.attrib['name']) and (audience in cb.attrib['name']):
                        latex_callback[audience] = True

                    if ('html ' in cb.attrib['name']) and (audience in cb.attrib['name']):
                        html_callback[audience] = True

            for audience in ['learner', 'teacher', 'correct']:
                if not html_callback[audience]:
                    print '✗         ',
                else:
                    print '✓         ',

            print xpath.text

