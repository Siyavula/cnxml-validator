# encoding: utf-8

DEBUG = True


def raise_error(message, element=None, exception=ValueError):
    from lxml import etree
    if element is not None:
        message = message + '\n' + etree.tostring(element).replace(
            ' xmlns:m="http://www.w3.org/1998/Math/MathML" xmlns:md="http://cnx.rice.edu/mdml/0.4" '
            'xmlns:style="http://siyavula.com/cnxml/style/0.1"', '')

    if exception is not None:
        raise exception(message)
    else:
        import sys
        sys.stderr.write('WARNING: ' + message + '\n')


def __replace_unicode_minus(text):
    return text.replace(u'\u2212', '-')


def is_version_number(element):
    text = element.text
    if len(text) == 0:
        raise_error("Version number cannot be empty", element)
    for ch in text:
        if not (('0' <= ch <= '9') or (ch == '.')):
            raise_error("Bad character ({}) in version number".format(repr(ch)), element)
    return True


def is_section_shortcode(element):
    return DEBUG


def is_exercise_shortcode(element):
    return DEBUG


def is_rich_media_shortcode(element):
    return DEBUG


def simulation_has_url_or_embed(element):
    return DEBUG


def is_integer(element):
    if len(element) != 0:
        raise_error("Integer element must have 0 children", element)
    text = element.text if element.text is not None else ''
    try:
        int(__replace_unicode_minus(text))
    except ValueError:
        raise_error("Could not interpret text as an integer", element)
    return True


def is_float(element):
    if len(element) != 0:
        raise_error("Float element must have 0 children", element)
    text = element.text if element.text is not None else ''
    try:
        float(text)
    except ValueError:
        raise_error("Could not interpret text as a float", element)
    return True


def is_valid_html(element):
    if len(element) != 0:
        raise_error("HTML element must have 0 children", element)
    from lxml import etree
    html = element.text if element.text is not None else ''
    etree.fromstring(html)  # Will raise exception if html is invalid
    return True


def is_figure_type(element):
    if len(element) != 0:
        raise_error("Figure type element must have 0 children", element)
    return element.text in ['figure', 'table']


def is_number(element):
    if len(element) == 0:
        # No children, means it's just a plain number: either int or float
        return is_numeric_value(element)
    else:
        # Scientific or exponential notation: parse out coefficient, base and exponent
        allowedChildren = ['base', 'coeff', 'exp']
        children = {}
        inbetweenText = element.text if element.text is not None else ''
        for child in element:
            if child.tag not in allowedChildren:
                raise_error("<number> cannot have a <{}> child".format(child.tag), element)
            if child.tag in children:
                raise_error(
                    "<number> cannot have more than one <{}> child".format(child.tag), element)
            children[child.tag] = child
            text = child.text if child.text is not None else ''
            if text[-3:] == '...':
                text = text[:-3]
            if '|' in text:
                text = text.replace('|', '')
            try:
                float(text)
            except ValueError:
                raise_error(
                    "<{}> of <number> not interpretable as float".format(child.tag), element)
            inbetweenText += child.tail if child.tail is not None else ''
        for tag in allowedChildren:
            if tag not in children:
                children[tag] = None

        if inbetweenText.strip() != '':
            raise_error("<number> with children cannot also contain text", element)

        if (children['coeff'] is None) and (children['exp'] is None):
            raise_error("<number> without <coeff> lacks an <exp>", element)

        if (children['coeff'] is not None and children['exp'] is None and
                children['base'] is not None):
            raise_error("<number> with <coeff> and <base> must have an <exp>", element)

    return True


def is_numeric_value(element):
    text = element.text if element.text is not None else ''
    if '{' in text or '/' in text:
        if '/' in text:
            index = text.find('/')
            numerator = text[:index]
            denominator = text[index + 1:]
        else:
            index = text.find('}')
            numerator = text[6:index]
            denominator = text[index + 2:-1]
        try:
            float(__replace_unicode_minus(numerator))
            float(__replace_unicode_minus(denominator))
        except ValueError:
            raise_error(
                "<number> text {} not interpretable as float for fraction".format(text), element)
    else:
        if text[-3:] == '...':
            text = text[:-3]
        if '|' in text:
            text = text.replace('|', '')
        if '(' in text:
            text = text.replace('(', '')
            text = text.replace(')', '')
        if '[' in text:
            text = text.replace('[', '')
            text = text.replace(']', '')
        try:
            float(__replace_unicode_minus(text))
        except ValueError:
            raise_error("<number> text {} not interpretable as float".format(text), element)
    return True


def is_unit(element):
    if (len(element) == 0) and (element.text.strip() == ''):
        raise_error("<unit> is empty", element)
    for child in element:
        assert child.tag == 'sup'  # From spec.xml we already know that each child is a <sup>
        text = child.text if child.text is not None else ''
        try:
            int(__replace_unicode_minus(text))
        except ValueError:
            raise_error("<sup> of <unit> could not be interpreted as an integer", element)
    return True


def check_link_element(element):
    urlPresent = 'url' in element.attrib
    targetPresent = 'target-id' in element.attrib
    if urlPresent == targetPresent:
        raise_error("<link> must have either url or target-id (but not both)", element)
    if targetPresent and (element.text != ''):
        raise_error("<link> with target-id must not contain text")
    return True


def is_subject(element):
    valid = ['maths', 'science', 'wiskunde', 'wetenskap']
    subject = element.text.strip().lower()
    if subject not in valid:
        raise_error(
            "linked-concepts/concept/subject must be one of {}, found '{}' instead".format(
                valid, element.text))
    return True


def problemset_entry_contains_correct_and_shortcode(iEntryNode):
    assert iEntryNode.tag == 'entry'

    # Skip if this is a standalone exercise
    root = iEntryNode
    while root.getparent() is not None:
        root = root.getparent()
    if root.tag == 'exercise-container':
        return True

    # Count number of <correct> elements
    innerCount = len(iEntryNode.xpath('./solution//correct'))
    outerCount = len(iEntryNode.xpath('./correct'))
    if innerCount + outerCount != 1:
        raise_error(
            "Problem entry must contain exactly one correct element. Found %i inside the solution "
            "and %i outside the solution." % (
                innerCount, outerCount), iEntryNode, exception=None)
    '''
    # Count number of <shortcode> elements
    shortcodes = [element.text for element in iEntryNode.xpath('./shortcode')]
    if len(shortcodes) == 0:
        raise_error("Found problem entry without shortcode.", iEntryNode, exception=None)
    elif len(shortcodes) != 1:
        raise_error(
            "Found problem entry with multiple (%i) shortcodes, namely %s." % (
                count, repr(shortcodes)), iEntryNode, exception=None)
    '''
    return True


def response_entries_count_matches(iResponseNode):
    # TODO
    return True


def is_language_code(iNode):
    return iNode.text.strip() in ['en', 'en-ZA', 'af', 'af-ZA']


def is_iso8601(iNode):
    from dateutil.parser import parse
    string = (iNode.text or '').strip()
    try:
        parse(string)
        return True
    except ValueError:
        raise_error("The ISO8601 timestamp %s is not valid" % repr(string), iNode)
