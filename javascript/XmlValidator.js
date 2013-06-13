function XmlValidator(iSpec) {
    var specDom;
    if(typeof iSpec == "string") {
	specDom = parse_xml_string(iSpec);
    } else if(iSpec instanceof Document) {
	specDom = iSpec;
    } else {
	throw "XML spec needs to be either an XML string or a DOM";
    }
    dom_to_etree(specDom);
    this.spec = specDom.firstChild;
}

XmlValidator.prototype.__get_full_dom_path = function(iNode) {
    return get_full_dom_path(iNode, this.spec);
}

XmlValidator.prototype.__validate_traverse_children_xml = function(iPatternNode) {
    if(iPatternNode == null)
	return null;
    if(iPatternNode.etreeChildren.length == 0) {
        // Leaf: should contain tag name
	var tag = iPatternNode.etreeText.trim();
	if(iPatternNode.nodeName == "reference") {
	    var referenceEntry = etree_node_xpath(this.spec, '/spec/entry[@id="' + tag + '"]', null).iterateNext();
	    return this.__validate_traverse_children_xml(etree_node_find(referenceEntry, "children"));
	} else if(iPatternNode.nodeName == "optional")
	    return "(" + tag + ",)?";
	else
	    return "(" + tag + ",)";
    } else {
	var subPatterns = new Array();
	for(var i = 0; i < iPatternNode.etreeChildren.length; i++)
	    subPatterns.push(this.__validate_traverse_children_xml(iPatternNode.etreeChildren[i]));
	if(iPatternNode.nodeName == "children")
	    return "(" + subPatterns.join("") + ")";
	else if(iPatternNode.nodeName == "optional")
            return "((" + subPatterns.join("") + ")?)";
        else if(iPatternNode.nodeName == "subset-of")
            // TODO: this is currently broken and will also match
            // repetitions of the elements. it will match correct
            // patterns, but will also match some incorrect ones
            return "((" + subPatterns.join("|") + ")*)";
        else if(iPatternNode.nodeName == "any-number") {
	    var x;
	    x = iPatternNode.attributes.getNamedItem("from");
	    if(x == null)
		var from = "0";
	    else
		var from = x.nodeValue;
	    x = iPatternNode.attributes.getNamedItem("to");
	    if(x == null)
		var to = "";
	    else
		var to = x.nodeValue;
            return "((" + subPatterns.join("") + "){" + from + "," + to + "})";
	} else if(iPatternNode.nodeName == "one-of")
            return "(" + subPatterns.join("|") + ")";
	else if(iPatternNode.nodeName == "unordered")
            // TODO: this is currently broken and will also match
            // repetitions of the elements or a subset of the
            // elements. it will match correct patterns, but will also
            // match some incorrect ones
            return "((" + subPatterns.join("|") + ")*)";
        else
            // assert False
            return "(" + subPatterns.join("") + ")";
    }
}

XmlValidator.prototype.__validate_traverse = function(iNode) {
    // Validate children
    for(var i = 0; i < iNode.etreeChildren.length; i++)
	this.__validate_traverse(iNode.etreeChildren[i]);

    // Get associated specification node
    var specEntry = iNode.specEntry;
    if(specEntry == null)
        throw "Unhandled element at " + this.__get_full_dom_path(iNode);

    // Check attributes
    var nodeAttributes = new Array();
    for(var i = 0; i < iNode.attributes.length; i++) {
	var x = iNode.attributes[i];
	if(x.nodeName.slice(0, 6) != 'xmlns:')
	    // Ignore namespace attributes
	    nodeAttributes.push([x.nodeName, x.nodeValue]);
    }
    var specAttributes = etree_node_find(specEntry, "attributes");
    if(specAttributes == null) {
	if(nodeAttributes.length > 0) {
	    if(!(((nodeAttributes.length == 1) && (nodeAttributes[0][0] == "id")) || (iNode.namespaceURI == 'http://www.w3.org/1998/Math/MathML')))
		throw "Extra attributes in " + this.__get_full_dom_path(iNode);
	}
    } else {
	var specAttributesEntries = specAttributes.etreeChildren;
	for(var specAttributesEntriesIndex = 0; specAttributesEntriesIndex < specAttributesEntries.length; specAttributesEntriesIndex++) {
	    var entry = specAttributesEntries[specAttributesEntriesIndex];
	    var attributeName = etree_node_find(entry, "name").etreeText;
	    var attributeType = etree_node_find(entry, "type").etreeText;
	    var attributeValue = null;
	    for(var i = 0; i < nodeAttributes.length; i++)
		if(nodeAttributes[i][0] == attributeName) {
		    // Retrieve attribute value and remove from nodeAttributes array
		    attributeValue = nodeAttributes.splice(i, 1)[0][1];
		    break;
		}

	    if(attributeValue == null) {
                var specDefaultNode = etree_node_find(entry, "default");
                if(specDefaultNode == null)
		    throw "Missing attribute '" + attributeName + "' in " + this.__get_full_dom_path(iNode);
	    } else {
		var passed;
		if(attributeType == "string")
		    passed = true;
		else if(attributeType == "url")
                    // TODO: Make this more strict
                    passed = true;
                else if(attributeType == "number")
		    passed = !isNaN(+(attributeValue));
		else if(attributeType.slice(0, 7) == "integer") {
		    var intValue = +(attributeValue); // Parse attributeValue as number
		    passed = (!isNaN(intValue) && (intValue % 1 == 0)); // Check if number is integer
		    if(passed) {
                        attributeValue = intValue;
                        if(attributeType.length > 7) {
			    intRange = attributeType.slice(8, -1).split(",");
			    for(var i = 0; i < intRange.length; i++) {
				var x = intRange[i].trim();
				if(x == "")
				    x = null;
				else
				    x = +(x);
				intRange[i] = x;
			    }
                            if(intRange[0] != null)
                                if(attributeValue < intRange[0])
                                    passed = false;
                            if(intRange[1] != null)
                                if(attributeValue > intRange[1])
                                    passed = false;
			}
		    }
		} else if(attributeType.slice(0, 5) == "enum(") {
		    var options = eval("[" + attributeType.trim().slice(5, -1) + "]");
                    passed = (options.indexOf(attributeValue) != -1);
		} else {
		    passed = false;
		}
                if(!passed)
		    throw "Attribute value '" + attributeValue + "' does not conform to type '" + attributeType + "' in " + self.__get_full_dom_path(iNode);
	    }
	}
	if(nodeAttributes.length > 0) {
	    // There are still unhandled node attributes
	    var attributeKeys = new Array();
	    for(var i = 0; i < nodeAttributes.length; i++)
		attributeKeys.push(nodeAttributes[i][0]);
	    throw "Unknown attribute(s) '" + attributeKeys.join("', '") + "' in " + this.__get_full_dom_path(iNode);
	}
    }

    // Continue function: Validate children: build regex from spec
    var regex = this.__validate_traverse_children_xml(etree_node_find(specEntry, "children"));
    if(regex == null) {
	// No children
	if(iNode.etreeChildren.length != 0) {
	    var childTags = new Array();
	    for(var i = 0; i < iNode.etreeChildren.length; i++)
		childTags.push(iNode.etreeChildren[i].nodeName);
	    throw "No children expected in " + etree_node_find(iNode.specEntry, "xpath").etreeText + ", but found " + childTags.join(", ") + ".";
	}
    } else {
	var pattern = new RegExp("^" + regex + "$");
        // Validate children: build children pattern
	if(iNode.etreeChildren.length > 0) {
	    var childTags = new Array();
	    for(var i = 0; i < iNode.etreeChildren.length; i++)
		childTags.push(iNode.etreeChildren[i].nodeName);
	    var childrenPattern = childTags.join(",") + ",";
	} else
	    var childrenPattern = "";
	if(!pattern.test(childrenPattern)) {
            throw "Child match failed for a " + etree_node_find(iNode.specEntry, "xpath").etreeText + " element. I was expecting the children to follow this pattern: " + regex + " Instead I got these children: " + childrenPattern;
	}
    }
    // Check that text matches text spec
    if(etree_node_find(specEntry, "notext") != null) {
	var text = iNode.etreeText.trim();
	if(text != "")
	    var location = "at the beginning of the element";
	else {
	    for(var i = 0; i < iNode.etreeChildren.length; i++) {
		var child = iNode.etreeChildren[i];
		text = child.etreeTail.trim();
		if(text != "") {
		    var location = "after a " + child.nodeName + " child";
		    break;
		}
	    }
	}
        if(text != '')
	    throw etree_node_find(iNode.specEntry, "xpath").etreeText + " element must not have any text. Found the following text " + location + ': "' + text + '"';
    }

    // Do validation callback
    var callbackNode = etree_node_find(specEntry, "validation-callback");
    if(callbackNode != null) {
        var callbackFunctionName = callbackNode.etreeText.trim();
        var callbackFunction = eval(callbackFunctionName);
        if(!callbackFunction(iNode))
	    throw 'Validation callback "' + callbackFunctionName + '" failed on the element with path ' + this.__get_full_dom_path(iNode);
    }
    return true;
}

XmlValidator.prototype.validate = function(iXml) {
    var dom;
    if(typeof iXml == "string") {
	dom = parse_xml_string(iXml);
    } else if(iXml instanceof Document) {
	dom = iXml;
    } else {
	throw "XML input needs to be either an XML string or a DOM";
    }
    dom_to_etree(dom);
    dom = dom.etreeChildren[0];

    // Attach relevant spec entries to nodes in the DOM
    var namespaceResolver = this.spec.ownerDocument.createNSResolver(this.spec);
    var specChildren = this.spec.etreeChildren;
    for(var i = 0; i < specChildren.length; i++) {
	var entry = specChildren[i]
	var xpathNode = etree_node_find(entry, "xpath");
        if(xpathNode == null)
	    continue;
	var matchingNodesIterator = etree_node_xpath(dom, xpathNode.etreeText, namespaceResolver);
	var node = matchingNodesIterator.iterateNext();
	while(node) {
	    if(node.specEntry == null)
		node.specEntry = entry;
	    node = matchingNodesIterator.iterateNext();
	}
    }

    // Validate
    this.__validate_traverse(dom);
    this.dom = dom;
    return true;
}
