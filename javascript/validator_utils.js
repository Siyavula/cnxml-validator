function get_full_dom_path(iNode, iSpec=null) {
    path = "";
    var node = iNode;
    while(node != iNode.ownerDocument) {
        path = "/" + node.nodeName + path;
        node = node.parentNode;
    }
    return path;
}
