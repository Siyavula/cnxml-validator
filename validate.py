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
    for node in document.xpath(entry.find('xpath').text, namespaces=spec.nsmap):
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
        
def tag_namespace_to_prefix(tag, spec):
    if tag[0] == '{':
        closingBracePos = tag.find('}')
        namespaceUri = tag[1:closingBracePos]
        prefix = dict([(value, key) for key, value in spec.nsmap.iteritems()])[namespaceUri]
        return prefix + ':' + tag[closingBracePos+1:]
    else:
        return tag

def get_full_dom_path(iNode):
    node = iNode
    path = '/' + tag_namespace_to_prefix(node.tag, spec)
    while node.getparent() is not None:
        node = node.getparent()
        path = '/' + tag_namespace_to_prefix(node.tag, spec) + path
    return path

def traverse(iNode, spec):
    global documentSpecEntries
    children = iNode.getchildren()
    for child in children:
        traverse(child, spec)

    # Get associated specification node
    specEntry = documentSpecEntries.get(iNode)

    # Check attributes
    if specEntry is not None:
        nodeAttributes = dict(iNode.attrib)
        specAttributes = specEntry.find('attributes')
        if specAttributes is None:
            if len(nodeAttributes) > 0:
                if False:
                    if len(iNode.attrib) > 0:
                        print get_full_dom_path(iNode), iNode.attrib
                pass # TODO: This will ignore any nodes that have attributes, even when the spec does not specify any. Make this more strict later to force all attributes to be in the spec.
        else:
            for entry in specAttributes:
                attributeName = entry.find('name').text
                attributeValue = nodeAttributes.get(attributeName)
                if (entry.find('default') is None) and (attributeValue is None):
                    raise KeyError, "Missing attribute '%s' in %s"%(attributeName, get_full_dom_path(iNode))
                if attributeValue is not None:
                    # TODO: check that attribute value conforms to spec type
                    del nodeAttributes[attributeName]
            if len(nodeAttributes) > 0:
                # There are still unhandled node attributes
                raise KeyError, "Unknown attribute(s) '%s' in %s"%("', '".join(nodeAttributes.keys()), get_full_dom_path(iNode))

    # Validate children: build regex from spec
    if specEntry is None:
        if True:
            print get_full_dom_path(iNode)
        return # TODO: This will ignore any node without matching xpath in spec. Be more strict later.
    regex = traverseChildrenXml(specEntry.find('children'))
    if regex is None:
        # No children
        if len(children) != 0:
            raise ValueError, "No children expected in %s"%get_full_dom_path(iNode)
    else:
        import re
        pattern = re.compile('^' + regex + '$')
        # Validate children: build children pattern
        if len(children) > 0:
            childrenPattern = ','.join([tag_namespace_to_prefix(child.tag, spec) for child in children]) + ','
        else:
            childrenPattern = ''
        if pattern.match(childrenPattern) is None:
            raise ValueError, 'Child match failed for %s entry: %s'%(documentSpecEntries[iNode].find('xpath').text, childrenPattern)

    # TODO: Check that text matches text spec
    # TODO: Do callback

traverse(document, spec)
