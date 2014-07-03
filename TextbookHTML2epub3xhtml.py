# -*- coding: utf-8 -*-
import sys
import os
import re 

import logging
from lxml import etree

from subprocess import Popen, PIPE

def replace_math_inside_text(text):
    r''' Find and replace math commands inside \text{} environments'''
    operators = [r'\^{.*?}', r'_{.*?}']
    for op in operators:
        mathtext = re.findall(op, text)
        for m in mathtext:
            index = text.find(m)
            if index > 0:
                if text[index-1] != '$':
                    text = text.replace(m, '$%s$' % m )

    return text

def find_and_replace_inline_math(text):
    
    equations = re.findall(r'\\\(.*?\\\)', text)
    for e in equations:
        tex = e[2:-2]
        tex = tex.replace(r'<sup>' , r'$^{').replace(r'</sup>', r'}$')
        tex = tex.replace("&#183;", "$&#183;$")
        math = r'<math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mtext>CLICKME</mtext><annotation encoding="TeX">{tex}</annotation></semantics></math>'.format(tex=tex)
        text = text.replace(e, math)
        text = text.replace(r'~<math', r' <math') 

        # fix ^{blah} inside \text{ } 

        

    return text



def add_namespaces(text):
    '''Given text, search and replace some tags and add the name spaces
    lxml cannot change namespaces after content has been parsed.
    '''
    # <html>
    text = text.replace(r'<html>', r'<html xmlns="http://www.w3.org/1999/xhtml">')

    # <math> tags
    text = text.replace(r'<math>', r'<math xmlns="http://www.w3.org/1998/Math/MathML">')

    return text


def clean(element):
    '''Given an element, clean up its attributes, if necessary'''

    if element.tag == 'div':
        typeattribute = element.attrib.get('type')
        if typeattribute is not None:
            del element.attrib['type']
            element.attrib['data-type'] = typeattribute

    if element.tag == 'table':
        typeattribute = element.attrib.get('summary')
        if typeattribute is not None:
            del element.attrib['summary']
            element.attrib['data-summary'] = typeattribute

    if element.tag == 'math':
        # for every math tag, there is an <annotation> tag that contains the LaTeX
        # find this, write it to a temp file and run tralics on it to get mathml.
        # replace math tag with mathml.
        annotation = element.find('.//annotation')
        annotation.text = replace_math_inside_text(annotation.text)
        if element.tail is None:
            element.tail = ''
        if "begin{align" in annotation.text:
            element.tail = "\[{tex}\]".format(tex=annotation.text) + element.tail
        else:
            element.tail = "\({tex}\)".format(tex=annotation.text) + element.tail

        
    return 
 

if __name__ == "__main__":
    inputfile = sys.argv[1]
    content = add_namespaces(open(inputfile, 'r').read())
    html = etree.HTML(content)
    
    # Find inline \(blah\) tex equations and transform into mathml.
    #htmltext = etree.tostring(html, pretty_print=True, method='xml')
    #htmltext = find_and_replace_inline_math(htmltext)
    #html = etree.HTML(htmltext)
    
    # replace all the Textbook hacked math elements with ones that will work in an epub.
    for element in html.iter():
        clean(element)

    etree.strip_elements(html, 'math', with_tail=False)

    print etree.tostring(html, pretty_print=True, method='xml')



