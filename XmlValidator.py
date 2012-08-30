from __future__ import division
from lxml import etree

import utils


class XmlValidationError(Exception):
    pass


class XmlValidator(object):

    def __init__(self, iSpec):
        if isinstance(iSpec, basestring):
            # This parser automatically strips comments
            parser = etree.ETCompatXMLParser()
            parser.feed(iSpec)
            specDom = parser.close()
        elif isinstance(iSpec, etree._Element):
            specDom = iSpec
        else:
            raise TypeError, "XML spec needs to be either an XML string or a DOM"

        # Normalize text and tail of nodes
        for node in specDom.xpath('//*'):
            if node.text is None:
                node.text = ''
            if node.tail is None:
                node.tail = ''

        self.spec = specDom


    def __tag_prefix_to_namespace(self, iTag):
        return utils.tag_prefix_to_namespace(iTag, iSpec=self.spec)


    def __tag_namespace_to_prefix(self, iTag):
        return utils.tag_namespace_to_prefix(iTag, iSpec=self.spec)


    def __get_full_dom_path(self, iNode):
        return utils.get_full_dom_path(iNode, iSpec=self.spec)


    def __log_warning_message(self, iMessage):
        return utils.warning_message(iMessage)


    def __log_error_message(self, iMessage):
        utils.error_message(iMessage, terminate=False)
        raise XmlValidationError


    def __validate_traverse_children_xml(self, iPatternNode):
        if iPatternNode is None:
            return None
        if len(iPatternNode) == 0:
            # Leaf: should contain tag name
            assert iPatternNode.tag in ['optional', 'element', 'reference'], iPatternNode.tag
            assert iPatternNode.text is not None
            tag = iPatternNode.text.strip()
            assert tag != ''
            if iPatternNode.tag == 'reference':
                referenceEntry = [child for child in self.spec if child.attrib.get('id') == tag][0]
                return self.__validate_traverse_children_xml(referenceEntry.find('children'))
            if iPatternNode.tag == 'optional':
                return '(' + tag + ',)?'
            else:
                return '(' + tag + ',)'
        else:
            assert iPatternNode.tag in ['children', 'optional', 'subset-of', 'any-number', 'one-of', 'unordered'], iPatternNode.tag
            subPatterns = [self.__validate_traverse_children_xml(child) for child in iPatternNode.getchildren()]
            if iPatternNode.tag == 'children':
                return '(' + ''.join(subPatterns) + ')'
            elif iPatternNode.tag == 'optional':
                return '((' + ''.join(subPatterns) + ')?)'
            elif iPatternNode.tag == 'subset-of':
                # TODO: this is currently broken and will also match repetitions of the elements. it will match correct patterns, but will also match some incorrect ones
                return '((' + '|'.join(subPatterns) + ')*)'
            elif iPatternNode.tag == 'any-number':
                return '((' + ''.join(subPatterns) + '){%s,%s})'%(iPatternNode.attrib.get('from', ''), iPatternNode.attrib.get('to', ''))
            elif iPatternNode.tag == 'one-of':
                return '(' + '|'.join(subPatterns) + ')'
            elif iPatternNode.tag == 'unordered':
                # TODO: this is currently broken and will also match repetitions of the elements or a subset of the elements. it will match correct patterns, but will also match some incorrect ones
                return '((' + '|'.join(subPatterns) + ')*)'
            else:
                assert False
                return '(' + ''.join(subPatterns) + ')'


    def __validate_traverse(self, iNode, iCleanUp):
        children = iNode.getchildren()
        for child in children:
            self.__validate_traverse(child, iCleanUp)

        # Get associated specification node
        specEntry = self.documentSpecEntries.get(iNode)
        if specEntry is None:
            self.__log_warning_message('Unhandled element at ' + self.__get_full_dom_path(iNode))
            return # TODO: This will ignore any node without matching xpath in spec. Be more strict later.

        # Check attributes
        nodeAttributes = dict(iNode.attrib)
        for key in nodeAttributes:
            if key[0] == '{': # attribute name has namespace
                value = nodeAttributes[key]
                del nodeAttributes[key]
                nodeAttributes[self.__tag_namespace_to_prefix(key)] = value
        specAttributes = specEntry.find('attributes')
        if specAttributes is None:
            if len(nodeAttributes) > 0:
                if len(iNode.attrib) > 0:
                    if not ((iNode.attrib.keys() == ['id',]) or (iNode.tag[:36] == '{http://www.w3.org/1998/Math/MathML}')):
                        self.__log_warning_message('Extra attributes in ' + self.__get_full_dom_path(iNode) + ': ' + repr(iNode.attrib))
                pass # TODO: This will ignore any nodes that have attributes, even when the spec does not specify any. Make this more strict later to force all attributes to be in the spec.
        else:
            for entry in specAttributes:
                attributeName = entry.find('name').text
                attributeValue = nodeAttributes.get(attributeName)
                if attributeValue is None:
                    specDefaultNode = entry.find('default')
                    if specDefaultNode is None:
                        raise KeyError, "Missing attribute '%s' in %s"%(attributeName, self.__get_full_dom_path(iNode))
                    elif iCleanUp and (specDefaultNode.text != ''):
                        iNode.attrib[self.__tag_prefix_to_namespace(attributeName)] = specDefaultNode.text
                else:
                    # TODO: check that attribute value conforms to spec type
                    del nodeAttributes[attributeName]
            if len(nodeAttributes) > 0:
                # There are still unhandled node attributes
                raise KeyError, "Unknown attribute(s) '%s' in %s"%("', '".join(nodeAttributes.keys()), self.__get_full_dom_path(iNode))

        # Validate children: build regex from spec
        regex = self.__validate_traverse_children_xml(specEntry.find('children'))
        if regex is None:
            # No children
            if len(children) != 0:
                self.__log_error_message('''No children expected in ''' + documentSpecEntries[iNode].find('xpath').text + '''
    *** These are superfluous children:
    ''' + ','.join([self.__tag_namespace_to_prefix(child.tag) for child in children]) + '''
    *** The offending element looks like this:
    ''' + etree.tostring(iNode))
        else:
            import re
            pattern = re.compile('^' + regex + '$')
            # Validate children: build children pattern
            if len(children) > 0:
                childrenPattern = ','.join([self.__tag_namespace_to_prefix(child.tag) for child in children]) + ','
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
                if iCleanUp:
                    iNode.text = None
            if text == '':
                for child in iNode.getchildren():
                    if child.tail is not None:
                        text = child.tail.strip()
                        if text != '':
                            location = 'after a %s child'%child.tag
                            break
                        if iCleanUp:
                            child.tail = None
            if text != '':
                self.__log_error_message(documentSpecEntries[iNode].find('xpath').text + ''' element must not have any text.
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


    def validate(self, iXml, iCleanUp=False):
        if isinstance(iXml, basestring):
            # This parser automatically strips comments
            parser = etree.ETCompatXMLParser()
            parser.feed(iXml)
            dom = parser.close()
        elif isinstance(iXml, etree._Element):
            dom = iXml
        else:
            raise TypeError, "XML input needs to be either an XML string or a DOM"

        # Normalize text and tail of nodes
        self.documentNodePath = {None: []}
        for node in dom.xpath('//*'):
            if node.text is None:
                node.text = ''
            if node.tail is None:
                node.tail = ''
            self.documentNodePath[node] = self.documentNodePath[node.getparent()] + [node.tag]

        # Attach relevant spec entries to nodes in the DOM
        self.documentSpecEntries = {}
        for entry in self.spec:
            if entry.find('xpath') is None:
                continue
            for node in dom.xpath(entry.find('xpath').text, namespaces=self.spec.nsmap):
                if self.documentSpecEntries.get(node) is None:
                    self.documentSpecEntries[node] = entry

        # Validate
        self.__validate_traverse(dom, iCleanUp=iCleanUp)
        self.dom = dom
