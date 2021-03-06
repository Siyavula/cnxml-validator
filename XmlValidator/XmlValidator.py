from __future__ import division

import os
import re
import utils

from lxml import etree
from termcolor import colored


class XmlValidationError(Exception):
    """Generic exception for any error raised during validation of XML content."""

    pass


class XmlValidator(object):
    """Validate the XML in a given document according to a specific XML rules file."""

    def __init__(self, iSpec):
        self.warnings = []
        self.errors = []

        if isinstance(iSpec, basestring):
            # This parser automatically strips comments
            parser = etree.ETCompatXMLParser()
            parser.feed(iSpec)
            specDom = parser.close()
        elif isinstance(iSpec, etree._Element):
            specDom = iSpec
        else:
            raise TypeError("XML spec needs to be either an XML string or a DOM")

        # Resolve imports
        myPath = os.path.realpath(os.path.dirname(__file__))
        for element in specDom.xpath('/spec/import'):
            path = os.path.join(myPath, element.text.strip())
            with open(path, 'rt') as fp:
                subSpec = XmlValidator(fp.read())
            parent = element.getparent()
            index = parent.index(element)
            parent.remove(element)
            for entry in subSpec.spec:
                parent.insert(index, entry)

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
                try:
                    referenceEntry = [
                        child for child in self.spec if child.attrib.get('id') == tag][0]
                except IndexError:
                    raise ValueError(
                        "Could not find referenced entry {} in specification".format(repr(tag)))
                return self.__validate_traverse_children_xml(referenceEntry.find('children'))
            if iPatternNode.tag == 'optional':
                return '({},)?'.format(tag)
            else:
                return '({},)'.format(tag)
        else:
            assert iPatternNode.tag in [
                'children', 'optional', 'subset-of', 'any-number', 'one-of',
                'unordered'], iPatternNode.tag
            subPatterns = [self.__validate_traverse_children_xml(child) for child
                           in iPatternNode.getchildren()]
            if iPatternNode.tag == 'children':
                return '({})'.format(''.join(subPatterns))
            elif iPatternNode.tag == 'optional':
                return '(({})?)'.format(''.join(subPatterns))
            elif iPatternNode.tag == 'subset-of':
                return '(({})*)'.format('|'.join(subPatterns))
            elif iPatternNode.tag == 'any-number':
                return '((%s){%s,%s})' % (
                    ''.join(subPatterns), iPatternNode.attrib.get('from', ''),
                    iPatternNode.attrib.get('to', ''))
            elif iPatternNode.tag == 'one-of':
                return '({})'.format('|'.join(subPatterns))
            elif iPatternNode.tag == 'unordered':
                # TODO: this is currently broken and will also match repetitions of the
                # elements or a subset of the elements. it will match correct patterns,
                # but will also match some incorrect ones
                return '(({})*)'.format('|'.join(subPatterns))
            else:
                assert False
                return '({})'.format(''.join(subPatterns))

    def __validate_traverse(self, iNode, iCleanUp):
        children = iNode.getchildren()
        for child in children:
            self.__validate_traverse(child, iCleanUp)

        # Get associated specification node
        specEntry = self.documentSpecEntries.get(iNode)
        if specEntry is None:
            self.warnings.append('Unhandled element at {}'.format(self.__get_full_dom_path(iNode)))
            # TODO: This will ignore any node without matching xpath in spec. Be more strict later.
            return

        # Check attributes
        nodeAttributes = dict(iNode.attrib)
        for key in nodeAttributes:
            if key[0] == '{':  # attribute name has namespace
                value = nodeAttributes[key]
                del nodeAttributes[key]
                nodeAttributes[self.__tag_namespace_to_prefix(key)] = value
        specAttributes = specEntry.find('attributes')
        if specAttributes is None:
            if len(nodeAttributes) > 0:
                if not ((nodeAttributes.keys() == ['id', ]) or (
                        iNode.tag[:36] == '{http://www.w3.org/1998/Math/MathML}')):
                    self.errors.append(
                        'Extra attributes in {}; {}'.format(
                            self.__get_full_dom_path(iNode), repr(iNode.attrib)))

        else:
            for entry in specAttributes:
                attributeName = entry.find('name').text
                attributeType = entry.find('type').text
                attributeValue = nodeAttributes.get(attributeName)
                if attributeValue is None:
                    specDefaultNode = entry.find('default')
                    if specDefaultNode is None:
                        self.errors.append("Missing attribute '{}' in {}".format(
                            attributeName, self.__get_full_dom_path(iNode)))
                    elif iCleanUp and (specDefaultNode.text != ''):
                        iNode.attrib[self.__tag_prefix_to_namespace(
                            attributeName)] = specDefaultNode.text
                else:
                    if attributeType == 'string':
                        passed = True
                    elif attributeType == 'url':
                        # TODO: Make this more strict
                        passed = True
                    elif attributeType == 'number':
                        try:
                            float(attributeValue)
                            passed = True
                        except ValueError:
                            passed = False
                    elif attributeType[:7] == 'integer':
                        try:
                            attributeValue = int(attributeValue)
                            passed = True
                            if len(attributeType) > 7:
                                intRange = [x.strip() for x in attributeType[8:-1].split(',')]
                                intRange = [None if x == '' else int(x) for x in intRange]
                                if intRange[0] is not None:
                                    if attributeValue < intRange[0]:
                                        passed = False
                                if intRange[1] is not None:
                                    if attributeValue > intRange[1]:
                                        passed = False
                        except ValueError:
                            passed = False
                    elif attributeType[:5] == 'enum(':
                        options = eval(attributeType[4:])
                        assert type(options) is tuple
                        passed = (attributeValue in options)
                    else:
                        passed = False
                    if not passed:
                        self.errors.append(
                            'Attribute value {} does not conform to type {} in {}'.format(
                                repr(attributeValue), repr(attributeType),
                                self.__get_full_dom_path(iNode)))
                    del nodeAttributes[attributeName]
            if len(nodeAttributes) > 0:
                # There are still unhandled node attributes
                raise KeyError(
                    "Unknown attribute(s) '{}' in {}".format(
                        "', '".join(nodeAttributes.keys()), self.__get_full_dom_path(iNode)))

        # Validate children: build regex from spec
        regex = self.__validate_traverse_children_xml(specEntry.find('children'))
        if regex is None:
            if len(children) != 0:
                self.errors.append(
                    '{main_error}\n'
                    '{children_title}\n{children}\n'
                    '{offending_elements_title}\n{offending_elements}'.format(
                        main_error=colored('No children expected in {}'.format(
                            self.documentSpecEntries[iNode].find('xpath').text), 'red'),
                        children_title=colored('Superfluous children:', 'red'),
                        children=','.join(
                            [self.__tag_namespace_to_prefix(child.tag) for child in children]),
                        offending_elements_title=colored('Offending elements:', 'red'),
                        offending_elements=etree.tostring(iNode)))
        else:
            pattern = re.compile('^' + regex + '$')
            # Validate children: build children pattern
            if len(children) > 0:
                childrenPattern = ','.join(
                    [self.__tag_namespace_to_prefix(child.tag) for child in children]) + ','
            else:
                childrenPattern = ''

            if pattern.match(childrenPattern) is None:
                self.errors.append(
                    '{main_error}\n'
                    '{expecting_title}\n{expecting}\n'
                    '{got_title}\n{got}\n'
                    '{offending_elements_title}\n{offending_elements}\n'.format(
                        main_error=colored('Child match failed for a {} element'.format(
                            self.documentSpecEntries[iNode].find('xpath').text), 'red'),
                        expecting_title=colored('Expecting:', 'red'),
                        expecting=regex,
                        got_title=colored('Got:', 'red'),
                        got=childrenPattern,
                        offending_elements_title=colored('Offending elements:', 'red'),
                        offending_elements=etree.tostring(iNode)))

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
                            location = 'after a {} child'.format(child.tag)
                            break
                        if iCleanUp:
                            child.tail = None
            if text != '':
                self.errors.append(
                    '{main_error}\n'
                    '{found_title} {found}\n'
                    '{offending_elements_title} {offending_elements}'.format(
                        main_error=colored('{} element must not have any text'.format(
                            self.documentSpecEntries[iNode].find('xpath').text), 'red'),
                        found_title=colored('Found {}:'.format(location), 'red'),
                        found=text,
                        offending_elements_title=colored('Offending elements:', 'red'),
                        offending_elements=etree.tostring(iNode)))

        # Do validation callback
        callbackNode = specEntry.find('validation-callback')
        if callbackNode is not None:
            callbackFunctionName = callbackNode.text.strip()
            from . import callbacks  # noqa
            callbackFunction = eval('callbacks.' + callbackFunctionName)
            if not callbackFunction(iNode):
                self.errors.append(
                    "Validation callback {}\n"
                    "failed on the following element:\n{}".format(
                        repr(callbackFunctionName), etree.tostring(iNode)))

    def monassis_to_cnxml(self):
        assert len(
            self.dom.xpath('//monassis-template')) == 0, "monassis-template elements are deprecated"
        for templateNode in self.dom.xpath('//monassis-template'):
            renderer = templateNode.attrib.get('rendered-as', 'exercise')
            if renderer == "example":
                templateNode.tag = 'worked_example'
                titleNode = templateNode[0]
                assert titleNode.tag == 'title'
                contentNode = templateNode[1]
                assert contentNode.tag == 'content'
                index = 0
                if contentNode[index].tag == 'header':
                    headerNode = contentNode[index]
                    index += 1
                else:
                    headerNode = None
                problemNode = contentNode[index]
                index += 1
                assert problemNode.tag == 'problem'
                problemNode.tag = 'question'
                if headerNode is not None:
                    for node in headerNode.getchildren():
                        problemNode.insert(0, node)
                if contentNode[index].tag == 'response':
                    index += 1

                solutionNode = contentNode[index]
                assert solutionNode.tag == 'solution'
                solutionNode.tag = 'answer'
                del templateNode[1]
                templateNode.append(problemNode)
                templateNode.append(solutionNode)
                if solutionNode[0].tag == 'step':
                    for stepNode in solutionNode:
                        assert stepNode.tag == 'step'
                        stepNode.tag = 'workstep'
            elif renderer == "exercise":
                titleNode = templateNode[0]
                assert titleNode.tag == 'title'
                contentNode = templateNode[1]
                assert contentNode.tag == 'content'
                contentNode.tag = 'entry'
                index = 0
                if contentNode[index].tag == 'header':
                    headerNode = contentNode[index]
                    del contentNode[0]
                else:
                    headerNode = None
                problemNode = contentNode[index]
                index += 1
                assert problemNode.tag == 'problem'
                if headerNode is not None:
                    for node in headerNode.getchildren():
                        problemNode.insert(0, node)
                if contentNode[index].tag == 'response':
                    del contentNode[index]

                solutionNode = contentNode[index]
                assert solutionNode.tag == 'solution'
                if (len(solutionNode) > 0) and (solutionNode[0].tag == 'step'):
                    allSolutionChildren = []
                    while len(solutionNode) > 0:
                        assert solutionNode[0].tag == 'step'
                        solutionNodeChildren = solutionNode[0].getchildren()
                        if solutionNodeChildren[0].tag == 'title':
                            del solutionNodeChildren[0]
                        allSolutionChildren += solutionNodeChildren
                        del solutionNode[0]
                    for child in allSolutionChildren:
                        solutionNode.append(child)
                templateNode.getparent().replace(templateNode, contentNode)
            else:
                raise ValueError("Unknown renderer for monassis template: {}".format(renderer))

    def convert_exercises(self, dom):
        for exercisesNode in dom.xpath('//exercises'):
            index = 0
            if exercisesNode[0].tag == 'title':
                index += 1
            if (len(exercisesNode) > index + 1) or (exercisesNode[index].tag != 'problem-set'):
                problemsetNode = etree.Element('problem-set')
                for child in exercisesNode.getchildren()[index:]:
                    problemsetNode.append(child)
                assert len(exercisesNode) == index
                exercisesNode.append(problemsetNode)

    def validate(self, iXml, iCleanUp=False):
        if isinstance(iXml, basestring):
            # This parser automatically strips comments
            parser = etree.ETCompatXMLParser()
            parser.feed(iXml)
            dom = parser.close()
        elif isinstance(iXml, etree._Element):
            dom = iXml
        else:
            raise TypeError("XML input needs to be either an XML string or a DOM")

        # Normalize text and tail of nodes
        self.documentNodePath = {None: []}
        for node in dom.xpath('//*'):
            if node.text is None:
                node.text = ''
            if node.tail is None:
                node.tail = ''
            self.documentNodePath[node] = self.documentNodePath[node.getparent()] + [node.tag]

        # Convert old style <exercises> to new-style <exercises> with recursive <problem-set>s
        # NOTE: This is temporary while we're transitioning to a new
        # XML spec that requires <exercises> to contain <title> and <problem-set> only
        self.convert_exercises(dom)

        # Attach relevant spec entries to nodes in the DOM
        self.documentSpecEntries = {}
        for entry in self.spec:
            xpath = entry.find('xpath')
            if xpath is None:
                continue
            xpath = xpath.text
            for node in dom.xpath(xpath, namespaces=self.spec.nsmap):
                if self.documentSpecEntries.get(node) is None:
                    self.documentSpecEntries[node] = entry
                elif len(xpath.replace('//', '/').split('/')) > len(
                        self.documentSpecEntries.get(node).find('xpath').text.replace(
                            '//', '/').split('/')):
                    # If this xpath is more specific (has more parts to its path) than the
                    # existing one, replace it
                    self.documentSpecEntries[node] = entry

        # Validate
        self.__validate_traverse(dom, iCleanUp=iCleanUp)
        self.dom = dom


class ExerciseValidator(XmlValidator):
    """Validate the XML created in practice exercises."""

    def __init__(self):
        myPath = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(myPath, 'spec_exercise.xml')) as fp:
            super(ExerciseValidator, self).__init__(fp.read())
