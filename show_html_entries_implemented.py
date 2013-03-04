#!/usr/bin/env python
# -*- coding: utf-8 -*-
from lxml import etree


if __name__ == "__main__":
    spec = open('spec.xml', 'r').read()
    specxml = etree.XML(spec)
    print 'HTML     Xpath'
    for entry in specxml:
        xpath = entry.find('xpath')
        if xpath is not None:
            latex_callback = False
            html_callback = False

            callbacks = entry.findall('.//conversion-callback')
            for cb in callbacks:
                if 'latex' in cb.attrib['name']:
                    latex_callback = True

                if 'html ' in cb.attrib['name']:
                    html_callback = True


            if not html_callback:
                print '✗   ',
            else:
                print '✓   ',

            print xpath.text

