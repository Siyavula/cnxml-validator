#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from lxml import etree


if __name__ == "__main__":
    spec = open('spec.xml', 'r').read()
    specxml = etree.XML(spec)
    testdocs = [td.strip().replace('.cnxmlplus','') for td in os.listdir('testdocuments') if td.strip().endswith('.cnxmlplus')]
    for entry in specxml:
        xpath = entry.find('xpath')
        if xpath is not None:
            xpath = xpath.text
            element_name = xpath[xpath.find(r'//')+2:]
            element_name_end = element_name.find(r'/')
            element_name = element_name[0:element_name_end]
            print element_name
            if element_name not in testdocs:
                print '✗         ',
            else:
                print '✓         ',

