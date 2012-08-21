import sys
import entities

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

def tag_namespace_to_prefix(tag, iSpec=None):
    if (iSpec is not None) and (tag[0] == '{'):
        closingBracePos = tag.find('}')
        namespaceUri = tag[1:closingBracePos]
        prefix = dict([(value, key) for key, value in iSpec.nsmap.iteritems()])[namespaceUri]
        return prefix + ':' + tag[closingBracePos+1:]
    else:
        return tag

def tag_prefix_to_namespace(tag, iSpec=None):
    if iSpec is None:
        return tag
    pos = tag.find(':')
    if pos == -1:
        return tag
    prefix = tag[:pos]
    tag = tag[pos+1:]
    return '{%s}%s'%(iSpec.nsmap[prefix], tag)

def get_full_dom_path(iNode, iSpec=None):
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

def format_number(numString, decimalSeparator=',', thousandsSeparator=entities.unicode['nbsp'], minusSymbol=entities.unicode['minus'], iScientificNotation=u'%s\u00a0\u00d7\u00a010<sup>%s</sup>'):
    """
    Replace standard decimal point with new decimal separator
    (default: comma); add thousands and thousandths separators
    (default: non-breaking space).
    """
    numString = str(numString).strip()

    pos = numString.find('e')
    if pos != -1:
        # scientific notation
        exponent = str(int(numString[pos+1:].strip()))
        if exponent[0] == '-':
            exponent = minusSymbol + exponent[1:]
        numString = numString[:pos]
    else:
        exponent = None

    if numString[0] in '+-':
        sign = {'+': '+', '-': minusSymbol}[numString[0]]
        numString = numString[1:]
    else:
        sign = ''
    decimalPos = numString.find('.')
    if decimalPos == -1:
        intPart = numString
        fracPart = None
    else:
        intPart = numString[:decimalPos]
        fracPart = numString[decimalPos+1:]
    # Add thousands separator to integer part
    if len(intPart) > 4:
        pos = len(intPart)-3
        while pos > 0:
            intPart = intPart[:pos] + thousandsSeparator + intPart[pos:]
            pos -= 3
    # Add thousandths separator to fractional part
    if (fracPart is not None) and (len(fracPart) > 4):
        pos = 3
        while pos < len(fracPart):
            fracPart = fracPart[:pos] + thousandsSeparator + fracPart[pos:]
            pos += 3 + len(thousandsSeparator)
    numString = sign + intPart
    if fracPart is not None:
        numString += decimalSeparator + fracPart

    if exponent is not None:
        # scientific notation
        numString = iScientificNotation%(numString, exponent)

    return numString

class MmlTex:
    def __init__(self):
        import os
        from lxml import etree
        MY_PATH = os.path.realpath(os.path.dirname(__file__))
        self.__call__ = etree.XSLT(etree.parse(os.path.join(MY_PATH, 'mmltex/mmltex.xsl')))

def escape_latex(iText, iIgnore=''):
    """
    Escape the LaTeX special symbols in a string.

    Inputs:

      iText - The string to escape.
      iIgnore - A sequence of characters that should *not* be escaped.

    Output:

      The escaped string.
    """
    mapping = {
        '\\': r'\textbackslash{}',
        '%': r'\%',
        '$': r'\$',
        '&': r'\&',
        '#': r'\#',
        '_': r'\_',
        '~': r'{\raise.17ex\hbox{$\scriptstyle\sim$}}',
        '{': r'\{',
        '}': r'\}',
    }
    return ''.join(map(lambda x: x if x in iIgnore else mapping.get(x, x), iText))
