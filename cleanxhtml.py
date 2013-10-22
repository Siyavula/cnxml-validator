#!/usr/bin/env python

#
# Cleans xhtml files
# 
import sys

from lxml import etree




if __name__ == "__main__":
    xhtml = etree.XML(open(sys.argv[1], 'r').read())

        
