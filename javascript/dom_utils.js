function load_xml_document(iUrl) {
    var xhttp;
    if(window.XMLHttpRequest) {
	xhttp = new XMLHttpRequest();
    } else {
	xhttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
    xhttp.open("GET", iUrl, false);
    xhttp.send();
    return xhttp.responseXML;
}

function parse_xml_string(iString) {
    // Internet Explorer uses the loadXML() method to parse an XML
    // string, while other browsers use the DOMParser object.
    var specDom;
    if(window.DOMParser) {
	var parser = new DOMParser();
	specDom = parser.parseFromString(iString, "text/xml");
    } else {
	specDom = new ActiveXObject("Microsoft.XMLDOM");
	specDom.async = false;
	specDom.loadXML(iString);
    }
    return specDom;
}

function dom_to_etree(iDom) {
    // NOTE: This will strip comments
    var child = iDom.firstChild;
    // First phase: set etreeText
    iDom.etreeText = "";
    while(child != null) {
	if(child.nodeType == 1) { // Element => end of first phase
	    break;
	} else if(child.nodeType == 3) { // Text
	    iDom.etreeText += child.data;
	} else if(child.nodeType != 8) { // Comment
	    throw "Unknown node type: " + child.nodeType;
	}
	child = child.nextSibling;
    }
    // Second phase: build array of children and set etreeTail for each of them
    iDom.etreeChildren = new Array();
    while(child != null) {
	if(child.nodeType == 1) { // Element
	    child.etreeTail = "";
	    iDom.etreeChildren.push(child);
	    dom_to_etree(child);
	} else if(child.nodeType == 3) { // Text
	    iDom.etreeChildren[iDom.etreeChildren.length-1].etreeTail += child.data;
	} else if(child.nodeType != 8) { // Comment
	    throw "Unknown node type: " + child.nodeType;
	}
	child = child.nextSibling;
    }
}

function etree_node_find(iNode, iName) {
    var children = iNode.etreeChildren;
    for(var i = 0; i < children.length; i++) {
	var child = children[i];
	if((child.nodeType == 1) && (child.nodeName == iName))
	    return child;
    }
    return null;
}

function etree_node_xpath(iNode, iXpath, iNamespaceResolver) {
    // var xpathResult = document.evaluate(xpathExpression, contextNode, namespaceResolver, resultType, result);
    var dom = iNode.ownerDocument;
    var resultIterator = dom.evaluate(iXpath, iNode, iNamespaceResolver, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
    return resultIterator;
}

function etree_set_node_attribute(iNode, iKey, iValue) {
    var attr = iNode.ownerDocument.createAttribute(iKey);
    attr.nodeValue = iValue;
    iNode.attributes.setNamedItem(attr);
}
