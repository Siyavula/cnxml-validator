import sys

from lxml import etree
import difflib
from pprint import pprint as _pprint

if __name__ == "__main__":
    file1, file2 = sys.argv[1:]
    print "Comparing: ", file1, file2

    xml1 = etree.parse(file1)
    xml2 = etree.parse(file2)
   
    for entry in xml1.findall(".//entry"):
        xpath = entry.find('.//xpath')

        if xpath is not None:
            # find the same xpath in file2's entries
            for entry2 in xml2.findall(".//entry"):
                if entry2.find('xpath') is not None:
                    if etree.tostring(entry2.find('.//xpath')).strip() == etree.tostring(xpath).strip():
                        e1 = etree.tostring(entry).strip()
                        e2 = etree.tostring(entry2).strip()

                        if e1 != e2:
                            cc1 = len([cc for cc in entry.findall('conversion-callback')])
                            cc2 = len([cc for cc in entry2.findall('conversion-callback')])

                            print '\n', xpath.text
                            print '--------------------'
                            diff = difflib.Differ()
                            result = diff.compare(e1.splitlines(), e2.splitlines())
                            print '\n'.join(result)
                            print 'Conversion callbacks: ', cc1, cc2
                            print "\n\n==========================\n\n"



