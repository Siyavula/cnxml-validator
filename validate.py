from lxml import etree
import sys

# This parser automatically stripts comments
parser = etree.ETCompatXMLParser()
parser.feed(open('spec.xml','rt').read())
spec = parser.close()
if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'test.cnxmlplus'
parser.feed(open(filename,'rt').read())
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
    if entry.find('xpath') is None:
        continue
    for node in document.xpath(entry.find('xpath').text):
        if documentSpecEntries.get(node) is None:
            documentSpecEntries[node] = entry

def traverseChildrenXml(patternNode):
    global spec
    if patternNode is None:
        return None
    if len(patternNode) == 0:
        # Leaf: should contain tag name
        assert patternNode.tag in ['optional', 'element', 'reference'], patternNode.tag
        assert patternNode.text is not None
        tag = patternNode.text.strip()
        assert tag != ''
        if patternNode.tag == 'reference':
            referenceEntry = [child for child in spec if child.attrib.get('id') == tag][0]
            return traverseChildrenXml(referenceEntry.find('children'))
        if patternNode.tag == 'optional':
            return '(' + tag + ',)?'
        else:
            return '(' + tag + ',)'
    else:
        assert patternNode.tag in ['children', 'optional', 'subset-of', 'any-number', 'one-of'], patternNode.tag
        subPatterns = [traverseChildrenXml(child) for child in patternNode.getchildren()]
        if patternNode.tag == 'children':
            return '(' + ''.join(subPatterns) + ')'
        elif patternNode.tag == 'optional':
            return '((' + ''.join(subPatterns) + ')?)'
        elif patternNode.tag == 'subset-of':
            # TODO: this is currently broken and will also match repetitions of the elements. it will match correct patterns, but will also match some incorrect ones
            return '((' + '|'.join(subPatterns) + ')*)'
        elif patternNode.tag == 'any-number':
            return '((' + ''.join(subPatterns) + '){%s,%s})'%(patternNode.attrib.get('from', ''), patternNode.attrib.get('to', ''))
        elif patternNode.tag == 'one-of':
            return '(' + '|'.join(subPatterns) + ')'
        else:
            assert False
            return '(' + ''.join(subPatterns) + ')'
        
 
def traverse(node, spec):
    global documentSpecEntries
    children = node.getchildren()
    for child in children:
        traverse(child, spec)

    # Validate children: build regex from spec
    specEntry = documentSpecEntries.get(node)
    if specEntry is None:
        return # TODO: This will ignore any node without matching xpath in spec. Be more strict later.
    regex = traverseChildrenXml(specEntry.find('children'))
    if regex is None:
        # No children
        assert len(children) == 0
    else:
        import re
        pattern = re.compile('^' + regex + '$')
        print regex
        # Validate children: build children pattern
        if len(children) > 0:
            childrenPattern = ','.join([child.tag for child in children]) + ','
        else:
            childrenPattern = ''
        print repr(childrenPattern)
        if pattern.match(childrenPattern) is None:
            raise ValueError, 'Child match failed for %s entry: %s'%(documentSpecEntries[node].find('xpath').text, childrenPattern)
        print

    # TODO: Check that text matches text spec
    # TODO: Do callback

traverse(document, spec)
