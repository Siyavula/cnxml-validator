from lxml import etree

# This parser automatically stripts comments
parser = etree.ETCompatXMLParser()
parser.feed(open('spec.xml','rt').read())
spec = parser.close()
parser.feed(open('/home/carl/work/siyavula/fhsst/latex2cnxml/content/Science10/11-electromagnetic-radiation.cnxmlplus','rt').read())
document = parser.close()
for dom in spec, document:
    for node in dom.xpath('//*'):
        if node.text is None:
            node.text = ''
        if node.tail is None:
            node.tail = ''

# Attach relevant spec entries to nodes in the DOM
documentSpecEntries = {}
for entry in spec:
    for node in document.xpath(entry.find('xpath').text):
        if documentSpecEntries.get(node) is None:
            documentSpecEntries[node] = entry

def traverse(node, spec):
    global documentSpecEntries
    children = node.getchildren()
    for child in children:
        traverse(child, spec)
    # validate children
    #check that children match contains spec
    #check that text matches text spec
    #do callback

traverse(document, spec)
