function is_version_number(element) {
    text = element.etreeText;
    if(text.length == 0)
        throw "Version number cannot be empty";
    for(var i = 0; i < text.length; i++)
        if(((text[i] < '0') || (text[i] > '9')) && (text[i] != '.'))
            throw "Bad character (" + text[i] + ") in version number";
    return true;
}

function is_section_shortcode(element) {
    // TODO
    return true;
}

function is_exercise_shortcode(element) {
    // TODO
    return true;
}

function is_rich_media_shortcode(element) {
    // TODO
    return true;
}

function simulation_has_url_or_embed(element) {
    // TODO
    return true;
}

function is_integer(element) {
    if(element.etreeChildren.length != 0)
        throw "Integer element must have 0 children";
    var text = element.etreeText;
    var value = +(text);
    if((text == '') || isNaN(value) || (value % 1 != 0))
        throw "Could not interpret text as an integer";
    return true;
}

function is_float(element) {
    if(element.etreeChildren.length != 0)
        throw "Float element must have 0 children";
    var text = element.etreeText;
    if((text == '') || isNaN(+(text)))
        throw "Could not interpret text as a float";
    return true;
}

/*
function is_valid_html(element) {
    if(element.etreeChildren.length != 0)
        throw "HTML element must have 0 children";
    var html = element.etreeText;
    etree.fromstring(html) # Will raise exception if html is invalid
    return True
*/

function is_figure_type(element) {
    if(element.etreeChildren.length != 0)
        throw "Figure type element must have 0 children";
    return ((element.etreeText == 'figure') || (element.etreeText =='table'));
}

function is_number(element) {
    if(element.etreeChildren.length == 0) {
        // No children, means it's just a plain number: either int or float
        var text = element.etreeText;
	if((text == '') || isNaN(+(text)))
            throw "<number> text not interpretable as float";
    } else {
        // Scientific or exponential notation: parse out coefficient, base and exponent
        var allowedChildren = ['base', 'coeff', 'exp'];
        var children = [];
        var inbetweenText = element.etreeText;
	for(var childIndex = 0; childIndex < element.etreeChildren.length; childIndex++) {
	    var child = element.etreeChildren[childIndex];
            if(allowedChildren.indexOf(child.nodeName) == -1)
                throw "<number> cannot have a <" + child.nodeName + "> child";
            if(children.indexOf(child.nodeName) != -1)
                throw "<number> cannot have more than one <" + child.nodeName + "> child";
            children.push(child.nodeName);
            var text = child.etreeText;
	    if((text == '') || isNaN(+(text)))
		throw "<" + child.nodeName + "> of <number> not interpretable as float";
            inbetweenText += child.etreeTail;
	}
        if(inbetweenText.trim() != '')
            throw "<number> with children cannot also contain text";
        if((children.indexOf('coeff') == -1) && (children.indexOf('exp') == -1))
            throw "<number> without <coeff> lacks an <exp>";
        if((children.indexOf('coeff') != -1) && (children.indexOf('exp') == -1) && (children.indexOf('base') != -1))
           throw "<number> with <coeff> and <base> must have an <exp>";
    }
    return true;
}

function is_unit(element) {
    if((element.etreeChildren.length == 0) && (element.etreeText.trim() == ""))
        throw "<unit> is empty";
    for(var childIndex = 0; childIndex < element.etreeChildren.length; childIndex++) {
	var child = element.etreeChildren[childIndex];
        // assert child.tag == 'sup' # From spec.xml we already know that each child is a <sup>
        var text = child.etreeText;
	var value = +(text);
	if((text == '') || isNaN(value) || (value % 1 != 0))
            throw "<sup> of <unit> could not be interpreted as an integer";
    }
    return true;
}

function is_nuclear_notation(element) {
    var children = {};
    var tags = ['symbol', 'mass_number', 'atomic_number'];
    for(var i = 0; i < tags.length; i++) {
	var tag = tags[i];
	children[tag] = etree_node_find(element, tag).etreeText;
    }

    /*
    if children['symbol'] not in periodicTable:
        raise_error("Unknown element symbol %s"%repr(children['symbol']), element)
    */

    tags = ['mass_number', 'atomic_number'];
    for(i = 0; i < tags.length; i++) {
        var text = children[tags[i]];
	var value = +(text);
	if((text == '') || isNaN(value) || (value % 1 != 0))
            throw "Could not interpret <" + tags[i] + "> as integer";
    }

    /*
    if int(children['atomic_number']) != periodicTable[children['symbol']]:
        raise_error("Atomic number does not position in periodic table", element)
    */

    return true;
}

function check_link_element(element) {
    var urlPresent = (element.attributes.getNamedItem("url") != null);
    var targetPresent = (element.attributes.getNamedItem("target-id") != null);
    if(urlPresent == targetPresent)
	throw "<link> must have either url or target-id (but not both)";
    if(targetPresent && (element.etreeText != ""))
        throw "<link> with target-id must not contain text";
    return true;
}

function is_subject(element) {
    valid = ['maths', 'science'];
    subject = element.etreeText.trim().toLowerCase();
    if(valid.indexOf(subject) == -1)
        throw "linked-concepts/concept/subject must be one of [" + valid.join(", ") + "], but found '" + element.etreeText + "' instead";
    return true;
}

function problemset_entry_contains_correct_and_shortcode(iEntryNode) {
    // assert iEntryNode.tag == 'entry'
    // Count number of <correct> elements
    function iterator_length(iterator) {
	var count;
	var node;
	for(count = 0, node = iterator.iterateNext(); node; count += 1, node = iterator.iterateNext());
	return count;
    }
    var innerCount = iterator_length(etree_node_xpath(iEntryNode, "./solution//correct", null));
    var outerCount = iterator_length(etree_node_xpath(iEntryNode, "./correct", null));
    if(innerCount + outerCount != 1)
        throw "Problem entry must contain exactly one correct element. Found " + innerCount + " inside the solution and " + outerCount + " outside the solution.";

    /*
    // Count number of <shortcode> elements
    var shortcodes = [];
    iterator = etree_node_xpath(iEntryNode, "./shortcode", null);
    for(node = iterator.iterateNext(); node; node = iterator.iterateNext())
	shortcodes.push(node.etreeText);
    if(shortcodes.length == 0)
        throw "Found problem entry without shortcode.";
    else if(shortcodes.length != 1)
        throw "Found problem entry with multiple (" + shortcodes.length + ") shortcodes, namely [" + shortcodes.join(", ") + "]";
    */

    return true;
}
