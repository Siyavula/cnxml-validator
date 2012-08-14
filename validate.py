from lxml import etree
import sys, os
import argparse

from utils import warning_message, error_message, tag_namespace_to_prefix, get_full_dom_path, tag_prefix_to_namespace

MY_PATH = os.path.realpath(os.path.dirname(__file__))

# Parse command line arguments
argumentParser = argparse.ArgumentParser(description='Check the validity of a CNXML+ document.')
argumentParser.add_argument(
    '--clean-up', dest='produceCleanedXML', action='store_true',
    help='Write to standard output a cleaned-up version of the input XML. Will delete all offending elements.')
argumentParser.add_argument(
    '-o', dest='outputFilename',
    help='Write output to given filename rather than stdout.')
argumentParser.add_argument(
    'filename', nargs='+',
    help='One or more filenames to process.')
commandlineArguments = argumentParser.parse_args()

isSingleFile = (len(commandlineArguments.filename) == 1)

if commandlineArguments.outputFilename is None:
    outputFile = sys.stdout
else:
    outputFile = open(commandlineArguments.outputFilename, 'wt')

# This parser automatically strips comments
parser = etree.ETCompatXMLParser()
parser.feed(open(os.path.join(MY_PATH, 'spec.xml'),'rt').read())
spec = parser.close()
for node in spec.xpath('//*'):
    if node.text is None:
        node.text = ''
    if node.tail is None:
        node.tail = ''

def traverse_children_xml(patternNode):
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
            return traverse_children_xml(referenceEntry.find('children'))
        if patternNode.tag == 'optional':
            return '(' + tag + ',)?'
        else:
            return '(' + tag + ',)'
    else:
        assert patternNode.tag in ['children', 'optional', 'subset-of', 'any-number', 'one-of', 'unordered'], patternNode.tag
        subPatterns = [traverse_children_xml(child) for child in patternNode.getchildren()]
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
        elif patternNode.tag == 'unordered':
            # TODO: this is currently broken and will also match repetitions of the elements or a subset of the elements. it will match correct patterns, but will also match some incorrect ones
            return '((' + '|'.join(subPatterns) + ')*)'
        else:
            assert False
            return '(' + ''.join(subPatterns) + ')'

def traverse(iNode, spec):
    global documentSpecEntries
    children = iNode.getchildren()
    for child in children:
        traverse(child, spec)

    # Get associated specification node
    specEntry = documentSpecEntries.get(iNode)
    if specEntry is None:
        warning_message('Unhandled element at ' + get_full_dom_path(iNode, spec))
        return # TODO: This will ignore any node without matching xpath in spec. Be more strict later.

    # Check attributes
    nodeAttributes = dict(iNode.attrib)
    for key in nodeAttributes:
        if key[0] == '{': # attribute name has namespace
            value = nodeAttributes[key]
            del nodeAttributes[key]
            nodeAttributes[tag_namespace_to_prefix(key, spec)] = value
    specAttributes = specEntry.find('attributes')
    if specAttributes is None:
        if len(nodeAttributes) > 0:
            if len(iNode.attrib) > 0:
                if not ((iNode.attrib.keys() == ['id',]) or (iNode.tag[:36] == '{http://www.w3.org/1998/Math/MathML}')):
                    warning_message('Extra attributes in ' + get_full_dom_path(iNode, spec) + ': ' + repr(iNode.attrib))
            pass # TODO: This will ignore any nodes that have attributes, even when the spec does not specify any. Make this more strict later to force all attributes to be in the spec.
    else:
        for entry in specAttributes:
            attributeName = entry.find('name').text
            attributeValue = nodeAttributes.get(attributeName)
            if attributeValue is None:
                specDefaultNode = entry.find('default')
                if specDefaultNode is None:
                    raise KeyError, "Missing attribute '%s' in %s"%(attributeName, get_full_dom_path(iNode, spec))
                elif commandlineArguments.produceCleanedXML and (specDefaultNode.text != ''):
                    iNode.attrib[tag_prefix_to_namespace(attributeName, spec)] = specDefaultNode.text
            else:
                # TODO: check that attribute value conforms to spec type
                del nodeAttributes[attributeName]
        if len(nodeAttributes) > 0:
            # There are still unhandled node attributes
            raise KeyError, "Unknown attribute(s) '%s' in %s"%("', '".join(nodeAttributes.keys()), get_full_dom_path(iNode, spec))

    # Validate children: build regex from spec
    regex = traverse_children_xml(specEntry.find('children'))
    if regex is None:
        # No children
        if len(children) != 0:
            error_message('''No children expected in ''' + documentSpecEntries[iNode].find('xpath').text + '''
*** These are superfluous children:
''' + ','.join([tag_namespace_to_prefix(child.tag, spec) for child in children]) + '''
*** The offending element looks like this:
''' + etree.tostring(iNode))
    else:
        import re
        pattern = re.compile('^' + regex + '$')
        # Validate children: build children pattern
        if len(children) > 0:
            childrenPattern = ','.join([tag_namespace_to_prefix(child.tag, spec) for child in children]) + ','
        else:
            childrenPattern = ''
        if pattern.match(childrenPattern) is None:
            error_message('''Child match failed for a ''' + documentSpecEntries[iNode].find('xpath').text + ''' element.
*** I was expecting the children to follow this pattern:
''' + regex + '''
*** Instead I got these children:
''' + childrenPattern + '''
*** The offending element looks like this:
''' + etree.tostring(iNode))

    # Check that text matches text spec
    if specEntry.find('notext') is not None:
        text = ''
        if iNode.text is not None:
            text = iNode.text.strip()
            if text != '':
                location = 'at the beginning of the element'
            if commandlineArguments.produceCleanedXML:
                iNode.text = None
        if text == '':
            for child in iNode.getchildren():
                if child.tail is not None:
                    text = child.tail.strip()
                    if text != '':
                        location = 'after a %s child'%child.tag
                        break
                    if commandlineArguments.produceCleanedXML:
                        child.tail = None
        if text != '':
            error_message(documentSpecEntries[iNode].find('xpath').text + ''' element must not have any text.
*** Found the following text ''' + location + ': ' + text + '''
*** The offending element looks like this:
''' + etree.tostring(iNode))

    # Do validation callback
    callbackNode = specEntry.find('validation-callback')
    if callbackNode is not None:
        callbackFunctionName = callbackNode.text.strip()
        import callbacks
        callbackFunction = eval('callbacks.' + callbackFunctionName)
        if not callbackFunction(iNode):
            raise error_message("Validation callback " + repr(callbackFunctionName) + " failed on the following element:\n" + etree.tostring(iNode))

for filename in commandlineArguments.filename:
    if not isSingleFile:
        sys.stderr.write(filename + '\n')
    parser.feed(open(filename,'rt').read())
    document = parser.close()
    for node in document.xpath('//*'):
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

    traverse(document, spec)

    if commandlineArguments.produceCleanedXML:
        print etree.tostring(document, xml_declaration=True, encoding='utf-8')
