import sys

def warning_message(message, newLine=True):
    global commandlineArguments
    sys.stderr.write('WARNING: ' + message)
    if newLine:
        sys.stderr.write('\n')

def error_message(message, newLine=True, terminate=True):
    global commandlineArguments
    sys.stderr.write('ERROR: ' + message)
    if newLine:
        sys.stderr.write('\n')
    if not commandlineArguments.produceCleanedXML:
        sys.exit()

def tag_namespace_to_prefix(tag, spec):
    if tag[0] == '{':
        closingBracePos = tag.find('}')
        namespaceUri = tag[1:closingBracePos]
        prefix = dict([(value, key) for key, value in spec.nsmap.iteritems()])[namespaceUri]
        return prefix + ':' + tag[closingBracePos+1:]
    else:
        return tag

def get_full_dom_path(iNode, iSpec):
    node = iNode
    path = '/' + tag_namespace_to_prefix(node.tag, iSpec)
    while node.getparent() is not None:
        node = node.getparent()
        path = '/' + tag_namespace_to_prefix(node.tag, iSpec) + path
    return path

def etree_replace_with_node_list(parent, child, dummyNode, keepTail=True):
    index = parent.index(child)
    if keepTail and (child.tail is not None):
        childTail = child.tail
    else:
        childTail = ''
    del parent[index]

    if dummyNode.text is not None:
        if index == 0:
            if parent.text is None:
                parent.text = dummyNode.text
            else:
                parent.text += dummyNode.text
        else:
            if parent[index-1].tail is None:
                parent[index-1].tail = dummyNode.text
            else:
                parent[index-1].tail += dummyNode.text

    if len(dummyNode) == 0:
        if index == 0:
            if parent.text is None:
                parent.text = childTail
            else:
                parent.text += childTail
        else:
            if parent[index-1].tail is None:
                parent[index-1].tail = childTail
            else:
                parent[index-1].tail += childTail
    else:
        if dummyNode[-1].tail is None:
            dummyNode[-1].tail = childTail
        else:
            dummyNode[-1].tail += childTail
        for i in range(len(dummyNode)-1, -1, -1):
            parent.insert(index, dummyNode[i])
