from lxml import etree

# This parser automatically stripts comments
parser = etree.ETCompatXMLParser()
parser.feed(open('spec.xml','rt').read())
spec = parser.close()
parser.feed(open('test.cnxmlplus','rt').read())
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

def traverseChildrenXml(patternNode):
    if patternNode is None:
        return None
    if len(patternNode) == 0:
        # Leaf: should contain tag name
        assert patternNode.tag in ['optional', 'element']
        assert patternNode.text is not None
        tag = patternNode.text.strip()
        assert tag != ''
        if patternNode.tag == 'optional':
            return '(' + tag + ',)?'
        else:
            return '(' + tag + ',)'
    else:
        assert patternNode.tag in ['children', 'optional', 'subset-of', 'any-number', 'one-of'], patternNode.tag
        subPatterns = [traverseChildrenXml(child) for child in patternNode.getchildren()]
        if patternNode.tag == 'children':
            return '^(' + ''.join(subPatterns) + ')$'
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

    '''
    # Validate children: build map from tags to symbols
    tagList = []
    for child in children:
        if child.tag not in tagList:
            tagList.append(child.tag)
    formatString = '%%0%ii'%len('%i'%(len(tagMap)-1))
    tagMap = {}
    for i in xrange(len(tagList)):
        tagMap[tagList[i]] = formatString%i
    '''

    # Validate children: build regex from spec
    import re
    regex = traverseChildrenXml(documentSpecEntries[node].find('children'))
    if regex is None:
        # No children
        assert len(children) == 0
    else:
        pattern = re.compile(regex)
        print regex

        # Validate children: build
        if len(children) > 0:
            childrenPattern = ','.join([child.tag for child in children]) + ','
        else:
            childrenPattern = ''
        print childrenPattern    
        if pattern.match(childrenPattern) is None:
            raise ValueError, 'Child match failed for %s entry: %s'%(documentSpecEntries[node].find('xpath').text, childrenPattern)

    #check that children match contains spec
    #check that text matches text spec
    #do callback

traverse(document, spec)
