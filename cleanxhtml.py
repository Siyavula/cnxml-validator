#!/usr/bin/env python

#
# Cleans xhtml files
# 
import sys

from lxml import etree

def clean_duplicate_ids(xml):
    ids = []

    for element in xml.iter():
        Id = element.attrib.get('id')
        if Id is not None:
            if Id not in ids:
                ids.append(Id)
            else:
                i = 2
                newId = Id + '-' + str(i)
                while newId in ids:
                    i += 1
                    newId = Id + '-' + str(i)
                ids.append(newId)
                element.attrib['id'] = newId

    return xml



if __name__ == "__main__":
    xhtml = etree.XML(open(sys.argv[1], 'r').read())
    xhtml = clean_duplicate_ids(xhtml)
    print etree.tostring(xhtml, pretty_print=True, method='xml')
