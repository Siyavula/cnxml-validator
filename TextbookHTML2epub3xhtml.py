# -*- coding: utf-8 -*-
import sys
import os
import re 


from lxml import etree

from subprocess import Popen, PIPE



def find_and_replace_inline_math(text):


    equations = re.findall(r'\\\(.*?\\\)', text)
    for e in equations:
        tex = e[2:-2]
        tex = tex.replace(r'<sup>' , r'$^{').replace(r'</sup>', r'}$')
        tex = tex.replace(r"&#183;", r"$&#183;$")
        math = r'<math xmlns="http://www.w3.org/1998/Math/MathML"><semantics><mtext>CLICKME</mtext><annotation encoding="TeX">{tex}</annotation></semantics></math>'.format(tex=tex)
        text = text.replace(e, math)
    
        

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

        if 'begin' in annotation.text:
            TeX = r'''\documentclass{{article}}
\usepackage{{amsmath, amsthm, amsfonts, amssymb}}
\begin{{document}}
$${formula}$$
\end{{document}}'''.format(formula=annotation.text.replace(r'align*', 'aligned').encode('utf-8'))
        else:
            TeX = r'''\documentclass{{article}}
\usepackage{{amsmath, amsthm, amsfonts, amssymb}}
\begin{{document}}
${formula}$
\end{{document}}'''.format(formula=annotation.text.encode('utf-8'))

        # replace some pesky chars
        TeX = TeX.replace('&#183;', r'\cdot')
        TeX = TeX.replace('&#160;', ' ')
        tempfile = open('tmp.tex', 'w')
        tempfile.write(TeX)
        tempfile.close()
        process = Popen(['tralics', '-noentnames', 'tmp.tex'], stdout=PIPE)
        stdout, stderr = process.communicate()
        xmlfile = etree.parse('tmp.xml')
#       print etree.tostring(xmlfile)
        math = xmlfile.find('.//formula')[0]
        math = etree.tostring(math, pretty_print=True)
        math = math.replace('&#194;', ' ')
        math = etree.XML(math)

        semantics = element.find('.//semantics')
        semantics.clear()
        for m in math:
            semantics.append(m)





    return 
 

if __name__ == "__main__":
    inputfile = sys.argv[1]
    content = add_namespaces(open(inputfile, 'r').read())
    html = etree.HTML(content)
    
    # Find inline \(blah\) tex equations and transform into mathml.
    htmltext = etree.tostring(html, pretty_print=True, method='xml')
    htmltext = find_and_replace_inline_math(htmltext)
    html = etree.HTML(htmltext)
    
    # replace all the Textbook hacked math elements with ones that will work in an epub.
    for element in html.iter():
        clean(element)


    print etree.tostring(html, pretty_print=True, method='xml')



