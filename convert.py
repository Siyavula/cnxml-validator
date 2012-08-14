from lxml import etree
import sys, os

from utils import warning_message, error_message, tag_namespace_to_prefix, get_full_dom_path, etree_replace_with_node_list, MmlTex

MY_PATH = os.path.realpath(os.path.dirname(__file__))

# This parser automatically strips comments
parser = etree.ETCompatXMLParser()
parser.feed(open(os.path.join(MY_PATH, 'spec.xml'),'rt').read())
spec = parser.close()
for node in spec.xpath('//*'):
    if node.text is None:
        node.text = ''
    if node.tail is None:
        node.tail = ''

mathml_transform = MmlTex()

conversionFunctions = {} # Cache
def cache_conversion_function(iSpec):
    global conversionFunctions, spec

    if isinstance(iSpec, basestring):
        # xpath given rather than node
        specEntry = None
        for child in spec:
            xpathNode = child.find('xpath')
            if xpathNode is None:
                continue
            if xpathNode.text == iSpec:
                specEntry = child
                break
    else:
        specEntry = iSpec

    conversionFunction = conversionFunctions.get(specEntry)

    if conversionFunction is None:
        # Cache conversion function
        conversionFunctionNodes = specEntry.xpath('.//conversion-callback[@name="latex"]')
        if len(conversionFunctionNodes) == 0:
            warning_message('No conversion entry for ' + specEntry.find('xpath').text)
            conversionFunctionSource = 'conversionFunction = lambda self: None'
        else:
            if len(conversionFunctionNodes) != 1:
                error_message('More than 1 conversion entry for ' + get_full_dom_path(iNode, spec))
            conversionFunctionSource = conversionFunctionNodes[0].text.strip()
            if conversionFunctionSource == '':
                conversionFunctionSource = 'conversionFunction = lambda self: None'
            else:
                conversionFunctionSource = 'def conversionFunction(self):\n' + '\n'.join(['\t' + line for line in conversionFunctionSource.split('\n')]) + '\n'

        from lxml import etree
        import utils
        localVars = {
            'etree': etree,
            'utils': utils,
            'convert_using': convert_using,
            'warning_message': warning_message,
            'error_message': error_message,
            'mathml_transform': mathml_transform,
        }
        exec(conversionFunctionSource, localVars)
        conversionFunction = localVars['conversionFunction']
        conversionFunctions[specEntry] = conversionFunction

    return conversionFunction

def convert_using(node, path):
    f = cache_conversion_function(path)
    return f(node)

def traverse(iNode, spec):
    global documentSpecEntries, documentNodePath, conversionFunctions

    children = iNode.getchildren()
    for child in children:
        traverse(child, spec)

    # Get associated conversion function
    specEntry = documentSpecEntries.get(iNode)
    if specEntry is None:
        error_message('Unhandled element at ' + get_full_dom_path(iNode, spec))

    conversionFunction = cache_conversion_function(specEntry)
    parent = iNode.getparent()
    converted = conversionFunction(iNode)
    if isinstance(converted, basestring):
        if parent is None:
            return converted
        else:
            from lxml import etree
            dummyNode = etree.Element('dummy')
            dummyNode.text = converted
            etree_replace_with_node_list(parent, iNode, dummyNode)
    elif converted is not None:
        if parent is None:
            return converted
        else:
            etree_replace_with_node_list(iNode.getparent(), iNode, converted)

for filename in sys.argv[1:]:#commandlineArguments.filename:
    #if not isSingleFile:
    #    sys.stderr.write(filename + '\n')
    parser.feed(open(filename,'rt').read())
    document = parser.close()

    # Normalize text and tail and build path for each node
    documentNodePath = {None: []}
    for node in document.xpath('//*'):
        if node.text is None:
            node.text = ''
        if node.tail is None:
            node.tail = ''
        documentNodePath[node] = documentNodePath[node.getparent()] + [node.tag]

    # Attach relevant spec entries to nodes in the DOM
    documentSpecEntries = {}
    for entry in spec:
        if entry.find('xpath') is None:
            continue
        for node in document.xpath(entry.find('xpath').text, namespaces=spec.nsmap):
            if documentSpecEntries.get(node) is None:
                documentSpecEntries[node] = entry

    #print etree.tostring(traverse(document, spec), encoding="utf-8", xml_declaration=True)
    print traverse(document, spec).encode('utf-8')
